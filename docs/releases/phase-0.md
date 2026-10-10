# Phase 0 — Foundations and spikes

## Shipped

| Item | What |
|---|---|
| SPIKE-01 | `scripts/benchmark_baseline.py`; results in [benchmarks](../benchmarks.md) |
| SPIKE-02 | Recorded as open (no Ollama runtime in the build environment) |
| SPIKE-03 | `scripts/spikes/spike03_ocr.py`; OCR default chosen: 200 DPI, autocontrast + Otsu, `eng+hin+mar` |
| SPIKE-04 | `scripts/spikes/spike04_dicom.py`; `pydicom` + `pylibjpeg` decoder matrix on Linux |
| ADR-01..04 | [docs/adr](../adr/) — storage & encryption, job system, package layout, Mode B TLS |
| OPS-03 | Universal hash-pinned `requirements.lock` / `requirements-dev.lock` (Python 3.10–3.13), `scripts/lock_deps.sh`, Dependabot |
| OPS-04 (partial) | ruff lint + format, coverage, `pip-audit`, `gitleaks` in CI; Tesseract eng/hin/mar on CI runners |
| OPS-08 | Backend moved into the `healstation` package; `api.py` is the entry point |

## Measurements

- Rules-path text triage p95 11 ms, API RSS 62 MB, cold start 0.6 s (build container, not reference hardware).
- OCR on synthetic degraded reports: 100 % numeric recall at 200 DPI with binarisation, 0.65 s/page.
- 85 baseline tests pass on Python 3.10 and 3.13.

## Deviations from the exit criteria

- **Benchmarks are not from the reference hardware** and Gemma/Whisper timings are missing: the build
  environment has no Ollama runtime, no model weights and no access to Hugging Face. Re-run
  `scripts/benchmark_baseline.py` on the reference machine (PRD §4) with the model pulled.
- **SPIKE-02 is unanswered** for the same reason. Imaging assist (IMGX-08) is built behind
  `ENABLE_IMAGING_ASSIST=false` and must stay off until SPIKE-02 and QA-05 are done.
- **SPIKE-03 used synthetic reports**, not 20 real de-identified ones; **SPIKE-04 covered Linux only**.
- **D10 (clinical reviewers)** cannot be started from the code side; QA-01 vignettes written later are
  marked unreviewed until clinicians sign them off.

Later phases proceed on the code-side exit criteria and carry these items as open.
