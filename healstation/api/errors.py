"""Uniform v2 error envelope (API-02) and the reason codes of PRD Appendix B.

Every v2 error response is::

    {"error": {"code", "message_localized", "retryable", "retry_after_s"?}, "request_id"}

Messages are fixed, localized strings. Exception text never reaches a client.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from healstation.api.messages import ERROR_MESSAGES
from healstation.security.context import current_request_id

LANGUAGES = ("en", "hi", "mr")


@dataclass(frozen=True)
class ReasonCode:
    status: int
    retryable: bool = False


REASON_CODES: dict[str, ReasonCode] = {
    # Appendix B — upload and processing outcomes
    "FILE_TOO_LARGE": ReasonCode(413),
    "UNSUPPORTED_TYPE": ReasonCode(415),
    "TYPE_MISMATCH": ReasonCode(415),
    "POLYGLOT_FILE": ReasonCode(415),
    "CORRUPT_FILE": ReasonCode(422),
    "AUDIO_TOO_LONG": ReasonCode(413),
    "AUDIO_NO_SPEECH": ReasonCode(422),
    "IMAGE_TOO_LARGE": ReasonCode(413),
    "PDF_ENCRYPTED": ReasonCode(422),
    "PDF_TOO_MANY_PAGES": ReasonCode(413),
    "PDF_UNREADABLE": ReasonCode(422),
    "ZIP_BOMB": ReasonCode(413),
    "ZIP_PATH_TRAVERSAL": ReasonCode(422),
    "DICOM_UNSUPPORTED_SOP": ReasonCode(415),
    "DICOM_UNSUPPORTED_SYNTAX": ReasonCode(415),
    "DICOM_DEID_FAILED": ReasonCode(422),
    "BURNED_IN_PHI_UNMASKED": ReasonCode(422),
    "MALWARE_DETECTED": ReasonCode(422),
    "QUEUE_FULL": ReasonCode(429, retryable=True),
    "STORAGE_FULL": ReasonCode(507),
    "JOB_TIMED_OUT": ReasonCode(504, retryable=True),
    "MODEL_UNAVAILABLE": ReasonCode(503, retryable=True),
    # Request handling
    "BAD_REQUEST": ReasonCode(400),
    "VALIDATION_ERROR": ReasonCode(422),
    "REQUEST_TOO_LARGE": ReasonCode(413),
    "NO_FILE": ReasonCode(400),
    "MULTIPLE_FILES": ReasonCode(400),
    "EMPTY_FILE": ReasonCode(400),
    "TOO_MANY_ATTACHMENTS": ReasonCode(409),
    "INVALID_IDEMPOTENCY_KEY": ReasonCode(400),
    "IDEMPOTENCY_CONFLICT": ReasonCode(409),
    "NOT_FOUND": ReasonCode(404),
    "METHOD_NOT_ALLOWED": ReasonCode(405),
    "STT_UNAVAILABLE": ReasonCode(503, retryable=True),
    "JOB_FAILED": ReasonCode(500, retryable=True),
    "JOB_INTERRUPTED": ReasonCode(500, retryable=True),
    "INTERNAL_ERROR": ReasonCode(500, retryable=True),
    # Identity and consent (Mode B)
    "UNAUTHORIZED": ReasonCode(401),
    "FORBIDDEN": ReasonCode(403),
    "CSRF_FAILED": ReasonCode(403),
    "RATE_LIMITED": ReasonCode(429, retryable=True),
    "ACCOUNT_LOCKED": ReasonCode(423),
    "CONSENT_REQUIRED": ReasonCode(409),
}


class ApiError(Exception):
    """Raised by v2 handlers; rendered as the error envelope."""

    def __init__(self, code: str, *, status: int | None = None, retry_after_s: int | None = None, **extra):
        if code not in REASON_CODES:
            raise ValueError(f"unknown reason code {code}")
        super().__init__(code)
        self.code = code
        self.status = status or REASON_CODES[code].status
        self.retry_after_s = retry_after_s
        # Extra non-PHI fields merged into the envelope (e.g. the fast-path result).
        self.extra = extra


def request_language(request: Request) -> str:
    explicit = request.headers.get("x-healstation-language", "").strip().lower()
    if explicit[:2] in LANGUAGES:
        return explicit[:2]
    for part in request.headers.get("accept-language", "").split(","):
        tag = part.split(";", 1)[0].strip().lower()[:2]
        if tag in LANGUAGES:
            return tag
    return "en"


def localized(code: str, language: str) -> str:
    messages = ERROR_MESSAGES.get(code) or ERROR_MESSAGES["INTERNAL_ERROR"]
    return messages.get(language) or messages["en"]


def envelope(code: str, language: str, retry_after_s: int | None = None) -> dict:
    error = {
        "code": code,
        "message_localized": localized(code, language),
        "retryable": REASON_CODES[code].retryable,
    }
    if retry_after_s is not None:
        error["retry_after_s"] = retry_after_s
    return {"error": error, "request_id": current_request_id()}


def error_response(
    request: Request, code: str, status: int | None = None, retry_after_s: int | None = None, extra=None
) -> JSONResponse:
    body = envelope(code, request_language(request), retry_after_s)
    body.update(extra or {})
    headers = {"Retry-After": str(retry_after_s)} if retry_after_s is not None else None
    return JSONResponse(status_code=status or REASON_CODES[code].status, content=body, headers=headers)


def _is_v2(request: Request) -> bool:
    return request.url.path.startswith("/api/v2")


_STATUS_CODES = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}


def install_error_handlers(app: FastAPI) -> None:
    from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, error: ApiError):
        return error_response(request, error.code, error.status, error.retry_after_s, error.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError):
        if not _is_v2(request):
            return await request_validation_exception_handler(request, error)
        # Field locations only; the submitted values may be patient data.
        fields = sorted({".".join(str(p) for p in item.get("loc", ())[1:]) for item in error.errors()})
        return error_response(request, "VALIDATION_ERROR", extra={"fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, error: StarletteHTTPException):
        if not _is_v2(request):
            return await http_exception_handler(request, error)
        return error_response(request, _STATUS_CODES.get(error.status_code, "INTERNAL_ERROR"), error.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, error: Exception):
        import logging

        logging.getLogger("healstation.api").error("Unhandled error", exc_info=error)
        if not _is_v2(request):
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        return error_response(request, "INTERNAL_ERROR")
