"""FastAPI application: middleware, routers and the bundled UI."""

import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import CORS_ALLOW_ORIGINS, FRONTEND_DIST_DIR, MAX_REQUEST_MB
from healstation import __version__
from healstation.api import v1, v2
from healstation.api.errors import envelope, install_error_handlers, request_language
from healstation.api.middleware import BodySizeLimitMiddleware, RequestContextMiddleware
from healstation.settings import Settings
from healstation.speech import response_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("healstation")

MB = 1024 * 1024
# Streaming upload routes enforce their own per-type limits while reading;
# this outer cap only bounds the request as a whole.
_UPLOAD_ROUTE = re.compile(r"^/api/v2/cases/[^/]+/(attachments|transcriptions)$")
_UPLOAD_OVERHEAD_BYTES = 1 * MB


def _max_upload_bytes() -> int:
    s = Settings()
    return max(s.max_audio_bytes, s.max_image_bytes, s.max_pdf_bytes, s.max_dicom_upload_bytes)


def _body_limit(scope) -> int:
    if scope.get("method") == "POST" and _UPLOAD_ROUTE.match(scope.get("path", "")):
        return _max_upload_bytes() + _UPLOAD_OVERHEAD_BYTES
    return MAX_REQUEST_MB * MB


def _too_large_response(scope):
    request = Request(scope)
    if scope.get("path", "").startswith("/api/v2"):
        return JSONResponse(status_code=413, content=envelope("REQUEST_TOO_LARGE", request_language(request)))
    return JSONResponse(status_code=413, content={"detail": f"Request body exceeds {MAX_REQUEST_MB} MB."})


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Recordings from a previous run may hold patient data; purge stale ones.
    response_audio.cleanup_old_audio_files()
    runtime = getattr(app.state, "runtime", None)
    if runtime is not None:
        runtime.start()
    yield
    runtime = getattr(app.state, "runtime", None)
    if runtime is not None:
        runtime.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="HealStation AI — Emergency Triage API",
        description="Offline clinical triage powered by Gemma 4 (gemma4:e2b) via Ollama.",
        version=__version__,
        lifespan=lifespan,
    )
    install_error_handlers(app)

    # Added innermost first: requests pass RequestContext → CORS → body limit.
    app.add_middleware(
        BodySizeLimitMiddleware,
        limit_for=lambda scope: _body_limit(scope),
        on_too_large=_too_large_response,
    )
    # CORS: only the configured UI origins may call the API from a browser.
    # A wildcard would let any website the health worker visits read patient
    # triage results from this local server. No cookies are used, so no
    # credentials are allowed either.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Accept-Language", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
    )
    app.add_middleware(RequestContextMiddleware)

    frontend_built = (FRONTEND_DIST_DIR / "index.html").is_file()
    if not frontend_built:

        @app.get("/")
        def read_root():
            return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

    app.include_router(v1.router)
    app.include_router(v2.router)

    # Serve the built React app (frontend/dist) from the API when it exists, so a
    # deployment is a single offline process. Mounted last: API routes win.
    if frontend_built:
        app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
    return app
