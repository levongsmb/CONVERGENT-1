# Changelog

Phase-by-phase build log per §18. Each phase gets a subsection. Only
user-visible behavior changes are recorded here — incidental refactors and
test additions live in git history.

## [Unreleased]

### G5 — Phase 3a MVP Evaluator Pattern (2026-04-18)

G4 signed off by Levon Galstian, CPA on 2026-04-18. First 5 evaluators
built per spec §5.5. Halts at G5 for user pattern review before
evaluators 6-50.

- **Migrated:** `rules_cache_bootstrap/{federal,california}/*.yaml` →
  `config/rules_cache/2026/{federal,california}/*.yaml` (20 YAMLs: 16
  federal + 4 California). Prior SIGNOFF.md companions and review
  checklist remain under `rules_cache_bootstrap/` as the Phase 0 audit
  trail. `config/VERSION.yaml` migration note updated.
- **Added:** `app/evaluators/_base.py` with `TaxImpact` and
  `StrategyResult` dataclasses, `RulesCache` and `Evaluator` protocols,
  `BaseEvaluator` class (with `_not_applicable()` helper), and
  `ConfigRulesAdapter` production rules-cache adapter.
- **Added:** `app/evaluators/_registry.py` with idempotent
  `register_all()` auto-discovery, `reset()` test hook, `get(code)`,
  `all_evaluators()`.
- **Added:** Five evaluators with 38 tests passing (7 + 7 + 7 + 8 + 9):
  `CAP_EST_TAX_SAFE_HARBORS` (§6654 safe harbors with elevated-pct
  detection and lumpy-income flag), `COMP_REASONABLE_COMP` (three-band
  classification RISK / DEFENSIBLE / EXCESSIVE with Mulcahy / Watson
  citations and quantified FICA savings on excessive posture),
  `COMP_WAGE_DIST_SPLIT` (OASDI base anchor with graceful degradation
  when base is awaiting user input, Medicare-delta math on above-base
  wage), `QBI_SCORP_WAGE_BALANCE` (spec §5.3 reference pattern — W-2
  and W-2+UBIA ceiling computation with binding detection),
  `CA_PTET_ELECTION` (SB 132 regime with 9.3% rate, SALT-cap overlap
  reduction, both S-corp and partnership applicability).
- **Added:** `app/evaluators/MVP_PATTERN_SIGNOFF.md` documenting the
  evaluator pattern, test shape, architectural invariants, and
  divergences from spec §5.3 with rationale; lists the remaining 45
  evaluators (6-50) in order for Phase 3a continuation.
- **Changed:** `__strategy_library/_audit/cross_check_summary.md`
  signed 2026-04-18 by Levon Galstian, CPA (G4 closed).
- **Gate status:** G4 closed. G5 sign-off pending at
  `app/evaluators/MVP_PATTERN_SIGNOFF.md`. Evaluators 6-50 blocked
  until G5 signed.
- **Test suite totals:** `pytest app/tests/` → 86 passed in 2.01s.
  Registry auto-discovery verified: 5 evaluators self-register and
  address correctly by SUBCATEGORY_CODE.

### G4 — Phase 2 Cross-Check Protocol (2026-04-18)

G3 signed off by Levon Galstian, CPA on 2026-04-18. Phase 2 infrastructure
produced per spec Section 4. Real Anthropic API pass deferred to user
invocation on the firm's API key.

- **Added:** `app/cross_check/` package — `runner.py` (orchestrator with
  `LLMClient` wrapper, checkpoint-every-N, escalation path, failure
  handling), `null_detection.py` (spec §4 trigger-field null detection
  across the six fields), `merge.py` (ruamel.yaml round-trip-safe merge
  that preserves existing non-null values), `audit.py` (JSONL audit log
  with sha16 prompt/response hashing), `__main__.py` (CLI with `--real`
  and `--dry-run` modes).
- **Changed:** `config/prompts/cross_check_subcategory.j2` template uses
  `sub["code"]`, `sub["short_label"]`, and `sub.get("detailed_description")`
  for safe access under the Jinja `StrictUndefined` environment in
  `app/config/prompts.py`. Output wording, schema constraints, and
  structure remain identical to the spec §0.5 template.
- **Added:** `app/tests/cross_check/test_cross_check.py` — 16-test suite
  covering null detection, ruamel-based merge (including the
  preserve-inline-cite invariant), audit log JSONL shape and hashing,
  dry-run mode (no mutation, correct counts), real-path population,
  escalation-on-low-confidence (sonnet → opus), two-attempt JSON parse
  retry with fallback to `cross_check_required=manual`, and
  API-error fallback to `cross_check_required=retry`.
