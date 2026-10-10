# ADR-003 — Backend package layout

- **Status:** Accepted (Phase 0)
- **PRD items:** OPS-08

## Context

`api.py` holds 2,000+ lines mixing HTTP routes, safety rules, prompts,
localization and audio handling. New ingestion, storage, security and fusion
code would make it unmanageable and hard to review for invariant violations.

## Decision

All backend code lives in the `healstation` package; `api.py` at the repository
root stays as the thin entry point (`python api.py`, `uvicorn api:app`).

```
healstation/
  api/        FastAPI app factory, middleware, error envelope, v1 (legacy) and v2 routes
  triage/     safety rules (toxin lane, red flags, critical vitals, critical labs),
              Gemma client and prompts, rules-based fallback, localization
  fusion/     clinical context, urgency fusion (max rule), provenance, context budget
  ingest/     type detection, limits, quarantine, audio, images, PDF, labs, DICOM
  store/      database, migrations, encryption, blob store, cases, retention
  jobs/       persistent queue and worker pools
  security/   logging hygiene, security headers, auth, sessions, audit log
  referral/   referral slip
  assets/     bundled fonts
config.py     the only place that reads the environment (unchanged location)
emergency_triage/  existing scoring and hospital-routing package (kept)
```

Rules:
- Dependencies point inward: `api → (fusion, ingest, jobs, store, security) →
  triage`. `triage` imports nothing from the HTTP layer.
- `config.py` remains the single source of configuration; modules read
  settings from it, and tests override them through fixtures.
- `brain_of_the_doctor.py` is removed after its multilingual prompts are
  ported to `healstation/triage/prompts.py`.

## Consequences

Tests patch functions in their new modules (for example
`healstation.triage.model_client.run_local_gemma_triage`) instead of `api.*`;
their assertions are unchanged.
