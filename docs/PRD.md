# HealStation AI — Production Readiness PRD

| | |
|---|---|
| **Version** | 1.0 (final) |
| **Status** | Approved for implementation, pending the decisions in §14 |
| **Product owner** | aj4344 |
| **Repository** | `aj4344/gemma-guardians-HealstationAI` |
| **Baseline** | commit `9b199e2` on branch `aj4344-claude/inspiring-wozniak-dsc4ud` (audit + hardening pass) |
| **Reference repo** | `aj4344/PiedPiper_HealStation_MedicalTriage` (earlier cloud version; borrow list in Appendix E) |

---

## 0. Instructions for the implementing agent (read first)

1. **Start from the baseline.** Your working branch must contain commit `9b199e2`. Check with `git merge-base --is-ancestor 9b199e2 HEAD`; if it fails (e.g. your branch was cut from `main` before the hardening branch was merged), run `git fetch origin aj4344-claude/inspiring-wozniak-dsc4ud && git merge origin/aj4344-claude/inspiring-wozniak-dsc4ud` first. Then run the baseline checks before changing anything:
   ```bash
   pip install -r requirements-dev.txt && python -m pytest          # expect: 85 passed
   cd frontend && npm ci && npm run lint && npm run build             # expect: clean
   ```
2. **Work phase by phase (§11), in order.** Within a phase, work items are ordered; do not start a phase until the previous phase's exit criteria are met.
3. **One work item = one focused commit** (or PR), titled with its ID, e.g. `ING-03: stream uploads to encrypted quarantine`. Every commit keeps CI green.
4. **Every work item ships with tests** that would fail without the change. Requirements marked **[INV]** are safety/privacy invariants: each needs a dedicated regression test and must never be weakened.
5. **Do not guess on items marked [DECISION].** Use the recommended default in §14 if the product owner has not answered, and say so in the commit message.
6. **Never** (non-negotiable): send patient data off the device by default; log patient content; fabricate data (ratings, dispatches, results); let a model or upload *lower* urgency set by a safety rule; return "low" for a patient nobody assessed; copy the reference repo's mock ambulance dispatch or wildcard CORS.
7. Keep `README.md`, `.env.example` and the OpenAPI schema in sync with every change. Configuration lives only in `config.py`.

---

## 1. Summary

HealStation AI is an offline-first emergency triage assistant for ASHA and frontline health workers in rural India. A worker describes symptoms by voice or text in English, Hindi or Marathi and gets a structured triage decision (urgency, reasons, actions, specialist, nearest capable hospital) from Gemma 4 running locally via Ollama, guarded by deterministic clinical safety rules.

The baseline is a hardened hackathon build: the triage core is sound and tested, but the product cannot yet safely accept the data health workers actually have — **PDF lab reports, photos, CT/X-ray scans (DICOM) and voice recordings**. Uploaded files are currently accepted as base64 JSON and then ignored. There is no persistent case record, no authentication, no encryption at rest, no job queue, and no clinical validation harness.

This PRD defines the work to turn it into a production product: a single, streamlined, leak-proof, resource-bounded pipeline for every input type, multimodal triage fusion with provenance, secure case management and referral workflow, and the operational and clinical-validation scaffolding required to deploy it.

## 2. Problem statement

| # | Problem | Evidence in baseline |
|---|---|---|
| P1 | Uploaded PDFs/images do nothing | `image_data`/`pdf_data` only counted in `consensus_explanation`; README now states "not yet analysed" |
| P2 | Uploads can exhaust memory ("burst") | Files sent as base64 inside JSON (≈33 % overhead), fully buffered, up to `MAX_REQUEST_MB=60` per request; no queue, no concurrency limit on the LLM |
| P3 | No CT / X-ray support | No DICOM parsing, no de-identification; scans carry patient name/ID/DOB/institution in headers |
| P4 | Patient data has no lifecycle | No case store; nothing encrypted at rest; only TTS audio has a retention rule |
| P5 | No identity or access control | API binds to localhost but has no auth; unusable on a shared PHC network |
| P6 | Safety not measured | 85 unit tests, but no labelled clinical vignette set, no under-triage metric, no model-change gate |
| P7 | Thin product workflow | No case history, referral slip, follow-up, or first-aid guidance; hospital list covers 7 cities; specialist directory unverified |
| P8 | Frontend not scalable | `App.jsx` ≈ 2,900 lines; many user-facing strings hardcoded in English; no offline shell |

## 3. Goals and non-goals

### Goals (release 1.0)
- **G1 Streamlined ingestion:** one pipeline for audio, images, PDFs and DICOM: stream → quarantine → validate → sanitize → extract → feed triage → retain/erase.
- **G2 Never leaks:** patient data stays on the device (or PHC hub), is encrypted at rest, never appears in logs, and is deleted on a defined schedule or on demand.
- **G3 Never bursts:** hard limits on every input dimension, bounded concurrency per heavy resource, back-pressure instead of crashes, and an emergency fast path that never waits behind long jobs.
- **G4 Multimodal value:** lab values, document text and image observations measurably improve triage, with every reason traceable to its source.
- **G5 Clinically measurable:** a labelled evaluation set and a release gate on under-triage.
- **G6 Deployable product:** case records, referral slip, roles and audit, containerized install, observability without PHI.

### Non-goals (1.0)
- Autonomous diagnosis or treatment prescribing. The product supports triage and referral decisions; a clinician decides.
- Radiology reporting. Imaging support is de-identification, viewing, store-and-forward and **optional, flagged** AI observations (§6.4).
- Cloud inference by default. An opt-in online tier is out of scope for 1.0.
- Real ambulance dispatch integration (no public 108 API). The product links to calling 108 and shows **estimates** only.
- Payments, telemedicine video, EHR/HMIS bi-directional integration (roadmap).

## 4. Users and deployment modes

### Personas
| Persona | Context | Needs |
|---|---|---|
| **ASHA / frontline worker** (primary) | Village visits, low-end Android phone/tablet or shared laptop, intermittent or no internet, Hindi/Marathi | Fast, unambiguous "what to do now"; voice input; works offline; minimal typing |
| **PHC Medical Officer** | Primary Health Centre, receives referrals | Case summary with vitals, labs, scans and AI reasoning; trust signals (sources, confidence) |
| **PHC admin / IT** | Installs and maintains | One-command install, updates, backups, user management, no cloud dependency |
| **Programme / quality lead** | District level | De-identified quality metrics: under-triage, fairness by language/age/sex |

### Deployment modes
- **Mode A — Single device (1.0 must-have):** one laptop runs Ollama + API + UI (`python api.py` or Docker). One or a few workers use it directly. Bound to `127.0.0.1`.
- **Mode B — PHC hub (1.0 should-have, [DECISION D1]):** one PHC machine serves several tablets on the local network. Requires authentication, TLS on the LAN, per-user access control and an audit log.

### Reference hardware [DECISION D2]
Default until decided: **8 GB RAM, 4-core x86-64 CPU, no GPU, 128 GB SSD, Windows 11 or Ubuntu 22.04/24.04.** All performance budgets are measured on this machine (Phase 0 establishes the baseline).

## 5. Product principles and invariants

| ID | Invariant **[INV]** |
|---|---|
| INV-1 | Deterministic safety rules (toxin fast-lane, red-flag guardrail, critical vitals, **critical lab values**) run before and independently of any model, and their result is returned to the user **before** any queued work completes. |
| INV-2 | Urgency can only be **raised** by later stages. Models, extracted documents and image observations never lower an urgency set by a rule. Final urgency = max(all sources). |
| INV-3 | A patient nobody assessed is never shown "low". Failures are shown as failures with "call 108 if severe" guidance in the user's language. |
| INV-4 | No patient content (symptoms, transcripts, extracted text, filenames, model output, coordinates, images) in logs, metrics, error responses, URLs or browser storage. |
| INV-5 | No patient data leaves the deployment unless a user explicitly triggers it for one case (referral PDF export, opt-in SMS), and each such action is audited. |
| INV-6 | Every stored patient artefact is encrypted at rest and has an expiry; raw uploads are deleted as soon as extraction completes unless retention is explicitly configured. |
| INV-7 | DICOM data is de-identified before anything other than the de-identifier reads it, and only de-identified derivatives are stored. |
| INV-8 | No fabricated data: no invented ratings, slots, dispatches, verifications or lab values. Unverified data is labelled unverified. |
| INV-9 | Every input has hard limits (bytes, pages, pixels, duration, files, ratio) enforced while streaming, before full parsing. |
| INV-10 | AI-generated imaging content is labelled "AI observations — not a diagnosis — requires clinician/radiologist review" wherever displayed or exported. |

