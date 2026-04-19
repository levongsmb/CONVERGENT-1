# G8 — STATE_SALT Evaluators Complete

> **Governance note (added 2026-04-18):** This SIGNOFF was
> originally labeled G7 in error. G7 is the
> COMPLIANCE_AND_PROCEDURAL gate. STATE_SALT is the second Phase 3b
> category and therefore G8. The evaluator work itself was
> committed in 8f9f518 before G7 was signed, violating per-category
> sign-off ordering. Retroactive reconciliation landed in the G8
> CHANGELOG entry.

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec sections: 5.6 (Phase 3b) and 8 (Sign-Off Gates)

Per spec Section 5.6:

> After each category in Phase 3b, halt for per-category sign-off
> before moving to the next in MANIFEST sequence order.

Phase 3b category 2 — **STATE_SALT** (MANIFEST sequence order 2). All
25 subcategories now have evaluators and tests.

## Deliverables

| # | Component | Count |
|---|---|---:|
| 1 | Evaluator modules under `app/evaluators/STATE_SALT/` | 25 |
| 2 | Test modules under `app/tests/evaluators/STATE_SALT/` | 25 |
| 3 | Total test cases | 126 |

## Subcategory coverage

All 25 subcategories from the `STATE_SALT.yaml` manifest category:

| # | Code | Tests | Introduced in |
|---|------|------:|---------------|
| 1 | SSALT_PTET_MODELING | 5 | Phase 3b |
| 2 | SSALT_RESIDENT_CREDIT | 5 | Phase 3b |
| 3 | SSALT_164_SALT_CAP | 5 | Phase 3b |
| 4 | SSALT_OBBBA_CAP_MODELING | 6 | MVP batch 3 |
| 5 | SSALT_PROPERTY_TAX_TIMING | 5 | Phase 3b |
| 6 | SSALT_STATE_ESTIMATES | 5 | Phase 3b |
| 7 | SSALT_COMPOSITE_VS_WITHHOLD | 5 | Phase 3b |
| 8 | SSALT_NONRESIDENT_WH | 5 | Phase 3b |
| 9 | SSALT_NOL_CREDIT_CARRYFWD | 5 | Phase 3b |
| 10 | SSALT_CONFORMITY_DECOUPLING | 5 | Phase 3b |
| 11 | SSALT_LOCAL_TAX_OVERLAYS | 5 | Phase 3b |
| 12 | SSALT_SALES_USE_EXPOSURE | 5 | Phase 3b |
| 13 | SSALT_TRANSFER_TAX | 5 | Phase 3b |
| 14 | SSALT_AUDIT_VDA | 5 | Phase 3b |
| 15 | SSALT_NYC_RESIDENT | 5 | Phase 3b |
| 16 | SSALT_NY_PTET | 5 | Phase 3b |
| 17 | SSALT_NY_INVESTMENT_CAPITAL | 5 | Phase 3b |
| 18 | SSALT_NY_CONVENIENCE_RULE | 5 | Phase 3b |
| 19 | SSALT_NY_MANSION_TAX | 5 | Phase 3b |
| 20 | SSALT_NJ_BAIT | 5 | Phase 3b |
| 21 | SSALT_NJ_RESIDENT_CREDIT | 5 | Phase 3b |
| 22 | SSALT_NJ_TRUST_RESIDENCY | 5 | Phase 3b |
| 23 | SSALT_HI_GET_INCOME | 5 | Phase 3b |
| 24 | SSALT_DC_UBFT | 5 | Phase 3b |
| 25 | SSALT_DC_SERVICE_SOURCING | 5 | Phase 3b |

## Key authorities covered

- **IRC §164(a) / §164(b)(6) as amended by OBBBA** — SALT cap regime
  (SSALT_164_SALT_CAP, SSALT_OBBBA_CAP_MODELING)
- **IRS Notice 2020-75** — PTET federal deductibility backbone
  (SSALT_PTET_MODELING, SSALT_NY_PTET, SSALT_NJ_BAIT)
