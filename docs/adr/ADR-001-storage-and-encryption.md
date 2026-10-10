# ADR-001 — Case storage and encryption at rest

- **Status:** Accepted (Phase 0)
- **PRD items:** PRIV-01, PRIV-02, PRIV-03, ING-03, ING-06, INV-6, INV-7

## Context

Patient data must be encrypted at rest, expire on a schedule, and be
unrecoverable after "End visit & erase" — including from a copy of the disk.
The product runs offline on one laptop (Mode A) or one PHC machine (Mode B),
so there is no database server, no KMS and no cloud.

## Decision

1. **One SQLite database** (`DATA_DIR/healstation.db`) in WAL mode, accessed
   through SQLAlchemy 2, schema managed by Alembic migrations that run on
   startup. `PRAGMA secure_delete=ON` so deleted rows are overwritten, not left
   in free pages.
2. **Three-level key hierarchy**
   - **KEK** (key-encryption key, 256-bit). Loaded, in order, from
     `HEALSTATION_KEK` (base64, containers), `KEK_FILE` (a secret file outside
     `DATA_DIR`), or the OS keyring (Windows Credential Manager/DPAPI, macOS
     Keychain, Linux Secret Service). In Mode A a missing KEK is generated once
     and stored in the keyring, or in `KEK_FILE` when no keyring backend
     exists. Mode B refuses to start without one (OPS-07). The KEK is never
     logged and never written under `DATA_DIR`.
   - **Case DEK** (one random 256-bit key per case), stored only wrapped by the
     KEK (AES-256-GCM, AAD = case id) in the `case_keys` table.
   - **File key** (one per blob), wrapped by the case DEK and stored in the blob
     header.
3. **Field-level encryption** of clinical content (symptoms, transcripts,
   extracted text, lab tables, model output, filenames, area, ABHA number)
   with the case DEK using AES-256-GCM. AAD binds each value to its table,
   column and row id, so ciphertexts cannot be swapped between rows. Only
   non-clinical fields stay plaintext (ids, stages, timestamps, sizes, reason
   codes, and the final `urgency` used for metrics).
4. **File format `HSE1`** for every blob, including the upload quarantine:
   header (magic, version, chunk size, wrapped file key, 7-byte nonce prefix),
   then 64 KiB plaintext chunks each sealed with AES-256-GCM. The nonce is
   `prefix ‖ chunk index (4 B) ‖ last-chunk flag (1 B)` and the header is
   authenticated as AAD, which detects reordering, truncation and header
   tampering. Fixed chunk sizes make the reader seekable, so `zipfile`,
   `pydicom`, Pillow and PyAV read straight from the encrypted blob without
   writing plaintext to disk.
5. **Crypto-shred:** erasing a case deletes its wrapped DEK first (with
   `secure_delete`), then its blobs and rows. Once the DEK is gone, any copy of
   the database or blob files is unreadable.

## Consequences

- Losing the KEK makes all data unreadable. Mode A data is short-lived by
  design (7 days); Mode B documents a sealed KEK backup (OPS-06).
- Processing happens on decrypted bytes in memory. Tools that need a file
  (Tesseract) are fed through stdin; the PDF parser runs in a sandboxed
  subprocess that reads bytes from a pipe.
- SQLite limits write concurrency; all writes go through short transactions
  and the job workers are few (PRD Appendix A pools), which keeps this well
  within SQLite's limits for 10 tablets.