## 6. Functional requirements

Priorities: **P0** = release blocker, **P1** = required for 1.0, **P2** = nice to have.

### 6.1 Unified ingestion pipeline (ING)

All file inputs go through one state machine:

```
RECEIVING → QUARANTINED → VALIDATING → SANITIZING → EXTRACTING → READY
                 │             │             │            │
                 └──────────── REJECTED (reason code) ────┘        → EXPIRED / ERASED
```

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| ING-01 | P0 | Replace base64-in-JSON with **multipart streaming uploads** (`POST /api/v2/cases/{case_id}/attachments`), one file per request. | 300 MB DICOM zip upload keeps API RSS growth < 50 MB; request body never fully buffered (test with a generator body). |
| ING-02 | P0 | Enforce per-type limits **while streaming** (Appendix A); abort and delete partial data on breach. | Oversize upload returns `413` with reason code `FILE_TOO_LARGE` before the full body is read; no residue on disk. |
| ING-03 | P0 | Write incoming bytes directly to an **encrypted quarantine** (AES-256-GCM, chunked, per-file key; §6.6). Server-generated UUID names only; the client filename is stored encrypted as metadata and never used in paths. | Quarantine files are unreadable without the key (test); path traversal filenames (`../../x`, `CON`, NUL bytes) stored safely. |
| ING-04 | P0 | **Type detection by magic bytes**, not client MIME or extension (Appendix B). Mismatch between declared and detected type → reject. Polyglots (multiple valid signatures) → reject. | Renamed `.exe`→`.pdf` rejected with `UNSUPPORTED_TYPE`; JPEG with `application/pdf` MIME rejected. |
| ING-05 | P0 | Per-attachment **status API** with stage, progress, reason codes and a de-identified summary of extracted content. Never returns raw file bytes to anyone but an authorized clinician view (Mode B). | `GET .../attachments/{id}` shows stage transitions; summary contains no filename. |
| ING-06 | P0 | **Delete** endpoint and automatic expiry (§6.6). Deleting a case deletes all its attachments, derivatives and outputs. | After delete, no file with that case ID exists on disk; DB rows tombstoned (no content). |
| ING-07 | P1 | **Duplicate detection** by content hash per case (hash stored keyed with a per-install secret so it cannot be used to confirm a known file elsewhere). | Same file twice → second returns the existing attachment. |
| ING-08 | P1 | **Malware scan hook** (ClamAV if installed, Mode B), run in VALIDATING. [DECISION D11] | With hook enabled, EICAR test file rejected `MALWARE_DETECTED`. |
| ING-09 | P1 | Startup **sweeper**: deletes orphaned quarantine/temp files and expired artefacts; runs hourly. | Kill the server mid-upload, restart → partial file removed within one sweep. |

#### 6.1.1 Audio (voice input)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| AUD-01 | P0 | Accept WebM/Opus, Ogg, WAV, MP3, M4A/AAC (detected by magic bytes). | Each format in fixtures transcribes; others rejected. |
| AUD-02 | P0 | Decode with PyAV (already a faster-whisper dependency) to **16 kHz mono PCM** in a 0700 temp dir; enforce max **duration** (default 300 s) by reading the container duration *and* counting decoded samples (headers lie). | A 10-minute file declared as 10 s is cut off at the limit with `AUDIO_TOO_LONG`. |
| AUD-03 | P0 | Run faster-whisper with VAD; return transcript, detected language, average log-probability and a **low-confidence flag**. If detected language ≠ selected language with high probability, warn the user ("Did you speak Hindi?"). | Low-quality fixture produces `low_confidence: true` and the UI asks the worker to confirm/edit. |
| AUD-04 | P0 | Transcript is shown for **confirmation/editing** before triage; triage uses the confirmed text. The raw audio is deleted after transcription (INV-6). | Audio file absent after transcription completes. |
| AUD-05 | P1 | Run the red-flag guardrail on the transcript immediately and show any emergency banner while the worker is still confirming. | Transcript "chest pain sweating" shows the emergency banner < 300 ms after transcript returns. |
| AUD-06 | P2 | Code-mixed speech (Hinglish/Marathi-English) handled: guardrail keyword lists include romanized Hindi/Marathi phrases ("seene mein dard", "saans phool rahi"). | Romanized fixtures trigger the correct categories. |

#### 6.1.2 Images (photos of wounds, skin, documents, prescriptions)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| IMG-01 | P0 | Accept JPEG, PNG, WebP, HEIC/HEIF (pillow-heif). Set `Image.MAX_IMAGE_PIXELS` to the limit; call `verify()` then reopen; reject truncated/corrupt files. | Decompression-bomb fixture (e.g. 30 000×30 000 PNG) rejected `IMAGE_TOO_LARGE` without allocating it. |
| IMG-02 | P0 | **Sanitize**: re-encode to JPEG/PNG, long edge ≤ 2048 px, apply EXIF orientation then **strip all metadata** (EXIF incl. GPS, XMP, ICC kept only if sRGB-safe). Only the sanitized derivative is kept. | Output has no EXIF/GPS (test reads tags); original deleted. |
| IMG-03 | P1 | **Classify** each image as `document` (report/prescription photo) or `clinical` (wound, rash, eye, etc.) using a fast heuristic (text density via OCR confidence) with model fallback. Documents go to OCR (§6.1.3); clinical photos go to imaging assist (§6.4). | Fixture set classified with ≥ 90 % accuracy. |
| IMG-04 | P1 | Image quality checks (blur via Laplacian variance, too dark/bright) produce actionable feedback ("Photo is blurry — retake in daylight"). | Blurry fixture → `quality_issues: ["blurry"]`, localized message. |

#### 6.1.3 PDFs and document photos (lab reports, discharge summaries)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| PDF-01 | P0 | Replace deprecated PyPDF2 with **pypdf**; parse only (never render JavaScript, forms, attachments, or external links). Reject encrypted PDFs (`PDF_ENCRYPTED`), enforce max pages and max decompressed stream size; run parsing in a **subprocess with CPU-time and memory limits** so a malicious PDF cannot hang or OOM the API. | Zip-bomb PDF and infinite-loop fixtures terminate within the job timeout with `PDF_UNREADABLE`; API stays responsive. |
| PDF-02 | P0 | Extract the text layer per page. If a page has < 30 extractable characters, mark it **scanned** and OCR it: render with pypdfium2 at 200 DPI → Tesseract (`eng+hin+mar`) → per-page confidence. OCR is capped at `MAX_OCR_PAGES`. | Scanned fixture yields text with mean confidence reported; pages beyond the cap listed as `not_processed`. |
| PDF-03 | P0 | **Structured lab extraction** to a fixed schema: `{test, value, unit, ref_low, ref_high, flag, page, source_text}` using a rules parser for common Indian lab formats first, then the LLM in JSON mode for leftovers, then **unit normalization** (mg/dL ↔ mmol/L for glucose; g/dL Hb; lakh/µL platelets). Values the LLM returns that do not appear in the source text are discarded (anti-hallucination check). | On 30 labelled reports: field-level precision ≥ 0.95, recall ≥ 0.85; zero values not present in source. |
| PDF-04 | P0 | **Critical lab values floor** (INV-1/INV-2): a clinician-approved table (draft in Appendix D) sets urgency HIGH and adds a reason citing the report and page. | Report with K⁺ 7.1 mmol/L forces `urgency: high` with reason "Potassium 7.1 mmol/L (report p.1) — critical". |
| PDF-05 | P1 | **Document summary** for the clinician: report type, date, facility (if present), abnormal values first, ≤ 120 words, in the selected language, with the original-language values preserved. | Summary lists abnormal results first; numbers identical to source. |
| PDF-06 | P1 | Report **date awareness**: results older than a configurable age (default 30 days) are labelled "old result" and do not trigger the critical floor alone. [DECISION D12] | 6-month-old critical value shows "old result" and only raises to MEDIUM. |

