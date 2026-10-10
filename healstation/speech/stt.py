# OFFLINE STT: Uses faster-whisper running entirely on-device.
# No audio data is sent to any external service.
"""
HealStation AI — Voice of the Patient (Offline STT)
Part of the HealStation AI Emergency Triage System.
Provides local, offline speech-to-text using faster-whisper.
Supports English (en), Hindi (hi), and Marathi (mr).
"""

import logging
import os
import re
import shutil
import tempfile
import time
from functools import lru_cache

from config import (
    STT_COMPUTE,
    STT_CPU_THREADS,
    STT_DEVICE,
    STT_LOCAL_FILES_ONLY,
    STT_MODEL_PATH,
    STT_MODEL_SIZE,
    STT_NUM_WORKERS,
)

logger = logging.getLogger(__name__)

# Re-export settings consumed by api.py for backward compatibility
LOCAL_STT_MODEL_SIZE = STT_MODEL_SIZE
LOCAL_STT_DEVICE = STT_DEVICE
LOCAL_STT_COMPUTE_TYPE = STT_COMPUTE

_LOCAL_STT_MODEL_PATH = STT_MODEL_PATH
_LOCAL_STT_CPU_THREADS = STT_CPU_THREADS
_LOCAL_STT_NUM_WORKERS = max(STT_NUM_WORKERS, 1)
_LOCAL_STT_LOCAL_FILES_ONLY = STT_LOCAL_FILES_ONLY


def _normalize_language(language_code: str) -> str:
    raw = str(language_code or "en").strip().lower()
    if "-" in raw:
        raw = raw.split("-", 1)[0]
    return raw if raw in {"en", "hi", "mr"} else "en"


def _detect_audio_format(audio_path: str) -> str:
    """Detect actual audio container format by reading magic bytes."""
    with open(audio_path, "rb") as audio_file:
        header = audio_file.read(16)
    if header.startswith(b"RIFF") and b"WAVE" in header:
        return "wav"
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if header.startswith(b"ID3") or header[:2] == b"\xff\xfb":
        return "mp3"
    if header.startswith(b"OggS"):
        return "ogg"
    if header[4:8] == b"ftyp":
        return "mp4"
    return "unknown"


def _prepare_audio_for_local_stt(audio_path: str):
    """Copy audio to a temp file with the correct extension for faster-whisper."""
    detected_format = _detect_audio_format(audio_path)
    suffix = f".{detected_format}" if detected_format != "unknown" else os.path.splitext(audio_path)[1] or ".audio"
    prepared = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    prepared.close()
    shutil.copyfile(audio_path, prepared.name)
    file_size = os.path.getsize(audio_path)
    logger.info("[LOCAL STT] Audio format detected: %s, size=%d bytes", detected_format, file_size)
    return prepared.name, detected_format


# Common transcription corrections for Marathi and Hindi
TRANSCRIPTION_CORRECTIONS = {
    'mr': {
        # Common misheard words in Marathi
        'मला': ['माला', 'मलाह', 'मलां'],
        'काय': ['काई', 'काइ', 'कै'],
        'झाले': ['जाले', 'जाळे', 'झालं'],
        'आहे': ['आहै', 'आये', 'आहेत'],
        'छातीत': ['चांदात', 'छाती', 'छातित'],
        'अंगात': ['अंगत', 'अंगाते', 'अंगामध्ये'],
        'आज': ['बगुन', 'बघुन', 'आजं'],
        'बघून': ['बगुन', 'बग्न', 'बाघुन'],
        'समस्या': ['समस्या', 'समसिया', 'समस्यां'],
        'वैद्यकीय': ['वैद्य', 'वैद्यकिय', 'वैदिकीय'],
        'तपासणी': ['तपासनी', 'तपास', 'तपासण्या'],
        'लक्षणे': ['लक्षणं', 'लक्षन', 'लक्षण'],
        'दुखते': ['दुखतं', 'दुखात', 'दुखत'],
        'त्रास': ['त्रासं', 'त्रासत', 'त्रास'],
        'श्वास': ['स्वास', 'शास', 'श्वास'],
        'कोंडणे': ['कोंडने', 'कोंडने'],
        'वेदना': ['वेधना', 'वेदना'],
    },
    'hi': {
        # Common misheard words in Hindi
        'मुझे': ['मुझ', 'मुझको', 'मुझसे'],
        'क्या': ['क्यां', 'कै', 'क्या'],
        'हुआ': ['हुवा', 'हुया', 'हुवा'],
        'है': ['हैं', 'हे', 'है'],
        'छाती': ['छाति', 'छातीं', 'छात'],
        'आज': ['आजं', 'आज़', 'आज'],
        'देखकर': ['देख', 'देखकरके', 'देखकर'],
        'समस्या': ['समसिया', 'समस्यां', 'समस्या'],
        'जांच': ['जाँच', 'जान्च', 'जांच'],
        'लक्षण': ['लक्षणं', 'लछन', 'लक्षण'],
        'दर्द': ['दर्दं', 'दरद', 'दर्द'],
        'परेशानी': ['परेशनी', 'परेशानीं', 'परेशानी'],
        'सांस': ['सास', 'साश', 'सांस'],
        'फूल': ['फुल', 'फूल'],
        'रही': ['रहि', 'रही'],
        'दिल': ['दील', 'देल', 'दिल'],
    },
}


