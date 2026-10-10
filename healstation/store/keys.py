"""Case keys and field-level encryption (ADR-001)."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from sqlalchemy.orm import Session

from healstation.store.crypto import (
    CryptoError,
    derive_key,
    keyed_digest,
    new_key,
    open_sealed,
    seal,
    unwrap_key,
    wrap_key,
)
from healstation.store.models import CaseKey


class CaseKeyMissing(CryptoError):
    """The case key was destroyed (erased case) or never existed."""


class KeyService:
    def __init__(self, kek: bytes):
        self._kek = kek
        # Sub-key for duplicate detection: content digests cannot be matched
        # against a known file on another installation (ING-07).
        self._digest_key = derive_key(kek, "healstation/attachment-digest/v1")

    def create_case_key(self, session: Session, case_id: str) -> bytes:
        key = new_key()
        session.add(CaseKey(id=case_id, wrapped_key=wrap_key(self._kek, key, f"case:{case_id}")))
        session.flush()  # the case row references this one
        return key

    def case_key(self, session: Session, case_id: str) -> bytes:
        row = session.get(CaseKey, case_id)
        if row is None:
            raise CaseKeyMissing("case key not found")
        return unwrap_key(self._kek, row.wrapped_key, f"case:{case_id}")

    def destroy_case_key(self, session: Session, case_id: str) -> None:
        row = session.get(CaseKey, case_id)
        if row is not None:
            session.delete(row)

    def content_digest(self, data: bytes) -> str:
        return keyed_digest(self._digest_key, data)

    def digest_hasher(self) -> hmac.HMAC:
        """Incremental keyed digest for content hashed while it streams in."""
        return hmac.new(self._digest_key, digestmod=hashlib.sha256)


class FieldSealer:
    """Seals one case's field values; associated data binds each value to its row and column."""

    def __init__(self, case_key: bytes, case_id: str):
        self._key = case_key
        self._case_id = case_id

    def _aad(self, field: str, row_id: str) -> bytes:
        return f"{self._case_id}|{field}|{row_id}".encode()

    def seal_text(self, field: str, row_id: str, value: str | None) -> bytes | None:
        if value is None:
            return None
        return seal(self._key, value.encode("utf-8"), self._aad(field, row_id))

    def open_text(self, field: str, row_id: str, sealed: bytes | None) -> str | None:
        if sealed is None:
            return None
        return open_sealed(self._key, sealed, self._aad(field, row_id)).decode("utf-8")

    def seal_json(self, field: str, row_id: str, value: Any) -> bytes | None:
        if value is None:
            return None
        return self.seal_text(field, row_id, json.dumps(value, ensure_ascii=False, separators=(",", ":")))

    def open_json(self, field: str, row_id: str, sealed: bytes | None) -> Any:
        text = self.open_text(field, row_id, sealed)
        return None if text is None else json.loads(text)
