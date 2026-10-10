"""
Quick verification that the offline stack is ready:
- Whisper small model loaded from local cache (no internet)
- Ollama/Gemma reachable at port 11434
- Safety guardrail triggers for emergency symptoms
"""

import io
import os
import sys
import time

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  HealStation AI - Offline Readiness Check")
print("=" * 55)

all_ok = True

sys.path.insert(0, ".")
from config import (
    LOCAL_GEMMA_MODEL,
    OLLAMA_BASE_URL,
    STT_COMPUTE,
    STT_DEVICE,
    STT_MODEL_PATH,
    STT_MODEL_SIZE,
)

# --- 1. Whisper STT -----------------------------------------
stt_model = STT_MODEL_PATH or STT_MODEL_SIZE
print(f"\n[1/3] Speech-to-Text (faster-whisper {stt_model})...")
try:
    from faster_whisper import WhisperModel

    t = time.time()
    m = WhisperModel(stt_model, device=STT_DEVICE, compute_type=STT_COMPUTE, local_files_only=True)
    print(f"      [OK] Loaded in {time.time() - t:.1f}s (no internet used)")
except Exception as e:
    print(f"      [FAIL] {e}")
    print("         -> Fix: run 'python download_stt_model.py' once while online")
    all_ok = False

# --- 2. Ollama / Gemma ---------------------------------------
print(f"\n[2/3] Local Gemma AI ({LOCAL_GEMMA_MODEL} at {OLLAMA_BASE_URL})...")
try:
    r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    r.raise_for_status()
    pulled = {model.get("name") for model in r.json().get("models", [])}
    if LOCAL_GEMMA_MODEL in pulled or f"{LOCAL_GEMMA_MODEL}:latest" in pulled:
        print("      [OK] Ollama is running and the model is pulled")
    else:
        print(f"      [FAIL] Model not pulled. Available: {sorted(pulled) or 'none'}")
        print(f"         -> Fix: ollama pull {LOCAL_GEMMA_MODEL}")
        all_ok = False
except Exception as e:
    print(f"      [FAIL] {e}")
    print("         -> Fix: Run 'ollama serve' or double-click start_offline.bat")
    all_ok = False

# --- 3. Safety Guardrail -------------------------------------
print("\n[3/3] Safety guardrail (no internet needed)...")
try:
    from healstation.triage.guardrails import evaluate_red_flag_guardrail

    result = evaluate_red_flag_guardrail("I have pain in my heart and breathlessness")
    if result["apply_guardrail"]:
        print("      [OK] CRITICAL override triggered correctly")
        print(f"           Categories: {result['matched_categories']}")
    else:
        print("      [FAIL] guardrail did NOT trigger for cardiac symptoms")
        all_ok = False
except Exception as e:
    print(f"      [FAIL] {e}")
    all_ok = False

# --- Summary -------------------------------------------------
print("\n" + "=" * 55)
if all_ok:
    print("  ALL CHECKS PASSED -- Safe to go offline!")
    print("  Use start_offline.bat to start everything together.")
else:
    print("  Some checks FAILED. Fix the issues above first.")
print("=" * 55)
sys.exit(0 if all_ok else 1)
