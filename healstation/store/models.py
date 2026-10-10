"""Database tables (PRD §8). Columns ending in ``_enc`` hold AES-GCM ciphertext
sealed with the case key; everything else is non-clinical metadata.

Schema changes go through an Alembic migration in ``store/migrations/versions``;
``tests/test_store.py`` checks the migrations and these models agree.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class CaseKey(Base):
    """A case's data key, wrapped by the KEK. Deleting the row crypto-shreds the case."""

    __tablename__ = "case_keys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    wrapped_key: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    pseudonym: Mapped[str | None] = mapped_column(String(16), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
    language: Mapped[str] = mapped_column(String(8), default="en")
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(16))
    area_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    abha_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_by: Mapped[str | None] = mapped_column(String(32))
    facility_id: Mapped[str | None] = mapped_column(String(64))
    key_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("case_keys.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    erased_at: Mapped[datetime | None] = mapped_column(DateTime)


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("ix_attachments_case_digest", "case_id", "content_digest"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # audio | image | pdf | dicom
    purpose: Mapped[str] = mapped_column(String(16), default="attachment")  # attachment | transcription
    stage: Mapped[str] = mapped_column(String(16))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    reason_code: Mapped[str | None] = mapped_column(String(40))
    detected_type: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # HMAC-SHA256 of the content under a per-install key (ING-07).
    content_digest: Mapped[str | None] = mapped_column(String(64))
    original_name_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    summary_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    # Blob id of the raw upload while it still exists (deleted after extraction).
    raw_blob_id: Mapped[str | None] = mapped_column(String(32))
    job_id: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Derivative(Base):
    __tablename__ = "derivatives"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    attachment_id: Mapped[str] = mapped_column(String(32), ForeignKey("attachments.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[str] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    # transcript | text | lab_table | summary | sanitized_image | key_image | observations
    type: Mapped[str] = mapped_column(String(32))
    content_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    blob_id: Mapped[str | None] = mapped_column(String(32))
    model_version: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(String(32))
    inputs_digest: Mapped[str | None] = mapped_column(String(64))
    fast_path_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    result_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    # Kept in plaintext for de-identified quality metrics (PRD §8).
    urgency: Mapped[str | None] = mapped_column(String(16))
    sources_json: Mapped[str | None] = mapped_column(Text)
    versions_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(String(32))
    resource: Mapped[str] = mapped_column(String(16))
    case_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    ref_id: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), index=True)
    stage: Mapped[str | None] = mapped_column(String(32))
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2)
    timeout_s: Mapped[float] = mapped_column(Float)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_code: Mapped[str | None] = mapped_column(String(40))
    payload_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    result_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class IdempotencyKey(Base):
    """Stored responses for retried POSTs (API-04)."""

    __tablename__ = "idempotency_keys"

    scope: Mapped[str] = mapped_column(String(128), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    case_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("cases.id", ondelete="CASCADE"))
    status_code: Mapped[int] = mapped_column(Integer)
    response_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    response_plain: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