- **Added:** Dependencies `ruamel.yaml` (round-trip YAML) and `anthropic`
  (SDK) installed in the dev environment.
- **Run:** Dry-run executed via `python -m app.cross_check --today-date
  2026-04-18`. Result: 616 of 616 subcategories need cross-check across
  all 40 categories, producing 616 unique prompt hashes with no
  collisions. Cost estimate for the real pass: ~$4.50 single-pass
  Sonnet; up to ~$27 worst case with 100% escalation; expected
  ~$7-10 with 10-15% escalation rate.
- **Added:** `__strategy_library/_audit/cross_check_2026-04-18.jsonl` —
  dry-run audit log with 616 rows.
- **Added:** `__strategy_library/_audit/cross_check_summary.md` — G4
  sign-off document with architecture diagram, dry-run statistics,
  missing-field pattern distribution (six distinct patterns), cost
  estimate, and invocation instructions for the real run.
- **Changed:** `__strategy_library/LIBRARY_SIGNOFF.md` signed 2026-04-18
  by Levon Galstian, CPA (G3 closed).
- **Gate status:** G3 closed. G4 sign-off pending. Phase 3a (MVP
  evaluator batch) blocked until user approves the real cross-check
  run and produces the populated metadata, OR until user explicitly
  authorizes Phase 3a to proceed with the current library state
  (evaluators reference subcategory codes, not populated metadata).
- **Test suite totals:** `pytest app/tests/` → 48 passed.

### G2 + G3 — Phase 1b Strategy Library Inventory (2026-04-18)

G1 signed off by Levon Galstian, CPA on 2026-04-18. Phase 1b produced
per spec Sections 3.1 through 3.4. G2 is informational per spec Section 8
(all category decisions already approved in the master build spec). G3
sign-off pending at `__strategy_library/LIBRARY_SIGNOFF.md`.

- **Added:** `__strategy_library/subcategories/MANIFEST.yaml` matching
  spec §3.1 line-for-line (40 categories with sequence orders 1-40).
- **Added:** 40 category YAML files at
  `__strategy_library/subcategories/<CATEGORY_CODE>.yaml` per spec §3.3.
  Total subcategory count: 616 (spec references ~590; falls within
  the test band 550-650).
- **Added:** 40 per-category `_SIGNOFF.md` companion files per spec §3.4
  with the six-checkbox structure awaiting per-category review.
- **Added:** `__strategy_library/_staging/CATEGORY_DECISIONS_SIGNOFF.md`
  — informational G2 record documenting the eight category-level merges
  (IRS_CONTROVERSY_DEFENSE, INFORMATION_REPORTING_WITHHOLDING,
  NEW_YORK_SPECIFIC, NEW_JERSEY_HAWAII_DC_SPECIFIC,
  EMPLOYMENT_PAYROLL_BENEFITS, ENERGY_CREDITS_INCENTIVES,
  EXIT_AND_SUCCESSION, DEFERRED_COMPENSATION_409A).
- **Added:** `__strategy_library/LIBRARY_SIGNOFF.md` — overall G3 gate
  document with integrity metrics, OBBBA coverage inventory, and the
  six spec-mandated sign-off checkboxes.
- **Added:** `app/tests/strategy_library/test_library_parses.py` with
  ten integrity tests: MANIFEST structure, file presence,
  no-orphan-file, code/sequence consistency, global subcategory
  uniqueness, cross_references resolution, merged_from legacy-only
  check, OBBBA statutory_cite well-formedness, total subcategory count
  in expected range, and evaluator_path format. Result:
  `pytest app/tests/strategy_library/` -> 10 passed in 0.96s.
- **Changed:** `app/scenario/SCHEMA_SIGNOFF.md` signed 2026-04-18 by
  Levon Galstian, CPA with all five spec §2.4 boxes checked.
- **Gate status:** G1 closed. G2 informational (no sign-off required).
  G3 sign-off pending. Phase 2 (cross-check protocol) blocked until G3
  signed.

### G1 — Phase 1a Client Scenario Schema (2026-04-18)

G0 signed off by Levon Galstian, CPA on 2026-04-18. Phase 1a produced.

