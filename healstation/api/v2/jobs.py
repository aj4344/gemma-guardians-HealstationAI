"""Job status (RES-02, RES-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from healstation.api.errors import REASON_CODES, ApiError, localized, request_language
from healstation.api.v2.cases import ID_PATTERN
from healstation.runtime import Runtime, get_runtime
from healstation.store.models import Job

router = APIRouter(prefix="/api/v2/jobs", tags=["jobs"])


def job_view(runtime: Runtime, job: Job, language: str) -> dict:
    view = {
        "job_id": job.id,
        "type": job.type,
        "status": job.status,
        "stage": job.stage,
        "progress": round(job.progress or 0.0, 3),
        "attempts": job.attempts,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
    if job.error_code and job.error_code in REASON_CODES:
        view["error"] = {
            "code": job.error_code,
            "message_localized": localized(job.error_code, language),
            "retryable": REASON_CODES[job.error_code].retryable,
        }
    result = runtime.queue.result(job)
    if result is not None:
        view["result"] = result
    return view


def load_job(runtime: Runtime, job_id: str) -> Job:
    job = runtime.queue.get(job_id) if ID_PATTERN.fullmatch(job_id) else None
    if job is None or job.case_id is None:
        raise ApiError("NOT_FOUND")
    try:
        runtime.cases.get(job.case_id)
    except LookupError:
        raise ApiError("NOT_FOUND") from None
    return job


@router.get("/{job_id}")
def get_job(job_id: str, request: Request, runtime: Runtime = Depends(get_runtime)):
    return job_view(runtime, load_job(runtime, job_id), request_language(request))