#### 6.1.4 Ingestion of DICOM / CT / X-ray — see §6.4 (imaging), which reuses ING-01..09.

### 6.2 Resource governance — "must not burst" (RES)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| RES-01 | P0 | **Emergency fast path** (INV-1): `POST /api/v2/cases/{id}/assess` evaluates toxin lane, red-flag guardrail, critical vitals and already-extracted critical labs **synchronously** (no model, no queue) and returns them with a `job_id` for the full assessment. | p95 < 300 ms even while 20 jobs are queued and the LLM is busy (load test). |
| RES-02 | P0 | **Job queue** with persistent job table (SQLite) and per-resource worker pools: `llm=1`, `stt=1`, `ocr=2`, `imaging=1`, `pdf=2` (configurable). Jobs survive restart (resumed or marked failed). | Kill -9 during a job → on restart the job is retried once, then `FAILED` with a user-visible message. |
| RES-03 | P0 | **Back-pressure:** bounded queue depth (default 20); when full return `429` with `Retry-After` and a localized message; the emergency fast path is never subject to this limit. | 25 concurrent assessments → 20 queued, 5 receive 429; the fast path still answers. |
| RES-04 | P0 | **Timeouts** per job type (LLM 120 s, STT 2× audio duration + 30 s, OCR 20 s/page, imaging 180 s) with cancellation; partial results are kept and labelled. | LLM stub sleeping 300 s → job ends `TIMED_OUT`, rules-based result shown. |
| RES-05 | P0 | **Memory and disk budgets:** API process RSS ≤ 1.5 GB excluding Ollama (reference hardware); total case storage quota (default 5 GB) with eviction of expired data first and a clear "storage full" error otherwise; refuse uploads when free disk < 2 GB. | Filling the quota returns `507 STORAGE_FULL`; no crash. |
| RES-06 | P1 | **Progress events** via Server-Sent Events (`GET /api/v2/jobs/{id}/events`) with polling fallback; the UI shows stage names, not spinners only. | UI shows "Transcribing… → Reading report (page 2/5) → Assessing…". |
| RES-07 | P1 | **Model availability handling:** if Ollama is down or the model is missing, jobs degrade to the rules-based classifier within 2 s and the result says so; `/api/v2/health/ready` reports `degraded`. | Ollama stopped → assessment completes via `emergency_fallback` with a visible "AI model offline" notice. |
| RES-08 | P1 | **Context budget manager:** assemble the model prompt within `LOCAL_GEMMA_NUM_CTX` by priority — safety findings, confirmed symptoms, vitals, abnormal labs, document summary, image observations — truncating lowest priority first and recording what was dropped. | With 10 reports attached, prompt token estimate ≤ budget and `context_truncated` lists dropped items. |

### 6.3 Multimodal triage fusion (FUS)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FUS-01 | P0 | Build a structured **ClinicalContext** per assessment: demographics, confirmed symptom text, vitals, lab findings, document summaries, image observations, history, each item tagged with its **source** (`typed`, `transcript`, `report:<id>:p<n>`, `image:<id>`, `dicom:<series>`). | Unit test round-trips a context with all source types. |
| FUS-02 | P0 | **Fusion rule (INV-2):** final urgency = max(toxin lane, red-flag guardrail, critical vitals, critical labs, model urgency, imaging escalation flags, rules-based classifier when model confidence < threshold). [DECISION D8] | Property test: adding any input never lowers the final urgency. |
| FUS-03 | P0 | **Provenance:** every reason shown to the user cites its source(s); the UI renders them as chips ("from report p.2"). | Response schema: `reasons[] = {text, sources[]}`; UI test. |
| FUS-04 | P1 | Extend `consensus_explanation` to detect conflicts across modalities (e.g. typed "mild" vs transcript "severe", vitals critical vs text benign) and record the conservative resolution. | Conflict fixtures produce `conflict: true` with the specific pair. |
| FUS-05 | P1 | Guardrail upgrades: Hindi/Marathi negation ("दर्द नहीं", "दुखत नाही"), history context ("father had a stroke", "last year", "history of") reduces to MEDIUM instead of HIGH, never to LOW. | Fixtures; no regression in the existing red-flag tests. |
| FUS-06 | P1 | Model output schema v2 with JSON schema validation and one automatic repair retry; invalid output → rules-based result (never "low"). | Malformed-output fixtures covered. |

### 6.4 Imaging: DICOM, CT, X-ray and clinical photos (IMGX)

> Gemma 4 E2B accepts image input, but neither the model nor this product has been validated for reading CT or X-ray. Therefore 1.0 ships **store-and-forward imaging** by default and **AI imaging observations only behind `ENABLE_IMAGING_ASSIST` (default off)** until the validation in QA-05 passes. [DECISION D3]

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| IMGX-01 | P0 | Accept a single `.dcm` file or a **ZIP of a series/study**. ZIP safety: max entries (1,000), max total uncompressed size (1 GB), max per-entry compression ratio (100:1), reject absolute paths, `..`, symlinks and nested archives; stream-extract into the encrypted quarantine. | Zip-bomb and path-traversal fixtures rejected with specific reason codes. |
| IMGX-02 | P0 | Parse with **pydicom** (+ `pylibjpeg`/`gdcm` handlers for compressed transfer syntaxes); validate preamble `DICM`; reject non-image SOP classes (SR, PDF-in-DICOM handled separately or rejected). | Fixtures: CT, CR/DX X-ray, JPEG-2000 compressed; SR rejected. |
| IMGX-03 | P0 | **De-identify first (INV-7)** following the DICOM PS3.15 Annex E *Basic Application Level Confidentiality Profile*: remove/blank patient name, ID, birth date, addresses, physician names, institution, accession/study IDs, dates (shift or remove — [DECISION D13]), private tags; replace UIDs consistently within a case; keep only technical tags needed for display (modality, body part, slice thickness, pixel spacing, window centre/width, orientation). Record `PatientIdentityRemoved=YES` and the method. | Tag-scan test: none of the Appendix C tags remain in any stored derivative. |
| IMGX-04 | P0 | **Burned-in PHI:** if `BurnedInAnnotation=YES` or the modality is US/secondary capture, run OCR on the pixel border regions and **mask** detected text; if masking cannot be confirmed, keep the image out of AI processing and flag "may contain identifying text". | Fixture with burned-in name → masked derivative; masked region verified by OCR returning no text. |
| IMGX-05 | P0 | **Series handling:** group by SeriesInstanceUID, sort by ImagePositionPatient/InstanceNumber, apply modality LUT and **windowing presets** (CT brain 40/80, subdural 75/215, lung −600/1500, bone 400/1800, soft tissue 50/400; X-ray uses VOI LUT), select ≤ 16 key slices (evenly spaced, plus slices with maximal intensity variance), export 8-bit PNG derivatives ≤ 1024 px. | 300-slice CT → ≤ 16 PNGs in < 60 s on reference hardware; RSS within RES-05. |
| IMGX-06 | P0 | **Viewer:** the UI shows de-identified key images with window preset switching and slice scrubbing (no external viewer, no CDN). | Works offline on a mid-range Android tablet. |
| IMGX-07 | P0 | **Store-and-forward:** de-identified key images and series metadata are attached to the referral packet (§6.7) for the receiving clinician. | Referral PDF includes thumbnails + "de-identified" stamp; full derivatives exportable as a ZIP for the MO. |
| IMGX-08 | P1 | **Imaging assist (flagged):** vision prompt asks for *observations only* in a fixed schema `{observations[], urgent_flags[] ∈ {possible_bleed, possible_fracture, possible_pneumothorax, mass_effect, other}, quality_issues[], confidence}`; output can only **escalate** urgency (INV-2) and is always labelled per INV-10; never names a diagnosis as fact. | Flag off → no model call for images (test); flag on → schema-valid output and the INV-10 label in API, UI and PDF. |
| IMGX-09 | P1 | Clinical photos (wound, rash, eye, swelling) use the same assist path with photo-specific prompts and quality checks (IMG-04). | Fixture set produces schema-valid observations. |

