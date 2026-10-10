"""FastAPI application: middleware, routers and the bundled UI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import CORS_ALLOW_ORIGINS, FRONTEND_DIST_DIR, MAX_REQUEST_MB
from healstation import __version__
from healstation.api import v1
from healstation.speech import response_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("healstation")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Recordings from a previous run may hold patient data; purge stale ones.
    response_audio.cleanup_old_audio_files()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HealStation AI — Emergency Triage API",
        description="Offline clinical triage powered by Gemma 4 (gemma4:e2b) via Ollama.",
        version=__version__,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def limit_request_size(request: Request, call_next):
        """Reject oversized bodies before they are read into memory."""
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_MB * 1024 * 1024:
            return JSONResponse(status_code=413, content={"detail": f"Request body exceeds {MAX_REQUEST_MB} MB."})
        return await call_next(request)

    # CORS: only the configured UI origins may call the API from a browser.
    # A wildcard would let any website the health worker visits read patient
    # triage results from this local server. No cookies are used, so no
    # credentials are allowed either.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    frontend_built = (FRONTEND_DIST_DIR / "index.html").is_file()
    if not frontend_built:

        @app.get("/")
        def read_root():
            return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

    app.include_router(v1.router)

    # Serve the built React app (frontend/dist) from the API when it exists, so a
    # deployment is a single offline process. Mounted last: API routes win.
    if frontend_built:
        app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
    return app
