"""Case records (CASE-01) and erasure by crypto-shredding (PRIV-03)."""

from __future__ import annotations

import logging
import re
import secrets
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from healstation.settings import Settings
from healstation.store.blobs import BlobStore
from healstation.store.db import Database
from healstation.store.keys import FieldSealer, KeyService
from healstation.store.models import (
    Assessment,
    Attachment,
    Case,
    Derivative,
    IdempotencyKey,
    Job,
    Visit,
    utcnow,
)

logger = logging.getLogger("healstation.store")

SEXES = {"female", "male", "other", "unknown"}
# Crockford base32 without I, L, O, U: easy to read aloud and copy by hand.
_PSEUDONYM_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ABHA_NUMBER = re.compile(r"^\d{2}-?\d{4}-?\d{4}-?\d{4}$")


class CaseNotFound(LookupError):
    pass


def new_id() -> str:
    return uuid.uuid4().hex


def new_pseudonym() -> str:
    chars = "".join(secrets.choice(_PSEUDONYM_ALPHABET) for _ in range(8))
    return f"HS-{chars[:4]}-{chars[4:]}"


def normalize_abha_number(value: str) -> str:
    """ABHA numbers are 14 digits, usually written XX-XXXX-XXXX-XXXX."""
    text = value.strip()
    if not _ABHA_NUMBER.fullmatch(text):
        raise ValueError("ABHA number must be 14 digits (XX-XXXX-XXXX-XXXX)")
    digits = text.replace("-", "")
    return f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}-{digits[10:]}"


class CaseStore:
    def __init__(
        self,
        db: Database,
        keys: KeyService,
        blobs: BlobStore,
        settings: Settings,
        clock: Callable[[], datetime] = utcnow,
    ):
        self.db = db
        self.keys = keys
        self.blobs = blobs
        self.settings = settings
        self.clock = clock

    def create(
        self,
        *,
        language: str = "en",
        age: int | None = None,
        sex: str | None = None,
        area: str | None = None,
        abha_number: str | None = None,
        created_by: str | None = None,
        facility_id: str | None = None,
    ) -> Case:
        now = self.clock()
        for _attempt in range(5):
            case_id = new_id()
            try:
                with self.db.session() as session:
                    key = self.keys.create_case_key(session, case_id)
                    sealer = FieldSealer(key, case_id)
                    case = Case(
                        id=case_id,
                        pseudonym=new_pseudonym(),
                        language=language,
                        age=age,
                        sex=sex,
                        area_enc=sealer.seal_text("cases.area", case_id, area),
                        abha_enc=sealer.seal_text("cases.abha", case_id, abha_number),
                        created_by=created_by,
                        facility_id=facility_id,
                        key_id=case_id,
                        created_at=now,
                        updated_at=now,
                        expires_at=now + timedelta(days=self.settings.case_retention_days),
                    )
                    session.add(case)
                    session.add(Visit(id=new_id(), case_id=case_id, started_at=now))
                return case
            except IntegrityError as error:
                if "pseudonym" not in str(error.orig):
                    raise
                continue  # pseudonym collision; try another
        raise RuntimeError("could not allocate a unique case pseudonym")

    def get(self, case_id: str) -> Case:
        with self.db.session() as session:
            case = session.get(Case, case_id)
            if case is None or case.status != "open":
                raise CaseNotFound(case_id)
            return case

    def key(self, case_id: str) -> bytes:
        with self.db.session() as session:
            return self.keys.case_key(session, case_id)

    def sealer(self, case_id: str) -> FieldSealer:
        return FieldSealer(self.key(case_id), case_id)

    def details(self, case: Case) -> dict:
        sealer = self.sealer(case.id)
        return {
            "area": sealer.open_text("cases.area", case.id, case.area_enc),
            "abha_number": sealer.open_text("cases.abha", case.id, case.abha_enc),
        }

    def erase(self, case_id: str) -> bool:
        """Crypto-shred a case: destroy its key, then delete its rows and files.

        The key goes first and is committed before anything else, so a crash
        part-way leaves only unreadable ciphertext for the sweeper to remove.
        """
        with self.db.session() as session:
            case = session.get(Case, case_id)
            if case is None or case.status == "erased":
                return False
            self.keys.destroy_case_key(session, case_id)
            case.key_id = None
        with self.db.session() as session:
            for model in (IdempotencyKey, Derivative, Assessment, Job, Attachment, Visit):
                session.execute(delete(model).where(model.case_id == case_id))
            case = session.get(Case, case_id)
            case.status = "erased"
            case.erased_at = self.clock()
            case.pseudonym = None
            case.age = None
            case.sex = None
            case.area_enc = None
            case.abha_enc = None
            case.created_by = None
        self.blobs.delete_case(case_id)
        logger.info("Case erased", extra={"hs": {"event": "case_erased"}})
        return True

    def expired_case_ids(self) -> list[str]:
        with self.db.session() as session:
            rows = session.scalars(select(Case.id).where(Case.status == "open", Case.expires_at <= self.clock())).all()
        return list(rows)

    def erased_case_ids(self) -> set[str]:
        with self.db.session() as session:
            return set(session.scalars(select(Case.id).where(Case.status == "erased")).all())

    def open_case_ids(self) -> set[str]:
        with self.db.session() as session:
            return set(session.scalars(select(Case.id).where(Case.status == "open")).all())
