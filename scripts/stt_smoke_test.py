"""
Offline faster-whisper STT smoke test.
Usage: python scripts/stt_smoke_test.py --en path.wav --hi path.webm --mr path.wav
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_of_the_patient import transcribe_audio

LANGUAGE_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


def main():
    parser = argparse.ArgumentParser(description="Offline faster-whisper STT smoke test for demo languages.")
    parser.add_argument("--en", help="English audio file path")
    parser.add_argument("--hi", help="Hindi audio file path")
    parser.add_argument("--mr", help="Marathi audio file path")
    args = parser.parse_args()

    samples = {
        "en": args.en,
        "hi": args.hi,
        "mr": args.mr,
    }
    selected = {language: path for language, path in samples.items() if path}

    if not selected:
        print("Usage: python scripts/stt_smoke_test.py --en path.wav --hi path.webm --mr path.wav")
        print("Provide at least one audio file. Browser WebM recordings are supported.")
        return 2

    failed = False
    for language, path in selected.items():
        print("=" * 70)
        print(f"Testing {LANGUAGE_LABELS[language]} ({language}): {path}")
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            failed = True
            continue

        text = transcribe_audio(path, language_code=language)
        print(f"Transcription: {text}")
        if not text or str(text).startswith("ERROR:"):
            failed = True

    print("=" * 70)
    if failed:
        print("Offline STT smoke test failed for one or more files.")
        return 1

    print("Offline STT smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
