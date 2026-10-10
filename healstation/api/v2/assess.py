"""Assessment: emergency fast path inline, full assessment as a job (RES-01, RES-03)."""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from healstation.api.errors import envelope, request_language
from healstation.api.v2.cases import Language, load_case
from healstation.jobs.queue import QueueFull
from healstation.runtime import Runtime, get_runtime
from healstation.security.context import mark_sensitive
from healstation.triage import fast_path
from healstation.triage.vitals import parse_vital_signs_from_text

router = APIRouter(prefix="/api/v2/cases", tags=["assessment"])


class Vitals(BaseModel):
    # Bounds reject impossible values only; critical readings stay accepted.
    heart_rate: int | None = Field(None, ge=0, le=400)
    bp_systolic: int | None = Field(None, ge=0, le=400)
    bp_diastolic: int | None = Field(None, ge=0, le=300)
    spo2: int | None = Field(None, ge=0, le=100)
    temperature: float | None = Field(None, ge=20, le=46, description="°C")
    respiratory_rate: int | None = Field(None, ge=0, le=120)


class AssessRequest(BaseModel):
    symptoms_confirmed: str = Field(..., min_length=1, max_length=20_000)
    vitals: Vitals | None = None
    language: Language | None = None


def _merged_vitals(body: AssessRequest) -> dict:
    structured = (body.vitals or Vitals()).model_dump()
    parsed = parse_vital_signs_from_text(body.symptoms_confirmed)
    return {name: structured.get(name) if structured.get(name) is not None else parsed.get(name) for name in structured}


@router.post("/{case_id}/assess")
def assess(case_id: str, body: AssessRequest, request: Request, runtime: Runtime = Depends(get_runtime)):
    """Run the safety rules now and queue the full assessment.

    The fast path never waits for the queue: when the queue is full the
    response is 429 with ``Retry-After`` and still carries the fast-path result.
    """
    case = load_case(runtime, case_id)
    mark_sensitive(body.symptoms_confirmed)
    language = body.language or case.language
    vitals = _merged_vitals(body)
    fast = fast_path.evaluate(body.symptoms_confirmed, language, vitals)

    digest = hashlib.sha256(
        json.dumps([body.symptoms_confirmed, vitals, language], ensure_ascii=False).encode()
    ).hexdigest()
    assessment_id = runtime.assessments.create(case_id, fast, digest)
    payload = {
        "assessment_id": assessment_id,
        "symptoms": body.symptoms_confirmed,
        "language": language,
        "vitals": vitals,
        "age": case.age,
        "sex": case.sex,
        "fast_path": fast,
    }
    try:
        job_id = runtime.queue.submit("assess", case_id, payload, ref_id=assessment_id)
    except QueueFull as full:
        content = envelope("QUEUE_FULL", request_language(request), full.retry_after_s)
        content.update(fast_path=fast, job_id=None, assessment_id=assessment_id)
        return JSONResponse(status_code=429, content=content, headers={"Retry-After": str(full.retry_after_s)})
    runtime.assessments.attach_job(assessment_id, job_id)
    return {"assessment_id": assessment_id, "fast_path": fast, "job_id": job_id}


@router.get("/{case_id}/assessments")
def list_assessments(case_id: str, runtime: Runtime = Depends(get_runtime)):
    load_case(runtime, case_id)
    return {"assessments": runtime.assessments.list(case_id)}
