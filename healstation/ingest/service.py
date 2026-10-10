"""Attachment lifecycle (ING-01..07): receive → quarantine → process → ready, or rejected.

    RECEIVING → QUARANTINED → VALIDATING → SANITIZING → EXTRACTING → READY
                      └──────────── REJECTED (reason code) ─────────┘

Bytes are encrypted as they arrive (ING-03). Rejections during streaming
(type, size, quota) remove every trace of the upload; later rejections keep
only the row with its reason code so the worker can see what happened.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select

from healstation.api.errors import ApiError
from healstation.ingest.filetypes import FileType, TypeRejected, detect
from healstation.settings import Settings
from healstation.store.blobs import BlobWriter
from healstation.store.cases import CaseStore, new_id
from healstation.store.keys import FieldSealer
from healstation.store.models import Attachment, Derivative, utcnow

logger = logging.getLogger("healstation.ingest")

RECEIVING = "RECEIVING"
QUARANTINED = "QUARANTINED"
VALIDATING = "VALIDATING"
SANITIZING = "SANITIZING"
EXTRACTING = "EXTRACTING"
READY = "READY"
REJECTED = "REJECTED"
STAGES = (RECEIVING, QUARANTINED, VALIDATING, SANITIZING, EXTRACTING, READY, REJECTED)
ACTIVE_STAGES = {RECEIVING, QUARANTINED, VALIDATING, SANITIZING, EXTRACTING}

ATTACHMENT_KINDS = {"image", "pdf", "dicom"}
TRANSCRIPTION_KINDS = {"audio"}


@dataclass
class UploadOutcome:
    attachment: Attachment
    duplicate: bool = False


class StorageGuard:
    """Storage budget (RES-05): a quota for case data and a free-disk floor."""

    def __init__(self, settings: Settings, usage: Callable[[], int]):
        self.settings = settings
        self.usage = usage

    def remaining_bytes(self) -> int:
        free = shutil.disk_usage(self.settings.data_dir).free - self.settings.min_free_disk_bytes
        return min(self.settings.storage_quota_bytes - self.usage(), free)

    def check(self) -> int:
        remaining = self.remaining_bytes()
        if remaining <= 0:
            raise ApiError("STORAGE_FULL")
        return remaining


class QuarantineSink:
    """Receives one upload into an encrypted quarantine blob, enforcing limits as it streams."""

    def __init__(
        self,
        service: AttachmentService,
        case_id: str,
        purpose: str,
        allowed_kinds: set[str],
        declared_length: int | None,
    ):
        self.service = service
        self.case_id = case_id
        self.purpose = purpose
        self.allowed_kinds = allowed_kinds
        self.declared_length = declared_length
        self.attachment_id = new_id()
        self.blob_id = new_id()
        self.detected: FileType | None = None
        self.filename = ""
        self.size = 0
        self.limit = 0
        self.remaining = service.storage.check()
        self._writer: BlobWriter | None = None
        self._digest = service.cases.keys.digest_hasher()
        self._row_created = False
        self._finished = False

    def begin(self, header: bytes, filename: str, content_type: str) -> None:
        try:
            self.detected = detect(header, content_type, filename, self.allowed_kinds)
        except TypeRejected as rejected:
            raise ApiError(rejected.code) from None
        self.filename = filename
        self.limit = self.service.limit_for(self.detected.kind)
        # Refuse early when the declared request size already exceeds the limit.
        if self.declared_length is not None and self.declared_length > self.limit + 64 * 1024:
            raise ApiError("FILE_TOO_LARGE")
        key = self.service.cases.key(self.case_id)
        with self.service.cases.db.session() as session:
            session.add(
                Attachment(
                    id=self.attachment_id,
                    case_id=self.case_id,
                    kind=self.detected.kind,
                    purpose=self.purpose,
                    stage=RECEIVING,
                    detected_type=self.detected.label,
                    raw_blob_id=self.blob_id,
                )
            )
        self._row_created = True
        self._writer = self.service.cases.blobs.writer(self.case_id, self.blob_id, key)

    def write(self, data: bytes) -> None:
        self.size += len(data)
        if self.size > self.limit:
            raise ApiError("FILE_TOO_LARGE")
        if self.size > self.remaining:
            raise ApiError("STORAGE_FULL")
        self._digest.update(data)
        self._writer.write(data)

    def finish(self) -> None:
        self._writer.close()
        self._finished = True

    def abort(self) -> None:
        if self._writer is not None and not self._finished:
            self._writer.abort()
        self.service.cases.blobs.delete(self.case_id, self.blob_id)
        if self._row_created:
            with self.service.cases.db.session() as session:
                row = session.get(Attachment, self.attachment_id)
                if row is not None:
                    session.delete(row)

    @property
    def digest(self) -> str:
        return self._digest.hexdigest()


class AttachmentService:
    def __init__(self, cases: CaseStore, settings: Settings, storage: StorageGuard):
        self.cases = cases
        self.settings = settings
        self.storage = storage
        # Called with the attachment row once an upload is quarantined (starts processing).
        self.on_quarantined: Callable[[Attachment], Any] | None = None

    def limit_for(self, kind: str) -> int:
        s = self.settings
        return {
            "audio": s.max_audio_bytes,
            "image": s.max_image_bytes,
            "pdf": s.max_pdf_bytes,
            "dicom": s.max_dicom_upload_bytes,
        }[kind]

    def check_capacity(self, case_id: str, purpose: str) -> None:
        maximum = (
            self.settings.max_recordings_per_case
            if purpose == "transcription"
            else self.settings.max_attachments_per_case
        )
        with self.cases.db.session() as session:
            count = session.scalar(
                select(func.count())
                .select_from(Attachment)
                .where(Attachment.case_id == case_id, Attachment.purpose == purpose, Attachment.stage != REJECTED)
            )
        if count >= maximum:
            raise ApiError("TOO_MANY_ATTACHMENTS")

    def sink(self, case_id: str, purpose: str, declared_length: int | None) -> QuarantineSink:
        self.check_capacity(case_id, purpose)
        allowed = TRANSCRIPTION_KINDS if purpose == "transcription" else ATTACHMENT_KINDS
        return QuarantineSink(self, case_id, purpose, allowed, declared_length)

    def complete(self, sink: QuarantineSink) -> UploadOutcome:
        """After the stream finished: de-duplicate (ING-07), then mark QUARANTINED."""
        sealer = self.cases.sealer(sink.case_id)
        digest = sink.digest
        with self.cases.db.session() as session:
            existing = session.scalars(
                select(Attachment).where(
                    Attachment.case_id == sink.case_id,
                    Attachment.content_digest == digest,
                    Attachment.purpose == sink.purpose,
                    Attachment.stage != REJECTED,
                    Attachment.id != sink.attachment_id,
                )
            ).first()
        if existing is not None:
            sink.abort()
            return UploadOutcome(existing, duplicate=True)
        with self.cases.db.session() as session:
            row = session.get(Attachment, sink.attachment_id)
            row.stage = QUARANTINED
            row.size_bytes = sink.size
            row.content_digest = digest
            row.original_name_enc = sealer.seal_text("attachments.original_name", row.id, sink.filename)
            attachment = row
        logger.info("Upload quarantined", extra={"hs": {"kind": attachment.kind, "size_bytes": sink.size}})
        if self.on_quarantined is not None:
            self.on_quarantined(attachment)
        return UploadOutcome(attachment)

    # ── reading and changing state ───────────────────────────────────────────
    def get(self, case_id: str, attachment_id: str) -> Attachment | None:
        with self.cases.db.session() as session:
            row = session.get(Attachment, attachment_id)
            return row if row is not None and row.case_id == case_id else None

    def list(self, case_id: str, purpose: str | None = None) -> list[Attachment]:
        with self.cases.db.session() as session:
            query = select(Attachment).where(Attachment.case_id == case_id).order_by(Attachment.created_at)
            if purpose:
                query = query.where(Attachment.purpose == purpose)
            return list(session.scalars(query).all())

    def set_stage(
        self,
        attachment_id: str,
        stage: str,
        *,
        progress: float | None = None,
        reason_code: str | None = None,
        job_id: str | None = None,
    ) -> None:
        with self.cases.db.session() as session:
            row = session.get(Attachment, attachment_id)
            if row is None:
                return
            row.stage = stage
            if progress is not None:
                row.progress = progress
            if reason_code is not None:
                row.reason_code = reason_code
            if job_id is not None:
                row.job_id = job_id
            row.updated_at = utcnow()

    def set_summary(self, case_id: str, attachment_id: str, summary: dict) -> None:
        sealer = self.cases.sealer(case_id)
        with self.cases.db.session() as session:
            row = session.get(Attachment, attachment_id)
            if row is not None:
                row.summary_enc = sealer.seal_json("attachments.summary", attachment_id, summary)

    def summary(self, case_id: str, attachment: Attachment) -> dict | None:
        if attachment.summary_enc is None:
            return None
        return self.cases.sealer(case_id).open_json("attachments.summary", attachment.id, attachment.summary_enc)

    def delete_raw(self, attachment: Attachment) -> None:
        """Delete the original upload once extraction is done (INV-6)."""
        if attachment.raw_blob_id is None or self.settings.retain_raw_uploads:
            return
        self.cases.blobs.delete(attachment.case_id, attachment.raw_blob_id)
        with self.cases.db.session() as session:
            row = session.get(Attachment, attachment.id)
            if row is not None:
                row.raw_blob_id = None

    def reject(self, attachment: Attachment, reason_code: str) -> None:
        """Keep only the outcome: the upload and anything derived from it are deleted."""
        self._delete_files(attachment)
        with self.cases.db.session() as session:
            for derivative in session.scalars(select(Derivative).where(Derivative.attachment_id == attachment.id)):
                session.delete(derivative)
            row = session.get(Attachment, attachment.id)
            if row is not None:
                row.stage = REJECTED
                row.reason_code = reason_code
                row.raw_blob_id = None
                row.summary_enc = None
        logger.info("Upload rejected", extra={"hs": {"kind": attachment.kind, "reason_code": reason_code}})

    def delete(self, attachment: Attachment) -> None:
        self._delete_files(attachment)
        with self.cases.db.session() as session:
            row = session.get(Attachment, attachment.id)
            if row is not None:
                session.delete(row)

    def _delete_files(self, attachment: Attachment) -> None:
        with self.cases.db.session() as session:
            blob_ids = [
                d.blob_id
                for d in session.scalars(select(Derivative).where(Derivative.attachment_id == attachment.id))
                if d.blob_id
            ]
        for blob_id in [*blob_ids, attachment.raw_blob_id]:
            if blob_id:
                self.cases.blobs.delete(attachment.case_id, blob_id)

    # ── derivatives ──────────────────────────────────────────────────────────
    def add_derivative(
        self,
        attachment: Attachment,
        type_: str,
        *,
        content: Any = None,
        data: bytes | None = None,
        model_version: str | None = None,
    ) -> str:
        derivative_id = new_id()
        sealer = FieldSealer(self.cases.key(attachment.case_id), attachment.case_id)
        blob_id = None
        if data is not None:
            blob_id = new_id()
            self.cases.blobs.write_bytes(attachment.case_id, blob_id, self.cases.key(attachment.case_id), data)
        with self.cases.db.session() as session:
            session.add(
                Derivative(
                    id=derivative_id,
                    attachment_id=attachment.id,
                    case_id=attachment.case_id,
                    type=type_,
                    content_enc=sealer.seal_json("derivatives.content", derivative_id, content),
                    blob_id=blob_id,
                    model_version=model_version,
                )
            )
        return derivative_id

    def derivatives(self, case_id: str, attachment_id: str | None = None, type_: str | None = None) -> list[dict]:
        sealer = self.cases.sealer(case_id)
        with self.cases.db.session() as session:
            query = select(Derivative).where(Derivative.case_id == case_id).order_by(Derivative.created_at)
            if attachment_id:
                query = query.where(Derivative.attachment_id == attachment_id)
            if type_:
                query = query.where(Derivative.type == type_)
            rows = list(session.scalars(query).all())
        return [
            {
                "id": row.id,
                "attachment_id": row.attachment_id,
                "type": row.type,
                "content": sealer.open_json("derivatives.content", row.id, row.content_enc),
                "blob_id": row.blob_id,
                "model_version": row.model_version,
            }
            for row in rows
        ]