### 6.5 Voice output (TTS)
| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| TTS-01 | P1 | [DECISION D5] Prefer **browser `speechSynthesis`** when a voice for the language exists on the device (no server audio, no files); fall back to server pyttsx3 (current behaviour) otherwise. | On a device with a Hindi voice, no `/api/audio` request is made. |
| TTS-02 | P1 | Server TTS output follows INV-6 (already: random names, 1 h retention) and moves under the encrypted case store. | Audio files encrypted at rest; served decrypted in-stream only to the case owner. |

### 6.6 Data protection and privacy (SEC/PRIV)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| PRIV-01 | P0 | **Encrypted case store:** SQLite (via SQLAlchemy + Alembic migrations) with field-level encryption for clinical content, and AES-256-GCM chunked encryption for files. Per-case data key wrapped by a key-encryption key from the OS keyring (Windows DPAPI / Linux Secret Service) or an env/secret file in containers. Keys never logged or stored beside data. | DB file and blobs contain no plaintext symptom text (grep test); losing the KEK makes data unreadable. |
| PRIV-02 | P0 | **Retention policy** (Appendix A defaults): raw uploads deleted after extraction; derivatives and case content expire after `CASE_RETENTION_DAYS` (default 30, Mode A 7); TTS audio 1 h. Expiry enforced by the sweeper (ING-09). | Time-travel test advances the clock; all expired artefacts gone. |
| PRIV-03 | P0 | **"End visit & erase"** button and `DELETE /api/v2/cases/{id}`: crypto-shred (destroy the case key), then delete files and rows. | After erase, artefacts are unrecoverable even from a disk copy (key destroyed). |
| PRIV-04 | P0 | **Log hygiene (INV-4) enforced in code:** a logging filter allowlists structured fields; free-text messages are scanned for patient content patterns and dropped; uvicorn access logs strip query strings; exceptions logged with type and traceback but without locals or request bodies. | Test injects a sentinel symptom string through every endpoint and asserts it never appears in captured logs. |
| PRIV-05 | P0 | **Consent and notice** (DPDP Act 2023 / DPDP Rules 2025 — main obligations apply from May 2027): before the first case of each patient, show a short notice in en/hi/mr (what is collected, purpose, retention, rights) and record consent (who, when, notice version). Legal review required. [DECISION D7] | Case cannot be assessed without a consent record, except via the emergency fast path (vital interest), which records `consent: emergency_exception`. |
| PRIV-06 | P1 | **Data-principal requests** (Mode B): export a patient's data as a PDF/JSON bundle and erase on request; both audited. | Endpoint + audit entries. |
| PRIV-07 | P0 | **Browser hygiene:** no patient data in `localStorage`/`IndexedDB`/service-worker caches; in-memory state cleared on "End visit", logout and idle timeout; `Cache-Control: no-store` on all `/api` responses. | Playwright test inspects storage after a full case: empty. |
| PRIV-08 | P1 | **Export controls (INV-5):** referral PDF/ZIP export and SMS require an explicit action with a preview; each creates an audit event; exports are watermarked with case pseudonym and timestamp. | Audit log shows each export; no automatic exports anywhere. |

### 6.7 Identity, access and audit (IAM) — required for Mode B, optional PIN lock for Mode A

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| IAM-01 | P0 (Mode B) | Local accounts with roles: `health_worker`, `medical_officer`, `admin`. Passwords hashed with Argon2id; first-run admin bootstrap via CLI, not a default password. | No default credentials anywhere (test). |
| IAM-02 | P0 (Mode B) | Sessions: HttpOnly, Secure, SameSite=Strict cookies + CSRF token on state-changing requests; idle timeout 15 min, absolute 12 h; login rate limiting and lockout. | Security tests for CSRF, fixation, lockout. |
| IAM-03 | P0 (Mode B) | Authorization: workers see their own cases; MOs see their facility's cases; admins manage users and settings but **cannot read clinical content**. Fairness/quality metrics only for MO/admin (today they are returned to every client). | Access-matrix tests for every endpoint. |
| IAM-04 | P1 (Mode A) | Optional device PIN lock with auto-lock after inactivity. | Locked UI hides case data. |
| IAM-05 | P0 | **Audit log** (append-only, hash-chained, no clinical content): login, case create/view/assess/export/erase, settings change, user management. | Tampering with a past entry breaks verification (test). |
| IAM-06 | P0 (Mode B) | TLS on the LAN via a bundled reverse proxy (e.g. Caddy) with a local CA and documented device enrolment; API refuses non-loopback plaintext unless `ALLOW_INSECURE_LAN=true` (dev only). | Starting with `API_HOST=0.0.0.0` and no TLS proxy logs a fatal config error. |

