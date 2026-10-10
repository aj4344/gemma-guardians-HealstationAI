# ADR-004 — TLS for the PHC hub (Mode B)

- **Status:** Accepted (Phase 0)
- **PRD items:** IAM-02, IAM-06, OPS-07

## Context

In Mode B one PHC machine serves several tablets on the local network, often
without internet and without a public DNS name, so public certificate
authorities cannot issue certificates. Session cookies must be `Secure`, and
patient data must not cross the LAN in plaintext.

## Decision

1. **Caddy as the bundled TLS reverse proxy** (`deploy/Caddyfile`), using its
   internal CA (`tls internal`) to issue a certificate for the hub's LAN name
   or IP. Caddy listens on `:443` and forwards to the API on `127.0.0.1:8001`.
2. **The API never listens on the LAN itself.** With `DEPLOYMENT_MODE=hub` the
   API must bind to loopback and set `TLS_TERMINATED_BY_PROXY=true`; binding to
   `0.0.0.0` without that is a fatal configuration error unless
   `ALLOW_INSECURE_LAN=true` (development only, logged as a warning).
3. **Device enrolment:** the admin exports Caddy's root certificate
   (`deploy/enrol-device.md`) and installs it on each tablet once (Android:
   Settings → Security → Encryption & credentials → Install a certificate → CA
   certificate). The root key never leaves the hub.
4. The API trusts `X-Forwarded-Proto`/`X-Forwarded-For` only from loopback.

## Consequences

- One extra binary on the hub. Caddy is a single static executable available
  for Windows and Linux, and is included in the Docker Compose file.
- Losing the hub's Caddy data directory means re-enrolling devices; it is
  included in the Mode B backup (OPS-06).