- **CA R&TC §17024.5 / §17276 / §18662 / §19136 / §19191 /
  §11911** — CA conformity, NOL, withholding, estimates, VDA,
  documentary transfer tax
- **CA SB 132 (Ch. 17, Stats. 2025)** — CA PTET 2026-2030 regime
- **CA SB 167** — CA NOL / credit suspension 2024-2026
- **NY Tax Law §§860-866 + §867** — NY PTET and NYC PTET
  (SSALT_NY_PTET)
- **NY Tax Law §208.5** — NY investment-capital classification
  (SSALT_NY_INVESTMENT_CAPITAL)
- **NY Tax Law §1402 / §1402-a + NYC Admin Code §11-2101** — mansion
  tax (SSALT_NY_MANSION_TAX, SSALT_TRANSFER_TAX)
- **N.J.S.A. 54A:12-1 to 54A:12-10** — NJ BAIT (SSALT_NJ_BAIT)
- **HRS §237-13** — Hawaii GET (SSALT_HI_GET_INCOME)
- **D.C. Code §47-1808.01 et seq. / §47-1810.02** — DC UBFT and
  market-based sourcing (SSALT_DC_UBFT, SSALT_DC_SERVICE_SOURCING)
- **South Dakota v. Wayfair, 585 U.S. 162 (2018)** — economic nexus
  (SSALT_SALES_USE_EXPOSURE)
- **Wynne v. Maryland Comptroller, 575 U.S. 542 (2015)** — dormant
  Commerce Clause (SSALT_RESIDENT_CREDIT)
- **Matter of Gaied, 22 N.Y.3d 592 (2014)** — NY statutory residency
  (SSALT_NYC_RESIDENT)
- **Zelinsky / Huckaby** — NY convenience of employer rule
  (SSALT_NY_CONVENIENCE_RULE)
- **Kassner v. Director / Residuary Trust A v. Director** — NJ trust
  residency due-process limits (SSALT_NJ_TRUST_RESIDENCY)
- **Tannenbaum v. Director** — NJ resident credit framework
  (SSALT_NJ_RESIDENT_CREDIT)

## Cross-strategy coverage

Evaluators within this category reference:

- OBBBA SALT cap modeling (SSALT_OBBBA_CAP_MODELING)
- PTET ecosystem (CA_PTET_ELECTION, NY, NJ, MA, VA, CO)
- Conformity / decoupling on §168(k), §199A, §1202
- Transfer tax and estate / gift valuation (EST_*)
- Charitable bunching (CHAR_*)
- Compliance-and-procedural statute management (CAP_STATUTE_MGMT,
  CAP_PENALTY_ABATEMENT, CAP_EST_TAX_SAFE_HARBORS)
- Sales / M&A structuring (SALE_M_AND_A_STRUCTURING)

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
- Appropriate applicability gating (`self._not_applicable(reason)`
  when the subcategory does not apply to the scenario).

## Test suite totals after this category

- `pytest app/tests/evaluators/STATE_SALT/` → **126 passed in 1.27s**
- `pytest app/tests/` overall → **610 passed in 5.29s**
- Registry auto-discovery: **100 evaluators** registered
  (50 MVP + 26 COMPLIANCE_AND_PROCEDURAL + 24 STATE_SALT new)

## G8 sign-off checklist

- [x] All 25 subcategories in STATE_SALT.yaml have evaluator modules
- [x] All 25 have test modules with at least 5 tests each
- [x] Pin cites verified to primary authority (Code, Regs, Rev. Procs,
      TSB-Ms, FTB publications, case law)
- [x] Cross-strategy impacts reference valid subcategory codes per
      the MANIFEST
- [x] Architectural invariants hold (no hardcoded rates / cites /
      model strings; proper gating; complete StrategyResult)
- [x] Authorization to proceed to the next category in MANIFEST
      sequence order (CALIFORNIA_SPECIFIC, sequence_order 3)

Signed: Levon Galstian, CPA
Date: 2026-04-18
