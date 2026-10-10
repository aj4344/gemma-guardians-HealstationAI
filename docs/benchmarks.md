# Benchmarks

Measured with `scripts/benchmark_baseline.py` (SPIKE-01). Re-run it on the
reference hardware (PRD §4: 8 GB RAM, 4-core x86-64, no GPU, SSD) before
setting or changing any performance budget, and add a row here.

> **These numbers are not from the reference hardware.** They were taken in the
> 4-vCPU / 15 GB Linux build container used to implement the PRD, with no
> Ollama server and no Whisper weights reachable. They show the cost of the
> code around the model, not of the model itself.

## Baseline (commit `9b199e2`, build container, 2026-10-10)

| Measure | Result | Notes |
|---|---|---|
| Cold start (`import api`) | 0.62 s median | 3 runs |
| Text triage, rules path, p50 / p95 / max | 6.8 / 11.1 / 67 ms | 50 requests; Ollama unreachable, so every request used the red-flag guardrail (10) or the rules-based classifier (40) |
| API RSS after import / after 50 requests | 54 MB / 62 MB | excludes Ollama |
| STT `tiny` / `small` | not measured | Whisper weights are not cached in the container and Hugging Face is not reachable |
| Text triage with Gemma 4 (`gemma4:e2b`) | not measured | no Ollama runtime or weights in the container |

Raw output: [`spikes/spike01_baseline_results.json`](spikes/spike01_baseline_results.json).

## What still has to be measured on reference hardware

1. `scripts/benchmark_baseline.py --runs 50` with Ollama running `gemma4:e2b`
   and the `small` Whisper model downloaded (`python download_stt_model.py`).
2. `scripts/spikes/spike03_ocr.py` (OCR seconds per page) and, once Phase 3
   ships, the CT key-slice benchmark in `scripts/benchmark_imaging.py`.
3. Record the full-assessment p95 here; PRD §7 sets the text-only budget at
   ≤ 60 s pending this measurement.
