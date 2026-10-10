"""
HealStation AI — Central Configuration
Part of the HealStation AI Emergency Triage System.
All environment variables and runtime defaults are defined here.
Import from this module; never call os.getenv() directly in other files.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Values already set in the real environment (systemd, Docker, CI) win over .env.
load_dotenv(override=False)

PROJECT_ROOT = Path(__file__).resolve().parent


def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip())
    except (TypeError, ValueError):
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip())
    except (TypeError, ValueError):
        return default


def env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw or not raw.strip():
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ── Server ────────────────────────────────────────────────────────────────────
API_HOST = env_str("API_HOST", "127.0.0.1")
API_PORT = env_int("API_PORT", 8001)
# Browser origins allowed to call the API. The bundled UI served by the API
# itself is same-origin and needs no entry here.
CORS_ALLOW_ORIGINS = env_list(
    "CORS_ALLOW_ORIGINS",
    ["http://localhost:3000", "http://127.0.0.1:3000"],
)
# Built React app; served at "/" when present (see README → Production).
FRONTEND_DIST_DIR = Path(env_str("FRONTEND_DIST_DIR", str(PROJECT_ROOT / "frontend" / "dist")))
MAX_REQUEST_MB = env_int("MAX_REQUEST_MB", 60)

# ── Ollama / Gemma 4 ──────────────────────────────────────────────────────────
OLLAMA_BASE_URL = env_str("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = env_str("OLLAMA_MODEL", "gemma4:e2b")
# Lower-spec hardware alternative: set OLLAMA_MODEL=gemma2:2b in .env

# Triage-call tuning. LOCAL_GEMMA_MODEL / LOCAL_GEMMA_URL are optional
# overrides; by default triage uses the same model and server as above.
LOCAL_GEMMA_MODEL = env_str("LOCAL_GEMMA_MODEL", OLLAMA_MODEL)
LOCAL_GEMMA_URL = env_str("LOCAL_GEMMA_URL", f"{OLLAMA_BASE_URL}/api/chat")
LOCAL_GEMMA_TIMEOUT_SECONDS = env_int("LOCAL_GEMMA_TIMEOUT_SECONDS", 120)
LOCAL_GEMMA_NUM_CTX = env_int("LOCAL_GEMMA_NUM_CTX", 1024)
LOCAL_GEMMA_NUM_PREDICT = env_int("LOCAL_GEMMA_NUM_PREDICT", 1400)
LOCAL_TRIAGE_CONFIDENCE_THRESHOLD = env_float("LOCAL_TRIAGE_CONFIDENCE_THRESHOLD", 0.6)
ENABLE_LOCAL_TRIAGE = env_bool("ENABLE_LOCAL_TRIAGE", True)
FAIRNESS_PARITY_THRESHOLD = env_float("FAIRNESS_PARITY_THRESHOLD", 0.05)

# ── Local STT (faster-whisper) ────────────────────────────────────────────────
ENABLE_LOCAL_STT = env_bool("ENABLE_LOCAL_STT", True)
STT_MODEL_SIZE = env_str("LOCAL_STT_MODEL_SIZE", "small")
STT_MODEL_PATH = env_str("LOCAL_STT_MODEL_PATH", "")
STT_DEVICE = env_str("LOCAL_STT_DEVICE", "cpu")
STT_COMPUTE = env_str("LOCAL_STT_COMPUTE_TYPE", "int8")
STT_CPU_THREADS = env_int("LOCAL_STT_CPU_THREADS", 0)
STT_NUM_WORKERS = env_int("LOCAL_STT_NUM_WORKERS", 1)
STT_LOCAL_FILES_ONLY = env_bool("LOCAL_STT_LOCAL_FILES_ONLY", True)
MAX_AUDIO_UPLOAD_MB = env_int("MAX_AUDIO_UPLOAD_MB", 25)

# ── Local TTS (pyttsx3) ───────────────────────────────────────────────────────
LOCAL_TTS_ENABLED = env_bool("LOCAL_TTS_ENABLED", True)
AUDIO_OUTPUT_DIR = Path(env_str("AUDIO_OUTPUT_DIR", str(PROJECT_ROOT / "audio_outputs")))
# Generated speech contains patient health information; keep it briefly.
AUDIO_RETENTION_SECONDS = env_int("AUDIO_RETENTION_SECONDS", 3600)

# ── Hospital Routing ──────────────────────────────────────────────────────────
HOSPITAL_OFFLINE_FIRST = True  # Always use static DB first

# ── Supported Languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
}
