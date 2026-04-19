# ARCHITECTURE.md — Convergent

File-by-file map of the repository, grouped by module. Two build layers
coexist: the new `app/` + `config/` + `__strategy_library/` layer (active
development, Phases 0-3b) and the older `convergent/` package (v3 scaffolding
from `docs/REPO_LAYOUT.md`, partly stub).

## Root

- `README.md` — Phase 0 status note, build prerequisites, installer platform
  targets, pointer to the master build spec.
- `pyproject.toml` — Python 3.12 pinning, exact-version deps, ruff/mypy/pytest
  config, CLI entry points (`convergent`, `convergent-bootstrap`,
  `convergent-mine`).
- `CHANGELOG.md` — phase-by-phase build log. Each G<N> gate has a subsection.
- `OPEN_QUESTIONS.md` — questions blocking phase entry (Q0.6 deferred — the
  strategy library category order awaiting user paste-back).
- `BACKLOG_V2.md` — additive-only deferred-feature list.
- `.gitignore` — excludes caches, venvs, installer artifacts.

## Governance docs — `docs/`

- `docs/PROMPT_V3.md` — the consolidated master build spec (§§1-19).
- `docs/REPO_LAYOUT.md` — canonical v3 layout (reference; partially
  superseded by new `app/` + `config/` layer under Decision 0010).
- `docs/decisions.md` — tax-judgment fork index.
- `docs/decisions/0001-phase0-scope.md` through `0010-master-build-supersession.md`
  — one file per decision. 0005 pins Claude model family. 0008 narrows OBBBA
  Notice scope. 0010 declares prior discussion threads superseded by the
  master build spec.

## New build layer — `app/`

Phase 0 (G0) introduced a hot-swappable configuration architecture.

### `app/config/` — configuration loaders

- `router.py` — `LLMConfig` dataclass, `get_llm_config(task_class)` returns
  `{model, max_tokens, temperature}` per `config/models.yaml`.
- `rules.py` — `get_rule(...)` + `RuleBundle` + `cache_version()`. Single
  point of access for parameter lookup.
- `authorities.py` — id-unique-per-year index across
  `config/authorities/<year>/*.yaml`.
- `forms.py` — loads `config/forms/**/*.yaml`, enforces `applies_to_tax_years`.
- `prompts.py` — Jinja2 `StrictUndefined` loader for `config/prompts/`.
- `validate.py` — pre-commit validator; `python -m app.config.validate`.

### `app/scenario/` — client-scenario models (G1)

- `models.py` — complete Pydantic-v2 model set per spec §2.2. `ClientScenario`
  with `Identity`, `IncomeItem`, `K1Income`, `Income`, `Entity`, `Asset`,
  `Deductions`, `PlanningContext`, `PriorYearContext`. Enums: `FilingStatus`,
  `EntityType`, `AssetType`, `StateCode` (50+DC+5 territories). Two
  `model_validator`s for orphan-K-1 and filing-status/spouse coupling.
- `validators.py` — eight cross-field diagnostic checks.
- `loader.py` — canonical YAML→model entry point.
- `schema.yaml` — auto-generated JSON-schema export (1,068 lines) for diffing.
- `SCHEMA_SIGNOFF.md` — G1 sign-off (signed 2026-04-18).
- `fixtures/` — seven realistic scenarios: `scenario_single_1040.yaml`,
  `scenario_mfj_scorp_owner.yaml`, `scenario_partnership_owner.yaml`,
  `scenario_real_estate_investor.yaml`, `scenario_qsbs_founder.yaml`,
  `scenario_trust_beneficiary.yaml`, `scenario_liquidity_event.yaml`.

### `app/cross_check/` — Phase 2 cross-check protocol (G4)

- `runner.py` — orchestrator. `LLMClient` wrapper with checkpoint-every-N,
  escalation path (Sonnet → Opus on low confidence), failure handling.
- `null_detection.py` — §4 trigger-field null detection across the six
  metadata fields.
- `merge.py` — `ruamel.yaml` round-trip-safe merge that preserves user-signed
  inline citations.
