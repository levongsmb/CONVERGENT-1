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

- **Dependency upgrade pass (post-Phase-5 golden-suite).** Audit
  2026-04-19 flagged public advisories for pinned `nicegui==2.7.0`,
  `jinja2==3.1.4`, `pillow==11.0.0`, `cryptography==43.0.3`,
  `pytest==8.3.3`. Deferred per CLAUDE.md "Never auto-update
  dependencies" standing rule and spec §18 (any upgrade requires
  re-running the full golden-scenario suite, which is Phase 5+).
  Revisit after the golden-suite harness exists. Scope: per-package
  advisory review, targeted upgrade, lockfile introduction.
- **Married-scenario validation hardening.** Audit 2026-04-19
  flagged `app/scenario/models.py:334-339` requires `spouse_dob` for
  MFJ/MFS but not `spouse_state_domicile`, and
  `app/scenario/validators.py:146-164` only emits the
  community-property reminder when `spouse_state_domicile` is present.
  Deferred as optional — low impact today (scenarios parse); revisit
  when community-property math becomes a real cross-check target.
- **Convergence engine (PRD §5.4) tracking placeholder.** The
  fixed-point iteration that resolves officer-comp ↔ §199A ↔ taxable-
  income ↔ threshold ↔ W-2 wage-limit ↔ retirement-base ↔ PTET-base
  interactions is the namesake computation of the product. No
  scaffolding, regression harness, or decision record exists yet.
  Per the PRD it is the highest-risk component (wrong convergence
  silently corrupts every downstream scenario). Target landing is
  Phase 5 (Scenario Engine and Optimizer); adding here for visibility
  until a Phase 5 decision file and test harness exist. Prereqs:
  tolerance/max-iteration/damping parameterization, golden-scenario
  regression suite (Phase 5 gate blocks UI work until green), and an
  OPEN_QUESTIONS entry for the default damping factor in pathological-
  cycle cases.
- **§1401 (SECA) explicit entry in `config/authorities/2026/irc_sections.yaml`.**
  SECA is referenced by 100+ evaluator assertions but not listed
  explicitly in the IRC-sections authority YAML. Non-blocking
  (evaluators read parameters from `rules_cache/` without authority
  dependence), but asymmetric relative to §1411, §199A, etc.
  Add an entry when the authority cross-check begins consuming
  payroll-tax authorities.
