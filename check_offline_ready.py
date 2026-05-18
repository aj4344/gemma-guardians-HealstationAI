"""
Quick verification that the offline stack is ready:
- Whisper small model loaded from local cache (no internet)
- Ollama/Gemma reachable at port 11434
- Safety guardrail triggers for emergency symptoms
"""
import sys, os, time, requests, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  HealStation AI - Offline Readiness Check")
print("=" * 55)

all_ok = True

# --- 1. Whisper STT -----------------------------------------
print("\n[1/3] Speech-to-Text (faster-whisper small)...")
try:
    from faster_whisper import WhisperModel
    t = time.time()
    m = WhisperModel("small", device="cpu", compute_type="int8", local_files_only=True)
    print(f"      [OK] Loaded in {time.time()-t:.1f}s (no internet used)")
except Exception as e:
    print(f"      [FAIL] {e}")
    all_ok = False

# --- 2. Ollama / Gemma ---------------------------------------
print("\n[2/3] Local Gemma AI (Ollama at port 11434)...")
try:
    r = requests.get("http://127.0.0.1:11434/", timeout=5)
    if r.status_code < 500:
        print("      [OK] Ollama is running and reachable")
    else:
        raise Exception(f"HTTP {r.status_code}")
except Exception as e:
    print(f"      [FAIL] {e}")
    print("         -> Fix: Run 'ollama serve' or double-click start_offline.bat")
    all_ok = False

# --- 3. Safety Guardrail -------------------------------------
print("\n[3/3] Safety guardrail (no internet needed)...")
try:
    sys.path.insert(0, ".")
    from api import _evaluate_red_flag_guardrail
    result = _evaluate_red_flag_guardrail("I have pain in my heart and breathlessness")
    if result["apply_guardrail"]:
        print(f"      [OK] CRITICAL override triggered correctly")
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
