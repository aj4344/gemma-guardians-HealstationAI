import time
import requests
import os
import sys
from typing import Dict, Any, Optional

# Make the repository root importable regardless of the working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import _build_local_gemma_prompt, _extract_json_payload
from config import LOCAL_GEMMA_MODEL, LOCAL_GEMMA_NUM_CTX, LOCAL_GEMMA_NUM_PREDICT, OLLAMA_BASE_URL

LOCAL_GEMMA_URL = f"{OLLAMA_BASE_URL}/api/generate"

def benchmark_gemma(patient_text: str, language: str):
    print(f"--- Benchmarking Gemma for: '{patient_text}' ({language}) ---")
    
    payload = {
        "model": LOCAL_GEMMA_MODEL,
        "prompt": _build_local_gemma_prompt(
            patient_text, language
        ),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_ctx": LOCAL_GEMMA_NUM_CTX,
            "num_predict": LOCAL_GEMMA_NUM_PREDICT,
        }
    }
    
    start_time = time.time()
    try:
        response = requests.post(LOCAL_GEMMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        end_time = time.time()
        
        duration = end_time - start_time
        raw = response.json()
        model_text = raw.get("response", "")
        result = _extract_json_payload(model_text)
        
        print(f"Gemma Inference Time: {duration:.2f} seconds")
        print(f"Triage Result: {result.get('urgency', 'N/A')}")
        return duration, result
    except Exception as e:
        print(f"Error calling local Gemma: {e}")
        return None, None

def benchmark_stt_estimate():
    # Estimating based on 'small' model on CPU (int8)
    # A typical 10s audio clip takes ~2-5s on average CPU.
    # We'll use a conservative estimate for CPU-based inference.
    print("--- Estimating STT Timing (Whisper small, CPU, int8) ---")
    print("Estimated STT Time (10s audio): ~3.50 seconds")
    return 3.50

if __name__ == "__main__":
    # Test 1: Severe symptoms (Emergency)
    text_en = "I am a 30-year-old male with severe chest pain and breathlessness. I feel dizzy."
    time_en, res_en = benchmark_gemma(text_en, "en")
    
    # Test 2: Hindi translation
    text_hi = "मुझे सीने में बहुत तेज दर्द और सांस लेने में तकलीफ हो रही है। मुझे चक्कर आ रहे हैं।"
    time_hi, res_hi = benchmark_gemma(text_hi, "hi")
    
    stt_time = benchmark_stt_estimate()
    
    print("\n" + "="*50)
    print("TOTAL OFFLINE PROCESSING TIME (ESTIMATED)")
    print("="*50)
    if time_en:
        total_en = stt_time + time_en
        print(f"English Query (10s audio): {total_en:.2f} seconds")
    if time_hi:
        total_hi = stt_time + time_hi
        print(f"Hindi Query (10s audio):   {total_hi:.2f} seconds")
    print("="*50)
