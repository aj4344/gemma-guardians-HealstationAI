#!/usr/bin/env python3
"""SPIKE-01 — measure the baseline on the machine this runs on.

Measures cold start, text-triage latency, process memory and (when the
models are present) speech-to-text speed. Anything that cannot be measured
on this machine is reported as "not measured" with the reason; nothing is
estimated.

Usage:
    python scripts/benchmark_baseline.py [--runs 50] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SAMPLE_TEXTS = [
    ("en", "Mild headache and runny nose for two days, no fever."),
    ("en", "Fever for three days with cough, able to walk and eat."),
    ("hi", "दो दिन से हल्का सिरदर्द और जुकाम है।"),
    ("mr", "दोन दिवसांपासून हलकी डोकेदुखी आणि सर्दी आहे."),
    ("en", "Crushing chest pain with sweating for 20 minutes."),
]


def _percentile(values, pct):
    ordered = sorted(values)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def _rss_mb() -> float:
    # ru_maxrss is KiB on Linux, bytes on macOS.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / 1024 if sys.platform != "darwin" else peak / (1024 * 1024)


def measure_cold_start(runs: int = 3) -> dict:
    timings = []
    for _ in range(runs):
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, "-c", "import api"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            env={**os.environ, "LOCAL_TTS_ENABLED": "false"},
        )
        timings.append(time.perf_counter() - start)
    return {"runs": runs, "median_s": round(statistics.median(timings), 3), "max_s": round(max(timings), 3)}


def ollama_reachable() -> bool:
    import requests

    from config import OLLAMA_BASE_URL

    try:
        return requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2).ok
    except Exception:
        return False


def measure_text_triage(runs: int) -> dict:
    os.environ["LOCAL_TTS_ENABLED"] = "false"
    from fastapi.testclient import TestClient

    import api

    api.LOCAL_TTS_ENABLED = False
    rss_after_import = _rss_mb()
    client = TestClient(api.app)
    latencies = []
    sources = {}
    for i in range(runs):
        language, text = SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)]
        start = time.perf_counter()
        response = client.post("/api/get-doctor-response", json={"patient_text": text, "language": language})
        latencies.append((time.perf_counter() - start) * 1000)
        source = response.json().get("triage_source", f"http_{response.status_code}")
        sources[source] = sources.get(source, 0) + 1
    return {
        "runs": runs,
        "model_reachable": ollama_reachable(),
        "triage_sources": sources,
        "p50_ms": round(_percentile(latencies, 50), 1),
        "p95_ms": round(_percentile(latencies, 95), 1),
        "max_ms": round(max(latencies), 1),
        "rss_after_import_mb": round(rss_after_import, 1),
        "rss_peak_after_requests_mb": round(_rss_mb(), 1),
    }


def measure_stt() -> dict:
    results = {}
    for size in ("tiny", "small"):
        try:
            from faster_whisper import WhisperModel

            start = time.perf_counter()
            model = WhisperModel(size, device="cpu", compute_type="int8", local_files_only=True)
            load_s = time.perf_counter() - start
        except Exception as error:  # model weights not cached on this machine
            results[size] = {"measured": False, "reason": f"model not available offline ({type(error).__name__})"}
            continue
        import numpy as np

        audio = (np.random.default_rng(0).standard_normal(16000 * 10) * 0.01).astype("float32")
        start = time.perf_counter()
        segments, _ = model.transcribe(audio, language="en", vad_filter=False)
        list(segments)
        results[size] = {
            "measured": True,
            "load_s": round(load_s, 2),
            "transcribe_10s_audio_s": round(time.perf_counter() - start, 2),
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    report = {
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "cold_start_import_api": measure_cold_start(),
        "text_triage": measure_text_triage(args.runs),
        "stt": measure_stt(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
