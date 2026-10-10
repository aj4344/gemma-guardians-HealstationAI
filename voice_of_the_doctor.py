"""
HealStation AI — Voice of the Doctor (TTS)
Part of the HealStation AI Emergency Triage System.
Generates speech for triage responses in English, Hindi, and Marathi.
Uses pyttsx3 exclusively — fully offline, no network required.
"""

import logging
import os
import re
import threading

logger = logging.getLogger(__name__)

# pyttsx3 shares one engine per process and its run loop is not re-entrant, so
# concurrent API requests must not drive it at the same time.
_TTS_LOCK = threading.Lock()


def _try_local_tts(text: str, output_filepath: str, lang: str):
    """Attempt TTS generation via pyttsx3 (offline, no network required)."""
    try:
        import pyttsx3
    except Exception as import_error:
        return None, f"Local TTS unavailable (pyttsx3 import failed): {import_error}"

    try:
        root, ext = os.path.splitext(output_filepath)
        local_output = output_filepath if ext.lower() == ".wav" else f"{root}.wav"

        with _TTS_LOCK:
            engine = pyttsx3.init()
            if lang in {"hi", "mr"}:
                voices = engine.getProperty("voices") or []
                for voice in voices:
                    langs = getattr(voice, "languages", []) or []
                    lang_blob = " ".join([str(item) for item in langs]).lower()
                    if lang in lang_blob:
                        engine.setProperty("voice", voice.id)
                        break

            engine.save_to_file(text, local_output)
            engine.runAndWait()

        if os.path.exists(local_output) and os.path.getsize(local_output) > 0:
            logger.info("pyttsx3 TTS generated: %s", local_output)
            return local_output, None
        return None, "Local TTS output file missing or empty"
    except Exception as tts_error:
        return None, f"Local TTS failed: {tts_error}"

# Function to clean text for better audio generation
def clean_text_for_audio(text, language="en"):
    """
    Clean text to remove markdown formatting and improve audio quality,
    especially for Marathi and Hindi languages.
    """
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold **text**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove italic *text*
    text = re.sub(r'#+\s*', '', text)               # Remove headers ###
    text = re.sub(r'`([^`]+)`', r'\1', text)        # Remove code blocks
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove links [text](url)
    
    # Remove markdown lists and formatting
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Remove bullet points
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Remove numbered lists
    
    # Language-specific cleaning for better pronunciation
    if language in ['mr', 'hi']:  # Marathi and Hindi
        # Replace common markdown symbols that cause repetition
        text = re.sub(r'[#*_`~]+', ' ', text)
        # Remove excessive punctuation that causes audio issues
        text = re.sub(r'[−–—]+', '-', text)  # Replace em/en dashes with hyphen
        text = re.sub(r'•', '', text)  # Remove bullet symbols
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Improve readability for TTS
        text = text.replace('/', ' किंवा ' if language == 'mr' else ' या ')
        text = text.replace('&', ' आणि ' if language == 'mr' else ' और ')
        
    # General cleanup
    text = re.sub(r'\n\s*\n', '\n', text)  # Remove extra newlines
    text = re.sub(r'\s+', ' ', text)       # Normalize whitespace
    text = text.strip()
    
    return text

# Configuration for the doctor's voice
# pyttsx3 properties for different languages
VOICE_CONFIG = {
    "en": {
        "rate": "-4%",
        "pitch": "+0Hz",
        "volume": "+0%"
    },
    "hi": {
        "rate": "-2%",
        "pitch": "+0Hz",
        "volume": "+0%"
    },
    "mr": {
        "rate": "0%",
        "pitch": "+0Hz",
        "volume": "+0%"
    }
}

def _text_to_speech_core(text, output_filepath, lang='en'):
    """
    Generate speech using pyttsx3 offline.
    No network calls are made.
    """
    cleaned_text = clean_text_for_audio(text, lang)
    logger.debug("[TTS] Original length: %d | Cleaned length: %d", len(text), len(cleaned_text))
    return _try_local_tts(cleaned_text, output_filepath, lang)

def generate_doctor_voice(text: str, output_filepath: str = "current_doctor_response.mp3", lang='en'):
    """
    Generate speech using pyttsx3 offline.
    
    Args:
        text (str): The text to convert to speech
        output_filepath (str): Where to save the generated audio
        lang (str): Language code for the voice (e.g., 'en' for English)
        
    Returns:
        str: Path to the generated audio file
    """
    output_path, error = _text_to_speech_core(text, output_filepath, lang)
    if error:
        logger.warning("Failed to generate speech: %s", error)
    return output_path

def speak_as_doctor(text: str, lang='en'):
    """
    Makes the doctor speak with a deep male voice.
    
    Args:
        text (str): The text to be spoken
        lang (str): Language code for the voice (e.g., 'en' for English)
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Doctor AI (Deep Male Voice): {text}")
    
    # Generate speech with pyttsx3
    output_path = generate_doctor_voice(text, lang=lang)
    
    if not output_path or not os.path.exists(output_path):
        print("Failed to generate doctor's voice.")
        return False
    
    try:
        # Play the generated speech
        from playsound import playsound
        playsound(output_path)
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False

def get_doctor_voice_for_ui(text: str, output_filepath: str = "doctor_response.mp3", language_code="en"):
    """
    Generate speech for the doctor's response for the UI.
    Uses language-specific voices.
    
    Args:
        text (str): The text to be spoken
        output_filepath (str): The path where to save the file
        language_code (str): Language code ("en", "hi", "mr")
        
    Returns:
        str: Path to the audio file for the UI
    """
    logger.debug("Generating doctor voice for UI in %s (%d chars)", language_code, len(text))

    output_path = generate_doctor_voice(text, output_filepath, lang=language_code)

    if not output_path or not os.path.exists(output_path):
        logger.warning("Failed to generate doctor's voice for UI in %s.", language_code)
        return None

    return output_path

# Add required functions for API compatibility
def text_to_speech_for_api(text, output_path, language="en"):
    """API function for text-to-speech generation - renamed to avoid conflicts"""
    return get_doctor_voice_for_ui(text, output_path, language_code=language)

def get_available_voices():
    """Return available voices for the UI"""
    available_voices = {}
    for lang_code in VOICE_CONFIG:
        available_voices[lang_code] = {
            "name": f"{lang_code.upper()} - Offline Voice",
            "is_neural": False
        }
    return available_voices

# --- Main execution for testing ---
if __name__ == "__main__":
    test_message = "Hello, I am Doctor Jones. I will analyze your symptoms and provide medical advice based on what I see."
    print("\n=== Doctor AI Voice System Test ===")
    
    print("\nGenerating and playing doctor's voice:")
    speak_as_doctor(test_message)
