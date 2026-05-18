"""
Run this script ONCE while internet is available to download the Whisper 'small' model.
After it completes, the model is cached and will work fully offline.

Usage:
    python download_stt_model.py

After success:
    1. Open .env
    2. Change LOCAL_STT_MODEL_SIZE=tiny  →  LOCAL_STT_MODEL_SIZE=small
    3. Change LOCAL_STT_LOCAL_FILES_ONLY=false  →  LOCAL_STT_LOCAL_FILES_ONLY=true
    4. Restart the backend server
"""
import time
print("=" * 60)
print("  HealStation AI - Whisper Model Downloader")
print("=" * 60)
print("\nDownloading faster-whisper 'small' model (~466MB)...")
print("This only needs to happen ONCE. Please stay connected.\n")

start = time.time()
try:
    from faster_whisper import WhisperModel
    print("[1/2] Loading 'small' model (will download if not cached)...")
    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8",
        local_files_only=False,  # Allow download
    )
    elapsed = time.time() - start
    print(f"[2/2] Model loaded successfully in {elapsed:.1f}s!\n")
    print("=" * 60)
    print("  SUCCESS! Model is now cached for offline use.")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open .env")
    print("  2. Set:  LOCAL_STT_MODEL_SIZE=small")
    print("  3. Set:  LOCAL_STT_LOCAL_FILES_ONLY=true")
    print("  4. Restart the backend server")
    print("\nYou can now disconnect WiFi and the system will work fully offline!")
except ImportError:
    print("ERROR: faster-whisper is not installed.")
    print("Run:  pip install faster-whisper")
except Exception as e:
    print(f"ERROR: Download failed: {e}")
    print("Make sure you have an internet connection and try again.")