def improve_transcription(text, language_code="en"):
    """
    Improve transcription accuracy by correcting common misheard words
    especially for Marathi and Hindi languages.
    """
    if language_code not in TRANSCRIPTION_CORRECTIONS:
        return text

    corrections = TRANSCRIPTION_CORRECTIONS[language_code]
    improved_text = text

    # Apply corrections
    for correct_word, variations in corrections.items():
        for variation in variations:
            # Case-insensitive replacement
            pattern = r'\b' + re.escape(variation) + r'\b'
            improved_text = re.sub(pattern, correct_word, improved_text, flags=re.IGNORECASE)

    # Additional cleanup for better medical context
    if language_code == 'mr':
        # Fix common medical term misunderstandings
        improved_text = re.sub(
            r'\b(माला|मला)\s+(काय|काई)\s+(जाले|झाले)\b', 'मला काय झाले', improved_text, flags=re.IGNORECASE
        )
        improved_text = re.sub(r'\b(बगुन|आज)\s+(माला|मला)\b', 'आज मला', improved_text, flags=re.IGNORECASE)

        # Fix common misinterpretations where English words creep in
        improved_text = re.sub(r'\bThe patient may mention\b.*?symptoms\.?\s*', '', improved_text, flags=re.IGNORECASE)
        improved_text = re.sub(
            r'\bbody parts,?\s*pain,?\s*medical conditions,?\s*and symptoms\.?\s*',
            '',
            improved_text,
            flags=re.IGNORECASE,
        )

    elif language_code == 'hi':
        # Fix common medical term misunderstandings for Hindi
        improved_text = re.sub(r'\b(मुझे|मुझको)\s+(क्या|क्यां)\s+(हुआ|हुवा)\b', 'मुझे क्या हुआ', improved_text, flags=re.IGNORECASE)
        improved_text = re.sub(r'\b(आज|आजं)\s+(मुझे|मुझको)\b', 'आज मुझे', improved_text, flags=re.IGNORECASE)

        # Fix common misinterpretations where English words creep in
        improved_text = re.sub(r'\bThe patient may mention\b.*?symptoms\.?\s*', '', improved_text, flags=re.IGNORECASE)
        improved_text = re.sub(
            r'\bbody parts,?\s*pain,?\s*medical conditions,?\s*and symptoms\.?\s*',
            '',
            improved_text,
            flags=re.IGNORECASE,
        )

    return improved_text


def _build_stt_prompt(language_code: str) -> str:
    """Provides medical context to Whisper to improve clinical transcription."""
    prompts = {
        "en": (
            "This is a medical consultation where a patient is describing their symptoms "
            "and health concerns to a doctor. The patient may mention body parts, pain, "
            "medical conditions, and symptoms."
        ),
        "hi": (
            "यह एक चिकित्सा परामर्श है जहाँ एक मरीज़ अपने लक्षणों और स्वास्थ्य संबंधी "
            "चिंताओं के बारे में डॉक्टर को बता रहा है। मरीज़ शरीर के अंगों, दर्द, चिकित्सा "
            "स्थितियों और लक्षणों जैसे 'सांस फूलना', 'दिल में दर्द', 'छाती में भारीपन' का उल्लेख कर सकता है।"
        ),
        "mr": (
            "हे एक वैद्यकीय सल्लामसलत आहे जिथे एक रुग्ण त्यांच्या लक्षणांचे आणि आरोग्याच्या "
            "समस्यांचे वर्णन डॉक्टरांना करत आहे। रुग्ण शरीराचे अवयव, वेदना, वैद्यकीय स्थिती "
            "आणि लक्षणांचा जसे 'श्वास कोंडणे', 'हृदयात वेदना' उल्लेख करू शकतो।"
        ),
    }
    # Add a global prefix to force clinical context for the 'small' model
    prefix = "Medical Triage Context: " if language_code == "en" else ""
    return prefix + prompts.get(language_code, prompts["en"])


