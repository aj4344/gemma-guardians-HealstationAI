"""Version 2 HTTP API: cases, streaming uploads, jobs (PRD §6.11)."""

from fastapi import APIRouter

from healstation.api.v2 import attachments, cases

router = APIRouter()
router.include_router(cases.router)
router.include_router(attachments.router)