- **Added:** `app/scenario/models.py` — complete Pydantic v2 model set per
  spec §2.2. `FilingStatus`, `EntityType`, `AssetType`, and a full
  `StateCode` enum covering all 50 states, DC, and the five US
  territories (PR, VI, GU, MP, AS). Models: `Identity`, `IncomeItem`,
  `K1Income`, `Income`, `Entity`, `Asset`, `Deductions`,
  `PlanningContext`, `PriorYearContext`, and top-level `ClientScenario`
  with two `model_validator` methods (orphan-K-1 check and
  filing-status/spouse check).
- **Added:** `app/scenario/validators.py` — eight cross-field diagnostic
  checks beyond Pydantic: entity ownership bounds, QSBS asset metadata
  completeness, S corp `stock_basis` presence, partnership
  `outside_basis` presence, `liquidity_event_planned` shape and
  objective-presence coupling, state-sourcing resident-state coverage,
  dependents shape, and informational community-property / MFS flag.
- **Added:** `app/scenario/loader.py` — single canonical YAML-to-model
  entry point used by tests and future orchestrator work.
- **Added:** `app/scenario/schema.yaml` — auto-generated JSON-schema
  export of `ClientScenario` (1,068 lines) for review diffing.
- **Added:** Seven realistic fixtures in `app/scenario/fixtures/`:
  `scenario_single_1040.yaml` (single W-2 baseline);
  `scenario_mfj_scorp_owner.yaml` (primary SMB CPA Group archetype with
  QBI / reasonable-comp / PTET triggers);
  `scenario_partnership_owner.yaml` (35% active LLC-as-partnership member
  with Soroban-risk posture);
  `scenario_real_estate_investor.yaml` (three rentals, commercial
  cost-seg candidate, REP status question, CA §168(k) nonconformity);
  `scenario_qsbs_founder.yaml` (single founder, pre-IPO C corp, pre- and
  post-OBBBA §1202 lots, 2029 liquidity target);
  `scenario_trust_beneficiary.yaml` (MFJ beneficiary of nongrantor trust
  with full K-1 distribution);
  `scenario_liquidity_event.yaml` (100% S corp owner, ~$18M EV sale
  planned in 18 months with earnout component).
- **Added:** `app/tests/scenarios/test_fixtures_parse.py` — 22-test
  pytest suite covering per-fixture parse, cross-field validator cleanness,
  fixture-set completeness, QBI component presence on the S-corp owner
  fixture, pre- and post-OBBBA QSBS lot presence on the founder fixture,
  liquidity-event block presence on the sale fixture, Decimal precision
  round-trip through YAML, and three model-level refusal tests.
- **Changed:** `config/CONFIG_ARCHITECTURE_SIGNOFF.md` signed
  2026-04-18 by Levon Galstian, CPA.
- **Gate status:** G0 closed. `pytest app/tests/scenarios/` green
  (22 passed in 0.51s). G1 sign-off pending at
  `app/scenario/SCHEMA_SIGNOFF.md`.

### G0 — Hot-swappable configuration architecture (2026-04-18)

