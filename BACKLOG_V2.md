# Convergent v2 Backlog

Per §19: "When mid-build you encounter a strategy or feature that feels
essential and isn't yet in the prompt, the answer is `OPEN_QUESTIONS.md`,
not silent inclusion. [...] Add to a v2 backlog file (`BACKLOG_V2.md`) for
post-Phase-11 consideration."

This file is strictly additive during Phases 0–11. Items added here do not
block the current build. User triages post-Phase-11.

## Seed items

- **macOS build.** Explicitly out of scope per §3.1. If the user later
  wants mac support, it becomes a separate product.
- **Multi-user / firm-wide data sharing.** The current build is single-user,
  desktop, local-only per §3.2 and §16. Firm-wide deployment needs a
  separate security model.
- **Auto-update.** §3.3 says "not in v1." Revisit after v1 is in production.
- **Commercial connector activations.** §12A.5 describes the optional
  CCH/Bloomberg/Checkpoint/RIA connectors. Base build ships them disabled.
  Post-Phase-11, evaluate which are worth turning on for the user's
  practice.
- **General ledger / trial balance ingestion.** Explicitly out of scope
  in §6B.2. Would be the natural next ingestion pillar.
- **Sales / use tax.** Out of scope per §6B.2.
- **Payroll return ingestion (941, 940, DE-9).** Out of scope per §6B.2.
- **State forms outside the enumerated nine.** Add states as real-engagement
  need surfaces.
- **Projected-rate modeling.** §14.2 says bracket parameters are held
  constant in v1 unless the user opts in. Surface the opt-in more
  prominently post-v1 if rate-change concerns are a frequent lever.

## Items added during build

(none yet)
