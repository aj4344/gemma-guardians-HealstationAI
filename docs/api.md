# HealStation AI — HTTP API

The running server publishes the authoritative OpenAPI schema at `/openapi.json` and interactive docs at
`/docs`. This page explains the endpoints in prose.

- **`/api/v2`** — the current API (cases, streaming uploads, jobs). Added in Phase 1; documented below as
  it lands.
- **`/api` (v1)** — the original endpoints. They keep working, are marked deprecated, and will be removed
  in release 1.1 once the UI has moved to v2.

## Version 2

All v2 errors use one envelope and a reason code (PRD Appendix B); the message is already in the
language from `Accept-Language` (`en`, `hi` or `mr`):

```json
{"error": {"code": "FILE_TOO_LARGE", "message_localized": "...", "retryable": false}, "request_id": "..."}
```

Every response carries `X-Request-ID`; every `/api` response is `Cache-Control: no-store`.

### Cases

| Method | Path | Result |
|---|---|---|
| POST | `/api/v2/cases` | `201 {case_id, pseudonym, language, created_at, expires_at}` |
| GET | `/api/v2/cases/{case_id}` | the case, including decrypted `area` and `abha_number` |
| DELETE | `/api/v2/cases/{case_id}` | `204` — ends the visit and erases everything (crypto-shred) |

Create body (all optional): `{"language": "en|hi|mr", "age": 0-130, "sex": "female|male|other|unknown",
"area": "≤120 chars", "abha_number": "14 digits"}`. Cases expire after `CASE_RETENTION_DAYS`.

### Attachments

`POST /api/v2/cases/{case_id}/attachments` — `multipart/form-data` with exactly one file part. Accepted:
JPEG, PNG, WebP, HEIC photos; PDF; a DICOM file or a ZIP of a series. The type is detected from the bytes;
the client's MIME type and extension must agree with it.

- `202` `{attachment_id, kind, stage: "QUARANTINED", ...}` — processing continues in the background.
- `200` with `"duplicate": true` — the same file was already attached to this case.
- `413 FILE_TOO_LARGE`, `415 UNSUPPORTED_TYPE | TYPE_MISMATCH | POLYGLOT_FILE`, `409 TOO_MANY_ATTACHMENTS`,
  `507 STORAGE_FULL`, `400 EMPTY_FILE | NO_FILE | MULTIPLE_FILES` — nothing is kept.

`GET /api/v2/cases/{case_id}/attachments[/{attachment_id}]` returns `stage` (`RECEIVING`, `QUARANTINED`,
`VALIDATING`, `SANITIZING`, `EXTRACTING`, `READY` or `REJECTED`), `progress`, `reason_code` with a localized
message when rejected, and a de-identified `summary`. The original filename is never returned.
`DELETE` removes the upload and everything derived from it.

### Assessment

`POST /api/v2/cases/{case_id}/assess`

```json
{"symptoms_confirmed": "text the worker confirmed", "language": "hi",
 "vitals": {"heart_rate": 120, "bp_systolic": 85, "bp_diastolic": 60, "spo2": 90, "temperature": 38.5, "respiratory_rate": 28}}
```

The safety rules (toxin lane, red-flag guardrail, critical vitals) run immediately — no model, no queue —
and the full assessment is queued:

```json
{"assessment_id": "…", "job_id": "…",
 "fast_path": {"urgency": "high" | null, "rules_fired": ["red_flag_guardrail"], "reasons": ["…"],
               "emergency_action_block": {…}}}
```

When no rule fires, `fast_path.urgency` is `null` with `status: "no_emergency_rule_triggered"` — never
"low". When the queue is full the response is `429 QUEUE_FULL` with `Retry-After`, and it still contains
`fast_path`. The full result's urgency is never lower than the fast path's.

`GET /api/v2/cases/{case_id}/assessments` lists a case's assessments with their fast-path and full results.

### Jobs

