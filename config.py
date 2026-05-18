"""
HealStation AI — Central Configuration
Part of the HealStation AI Emergency Triage System.
All environment variables and runtime defaults are defined here.
Import from this module; never call os.getenv() directly in other files.
"""
import os

from dotenv import load_dotenv

load_dotenv(override=True)

# ── Ollama / Gemma 4 ──────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
# Lower-spec hardware alternative: set OLLAMA_MODEL=gemma2:2b in .env

# ── Local STT (faster-whisper) ────────────────────────────────────────────────
STT_MODEL_SIZE  = os.getenv("LOCAL_STT_MODEL_SIZE", "small")
STT_DEVICE      = os.getenv("LOCAL_STT_DEVICE", "cpu")
STT_COMPUTE     = os.getenv("LOCAL_STT_COMPUTE_TYPE", "int8")

# ── Hospital Routing ──────────────────────────────────────────────────────────
HOSPITAL_OFFLINE_FIRST = True  # Always use static DB first

# ── Supported Languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
}
