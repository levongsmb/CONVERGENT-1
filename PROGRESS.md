# PROGRESS.md — Convergent

## RESUME HERE (last updated 2026-04-19)

**Checkpoint SHA:** 90f6c90 (audit-pass endpoint; this continuity commit advances main by one — run `git rev-parse origin/main` for the post-commit tip)
**Branch:** main (single authoritative branch; all claude/* branches pruned)
**Test suite:** 613 passing (verified 2026-04-19 via `pytest` after testpaths scoped to `app/tests/`); 100 evaluators (50 MVP + 26 COMPLIANCE_AND_PROCEDURAL + 24 STATE_SALT)
**Gates closed:** G0–G7 signed. G8 backfilled (STATE_SALT) — signature recorded in governance reconciliation commit be2f44b.
**Audit-pass milestone (2026-04-19):** 4 commits landed resolving 6 audit findings (F1-F6): pyproject deps+testpaths hygiene (f6a8777), convergent-mine CLI removal (0e34fbf), documentation truthfulness sweep (0f6c51a), hygiene baseline LICENSE+SECURITY.md+.gitattributes (90f6c90). F7 (dep upgrades) and F8 (spouse-domicile validation) recorded in BACKLOG_V2.md as deferred.
**Next task:** Begin Phase 3b category 3 — CALIFORNIA_SPECIFIC. One MVP evaluator (CA_PTET_ELECTION) already exists from G5; remaining 14 subcategories per `__strategy_library/subcategories/CALIFORNIA_SPECIFIC.yaml` MANIFEST.
**Open blockers:** Q0.6 (Strategy Library category sequence — accept default or reorder; not blocking current work per OPEN_QUESTIONS.md); outstanding ◐/☐ rows in `rules_cache_bootstrap/review_checklist.md`.
**Session-close rule:** Every gate close must git push to origin/main. Local-only commits are not durable state.
**Orientation order for new sessions:** CLAUDE.md → PROGRESS.md → CHANGELOG.md (last 3 entries) → OPEN_QUESTIONS.md → latest __strategy_library/subcategories/*_SIGNOFF.md.

---

## Current State

The project is in active Phase 3b development: building per-category
deterministic evaluators with per-category G<N> sign-off gates. As of the
most recent commit on `origin/main`:

- **Phase 0** complete through G0 (hot-swappable config architecture,
  signed 2026-04-18).
- **Phase 1a** complete through G1 (client-scenario Pydantic-v2 models +
  seven fixtures + 22 parse tests, signed 2026-04-18).
- **Phase 1b** complete through G3 (40-category Strategy Library MANIFEST,
  616 subcategories, 10 integrity tests, signed 2026-04-18).
- **Phase 2** complete through G4 (cross-check runner, ruamel-safe merge,
  audit log, dry-run shows 616/616 subcategories need cross-check,
  signed 2026-04-18). Real API run deferred to user invocation.
- **Phase 3a** complete through G6 (50 MVP evaluators across 19 categories,
  359 → 490 tests passing, signed 2026-04-18).
- **Phase 3b** in progress:
  - Category 1 of 40 — COMPLIANCE_AND_PROCEDURAL — complete through G7.
    26 new evaluators (27 total in category), 131 new tests
    (CAP_K2_K3 = 6, all others = 5), 613 tests passing after G7
    hardening commit 321b98e. G7 sign-off document present at
    `__strategy_library/subcategories/COMPLIANCE_AND_PROCEDURAL_EVALUATORS_SIGNOFF.md`.
  - Category 2 of 40 — STATE_SALT — complete per commit `8f9f518`
    ("Phase 3b — STATE_SALT complete (category 2 of 40)"). 25 evaluator
    files under `app/evaluators/STATE_SALT/`. Sign-off at
    `__strategy_library/subcategories/STATE_SALT_EVALUATORS_SIGNOFF.md`.
  - Categories 3-40 not yet started.
- **G6 remediation** (post-STATE_SALT, dated 2026-04-19): Task 0
  (rules-cache migration commit + `.gitignore` fix, commit `3bd0aae`)
  and Task 1 (widen §199A phase-in ranges per OBBBA §70431, commit
  `ebe6ad9`) landed. Presumably more remediation tasks pending.

Repo health: no uncommitted changes on the working branch. Test suite
last reported green at 613 passing (post-G7-hardening).

## Pending / Next Step

> **Superseded by RESUME HERE above.** The three options below were
> the open slate at session close; RESUME HERE has since selected
> option 2 (CALIFORNIA_SPECIFIC Phase 3b sequence 3) as the next
> task. Preserved for audit context only.

Awaiting direction on the branch task. Given the branch name
`claude/check-continuity-files-O93vl`, the apparent intent is the
bootstrap that just ran — creating `CLAUDE.md`, `ARCHITECTURE.md`,
`PROGRESS.md` themselves. After this commit, the logical next step for
the underlying build is:

1. Continue G6 remediation — the 2026-04-19 commits indicate an
   in-progress remediation task sequence (Task 0 and Task 1 landed;
   Task 2+ likely queued).
2. Start Phase 3b category 3 per the MANIFEST sequence order
   (after Q0.6 is resolved or the default order is confirmed).
3. Resolve Q0.6 in `OPEN_QUESTIONS.md` (Strategy Library category order
   paste-back) if the user is ready.

Waiting for user to specify which of these — or something else — to
tackle next.

## Open Questions

Per `OPEN_QUESTIONS.md`:

- **Q0.6 — Strategy Library category sequence** (deferred 2026-04-18).
  User owes either an explicit "accept default order" or a re-ordered
  sequence for the 20-category MANIFEST. Blocks Phase 1 sub-phase
  sequencing. Default order is reproduced in `OPEN_QUESTIONS.md`.
- **Sign-off companions still outstanding.** The Phase 0 acceptance gate
  requires every row in `rules_cache_bootstrap/review_checklist.md` to
  reach the ✓ state. Several ◐ and ☐ rows remain.

## Session History

### 2026-04-19 — Session continuity bootstrap (this session)

- Detected that `CLAUDE.md`, `PROGRESS.md`, `ARCHITECTURE.md` were absent
  at project root.
- Verified repo is a Git repository on branch
  `claude/check-continuity-files-O93vl` with clean working tree.
- Read `README.md`, `pyproject.toml`, `BACKLOG_V2.md`, `OPEN_QUESTIONS.md`,
  `docs/REPO_LAYOUT.md`, and the first 500 lines of `CHANGELOG.md` to
  reconstruct project state.
- Enumerated `app/`, `config/`, `__strategy_library/`, `convergent/`,
  `docs/decisions/`, `rules_cache_bootstrap/`, `installer/`, `scripts/`,
  and `tests/` subfolders.
- Inspected recent commits (last 20) — confirmed build through
  Phase 3b category 2 (STATE_SALT) + G6 remediation commits on 2026-04-19.
- Authored `CLAUDE.md` (purpose/stack/overview/conventions/standing
  rules/run-test), `ARCHITECTURE.md` (file-by-file map), and
  `PROGRESS.md` (this file).
- Will commit as "Add session continuity documentation".

### 2026-04-19 — Governance reconciliation session

- Investigated and documented STATE_SALT gate-ordering violation
- G7 hardening: added IRC §6511(b)(2) cap to CAP_PROTECTIVE_ELECTIONS
- Fixed CAP_K2_K3 test-count typo in G7 SIGNOFF (5 → 6)
- Cherry-picked session continuity docs from check-continuity-files
- Backfilled G8 CHANGELOG entry; renamed STATE_SALT SIGNOFF G7 → G8
- Test suite: 610 → 613 passing

### 2026-04-19 — Audit pass + session-close continuity

- External audit flagged 8 findings (1-H, 6-M, 1-L). Addressed F1-F6
  with 4 focused commits; F7 (dep upgrades) and F8 (spouse-domicile
  validation) deferred to BACKLOG_V2.md per CLAUDE.md standing rule
  and resolutions brief.
- `pyproject.toml`: added `ruamel.yaml==0.18.6` (closed undeclared-dep
  gap) and scoped `testpaths` to `["app/tests"]` (default `pytest`
  now targets active suite, 613 passing).
- Retired `convergent-mine` CLI entry point (previously raised
  `NotImplementedError` on invocation).
- Documentation truthfulness sweep across 7 files: README,
  OPEN_QUESTIONS, ARCHITECTURE, `config/VERSION.yaml`,
  `docs/REPO_LAYOUT.md`, CLAUDE.md, BACKLOG_V2 — all aligned with
  current Phase 3b state; removed references to non-existent `config/`
  directories from VERSION.yaml manifest.
- Hygiene baseline added: `LICENSE` (Proprietary, All Rights
  Reserved), `SECURITY.md` (private internal-channel reporting,
  no public bug bounty), `.gitattributes` (LF-default, CRLF for
  Windows-only scripts).
- Test suite unchanged at 613 passing throughout the pass (no code
  behavior touched).
- Session-close continuity commit refreshes this RESUME HERE block
  and adds a CHANGELOG Housekeeping entry.
