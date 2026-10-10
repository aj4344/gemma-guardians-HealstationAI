"""Case records (CASE-01) and erasure (PRIV-03)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field, field_validator

from healstation.api.errors import ApiError
from healstation.runtime import Runtime, get_runtime
from healstation.security.context import mark_sensitive
from healstation.store.cases import CaseNotFound, normalize_abha_number
from healstation.store.models import Case

router = APIRouter(prefix="/api/v2/cases", tags=["cases"])

ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
Language = Literal["en", "hi", "mr"]
Sex = Literal["female", "male", "other", "unknown"]


def load_case(runtime: Runtime, case_id: str) -> Case:
    """The open case with this id, or NOT_FOUND (also for malformed and erased ids)."""
    if not ID_PATTERN.fullmatch(case_id):
        raise ApiError("NOT_FOUND")
    try:
        return runtime.cases.get(case_id)
    except CaseNotFound:
        raise ApiError("NOT_FOUND") from None


class CaseCreate(BaseModel):
    language: Language = "en"
    age: int | None = Field(None, ge=0, le=130)
    sex: Sex | None = None
    area: str | None = Field(None, max_length=120)
    abha_number: str | None = Field(None, max_length=20)

    @field_validator("abha_number")
    @classmethod
    def _abha(cls, value: str | None) -> str | None:
        return normalize_abha_number(value) if value else None


class CaseCreated(BaseModel):
    case_id: str
    pseudonym: str
    language: Language
    created_at: datetime
    expires_at: datetime


class CaseView(CaseCreated):
    age: int | None = None
    sex: Sex | None = None
    area: str | None = None
    abha_number: str | None = None


@router.post("", status_code=201, response_model=CaseCreated)
def create_case(body: CaseCreate | None = None, runtime: Runtime = Depends(get_runtime)):
    body = body or CaseCreate()
    mark_sensitive(body.area)
    case = runtime.cases.create(
        language=body.language, age=body.age, sex=body.sex, area=body.area, abha_number=body.abha_number
    )
    return CaseCreated(
        case_id=case.id,
        pseudonym=case.pseudonym,
        language=case.language,
        created_at=case.created_at,
        expires_at=case.expires_at,
    )


@router.get("/{case_id}", response_model=CaseView)
def get_case(case_id: str, runtime: Runtime = Depends(get_runtime)):
    case = load_case(runtime, case_id)
    details = runtime.cases.details(case)
    return CaseView(
        case_id=case.id,
        pseudonym=case.pseudonym,
        language=case.language,
        created_at=case.created_at,
        expires_at=case.expires_at,
        age=case.age,
        sex=case.sex,
        **details,
    )


@router.delete("/{case_id}", status_code=204)
def erase_case(case_id: str, runtime: Runtime = Depends(get_runtime)):
    """End the visit and erase everything about this case (crypto-shred)."""
    load_case(runtime, case_id)
    runtime.cases.erase(case_id)
    return Response(status_code=204)