`GET /api/v2/jobs/{job_id}` → `{status: QUEUED|RUNNING|SUCCEEDED|FAILED|TIMED_OUT|CANCELLED, stage,
progress, error?, result?}`. A job that runs out of time ends `TIMED_OUT`; its `result` is the partial
(rules-based) result with `"partial": true`. Jobs interrupted by a restart are retried once, then fail
with `JOB_INTERRUPTED`.

## Version 1 (deprecated)

### 1. Core Health Endpoints
```
GET /
GET /api
GET /api/health-check
```

### 2. Voice Transcription Endpoint
```
POST /api/transcribe-audio
Content-Type: multipart/form-data

Form fields:
  - audio: file (required)
  - language: en|hi|mr (optional, default: en)

Response:
{
  "text": "transcribed text",
  "language": "en"
}
```

### 3. AI Consultation Endpoint
```
POST /api/get-doctor-response
Content-Type: application/json

Body:
{
  "patient_text": "string (required)",
  "language": "en|hi|mr",
  "image_data": ["base64_image_1", "base64_image_2"],
  "pdf_data": [{"name": "report.pdf", "data": "base64_pdf"}],
  "image_count": 0,
  "pdf_count": 0
}

Response (abridged):
{
  "doctor_response": "string",
  "audio_url": "/api/audio/doctor_response_<random>.wav",  // null when TTS is off/unavailable
  "urgency": "low|medium|high",
  "reasons": ["..."], "actions": ["..."],
  "specialist": "cardiologist", "confidence": 0.0-1.0,
  "triage_source": "toxin_fast_lane|red_flag_guardrail|local_gemma|emergency_fallback|unassessed",
  "emergency_action_block": { ... } | null
}

Errors: 422 for invalid input; 503 with a localized, patient-safe "detail" when the
assessment could not be completed (never a fabricated "low" result).
```

Vitals can be sent as fields (`heart_rate`, `bp_systolic`, `bp_diastolic`, `spo2`,
`temperature` in °C) or typed in the text as `BP: 140/90, Heart Rate: 85, Temp: 101°F, Oxygen: 96%`.
Critical vitals always produce `urgency: "high"`.

Uploaded images and PDFs are accepted (max 8) but **not yet analysed** by the triage
pipeline; they are only counted in `consensus_explanation`.

### 4. Audio Playback / Status Endpoints
```
GET /api/audio/{filename}        # streams the generated WAV (random, unguessable name)
GET /api/audio-status/{filename} # { ready, status, file_size }
GET /api/voices                  # supported TTS voices by language
```

### 5. Doctor Discovery Endpoints
```
POST /api/search-doctors
Content-Type: application/json

Body:
{
  "latitude": 18.5204,
  "longitude": 73.8567,
  "specialty": "cardiologist",
  "radius": 25000,
  "sort_by": "distance|rating|reviews|availability|experience",
  "limit": 20,
  "language": "en"
}
```

```
POST /api/search-doctors-by-city
Content-Type: application/json

Body:
{
  "city": "Mumbai",
  "specialty": "dermatologist",
  "sort_by": "distance|rating|reviews|availability|experience",
  "limit": 20,
  "language": "en",
  "user_latitude": 18.5204,
  "user_longitude": 73.8567
}
```

### 6. Emergency Triage Endpoints
```
POST /api/emergency-triage
Content-Type: application/json

Body:
{
  "symptoms": "string (required)",
  "age": 52,
  "gender": "male|female|other",
  "vital_signs": {
    "blood_pressure_systolic": 140,
    "blood_pressure_diastolic": 90,
    "heart_rate": 98,
    "temperature_celsius": 38.2,
    "oxygen_saturation": 95,
    "respiratory_rate": 20
  },
  "medical_history": ["diabetes", "hypertension"],
  "symptom_duration": "2 hours",
  "language": "en|hi|mr",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "ai_analysis": "optional prior AI analysis"
}
```

```
POST /api/emergency-triage/quick     # body: {"symptoms": "..."}
GET  /api/emergency-triage/quick     # deprecated: puts symptoms in the URL / access logs
POST /api/emergency-hospitals
GET /api/emergency-info
```


