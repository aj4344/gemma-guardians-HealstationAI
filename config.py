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


def env_choice(name: str, default: str, choices: set[str]) -> str:
    value = env_str(name, default).lower()
    return value if value in choices else default


def _default_kek_file() -> Path:
    # Outside DATA_DIR on purpose: keys are never stored beside the data (ADR-001).
    if os.name == "nt":
        return Path(os.getenv("APPDATA") or Path.home()) / "HealStation" / "kek.key"
    return Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / "healstation" / "kek.key"


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

# ── Deployment mode ───────────────────────────────────────────────────────────
# single: Mode A, one device, bound to loopback. hub: Mode B, a PHC machine
# serving tablets over the LAN behind the TLS proxy (ADR-004).
DEPLOYMENT_MODE = env_choice("DEPLOYMENT_MODE", "single", {"single", "hub"})
IS_HUB = DEPLOYMENT_MODE == "hub"

# ── Case data and encryption keys (ADR-001) ───────────────────────────────────
DATA_DIR = Path(env_str("DATA_DIR", str(PROJECT_ROOT / "data")))
# Key-encryption key, in order of precedence: HEALSTATION_KEK (base64, for
# containers), KEK_FILE (a secret file outside DATA_DIR), the OS keyring.
HEALSTATION_KEK = os.getenv("HEALSTATION_KEK", "").strip()
KEK_FILE = Path(env_str("KEK_FILE", str(_default_kek_file())))
KEK_USE_KEYRING = env_bool("KEK_USE_KEYRING", True)
# Mode A creates a key on first start; Mode B refuses to start without one.
KEK_AUTO_CREATE = env_bool("KEK_AUTO_CREATE", not IS_HUB)

# ── Retention (PRD Appendix A, decision D6) ───────────────────────────────────
CASE_RETENTION_DAYS = env_int("CASE_RETENTION_DAYS", 30 if IS_HUB else 7)
# Raw uploads are deleted as soon as extraction finishes unless this is set.
RETAIN_RAW_UPLOADS = env_bool("RETAIN_RAW_UPLOADS", False)
SWEEP_INTERVAL_SECONDS = env_int("SWEEP_INTERVAL_SECONDS", 3600)

# ── Upload limits, enforced while streaming (INV-9, Appendix A) ───────────────
MAX_AUDIO_MB = env_int("MAX_AUDIO_MB", env_int("MAX_AUDIO_UPLOAD_MB", 25))
MAX_AUDIO_SECONDS = env_int("MAX_AUDIO_SECONDS", 300)
MAX_IMAGE_MB = env_int("MAX_IMAGE_MB", 15)
MAX_IMAGE_PIXELS = env_int("MAX_IMAGE_PIXELS", 25_000_000)
IMAGE_MAX_EDGE_PX = env_int("IMAGE_MAX_EDGE_PX", 2048)
MAX_PDF_MB = env_int("MAX_PDF_MB", 20)
MAX_PDF_PAGES = env_int("MAX_PDF_PAGES", 50)
MAX_OCR_PAGES = env_int("MAX_OCR_PAGES", 10)
PDF_PARSER_CPU_SECONDS = env_int("PDF_PARSER_CPU_SECONDS", 30)
PDF_PARSER_MEMORY_MB = env_int("PDF_PARSER_MEMORY_MB", 512)
MAX_DICOM_UPLOAD_MB = env_int("MAX_DICOM_UPLOAD_MB", 300)
MAX_DICOM_FILES = env_int("MAX_DICOM_FILES", 1000)
MAX_DICOM_UNCOMPRESSED_MB = env_int("MAX_DICOM_UNCOMPRESSED_MB", 1024)
MAX_ZIP_RATIO = env_int("MAX_ZIP_RATIO", 100)
MAX_KEY_SLICES = env_int("MAX_KEY_SLICES", 16)
MAX_ATTACHMENTS_PER_CASE = env_int("MAX_ATTACHMENTS_PER_CASE", 10)
MAX_RECORDINGS_PER_CASE = env_int("MAX_RECORDINGS_PER_CASE", 20)

# ── Job queue and worker pools (ADR-002) ──────────────────────────────────────
MAX_QUEUE_DEPTH = env_int("MAX_QUEUE_DEPTH", 20)
POOL_LLM = env_int("POOL_LLM", 1)
POOL_STT = env_int("POOL_STT", 1)
POOL_OCR = env_int("POOL_OCR", 2)
POOL_PDF = env_int("POOL_PDF", 2)
POOL_IMAGING = env_int("POOL_IMAGING", 1)
TIMEOUT_OCR_PAGE_S = env_int("TIMEOUT_OCR_PAGE_S", 20)
TIMEOUT_IMAGING_S = env_int("TIMEOUT_IMAGING_S", 180)
# Speech-to-text gets 2 x the recording's duration + 30 s.

# ── Storage budget (RES-05) ───────────────────────────────────────────────────
CASE_STORAGE_QUOTA_GB = env_float("CASE_STORAGE_QUOTA_GB", 5)
MIN_FREE_DISK_GB = env_float("MIN_FREE_DISK_GB", 2)

# ── Ollama / Gemma 4 ──────────────────────────────────────────────────────────
OLLAMA_BASE_URL = env_str("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = env_str("OLLAMA_MODEL", "gemma4:e2b")
# Lower-spec hardware alternative: set OLLAMA_MODEL=gemma2:2b in .env

# Triage-call tuning. LOCAL_GEMMA_MODEL / LOCAL_GEMMA_URL are optional
# overrides; by default triage uses the same model and server as above.
LOCAL_GEMMA_MODEL = env_str("LOCAL_GEMMA_MODEL", OLLAMA_MODEL)
LOCAL_GEMMA_URL = env_str("LOCAL_GEMMA_URL", f"{OLLAMA_BASE_URL}/api/chat")
LOCAL_GEMMA_TIMEOUT_SECONDS = env_int("LOCAL_GEMMA_TIMEOUT_SECONDS", 120)
TIMEOUT_LLM_S = env_int("TIMEOUT_LLM_S", LOCAL_GEMMA_TIMEOUT_SECONDS)
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
MAX_AUDIO_UPLOAD_MB = MAX_AUDIO_MB  # legacy name used by the v1 endpoint

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
