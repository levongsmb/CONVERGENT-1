# G7 — COMPLIANCE_AND_PROCEDURAL Evaluators Complete

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec sections: 5.6 (Phase 3b) and 8 (Sign-Off Gates)

Per spec Section 5.6:

> After Phase 3a sign-off, build remaining ~540 evaluators in category
> order following MANIFEST sequence_order. Ship one category at a time
> with per-category sign-off before moving to the next.

Phase 3b opens with **COMPLIANCE_AND_PROCEDURAL** (MANIFEST sequence
order 1). All 27 subcategories now have evaluators and tests.

## Deliverables

| # | Component | Count |
|---|---|---:|
| 1 | Evaluator modules under `app/evaluators/COMPLIANCE_AND_PROCEDURAL/` | 27 |
| 2 | Test modules under `app/tests/evaluators/COMPLIANCE_AND_PROCEDURAL/` | 27 |
| 3 | Total test cases | 138 |

## Subcategory coverage

All 27 subcategories from the `COMPLIANCE_AND_PROCEDURAL.yaml` manifest
category:

| # | Code | Tests | Introduced in |
|---|------|------:|---------------|
| 1 | CAP_EST_TAX_SAFE_HARBORS | 7 | MVP batch 1 |
| 2 | CAP_PENALTY_ABATEMENT | 5 | Phase 3b |
| 3 | CAP_FIRST_TIME_ABATE | 5 | Phase 3b |
| 4 | CAP_REASONABLE_CAUSE | 5 | Phase 3b |
| 5 | CAP_PROTECTIVE_ELECTIONS | 5 | Phase 3b |
| 6 | CAP_SUPERSEDING_VS_AMENDED | 5 | Phase 3b |
| 7 | CAP_STATUTE_MGMT | 5 | Phase 3b |
| 8 | CAP_3115_METHOD_CHANGE | 5 | Phase 3b |
| 9 | CAP_8275_DISCLOSURE | 5 | Phase 3b |
| 10 | CAP_ELECTION_CALENDAR | 5 | Phase 3b |
| 11 | CAP_RECORD_RECONSTRUCTION | 5 | Phase 3b |
| 12 | CAP_7508A_DISASTER | 5 | Phase 3b |
| 13 | CAP_IDENTITY_POA | 5 | Phase 3b |
| 14 | CAP_BBA_AUDIT_REGIME | 5 | Phase 3b |
| 15 | CAP_PUSH_OUT_ELECTION | 5 | Phase 3b |
| 16 | CAP_PR_CONTROLS | 5 | Phase 3b |
| 17 | CAP_453D_ELECTION_OUT | 5 | Phase 3b |
| 18 | CAP_EXAMS_APPEALS | 5 | Phase 3b |
| 19 | CAP_ACCOUNTING_METHOD_DEFENSE | 5 | Phase 3b |
| 20 | CAP_ERC_DEFENSE | 5 | Phase 3b |
| 21 | CAP_1099 | 5 | Phase 3b |
| 22 | CAP_BACKUP_WITHHOLDING | 5 | Phase 3b |
| 23 | CAP_W8_W9 | 5 | Phase 3b |
| 24 | CAP_PAYROLL_REPORTING | 5 | Phase 3b |
| 25 | CAP_K2_K3 | 5 | Phase 3b |
| 26 | CAP_FORM_8308 | 5 | Phase 3b |
| 27 | CAP_NOTICE_2026_3 | 5 | Phase 3b |

## Key authorities covered

- **IRC §6501 / §6511** — SOL management (CAP_STATUTE_MGMT)
- **IRC §6651 / §6654 / §6662 / §6664** — penalty framework
- **IRC §6221-§6241** — BBA partnership audit regime
  (CAP_BBA_AUDIT_REGIME, CAP_PUSH_OUT_ELECTION, CAP_PR_CONTROLS)
- **IRC §446(b) / §446(e) / §481(a)** — method changes
  (CAP_3115_METHOD_CHANGE, CAP_ACCOUNTING_METHOD_DEFENSE)
- **IRC §453(d)** — installment election-out (CAP_453D_ELECTION_OUT)
- **IRC §6041 / §6050K / §6050W / §6041A** — information reporting
  (CAP_1099, CAP_FORM_8308)
- **IRC §3406 / §1441-§1474** — withholding (CAP_BACKUP_WITHHOLDING,
  CAP_W8_W9)
- **IRC §6672** — Trust Fund Recovery Penalty (CAP_PAYROLL_REPORTING)
- **IRC §7508A** — disaster postponements (CAP_7508A_DISASTER)
- **IRC §7121 / §7602 / §6330** — exams, closing agreements, CDP
  (CAP_EXAMS_APPEALS)
- **IRC §1062 + Notice 2026-3** — OBBBA farmland installment relief
  (CAP_NOTICE_2026_3)
- **Boyle v. United States, 469 U.S. 241 (1985)** — reasonable-cause
  reliance limitation (CAP_REASONABLE_CAUSE)
- **Haggar Co. v. Helvering, 308 U.S. 389 (1940)** — superseding return
  doctrine (CAP_SUPERSEDING_VS_AMENDED)
- **Cohan v. Commissioner, 39 F.2d 540 (2d Cir. 1930)** — reasonable
  estimation (CAP_RECORD_RECONSTRUCTION)

## Cross-strategy coverage

Evaluators within this category reference:
- Compensation / SE-tax coordination (COMP_*)
- Method-change ecosystem (AM_*)
- §1062 farmland ecosystem (FRA_*)
- International reporting (IO_*, II_*)
- Installment sales (INST_*)
- Partnership hot-asset sales (PS_*, PTE_*, SALE_*)

All cross-references validated against the MANIFEST subcategory index.

## Architectural invariants

Every evaluator in this category follows the G5 pattern:

- Extends `BaseEvaluator`; exports class `Evaluator`.
- Declares `SUBCATEGORY_CODE` and `CATEGORY_CODE` as class attributes.
- Declares `PIN_CITES` as a list of primary-authority strings.
- Returns `StrategyResult` with `applicable`, `pin_cites`,
  `inputs_required`, `assumptions`, `implementation_steps`,
  `risks_and_caveats`, `cross_strategy_impacts`,
  `verification_confidence`.
- Zero hardcoded Claude model strings, indexed rates, form-revision
  dates, or statutory cites that would properly live in
  `config/rules_cache/` or `config/authorities/`.
- Appropriate applicability gating (`self._not_applicable(reason)` when
  the subcategory does not apply to the scenario).

## Test suite totals after this category

- `pytest app/tests/evaluators/COMPLIANCE_AND_PROCEDURAL/` →
  **138 passed in 1.36s**
- `pytest app/tests/` overall → **490 passed in 5.41s**
- Registry auto-discovery: **76 evaluators** registered (50 MVP + 26 new)

## G7 sign-off checklist

- [ ] All 27 subcategories in COMPLIANCE_AND_PROCEDURAL.yaml have
      evaluator modules
- [ ] All 27 have test modules with at least 5 tests each
- [ ] Pin cites verified to primary authority (Code, Regs, Rev. Procs,
      IRM, case law)
- [ ] Cross-strategy impacts reference valid subcategory codes per the
      MANIFEST
- [ ] Architectural invariants hold (no hardcoded rates / cites /
      model strings; proper gating; complete StrategyResult)
- [ ] Authorization to proceed to the next category in MANIFEST
      sequence order (STATE_SALT, sequence_order 2)

Signed: __________________________________
Date: __________________________________