Implements Phase 0 of the new master build specification ("STRATEGY
LIBRARY TAX PLANNING APPLICATION"). Prior Convergent v3 scaffolding
remains in place for reference; new build work proceeds under `app/`,
`config/`, and `__strategy_library/`.

- **Added:** `config/VERSION.yaml` top-level manifest with pointers to
  every config component and its version.
- **Added:** `config/models.yaml` with the four canonical task classes —
  `complex_reasoning` (claude-opus-4-7), `bulk_cross_check`
  (claude-sonnet-4-6), `classification` (claude-haiku-4-5-20251001),
  `memo_polish` (claude-opus-4-7) — escalation paths, and batching
  defaults.
- **Added:** `app/config/` package: `router.py` (LLMConfig dataclass
  and `get_llm_config()` per spec), `rules.py` (get_rule + RuleBundle +
  cache_version), `authorities.py` (id-unique-per-year index),
  `forms.py` (with `applies_to_tax_years` enforcement), `prompts.py`
  (Jinja2 `StrictUndefined`), `validate.py` (pre-commit validator).
- **Added:** `config/prompts/cross_check_subcategory.j2` — the Phase 2
  cross-check prompt externalized.
- **Added:** `config/authorities/2026/irc_sections.yaml` covering twelve
  IRC sections required by Phase 3a MVP evaluators (§199A, §1202 with
  pre/post-OBBBA split metadata, §164 with sunset schedule, §461, §151
  with §151(f) senior deduction, §1062, §174, §174A, §139L, §168, §2010,
  §1411).
- **Added:** `config/forms/california/3804.yaml` populated with the
  SB 132 regime parameters signed off under Decision 0004.
- **Added:** Directory structure for `config/rules_cache/2026/`,
  `config/authorities/2026/state/`, `config/forms/federal/`,
  `config/report_templates/`, `config/cross_check_schemas/`,
  `app/scenario/fixtures/`, `app/evaluators/`, `app/orchestrator/`,
  `app/reports/`, `app/tests/{evaluators,scenarios,orchestrator}/`,
  `__strategy_library/{subcategories,_staging,_audit}/`.
- **Added:** Decision 0010 recording the supersession of prior
  discussion threads by the master build spec.
- **Gate status:** `python -m app.config.validate` passes. G0 sign-off
  pending at `config/CONFIG_ARCHITECTURE_SIGNOFF.md`.

### Phase 0 — Rules cache first sign-off pass (2026-04-18)

User answered the six Q0.1–Q0.5 gate questions (Q0.6 deferred for
paste-back) and supplied confirmed values for the most consequential
parameter families.

- **Added:** Decision 0005 (Claude model pinning — 4.7 / 4.6 / 4.5
  family), 0006 (unsigned Phase 0 installer), 0007 (per-file SIGNOFF.md
  review method), 0008 (narrow OBBBA Notice scope — 13 provisions),
  0009 (strategy category order — deferred).
- **Changed:** decisions 0001–0004 marked ANSWERED with implementation
  notes; Decision 0004 records the CA PTET corrections.
- **Changed:** `rules_cache_bootstrap/california/ptet.yaml` rewritten to
  SB 132 authority with (a) dual deadline fields
  (`election_and_balance_due_date` and `election_minimum_prepayment_date`
  replacing the single prior field), (b) explicit June 15 minimum
  prepayment floor ($1,000) and pct-of-prior-year (50%), (c) shortfall-
  based credit reduction mechanic at 12.5% measured at return filing
  date, and (d) 2026–2030 effective window. RTC §§19900 et seq. moved
  to secondary-only for 2026+.
- **Changed:** `authority_layer/pitfalls.yaml` CA PTET entry renamed to
  `ca_ptet_june15_shortfall_credit_reduction` with SB 132 primary
  authority and shortfall-based mechanic narrative.
- **Changed:** `rules_cache_bootstrap/federal/section_1202.yaml`
  rewritten with OBBBA regime (QSBS issued after 2025-07-04 — $15M /
  10× cap indexing from 2027, $75M gross assets ceiling indexing from
  2027, 50 / 75 / 100% exclusion at 3 / 4 / 5 years) and pre-OBBBA
  grandfathered regime ($10M / $50M / 5-year).
- **Changed:** `rules_cache_bootstrap/federal/salt_cap_obbba.yaml`
  rewritten with the full indexed schedule (2025 $40K → 2026 $40,400 →
  2027–2029 prior × 1.01 → 2030 reversion to $10K), 30% phaseout rate,
  MFJ / MFS thresholds, $10K / $5K floors, and Sunset Watch anchor year
  2030.
- **Changed:** `rules_cache_bootstrap/federal/retirement_limits.yaml`
  rewritten with confirmed 2026 values from IRS Notice 2025-67 covering
  §402(g), §414(v), super catch-up, IRAs, SIMPLE standard and higher
  limits, §415(c), §414(q), §401(a)(17), Roth IRA and Traditional IRA
  MAGI phaseouts, Saver's Credit caps, and SECURE 2.0 mandatory Roth
  catch-up threshold at $150,000. §415(b) DB limit remains
  `awaiting_user_input` (not in the user's supplied table).
- **Changed:** `rules_cache_bootstrap/federal/individual_brackets.yaml`
  rewritten with Rev. Proc. 2025-32 Single and MFJ tables; MFS, HoH,
  and trusts/estates tables retained as `awaiting_user_input` per user
  instruction to copy verbatim from the Rev. Proc. PDF.
- **Added:** `rules_cache_bootstrap/federal/standard_deduction.yaml`
  (MFJ $32,200 / HoH $24,150 / Single-MFS $16,100 / +$2,050 or +$1,650
  per qualifying factor).
- **Added:** `rules_cache_bootstrap/federal/amt_individual.yaml` with
  Single exemption $90,100 / MFJ $140,200, phaseout starts $500K /
  $1M, 50% phaseout rate (OBBBA), $244,500 / $122,250 MFS 28% rate
  threshold.
- **Added:** `rules_cache_bootstrap/federal/obbba_senior_deduction_151f.yaml`
  ($6,000 per qualifying taxpayer age 65+, 6% phaseout over $75K / $150K
  MAGI, effective 2025–2028).
- **Added:** `rules_cache_bootstrap/federal/capital_gain_brackets.yaml`
  (0 / 15 / 20% rates, 28% §1202 non-excluded, 28% collectibles, 25%
  unrecaptured §1250; bracket breakpoints pending PDF copy).
- **Added:** `rules_cache_bootstrap/federal/misc_2026_indexed.yaml`
  (FEIE $132,900; EITC max 3+ kids $8,231; §179 $2,560,000 / $4,090,000;
  adoption credit $17,670; §24 CTC base $2,200; §132(f) $340; health
  FSA $3,400 / $680).
- **Changed:** `rules_cache_bootstrap/federal/estate_gift_gst.yaml`
  with confirmed basic exclusion $15,000,000, GST exemption
  $15,000,000, annual exclusion $19,000.
- **Changed:** `rules_cache_bootstrap/obbba_notices.yaml` scope filter
  narrowed to 13 return-line-impact OBBBA provisions per Decision 0008.
- **Added:** `rules_cache_bootstrap/_SIGNOFF_TEMPLATE.md` plus SIGNOFF
  companion files for every rewritten / newly-added YAML per Q0.1.
- **Changed:** `convergent/authority_layer/api.py` adds
  `DEFAULT_COMMENTARY_MODEL = "claude-opus-4-7"`,
  `DEFAULT_BULK_MODEL = "claude-sonnet-4-6"`,
  `DEFAULT_ROUTING_MODEL = "claude-haiku-4-5-20251001"` per Decision 0005.
- **Changed:** `rules_cache_bootstrap/review_checklist.md` reworked as a
  navigation index pointing to per-file SIGNOFF.md companions per
  Decision 0007.
- **Changed:** `OPEN_QUESTIONS.md` reduced to Q0.6 only (awaiting
  paste-back) plus a moved-to-decisions summary.
- **Gate status:** SIGNOFF companions in place for 12 YAML files out
  of 18. Master sign-off line in `review_checklist.md` still pending;
  remaining ◐/☐ rows require user follow-up before Phase 0 formally
  closes. Q0.6 paste-back closes Phase 1 entry gate.

### Phase 0 — Repo scaffold, rules cache bootstrap (initial commit)

- **Added:** repository structure per `docs/REPO_LAYOUT.md`
- **Added:** `pyproject.toml` with pinned dependencies (numpy 2.1.3, scipy
  1.14.1, pandas 2.2.3, pydantic 2.9.2, NiceGUI 2.7.0, plotly 5.24.1,
  SQLAlchemy 2.0.36, anthropic 0.39.0, pytesseract 0.3.13, pdfplumber
  0.11.4, camelot 0.11.0, python-docx 1.1.2, reportlab 4.2.5, cryptography
  43.0.3, argon2-cffi 23.1.0, pyinstaller 6.11.1 for dev)
- **Added:** `docs/decisions.md` index + initial decision files 0001–0004
- **Added:** `OPEN_QUESTIONS.md` with the Phase 0 blocking queue
- **Added:** `BACKLOG_V2.md` seed
- **Added:** SQLite schema scaffolding for engagement, rules cache,
  authority cache (persistence package not yet functional)
- **Added:** Statutory Mining subsystem scaffold with per-source stubs
- **Added:** Rules cache bootstrap skeleton with first-pass YAML files
  (values pending user sign-off per §18 acceptance gate)
- **Added:** Strategy Library `MANIFEST.yaml` scaffold (category
  directories only; strategy YAMLs land in Phase 1)
- **Added:** Authority Layer skeleton with `authority.query()` stub,
  Pitfall Library YAML seed, prompt template placeholders
- **Added:** Installer skeleton — PyInstaller spec, Inno Setup script,
  vendor directory for tesseract/ghostscript (binaries not yet bundled)
- **Gate status:** AWAITING USER SIGN-OFF on rules cache parameters (see
  `rules_cache_bootstrap/README.md`)

Phase 0 is **not complete**. Phase 1 cannot begin until the user signs off
every rule parameter in `rules_cache_bootstrap/` per §18.

## Format

We follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with
sections: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**,
**Security**, and the Convergent-specific **Gate status**.