- `audit.py` — JSONL audit log with sha16 hashing of prompts + responses.
- `__main__.py` — CLI (`--real`, `--dry-run`, `--today-date`).

### `app/evaluators/` — Phase 3a/3b deterministic strategy evaluators

- `_base.py` — `TaxImpact` + `StrategyResult` dataclasses; `RulesCache` and
  `Evaluator` protocols; `BaseEvaluator` with `_not_applicable()` helper;
  `ConfigRulesAdapter` production rules-cache adapter.
- `_registry.py` — idempotent `register_all()` auto-discovery, `reset()`
  test hook, `get(code)`, `all_evaluators()`.
- `MVP_PATTERN_SIGNOFF.md` — G5 sign-off (signed 2026-04-18).
- `MVP_50_SIGNOFF.md` — G6 sign-off (signed 2026-04-18).

Per-category subdirectories (one folder per MANIFEST category code), each with
evaluator modules and an `__init__.py`. Categories currently populated:
`ACCOUNTING_METHODS/`, `CALIFORNIA_SPECIFIC/`, `CAPITAL_GAINS_LOSSES/`,
`CHARITABLE/`, `COMPENSATION/`, `COMPLIANCE_AND_PROCEDURAL/` (G7 complete),
`CREDITS/`, `ENTITY_SELECTION/`, `INSTALLMENT_AND_DEFERRED_SALES/`,
`LOSS_LIMIT_NAVIGATION/`, `NIIT_1411/`, `PTE_BASIS_AND_DISTRIBUTIONS/`,
`QBI_199A/`, `QSBS_1202/`, `REAL_ESTATE_DEPRECIATION/`, `RETIREMENT/`,
`SALE_TRANSACTION/`, `SELF_EMPLOYMENT_TAX/`, `STATE_SALT/` (G8 in progress —
25 evaluator files).

Current registry size: 76 evaluators (50 MVP from G6 + 26 from COMPLIANCE
category G7). Test suite: 490 passed at G7 sign-off.

### `app/tests/` — test suite

- `cross_check/test_cross_check.py` — 16-test suite for runner, null detection,
  merge, audit, dry-run, real path, escalation, retry.
- `evaluators/<CATEGORY>/test_<CODE>.py` — per-evaluator test modules
  (average 5-7 tests per evaluator, deterministic anchors required).
- `scenarios/test_fixtures_parse.py` — 22-test fixture-parse suite.
- `strategy_library/test_library_parses.py` — 10 integrity tests for the
  MANIFEST and per-category YAMLs.

## Configuration — `config/`

- `VERSION.yaml` — top-level manifest with component-by-component version.
- `models.yaml` — four task classes with escalation paths.
- `CONFIG_ARCHITECTURE_SIGNOFF.md` — G0 sign-off (signed 2026-04-18).
- `authorities/2026/irc_sections.yaml` — twelve IRC sections required by
  Phase 3a MVP (§199A, §1202 split, §164 sunset schedule, §461, §151 with
  §151(f) senior deduction, §1062, §174, §174A, §139L, §168, §2010, §1411).
- `rules_cache/2026/federal/` — post-migration rules cache (federal YAMLs).
- `rules_cache/2026/california/` — post-migration CA YAMLs.
- `forms/california/3804.yaml` — SB 132 PTET form parameters.
- `prompts/cross_check_subcategory.j2` — externalized Phase 2 prompt.

## Strategy Library — `__strategy_library/`

Phase 1b deliverable per spec §§3.1-3.4.

- `LIBRARY_SIGNOFF.md` — G3 sign-off (signed 2026-04-18).
- `subcategories/MANIFEST.yaml` — 40 categories with sequence orders 1-40.
- `subcategories/<CATEGORY_CODE>.yaml` — 40 category files, 616 subcategories
  total (within spec band 550-650).
- `subcategories/<CATEGORY>_SIGNOFF.md` — 40 per-category companions (mix of
  signed and pending).
- `subcategories/COMPLIANCE_AND_PROCEDURAL_EVALUATORS_SIGNOFF.md` — G7 gate
  document.