### 6.8 Case management and referral workflow (CASE) — the product value

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| CASE-01 | P0 | **Case record:** pseudonymous patient ID, age band/age, sex, village/area (optional), ABHA number (optional, validated format), visits with assessments, attachments and outcome. | CRUD with tests; no free-text fields indexed in plaintext. |
| CASE-02 | P0 | **Assessment result screen:** urgency banner localized (today it is English-only), actions as a numbered checklist, reasons with source chips, vitals/labs table with abnormal values highlighted, "Call 108" button, nearest capable hospital. | Visual regression snapshot per urgency × language. |
| CASE-03 | P0 | **Referral slip** (bilingual PDF, printable and shareable on explicit action): patient pseudonym, timestamp, urgency, reasons with sources, vitals, abnormal labs, imaging key images (de-identified) with INV-10 label, actions taken, referring worker, destination facility. | Golden-file PDF test; no data beyond the listed fields. |
| CASE-04 | P1 | **Follow-up:** worker sets a follow-up date/outcome (`admitted`, `treated`, `referred_on`, `died`, `unknown`); due follow-ups listed on the home screen. Outcomes feed the quality metrics (QA-03). | Follow-up list and outcome capture with tests. |
| CASE-05 | P1 | **First-aid guidance while waiting** (borrowed idea from the reference repo's `/api/ambulance/first-aid/{type}`): clinician-reviewed, offline, en/hi/mr, per emergency type (cardiac, stroke, bleeding, burns, poisoning, snakebite, seizure, choking, drowning, heat stroke, childbirth). | Content file versioned with reviewer and date; shown on HIGH results. |
| CASE-06 | P1 | **Hospital routing data:** replace the 7-city static list with an importable, versioned dataset (source, licence, date) built from public registries (e.g. ABDM Health Facility Registry / data.gov.in hospital directory) via `scripts/import_facilities.py`; capability fields only where the source provides them. Optional online refresh via Overpass (reference repo) cached locally, off by default. | Import tool + dataset metadata displayed in UI ("Data as of …"). |
| CASE-07 | P1 | **Specialist directory:** remove named-doctor entries (unverified, INV-8) in favour of facility-level departments from the imported dataset. [DECISION D4] | No personal names in shipped data. |
| CASE-08 | P2 | **Family SMS alert** (reference repo's Fast2SMS service, re-designed): opt-in per case, explicit preview, only when online, queued in an outbox, consent recorded, no demo mode in production builds, message excludes clinical detail beyond urgency and hospital. [DECISION D7] | Outbox tests; production build refuses `SMS_DEMO_MODE`. |
| CASE-09 | P2 | **ETA estimate** to the chosen hospital (Haversine × road factor × time-of-day speed table), always labelled "estimate". **No dispatch endpoint** — the reference repo's mock dispatch must not be ported. | UI label test; grep test that no "dispatched" wording exists. |

### 6.9 Clinical safety and quality (QA)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| QA-01 | P0 | **Golden vignette set** `eval/vignettes/*.jsonl`: ≥ 300 cases (≥ 100 per language), each with symptoms, optional vitals/labs, expected urgency, red-flag category, and reviewer ID; includes typos, code-mixed text, negations, family history and paediatric/obstetric cases. [DECISION D10] | Schema-validated; reviewed by ≥ 2 clinicians. |
| QA-02 | P0 | **Evaluation harness** `scripts/eval_triage.py` runs the full pipeline against live Ollama and reports: sensitivity for HIGH, **under-triage rate**, over-triage rate, per-language/age/sex parity, latency percentiles, JSON validity rate. | Report artefact (markdown + JSON) per run. |
| QA-03 | P0 | **Release gate:** sensitivity(HIGH) ≥ 0.95 (target 0.98) on the red-flag subset, under-triage ≤ 2 % overall, per-language sensitivity gap ≤ 5 pp, zero INV regressions. Any model, prompt or threshold change must re-run the gate. | CI job (manual trigger, needs Ollama runner) blocks release tagging. |
| QA-04 | P1 | **"Report a problem with this assessment"** button: stores a de-identified snapshot (inputs, outputs, versions) locally for quality review; exportable by MO/admin. | Snapshot contains no direct identifiers. |
| QA-05 | P1 | **Imaging assist validation** before enabling IMGX-08 anywhere: ≥ 200 de-identified, labelled studies per supported finding; report sensitivity/specificity of `urgent_flags`; product owner + clinician sign-off recorded. | Validation report committed under `eval/imaging/`. |
| QA-06 | P0 | **Versioning:** every assessment records model tag + digest, prompt version, rule-table versions and app version. | Present in API response metadata and stored assessment. |
| QA-07 | P0 | **Regulatory note:** document the intended-use statement and obtain a regulatory assessment of whether the product is Software as a Medical Device under India's Medical Devices Rules, 2017 (CDSCO) before field deployment. [DECISION D9] | `docs/INTENDED_USE.md` signed off. |

### 6.10 Frontend (FE)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| FE-01 | P0 | Split `App.jsx` (~2,900 lines) into feature modules: `features/intake` (voice, text, vitals), `features/attachments`, `features/assessment`, `features/case`, `features/emergency`, `features/settings`; shared `api/` client with typed endpoints and error mapping. No behaviour change in this step. | Playwright smoke (existing e2e flow) passes before/after; no file > 600 lines. |
| FE-02 | P0 | **i18n:** move every user-visible string (incl. alerts, urgency banners, errors, status badges) to `locales/{en,hi,mr}.json`; CI check fails on hardcoded user-facing English in JSX. | Missing-key test across all three locales. |
| FE-03 | P0 | **Attachment UX:** per-file upload progress, stage display (RES-06), reason-coded rejections with localized fixes, retry, remove; DICOM ZIP support; camera capture on mobile. | e2e tests for success, oversize, wrong type, cancel. |
| FE-04 | P1 | **PWA offline shell:** service worker caches only static assets; `/api` responses never cached (PRIV-07); install prompt on Android. | Lighthouse PWA checks; storage test. |
| FE-05 | P1 | **Accessibility WCAG 2.1 AA:** contrast, 48 px touch targets, focus order, ARIA live region for the urgency result, screen-reader labels in all languages. | axe-core in Playwright: zero serious/critical violations. |
| FE-06 | P1 | **Performance budget:** initial JS ≤ 250 kB gzip; time-to-interactive ≤ 4 s on a mid-range Android device over local Wi-Fi; images lazy-loaded. | Bundle-size CI check; manual device test recorded. |
| FE-07 | P1 | Frontend unit tests (Vitest + Testing Library) for API client, i18n and result rendering. | Coverage ≥ 70 % on `api/` and `features/assessment`. |

### 6.11 API v2 (API)

| ID | Pri | Requirement |
|---|---|---|
| API-01 | P0 | Versioned `/api/v2` with OpenAPI docs; v1 endpoints keep working, marked deprecated, until the frontend has migrated (then removed in 1.1). |
| API-02 | P0 | Uniform error envelope: `{error: {code, message_localized, retryable, retry_after_s?}, request_id}`; codes listed in Appendix B; never exception text. |
| API-03 | P0 | Every response carries `X-Request-ID`; all `/api` responses `Cache-Control: no-store`; security headers (CSP without external origins, `X-Content-Type-Options`, `Referrer-Policy: no-referrer`, `Permissions-Policy` limiting camera/mic/geolocation to self). |
| API-04 | P1 | Idempotency keys on `POST` creating cases/attachments/assessments (retries on flaky Wi-Fi must not duplicate). |

Endpoint sketch (shapes are normative; names may be refined in the OpenAPI):

```
POST   /api/v2/cases                                  → 201 {case_id}
GET    /api/v2/cases/{case_id}                         → case summary (no raw files)
DELETE /api/v2/cases/{case_id}                         → 204 (crypto-shred)
POST   /api/v2/cases/{case_id}/consent                 → 201
POST   /api/v2/cases/{case_id}/attachments  (multipart, one file) → 202 {attachment_id, stage}
GET    /api/v2/cases/{case_id}/attachments/{att_id}    → {stage, progress, reason_code?, summary?}
DELETE /api/v2/cases/{case_id}/attachments/{att_id}    → 204
POST   /api/v2/transcriptions (multipart audio)        → 202 {job_id}   (result: transcript, language, confidence)
POST   /api/v2/cases/{case_id}/assess  {symptoms_confirmed, vitals?, language}
                                                       → 200 {fast_path: {urgency, reasons, emergency_action_block}, job_id}
GET    /api/v2/jobs/{job_id}                           → {status, stage, progress, result?}
GET    /api/v2/jobs/{job_id}/events                    → SSE stream
POST   /api/v2/cases/{case_id}/referral                → 200 application/pdf (audited)
GET    /api/v2/cases/{case_id}/imaging/{series}/slices/{n}?window=brain → image/png (de-identified)
GET    /api/v2/health/live | /api/v2/health/ready      → liveness / readiness incl. model + queue saturation
GET    /api/v2/metrics                                 → Prometheus text, no PHI, admin/loopback only
POST   /api/v2/auth/login | /logout                    (Mode B)
```

### 6.12 Platform and operations (OPS)

| ID | Pri | Requirement | Acceptance criteria |
|---|---|---|---|
| OPS-01 | P0 | **Container:** multi-stage Dockerfile (builds the frontend, then a slim Python runtime), non-root user, read-only root FS except data volume, `HEALTHCHECK` on `/api/v2/health/live`, `tesseract-ocr` + `hin`/`mar` traineddata + `espeak-ng` installed; `docker-compose.yml` with Ollama service and a named encrypted-data volume. (Reference repo's Dockerfile is a starting point but runs as root and exposes 0.0.0.0 without auth.) | `docker compose up` → working app offline after first model pull. |
| OPS-02 | P0 | **Native installers/scripts** for Windows and Linux (Mode A): install dependencies, pull model, download Whisper model, create first admin/PIN, register as a service; `check_offline_ready.py` extended to cover OCR languages, DICOM handlers and disk space. | Fresh-machine install documented and tested on the reference hardware. |
| OPS-03 | P0 | **Locked dependencies:** `requirements.lock` via `pip-tools`/`uv` with hashes; `package-lock.json` already present; Dependabot/Renovate configured; SBOM (CycloneDX) generated per release. | CI installs from lock with `--require-hashes`. |
| OPS-04 | P0 | **CI expansion:** ruff (lint+format), mypy on `api/ingest/fusion` packages, pytest with coverage ≥ 80 % on new code, `pip-audit`, `npm audit`, `bandit`/`semgrep`, `gitleaks`, Playwright e2e smoke with a stubbed model, Docker build. | All jobs required on PRs. |
| OPS-05 | P1 | **Observability without PHI:** structured JSON logs with request ID, stage, durations and reason codes; Prometheus metrics (queue depth, job durations by type, rejects by reason, model availability, disk usage); optional local dashboard. | Metrics endpoint test asserts no label carries free text. |
| OPS-06 | P1 | **Backups (Mode B):** encrypted nightly backup of DB + keys-wrapped blobs to an external drive path; documented restore drill. | Restore test in CI using a fixture backup. |
| OPS-07 | P1 | **Config validation at startup:** invalid combinations fail fast with a clear message (e.g. `API_HOST=0.0.0.0` without TLS proxy in Mode B; missing KEK; quota below minimum). | Tests for each fatal config. |
| OPS-08 | P1 | **Code structure:** move backend into a package (`healstation/api`, `ingest`, `fusion`, `triage`, `store`, `security`) with `api.py` as a thin entry point; remove unused `brain_of_the_doctor.py` after porting its multilingual prompts. | Imports cycle-free; old tests pass. |

## 7. Non-functional requirements

| Area | Requirement (reference hardware, §4) |
|---|---|
| Latency | Emergency fast path p95 < 300 ms; upload acknowledged (202) p95 < 1 s for local uploads; text-only full assessment p95 ≤ 60 s (re-baselined in Phase 0); STT ≤ 1× audio duration + 10 s for `small` int8, else document the slower budget; PDF text-layer extraction ≤ 2 s/page; OCR ≤ 20 s/page; CT key-slice extraction ≤ 60 s for 300 slices. |
| Capacity | Mode A: 1–3 concurrent workers; Mode B: 10 tablets, queue depth 20, no crash or OOM under 2× that load (load test). |
| Resources | API RSS ≤ 1.5 GB excluding Ollama; disk quota enforced; no unbounded in-memory buffers (largest buffer = 1 MiB chunk or decoded-image limit). |
| Availability | Survives Ollama outage (rules-based), process restart (jobs resume), power loss (SQLite WAL, no corrupt store). |
| Security | OWASP ASVS L2 for Mode B; zero high/critical findings from `pip-audit`/`npm audit`/`semgrep` at release; external review of upload parsers before 1.0. |
| Privacy | INV-4..7 enforced by automated tests; DPDP notice/consent flows reviewed by counsel. |
| Localization | 100 % of UI strings in en/hi/mr; clinical content (first aid, notices) reviewed by native-speaking clinicians. |
| Accessibility | WCAG 2.1 AA. |
| Offline | Every 1.0 feature except optional SMS/Overpass refresh works with networking disabled (CI test runs the e2e suite in a network-isolated container). |

## 8. Data model (initial)

| Table | Key fields (encrypted ⚿) | Notes |
|---|---|---|
| `users` | id, role, username, argon2 hash, facility_id, status | Mode B |
| `cases` | id, pseudonym, age, sex, area ⚿, abha_number ⚿, created_by, created_at, expires_at, key_id | Crypto-shred by destroying `key_id` |
| `consents` | id, case_id, notice_version, method (`verbal_recorded`/`signed`/`emergency_exception`), recorded_by, at | |
| `visits` | id, case_id, started_at, ended_at | |
| `attachments` | id, case_id, kind (`audio`/`image`/`pdf`/`dicom`), stage, reason_code, sha256_keyed, size, original_name ⚿, blob_ref, expires_at | Raw blob deleted after extraction |
| `derivatives` | id, attachment_id, type (`transcript`/`text`/`lab_table`/`summary`/`key_image`/`observations`), content ⚿ / blob_ref, model_version | |
| `assessments` | id, case_id, inputs_hash, fast_path ⚿, result ⚿, urgency, sources, versions (model digest, prompt, rules), created_at | `urgency` kept plaintext for metrics |
| `jobs` | id, type, case_id, status, stage, progress, attempts, deadline, error_code | Persistent queue |
| `audit_events` | id, at, actor, action, object_ref, prev_hash, hash | No clinical content |
| `outbox` | id, case_id, channel (`sms`), payload ⚿, consent_id, status | P2 |

## 9. Success metrics

| Metric | Target at 1.0 | Source |
|---|---|---|
| Under-triage rate (golden set) | ≤ 2 % | QA-02 |
| Sensitivity for HIGH (red-flag subset) | ≥ 0.95 (target 0.98) | QA-02 |
| Per-language sensitivity gap | ≤ 5 pp | QA-02 |
| Lab extraction field precision | ≥ 0.95 | PDF-03 |
| Upload-related crashes / OOM in load test | 0 | RES-* |
| PHI sentinel leaks in logs/metrics/errors | 0 | PRIV-04 |
| Time from first input to emergency banner (fast path) | p95 < 1 s end-to-end in UI | RES-01 |
| Field pilot (post-1.0): referral slip used in % of HIGH cases | ≥ 80 % | CASE-03 + outcomes |
| Field pilot: follow-up outcome recorded | ≥ 60 % of referrals | CASE-04 |

## 10. Dependencies and technology choices

| Need | Choice | Why |
|---|---|---|
| PDF parsing | `pypdf` (replaces deprecated PyPDF2) in a sandboxed subprocess | Pure Python, maintained; subprocess limits contain malicious files |
| PDF rendering for OCR | `pypdfium2` | Fast, no Ghostscript |
| OCR | Tesseract 5 + `eng`, `hin`, `mar` traineddata via `pytesseract` | Offline, supports Devanagari |
| Images | Pillow + `pillow-heif` | HEIC from phones; bomb protection |
| DICOM | `pydicom`, `pylibjpeg` (+ openjpeg/libjpeg plugins) or `python-gdcm` | Compressed transfer syntaxes |
| Audio | PyAV (via faster-whisper) | Already installed; no system ffmpeg needed |
| Type detection | Own magic-byte table (Appendix B) + `filetype` | No libmagic dependency on Windows |
| Store | SQLite (WAL) + SQLAlchemy 2 + Alembic | Single-file, offline, crash-safe |
| Crypto | `cryptography` (AES-GCM), `keyring` | Standard, cross-platform key storage |
| Passwords | `argon2-cffi` | Argon2id |
| Jobs | In-process worker pools + persistent `jobs` table | No Redis; works offline on one machine |
| SSE | `sse-starlette` | Progress events |
| Vision/LLM | Ollama `gemma4:e2b` (`images` field on `/api/chat`) | Image input is documented for E2B; audio input reported unreliable → keep faster-whisper |

Phase 0 must confirm each choice installs on Windows and Linux for Python 3.10–3.13 and on the reference hardware.

## 11. Delivery plan (phases, in order)

Each phase ends with: CI green, docs updated, a short `docs/releases/phase-N.md` note (what shipped, measurements, deviations).

### Phase 0 — Foundations and spikes
1. **SPIKE-01** Measure baseline on reference hardware: text triage latency, RSS, STT speed for `tiny`/`small`, cold-start; record in `docs/benchmarks.md`.
2. **SPIKE-02** Verify `gemma4:e2b` image input through Ollama `/api/chat` with base64 images; measure latency per image and JSON-mode reliability; record limits.
3. **SPIKE-03** OCR quality on 20 real-world (de-identified) Hindi/Marathi/English lab reports; choose DPI and preprocessing.
4. **SPIKE-04** DICOM library matrix: decode CT (uncompressed, JPEG-LS, JPEG-2000) on Windows and Linux.
5. **ADR-01..04** Architecture decision records: storage & encryption, job system, package layout, Mode B TLS approach.
6. **OPS-03, OPS-04 (partial)** Locked deps, ruff, pip-audit, gitleaks in CI.
7. **OPS-08** Package layout refactor (no behaviour change).
**Exit:** benchmarks recorded; all spikes answered; CI expanded; 85 baseline tests still pass.

### Phase 1 — Safe ingestion core (the "no leak, no burst" foundation)
1. PRIV-01 encrypted store + Alembic; CASE-01 minimal case record.
2. ING-01..07, ING-09 streaming uploads, quarantine, magic bytes, status, delete, de-duplication, sweeper.
3. RES-01..05 fast path, job queue, back-pressure, timeouts, budgets.
4. AUD-01..05 audio pipeline on v2.
5. IMG-01, IMG-02 image sanitization.
6. PRIV-02, PRIV-03, PRIV-04, PRIV-07 retention, erase, log hygiene, browser hygiene.
7. API-01..04 v2 envelope, headers and idempotency keys; FE-01 split App.jsx; FE-03 attachment UX; RES-06 progress.
**Exit:** load test (2× Mode B load + malicious-file corpus) passes with zero crashes/OOM; PHI sentinel test passes on every endpoint; frontend uses v2 for voice and uploads.

### Phase 2 — Documents and multimodal triage
1. PDF-01..06 parsing, OCR, lab extraction, critical-lab floor, summaries, result-age awareness.
2. FUS-01..03, FUS-06 clinical context, fusion rule, provenance, schema v2.
3. RES-07, RES-08 degraded mode and context budget.
4. QA-01, QA-02, QA-06 golden set, harness, versioning; run the gate (QA-03) for the first time.
5. FE-02 i18n completion; CASE-02 result screen.
**Exit:** lab extraction metrics met; QA-03 gate measured and reported (must pass by end of Phase 5); provenance visible in UI.

### Phase 3 — Imaging (DICOM, CT, X-ray, photos)
1. IMGX-01..05 ZIP safety, parsing, de-identification, burned-in PHI, series/windowing.
2. IMGX-06, IMGX-07 viewer and store-and-forward into the referral packet.
3. IMG-03, IMG-04 photo classification and quality.
4. IMGX-08, IMGX-09 imaging assist behind `ENABLE_IMAGING_ASSIST=false`; QA-05 validation plan written (execution may continue after 1.0).
**Exit:** de-identification tag-scan test passes on a public DICOM test corpus; CT key slices within budget; flag-off path makes zero model calls for images.

### Phase 4 — Identity, consent, audit, Mode B
1. IAM-01..03, IAM-05, IAM-06 (Mode B) and IAM-04 (Mode A PIN).
2. PRIV-05 consent flow; PRIV-06 data-principal requests; PRIV-08 export controls.
3. OPS-07 config validation; ING-08 malware hook.
**Exit:** access-matrix tests for every endpoint; Mode B install on two tablets over TLS documented and tested.

### Phase 5 — Product workflow and polish
1. CASE-03 referral PDF; CASE-04 follow-ups; CASE-05 first aid; CASE-06, CASE-07 facility dataset import and named-doctor removal.
2. FUS-04, FUS-05 conflict detection, multilingual negation/history; AUD-06 code-mixed speech; QA-04 "report a problem" snapshots.
3. TTS-01, TTS-02; FE-04..07 PWA, accessibility, performance, frontend tests.
4. CASE-08, CASE-09 (P2) if time permits.
**Exit:** QA-03 gate **passes**; accessibility and performance budgets met.

### Phase 6 — Release hardening (1.0)
1. OPS-01, OPS-02 container and native installers; OPS-05 observability; OPS-06 backups.
2. External security review of upload parsers and auth; fix all high/critical findings.
3. QA-07 intended-use and regulatory note signed off; consent text legal review.
4. Release checklist (Appendix F); tag `v1.0.0`.

## 12. Testing strategy

- **Unit:** every parser, limit, sanitizer, de-identifier, fusion rule, crypto wrapper.
- **Property-based (Hypothesis):** fusion monotonicity (INV-2); vitals/lab parsers never raise; ZIP/PDF limit enforcement with random sizes.
- **Malicious-file corpus** `tests/fixtures/hostile/`: zip bombs, PDF bombs/loops, decompression-bomb images, polyglots, truncated files, path-traversal names, DICOM with burned-in text, EICAR. Each must be rejected within limits with the right reason code.
- **Privacy sentinels:** a unique marker string injected through every input channel must never appear in logs, metrics, error bodies, URLs or browser storage.
- **Load:** Locust/k6 scenario mixing uploads, assessments and fast-path calls at 2× Mode B capacity; assert no 5xx except 429/503 with `Retry-After`, RSS within budget.
- **Clinical:** QA-01..03 golden set and gate.
- **E2E:** Playwright against the built UI served by the API, model stubbed; plus a nightly job against a real Ollama runner.
- **Offline:** e2e suite in a network-isolated container.

**Definition of Done (every work item):** code + tests (incl. INV tests where relevant) + docs/OpenAPI/.env.example updated + CI green + no new `pip-audit`/`npm audit` high findings + PHI sentinel test still passing + reviewed for INV-1..10.

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Small on-device model misreads images or labs | Wrong reassurance | INV-2 (only escalate), anti-hallucination check (PDF-03), imaging assist off by default (IMGX-08), QA-05 validation |
| Malicious or malformed files crash or hang the API | Outage on the only device | Streaming limits, subprocess sandbox for PDF, bounded pools, timeouts, hostile corpus in CI |
| PHI leakage via logs, backups, temp files | Legal and trust harm | Encryption at rest, crypto-shred, log filter + sentinels, temp dir sweeps, no browser storage |
| Reference hardware too slow for LLM + OCR + Whisper | Unusable latency | Phase 0 benchmarks; per-resource pools; fast path first; smaller STT model option |
| DPDP / medical-device regulation | Launch blocked | PRIV-05, QA-07, legal review before field use |
| Lost encryption key | Data unrecoverable | Documented key backup for Mode B (sealed export); Mode A data is short-lived by design |
| Clinician reviewer availability | Gate cannot be measured | Start QA-01 recruitment in Phase 0 (D10) |
| Scope creep (telemedicine, EHR) | Delays 1.0 | Non-goals §3 |

## 14. Decisions needed from the product owner

| ID | Decision | Recommended default (used if unanswered) |
|---|---|---|
| D1 | Ship Mode B (PHC hub) in 1.0? | Yes, after Mode A; Phase 4 |
| D2 | Reference hardware | 8 GB RAM, 4-core CPU, no GPU (§4) |
| D3 | AI imaging observations in 1.0? | Store-and-forward only; assist behind flag, off |
| D4 | Keep named doctors in the directory? | No — facility-level data only |
| D5 | TTS approach | Browser speech first, server pyttsx3 fallback |
| D6 | Retention defaults | Raw uploads: delete after extraction; cases: 7 days (Mode A) / 30 days (Mode B); TTS: 1 h |
| D7 | Consent wording and SMS provider | Draft notice in en/hi/mr for legal review; SMS deferred to P2 |
| D8 | Low-confidence model HIGH vs rules LOW | Take the max (conservative) — changes one existing test |
| D9 | Regulatory path / intended use | Decision-support for referral, not diagnosis; obtain assessment before pilot |
| D10 | Clinical reviewers for the golden set and thresholds | Minimum two clinicians; one per language |
| D11 | Malware scanning | ClamAV hook in Mode B only |
| D12 | Age threshold for "old" lab results | 30 days |
| D13 | DICOM dates | Remove; keep series-relative timing only |

## 15. Out of scope for 1.0
Telemedicine video, e-prescriptions, payments, cloud sync, ABDM/HMIS integration (beyond ABHA number capture), real ambulance dispatch, additional languages, radiology reporting, iOS native app.

---

## Appendix A — Limits and defaults (single source of truth → `config.py`)

| Setting | Default | Notes |
|---|---|---|
| `MAX_AUDIO_MB` / `MAX_AUDIO_SECONDS` | 25 / 300 | Duration checked on decoded samples |
| `MAX_IMAGE_MB` / `MAX_IMAGE_PIXELS` | 15 / 25,000,000 | Sanitized long edge 2048 px |
| `MAX_PDF_MB` / `MAX_PDF_PAGES` / `MAX_OCR_PAGES` | 20 / 50 / 10 | Parser in subprocess: 30 s CPU, 512 MB RAM |
| `MAX_DICOM_UPLOAD_MB` / `MAX_DICOM_FILES` / `MAX_DICOM_UNCOMPRESSED_MB` / `MAX_ZIP_RATIO` | 300 / 1,000 / 1,024 / 100 | Per upload |
| `MAX_KEY_SLICES` | 16 | Per series |
| `MAX_ATTACHMENTS_PER_CASE` | 10 | |
| `MAX_QUEUE_DEPTH` | 20 | Fast path exempt |
| `POOL_LLM` / `POOL_STT` / `POOL_OCR` / `POOL_PDF` / `POOL_IMAGING` | 1 / 1 / 2 / 2 / 1 | |
| `TIMEOUT_LLM_S` / `TIMEOUT_OCR_PAGE_S` / `TIMEOUT_IMAGING_S` | 120 / 20 / 180 | STT: 2× duration + 30 s |
| `CASE_STORAGE_QUOTA_GB` / `MIN_FREE_DISK_GB` | 5 / 2 | |
| `CASE_RETENTION_DAYS` | 7 (Mode A) / 30 (Mode B) | D6 |
| `AUDIO_RETENTION_SECONDS` | 3600 | Existing |
| `ENABLE_IMAGING_ASSIST` | false | D3 |
| `SESSION_IDLE_MINUTES` / `SESSION_MAX_HOURS` | 15 / 12 | Mode B |

## Appendix B — Accepted types (magic bytes) and reason codes

| Kind | Accepted | Signature check |
|---|---|---|
| Audio | WebM/Matroska, Ogg, WAV, MP3, MP4/M4A | `1A 45 DF A3`; `OggS`; `RIFF....WAVE`; `ID3` or frame sync `FF Fx`; `....ftyp` |
| Image | JPEG, PNG, WebP, HEIC/HEIF | `FF D8 FF`; `89 50 4E 47 0D 0A 1A 0A`; `RIFF....WEBP`; `ftypheic/heix/mif1` |
| PDF | PDF 1.x/2.0 | `%PDF-` within first 1024 bytes; `%%EOF` near end |
| DICOM | Part 10 file; ZIP of Part 10 files | 128-byte preamble + `DICM`; ZIP `50 4B 03 04` |

Reason codes: `FILE_TOO_LARGE`, `UNSUPPORTED_TYPE`, `TYPE_MISMATCH`, `POLYGLOT_FILE`, `CORRUPT_FILE`, `AUDIO_TOO_LONG`, `AUDIO_NO_SPEECH`, `IMAGE_TOO_LARGE`, `PDF_ENCRYPTED`, `PDF_TOO_MANY_PAGES`, `PDF_UNREADABLE`, `ZIP_BOMB`, `ZIP_PATH_TRAVERSAL`, `DICOM_UNSUPPORTED_SOP`, `DICOM_DEID_FAILED`, `BURNED_IN_PHI_UNMASKED`, `MALWARE_DETECTED`, `QUEUE_FULL`, `STORAGE_FULL`, `JOB_TIMED_OUT`, `MODEL_UNAVAILABLE`.

## Appendix C — DICOM attributes that must not survive de-identification (minimum)

Patient's Name (0010,0010), Patient ID (0010,0020), Issuer of Patient ID (0010,0021), Patient's Birth Date (0010,0030), Patient's Birth Time (0010,0032), Other Patient IDs (0010,1000), Other Patient Names (0010,1001), Patient's Address (0010,1040), Patient's Telephone Numbers (0010,2154), Patient's Mother's Birth Name (0010,1060), Medical Record Locator (0010,1090), Ethnic Group (0010,2160), Patient Comments (0010,4000), Accession Number (0008,0050), Institution Name (0008,0080), Institution Address (0008,0081), Referring Physician's Name (0008,0090), Station Name (0008,1010), Institutional Department Name (0008,1040), Performing Physician's Name (0008,1050), Operators' Name (0008,1070), Physician(s) of Record (0008,1048), Study ID (0020,0010), Device Serial Number (0018,1000), Request Attributes Sequence (0040,0275), all dates/times per D13, all private tags (odd groups); Study/Series/SOP Instance UIDs replaced consistently. Full list: DICOM PS3.15 Annex E, Table E.1-1 (Basic Profile).

## Appendix D — Critical lab values (DRAFT — must be approved by clinicians before use)

| Test | Critical low | Critical high | Unit |
|---|---|---|---|
| Potassium | < 2.8 | > 6.2 | mmol/L |
| Sodium | < 120 | > 160 | mmol/L |
| Glucose | < 54 (3.0 mmol/L) | > 400 (22.2 mmol/L) | mg/dL |
| Haemoglobin | < 7.0 | — | g/dL |
| Platelets | < 20,000 | > 1,000,000 | /µL |
| WBC | < 2,000 | > 30,000 | /µL |
| Creatinine | — | > 4.0 (adult) | mg/dL |
| Troponin (I/T, any assay) | — | above assay's 99th-percentile URL / "positive" | as reported |
| INR (on warfarin) | — | > 5.0 | ratio |
| Calcium (total) | < 6.5 | > 13.0 | mg/dL |
| pH (blood gas) | < 7.20 | > 7.60 | — |

Paediatric and pregnancy-specific thresholds to be added by reviewers. The table is versioned (QA-06) and loaded from `emergency_triage/critical_labs.yaml`.

## Appendix E — Reference repo (`aj4344/PiedPiper_HealStation_MedicalTriage`): what to reuse

| Reuse (adapt to offline + invariants) | Do **not** reuse |
|---|---|
| Vision-vs-text model routing with text-only fallback when the vision call fails (`brain_of_the_doctor.get_doctor_advice_multimodal`) → apply to Ollama in IMGX-08 | Groq/cloud inference as default (breaks offline promise and INV-5) |
| PDF text injection into the prompt (3,000-char cap) → superseded by PDF-02/03 + RES-08 budget | `/api/ambulance/dispatch` mock that tells users an ambulance was dispatched (violates INV-8) |
| First-aid content per emergency type (`/api/ambulance/first-aid/{type}`) → CASE-05 after clinician review | `allow_origins=["*"]` CORS, `print()` logging of patient data |
| Overpass API hospital search with mirror fallback (`hospital_routing_service._search_overpass`) → optional cached refresh in CASE-06 | Static/mock doctor and ambulance-station data presented as real |
| Fast2SMS family alert (`sms_alert_service.py`) → CASE-08 with consent, outbox, no demo mode in prod | `SMS_DEMO_MODE` in production builds |
| Haversine + time-of-day traffic speed table (`ambulance_eta_service.py`) → CASE-09, labelled "estimate" | Root-user Dockerfile exposing 0.0.0.0 without auth (use OPS-01 instead) |
| Dockerfile / `.dockerignore` structure, frontend `config/api.js` endpoint map | Committed `frontend/.env.*` files (keep env out of git) |

## Appendix F — Release 1.0 checklist

- [ ] Phases 0–6 exit criteria met; `docs/releases/phase-*.md` present
- [ ] QA-03 gate passed on the release build; report attached
- [ ] Hostile-file corpus, PHI sentinels, load and offline suites green
- [ ] External security review: no open high/critical findings
- [ ] `pip-audit`, `npm audit`, `semgrep`, `gitleaks` clean; SBOM generated
- [ ] Intended-use statement and regulatory note signed (QA-07); consent text approved by counsel (PRIV-05)
- [ ] Clinical content (first aid, critical labs, notices) reviewed and versioned
- [ ] Install verified on reference hardware for Mode A (Windows + Linux) and Mode B (2 tablets over TLS)
- [ ] Backup and restore drill done (Mode B)
- [ ] README, `.env.example`, OpenAPI and user guide (en/hi/mr) updated
