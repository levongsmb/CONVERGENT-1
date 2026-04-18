# 0006 — Signing certificate posture

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 0 installer build

## Context

§3.3 of the prompt anticipates the signing certificate as a future
item. Phase 0 installer skeleton must ship without blocking Phase 1.

## Answer

**2026-04-18:** Unsigned Phase 0 installer. Revisit when Phase 1
stabilizes and the installer is distributed outside the firm.

## Implementation notes

- `scripts/build_installer.ps1` already emits an unsigned installer by
  default; `$env:CONVERGENT_SIGNING_CERT` activates signing when set.
- README documents the Windows SmartScreen warning on first run of an
  unsigned installer.
- Phase 10 tracks re-opening this decision when the firm's distribution
  footprint widens.