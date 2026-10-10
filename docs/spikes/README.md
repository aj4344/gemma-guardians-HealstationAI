# Phase 0 spikes

Each spike answers one question the later phases depend on. Results were
produced in the implementation build container (4 vCPU, 15 GB RAM, Linux,
Python 3.13, no GPU). Spikes marked **open** must be repeated on the
reference hardware or with real data before the item they gate ships.

| Spike | Question | Answer | Status |
|---|---|---|---|
| SPIKE-01 | Baseline latency, memory, STT speed, cold start | Rules path p95 11 ms, RSS 62 MB, cold start 0.6 s; STT and Gemma not measurable here — see [benchmarks](../benchmarks.md) | **open** for STT and Gemma timing |
| SPIKE-02 | Does `gemma4:e2b` take images through Ollama `/api/chat`; latency and JSON-mode reliability | Not answerable in the container: no Ollama runtime or model weights are reachable. The imaging-assist code path (IMGX-08) is built behind `ENABLE_IMAGING_ASSIST=false` and is tested against a stub only | **open** — blocks enabling IMGX-08 anywhere |
| SPIKE-03 | OCR quality and settings for Hindi/Marathi/English lab reports | On 20 synthetic, degraded reports: 200 DPI + autocontrast + Otsu binarisation recovered 100 % of numeric results (0.65 s/page); without binarisation 95.7 %; 150 DPI 92–96 %. **Chosen: 200 DPI, autocontrast + Otsu, `eng+hin+mar`, PSM 6** | **open** — repeat on ≥ 20 real de-identified reports |
| SPIKE-04 | Which DICOM transfer syntaxes decode on Windows and Linux | Linux: uncompressed (LE/BE/implicit), deflate, RLE, JPEG baseline, JPEG-LS lossless, JPEG 2000 (lossless and lossy) decode with `pydicom` + `pylibjpeg` (`openjpeg`, `libjpeg`). The 12-bit JPEG Extended sample fails with both `pylibjpeg` and `python-gdcm`, so `gdcm` is not added; such series are rejected with `DICOM_UNSUPPORTED_SYNTAX` | **open** for Windows |

## SPIKE-03 detail

Script: [`scripts/spikes/spike03_ocr.py`](../../scripts/spikes/spike03_ocr.py) —
results: [`spike03_ocr_results.json`](spike03_ocr_results.json).

| Render scale | Preprocessing | Numeric recall | Mean word confidence | s/page |
|---|---|---|---|---|
| ~150 DPI | none | 0.921 | 90.2 | 0.62 |
| ~150 DPI | Otsu | 0.957 | 88.2 | 0.62 |
| ~200 DPI | none | 0.957 | 90.3 | 0.65 |
| **~200 DPI** | **autocontrast + Otsu** | **1.000** | **89.9** | **0.65** |
| ~300 DPI | autocontrast + Otsu | 0.993 | 92.1 | 0.70 |

Limits of this result: the synthetic pages use clean fonts, a fixed table
layout and English test names; real reports have stamps, handwriting, folds,
mixed-script test names and low-end phone photos. Treat 1.000 as an upper bound.

## SPIKE-04 detail

Script: [`scripts/spikes/spike04_dicom.py`](../../scripts/spikes/spike04_dicom.py) —
results: [`spike04_dicom_results.json`](spike04_dicom_results.json).