- `subcategories/STATE_SALT_EVALUATORS_SIGNOFF.md` — G8 gate document (in
  progress; STATE_SALT evaluators exist, sign-off pending).
- `_staging/CATEGORY_DECISIONS_SIGNOFF.md` — informational G2 record of
  eight category-level merges.
- `_audit/cross_check_2026-04-18.jsonl` — G4 dry-run audit log (616 rows).
- `_audit/cross_check_summary.md` — G4 sign-off (signed 2026-04-18).

## Phase 0 audit trail — `rules_cache_bootstrap/`

Preserved as the Phase 0 audit trail after migration to `config/rules_cache/`.

- `README.md` — review workflow description.
- `review_checklist.md` — per-row sign-off status.
- `_SIGNOFF_TEMPLATE.md` — template for per-file companions.
- `federal/` + `california/` — original bootstrapped YAMLs (migrated copies
  now live in `config/rules_cache/2026/`).
- `listed_transactions.yaml`, `reportable_transactions.yaml`,
  `obbba_notices.yaml` — top-level regulatory lists.

## Legacy `convergent/` package — v3 scaffolding

Scaffolding laid during Phase 0. Many modules are stubs pending later phases.

- `__main__.py` — CLI entry.
- `config.py` — paths, env, app directories.
- `ingestion/` — §6B prior-return ingestion. `parsers/` subfolder.
- `intake/` — §6A household/entity wizard (not yet populated here).
- `goals/` — §6C (not yet populated).
- `engine/` — scenario engine (§8/§14) — currently `__init__.py` stub.
- `optimizer/` — PuLP/CBC MIP bundle + SLSQP param tuning (stub).
- `strategies/` — §12 modules (stub; real work is happening under
  `app/evaluators/`).
- `authority_layer/`:
  - `api.py` — `authority.query()` entry.
  - `citation_verifier.py`
  - `pii_sanitizer.py`
  - `prompts/` — footnote / flag / pitfall / commentary templates.
  - `statutory_mining/` — scheduler + bootstrap + source adapters (IRS,
    Treasury, US Tax Court, FTB, govinfo, eCFR, Federal Register).
- `cost_of_advice/` — §15 (stub).
- `memo/` — §10 generator (stub).
- `persistence/` — SQLCipher-encrypted stores:
  - `engagement_db.py`, `rules_cache_db.py`, `authority_cache_db.py`
  - `sqlcipher_key.py` — DPAPI-sealed key derivation (Win32).
  - `export_cvg.py` — portable `.cvg` export/import.
- `ui/` — NiceGUI views (stub; `views/` empty).
- `util/` — decimal tax helpers, derivation tree, logging, time windows.
- `goals/`, `intake/`, `engine/`, `optimizer/`, `strategies/`, `cost_of_advice/`,
  `memo/`, `ui/`, `util/` mostly contain only `__init__.py` today.

## Authority runtime assets — `authority_layer/`

- `pitfalls.yaml` — runtime pitfalls index (includes the CA PTET SB 132
  shortfall-credit-reduction entry updated under Decision 0004).

## Strategy library runtime assets — `strategy_library/`

- `MANIFEST.yaml` — 20-category sequence order (the "default" presented to
  the user in Q0.6). Mirrored/superseded by `__strategy_library/subcategories/
  MANIFEST.yaml` (40 categories).
- `README.md` — loader intro.

## Installer — `installer/`

- `convergent.iss` — Inno Setup 6 script.
- `pyinstaller.spec` — PyInstaller onefolder spec.
- `runtime_hooks/` — PyInstaller hook scripts.
- `vendor/` — bundled binaries (Tesseract, Ghostscript, tessdata).
- `README.md` — installer build notes.

## Scripts — `scripts/`

- `build_installer.ps1` — PyInstaller + Inno Setup driver (Windows-only).

## Tests (legacy scaffolding) — `tests/`

- `conftest.py` — shared pytest fixtures for the legacy layer.
- `unit/` — legacy unit tests (scaffolding).

(The active test suite for the new build layer is under `app/tests/`.)
