"""Spoken responses: generation, lookup and retention of generated audio files."""

import logging
import os
import re
import time
import uuid

from fastapi import HTTPException

from config import AUDIO_OUTPUT_DIR, AUDIO_RETENTION_SECONDS, LOCAL_TTS_ENABLED
from healstation.speech.tts import text_to_speech_for_api

logger = logging.getLogger("healstation")


_AUDIO_FILENAME_RE = re.compile(r"^doctor_response_[0-9a-f]{32}\.(?:wav|mp3)$")


def audio_path_for(filename: str) -> str:
    """Resolve a generated-audio filename, rejecting anything we did not create."""
    if not _AUDIO_FILENAME_RE.fullmatch(filename or ""):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return os.path.join(AUDIO_OUTPUT_DIR, filename)


def generate_response_audio(text: str, language: str) -> str | None:
    """Speak the response with offline TTS; returns its URL or None."""
    if not LOCAL_TTS_ENABLED:
        return None
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    # Random names: these files contain health information and are served
    # without authentication, so they must not be guessable.
    output_path = os.path.join(AUDIO_OUTPUT_DIR, f"doctor_response_{uuid.uuid4().hex}.wav")
    try:
        generated_path = text_to_speech_for_api(text=text, output_path=output_path, language=language)
    except Exception:
        logger.exception("TTS generation failed")
        return None
    if not generated_path or not os.path.exists(generated_path) or os.path.getsize(generated_path) == 0:
        logger.warning("TTS: audio file missing or empty")
        return None
    return f"/api/audio/{os.path.basename(generated_path)}"


# Utility Functions
def cleanup_old_audio_files():
    """Delete generated recordings older than AUDIO_RETENTION_SECONDS."""
    if not os.path.isdir(AUDIO_OUTPUT_DIR):
        return
    cutoff = time.time() - AUDIO_RETENTION_SECONDS
    for filename in os.listdir(AUDIO_OUTPUT_DIR):
        file_path = os.path.join(AUDIO_OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
        except OSError:
            # Another request may have removed it concurrently.
            pass
