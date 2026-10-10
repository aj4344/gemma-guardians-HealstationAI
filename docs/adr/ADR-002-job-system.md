# ADR-002 — Job system and resource governance

- **Status:** Accepted (Phase 0)
- **PRD items:** RES-01..RES-06, ING pipeline, AUD-02, PDF-01

## Context

The heavy resources (Gemma via Ollama, Whisper, Tesseract, the PDF parser,
DICOM processing) cannot all run at once on an 8 GB laptop. Requests must
never crash the process, the emergency rules must answer instantly whatever
is queued, and work must survive a restart. There is no Redis or message
broker offline.

## Decision

1. **Persistent job table** (`jobs`) in the case database: type, case, status
   (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `CANCELLED`),
   stage, progress, attempts, deadline, error code. The job's input is stored
   encrypted with the case DEK.
2. **In-process worker pools, one per resource**, sized from config
   (`POOL_LLM=1`, `POOL_STT=1`, `POOL_OCR=2`, `POOL_PDF=2`, `POOL_IMAGING=1`).
   A job declares its resource; at most *N* jobs of that resource run at once.
3. **Back-pressure:** at most `MAX_QUEUE_DEPTH` non-terminal jobs across all
   pools. Above that, new work is refused with `429 QUEUE_FULL` and
   `Retry-After`. The emergency fast path never enqueues, so it is never
   refused.
4. **Deadlines and cancellation:** each job type has a timeout. Subprocess work
   (PDF parsing, OCR) is killed at the deadline. Thread work receives a cancel
   flag it checks between stages; HTTP calls to Ollama use the remaining
   deadline as their timeout. A late result after `TIMED_OUT` is discarded.
   Partial results are kept and labelled.
5. **Restart recovery:** on startup, jobs left `RUNNING` are re-queued once
   (attempts + 1); a job that was already retried is marked `FAILED` with a
   user-visible, localized message.
6. **Progress** is written to the job row and streamed with Server-Sent Events
   (`/api/v2/jobs/{id}/events`), with plain polling as the fallback.

## Consequences

- A single process owns the pools; running several API worker processes would
  multiply the pool sizes. Deployment runs one uvicorn worker by design.
- Thread work cannot be force-killed; CPU-heavy parsers that could hang run in
  subprocesses for that reason.
