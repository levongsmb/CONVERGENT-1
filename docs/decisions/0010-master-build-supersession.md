# 0010 — Master build spec supersedes prior discussion threads

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** G0 (hot-swappable config architecture)

## Context

The firm issued a new master build specification ("STRATEGY LIBRARY TAX
PLANNING APPLICATION") on 2026-04-18 that explicitly states "All prior
discussion threads are superseded by this document." Prior scaffolding
under `convergent/`, `strategy_library/`, `authority_layer/`, and `tests/`
was produced under the older Convergent v3 prompt. The new spec defines a
different top-level structure (`app/`, `config/`, `__strategy_library/`),
a different project identity (SMB CPA Group, PC, not Convergent), and a
different architectural principle (hot-swappable config with code as
stable infrastructure).

## Decisions incorporated from the new spec

1. **Repository identity.** The application is the SMB CPA Group strategy
   library tax planning application. Prior "Convergent" naming is
   retained only in filenames that are not part of the new build (e.g.,
   `README.md` text will be rewritten as the new build advances).
2. **User preferences apply to all new content.** No contractions in code
   comments, documentation, or generated client-facing content. No
   emojis, no filler, no hype, no sign-off phrases. Body text #1A1A1A;
   accent #ED3812 reserved for marketing material only (never formal
   documents). Levon is a CPA, not an attorney — use "Confidential —
   Tax Practitioner Work Product" on formal documents.
3. **Task classes as stable API.** Code references `complex_reasoning`,
   `bulk_cross_check`, `classification`, and `memo_polish`. Model
   strings live in `config/models.yaml` and are fluid. Decision 0005's
   answer (pin to Claude 4.7 / 4.6 / 4.5 family) is implemented via the
   initial model strings in that config file and remains changeable
   without code modification.
4. **Phase 0 meaning.** Under the new spec, "Phase 0" is the
   hot-swappable configuration architecture, not the rules cache
   bootstrap. The prior Phase 0 (rules cache bootstrap) is acknowledged
   by the new spec as "COMPLETE, user signed off" and is migrated into
   `config/rules_cache/2026/` during Phase 1.
5. **Prior scaffolding disposition.** Directories `convergent/`,
   `strategy_library/`, `authority_layer/`, and `tests/` remain for
   reference through the transition. Content is migrated or obsoleted as
   the new build advances. No mass deletion at G0 — the master spec
   does not direct deletion, and prior sign-offs (rules cache, decisions
   0001-0009) remain authoritative for their subject matter.

## Answer

Proceed under the new master build spec. G0 closed by the deliverables
in `config/CONFIG_ARCHITECTURE_SIGNOFF.md`. Decisions 0001-0009 remain
in force for their subject matter (rules cache, CA PTET under SB 132,
claude model family, narrow OBBBA scope, signoff companions). Decision
0009 (strategy library category order) remains OPEN and is answered
under the new build's MANIFEST in Phase 1b.

## Implementation notes

- `config/` tree populated with VERSION manifest, models routing,
  reference authority file (`irc_sections.yaml` covering 12 sections),
  reference form file (`3804.yaml`), and reference prompt template
  (`cross_check_subcategory.j2`).
- `app/config/` package with router (exact signature per spec §0.5),
  rules loader, authority loader (with per-year id uniqueness),
  form loader (with applies_to_tax_years enforcement), Jinja2 prompt
  renderer (StrictUndefined), and config validator.
- `python -m app.config.validate` passes.
- Phase 1a cannot begin until user signs
  `config/CONFIG_ARCHITECTURE_SIGNOFF.md`.
