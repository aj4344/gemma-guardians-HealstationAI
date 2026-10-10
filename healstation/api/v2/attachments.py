"""Attachment uploads, status and deletion (ING-01..07)."""

from __future__ import annotations

import anyio
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from healstation.api.errors import ApiError, localized, request_language
from healstation.api.v2.cases import ID_PATTERN, load_case
from healstation.ingest.multipart import receive_single_file
from healstation.runtime import Runtime, get_runtime
from healstation.security.context import mark_sensitive
from healstation.store.models import Attachment

router = APIRouter(prefix="/api/v2/cases", tags=["attachments"])


def declared_length(request: Request) -> int | None:
    value = request.headers.get("content-length", "")
    return int(value) if value.isdigit() else None


def attachment_view(runtime: Runtime, attachment: Attachment, language: str, *, duplicate: bool = False) -> dict:
    """Status of one upload. Never includes the filename or any file bytes (ING-05)."""
    view = {
        "attachment_id": attachment.id,
        "kind": attachment.kind,
        "purpose": attachment.purpose,
        "stage": attachment.stage,
        "progress": round(attachment.progress or 0.0, 3),
        "detected_type": attachment.detected_type,
        "size_bytes": attachment.size_bytes,
        "job_id": attachment.job_id,
        "created_at": attachment.created_at.isoformat(),
        "updated_at": attachment.updated_at.isoformat(),
    }
    if attachment.reason_code:
        view["reason_code"] = attachment.reason_code
        view["message_localized"] = localized(attachment.reason_code, language)
    summary = runtime.attachments.summary(attachment.case_id, attachment)
    if summary:
        view["summary"] = summary
    if duplicate:
        view["duplicate"] = True
    return view


async def receive_upload(request: Request, runtime: Runtime, case_id: str, purpose: str):
    await anyio.to_thread.run_sync(load_case, runtime, case_id)
    sink = await anyio.to_thread.run_sync(runtime.attachments.sink, case_id, purpose, declared_length(request))
    fields = await receive_single_file(request, sink)
    mark_sensitive(sink.filename)
    outcome = await anyio.to_thread.run_sync(runtime.attachments.complete, sink)
    return outcome, fields


@router.post("/{case_id}/attachments", status_code=202)
async def upload_attachment(case_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    """Upload one file (multipart field `file`): a photo, a PDF, a DICOM file or a ZIP of a series."""
    outcome, _fields = await receive_upload(request, runtime, case_id, "attachment")
    view = await anyio.to_thread.run_sync(
        lambda: attachment_view(runtime, outcome.attachment, request_language(request), duplicate=outcome.duplicate)
    )
    return JSONResponse(status_code=200 if outcome.duplicate else 202, content=view)


def _load_attachment(runtime: Runtime, case_id: str, attachment_id: str) -> Attachment:
    load_case(runtime, case_id)
    attachment = runtime.attachments.get(case_id, attachment_id) if ID_PATTERN.fullmatch(attachment_id) else None
    if attachment is None:
        raise ApiError("NOT_FOUND")
    return attachment


@router.get("/{case_id}/attachments")
def list_attachments(case_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    load_case(runtime, case_id)
    language = request_language(request)
    return {
        "attachments": [
            attachment_view(runtime, a, language) for a in runtime.attachments.list(case_id, purpose="attachment")
        ]
    }


@router.get("/{case_id}/attachments/{attachment_id}")
def get_attachment(case_id: str, attachment_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    attachment = _load_attachment(runtime, case_id, attachment_id)
    return attachment_view(runtime, attachment, request_language(request))


@router.delete("/{case_id}/attachments/{attachment_id}", status_code=204)
def delete_attachment(case_id: str, attachment_id: str, runtime: Runtime = Depends(get_runtime)):
    attachment = _load_attachment(runtime, case_id, attachment_id)
    runtime.attachments.delete(attachment)
    return Response(status_code=204)