@lru_cache(maxsize=1)
def _get_local_stt_model():
    """
    Load and cache the faster-whisper model.
    Model size is configurable via LOCAL_STT_MODEL_SIZE env var (default: small).
    """
    try:
        from faster_whisper import WhisperModel
    except Exception as import_error:
        raise RuntimeError(f"faster-whisper not available: {import_error}") from import_error

    model_id = _LOCAL_STT_MODEL_PATH or LOCAL_STT_MODEL_SIZE
    kwargs = {
        "device": LOCAL_STT_DEVICE,
        "compute_type": LOCAL_STT_COMPUTE_TYPE,
        "num_workers": _LOCAL_STT_NUM_WORKERS,
        "local_files_only": _LOCAL_STT_LOCAL_FILES_ONLY,
    }
    if _LOCAL_STT_CPU_THREADS > 0:
        kwargs["cpu_threads"] = _LOCAL_STT_CPU_THREADS

    logger.info("[LOCAL STT] Loading model: %s on %s", model_id, LOCAL_STT_DEVICE)
    return WhisperModel(model_id, **kwargs)


def _transcribe_with_local_whisper(audio_path: str, language_code: str):
    if not audio_path or not os.path.exists(audio_path):
        return None, "Audio file not found for local STT"

    start_time = time.monotonic()
    prepared_audio_path = None
    try:
        model = _get_local_stt_model()
        prompt = _build_stt_prompt(language_code)
        prepared_audio_path, detected_format = _prepare_audio_for_local_stt(audio_path)

        segments, _info = model.transcribe(
            prepared_audio_path,
            language=language_code,
            beam_size=5,
            vad_filter=True,
            initial_prompt=prompt,
        )
        text_parts = [segment.text.strip() for segment in segments if segment.text]
        raw_text = " ".join(text_parts).strip()
        if not raw_text:
            return None, "Local STT returned empty transcription"

        improved_text = improve_transcription(raw_text, language_code)
        elapsed = time.monotonic() - start_time
        # Never log the transcript itself: it is the patient's description of their health.
        logger.info("[LOCAL STT] Transcription completed in %.2fs (%d chars)", elapsed, len(improved_text))
        return improved_text, None
    except Exception as error:
        elapsed = time.monotonic() - start_time
        detected_format = "unknown"
        first_bytes = ""
        try:
            detected_format = _detect_audio_format(audio_path)
            with open(audio_path, "rb") as audio_file:
                first_bytes = audio_file.read(16).hex()
        except OSError:
            first_bytes = "unreadable"
        return (
            None,
            f"Local STT failed after {elapsed:.2f}s: {error} | format={detected_format} | first_bytes={first_bytes}",
        )
    finally:
        if prepared_audio_path and os.path.exists(prepared_audio_path):
            try:
                os.remove(prepared_audio_path)
            except OSError:
                pass


def transcribe_audio_offline(audio_path: str, language_code: str = "en") -> str:
    """
    Transcribe audio entirely offline using faster-whisper.
    Returns the transcription text, or an ERROR: prefixed message on failure.
    Supports language_code: 'en', 'hi', 'mr'.
    """
    language_code = _normalize_language(language_code)
    if not audio_path or not os.path.exists(audio_path):
        return "ERROR: No audio file submitted or file not found."
    text, error = _transcribe_with_local_whisper(audio_path, language_code)
    if text:
        logger.info("[LOCAL STT] Transcription successful.")
        return text
    logger.error("[LOCAL STT] Transcription failed: %s", error)
    return f"ERROR: {error or 'Transcription failed — please type your symptoms instead.'}"


def transcribe_audio(audio_path, language_code="en"):
    """
    Offline speech-to-text entry point — delegates to faster-whisper.
    No audio is sent to any external service.
    """
    return transcribe_audio_offline(audio_path, language_code=language_code)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    audio_filepath = sys.argv[1] if len(sys.argv) > 1 else "patient_voice_test_for_patient.wav"
    result = transcribe_audio_offline(audio_filepath)
    if result.startswith("ERROR"):
        logger.error(result)
    else:
        logger.info("Patient said: %s", result)
