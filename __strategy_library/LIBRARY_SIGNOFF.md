# G3 — Phase 1b Strategy Library Sign-Off

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec section: 3 (Phase 1b — Strategy Library Inventory) and Section 8 (Sign-Off Gates)

This gate certifies that the canonical strategy library inventory is in
place and that Phase 2 (cross-check protocol) may begin.

## Deliverables produced under G3

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Final 40-category manifest | `__strategy_library/subcategories/MANIFEST.yaml` |
| 2 | 40 category YAML files per spec §3.3 | `__strategy_library/subcategories/<CATEGORY_CODE>.yaml` |
| 3 | 40 per-category sign-off companions per spec §3.4 | `__strategy_library/subcategories/<CATEGORY_CODE>_SIGNOFF.md` |
| 4 | G2 informational decisions record | `__strategy_library/_staging/CATEGORY_DECISIONS_SIGNOFF.md` |
| 5 | Integrity test suite | `app/tests/strategy_library/test_library_parses.py` |

## Integrity metrics

- 40 categories, sequence orders 1-40, no gaps, no duplicates
- 616 subcategories total, none duplicated across categories
- 0 unresolved `cross_references`
- 0 `merged_from` values pointing at current category codes (all point
  to retired legacy names: IRS_CONTROVERSY_DEFENSE,
  INFORMATION_REPORTING_WITHHOLDING, NEW_YORK_SPECIFIC,
  NEW_JERSEY_HAWAII_DC_SPECIFIC, EMPLOYMENT_PAYROLL_BENEFITS,
  ENERGY_CREDITS_INCENTIVES, EXIT_AND_SUCCESSION,
  DEFERRED_COMPENSATION_409A)
- `python -m pytest app/tests/strategy_library/` -> 10 passed in 0.96s

## Distribution of subcategories by category (top 15)

| Count | Category |
|------:|----------|
| 27 | COMPLIANCE_AND_PROCEDURAL |
| 25 | STATE_SALT |
| 23 | COMPENSATION |
| 21 | RETIREMENT |
| 21 | SALE_TRANSACTION |
| 20 | ACCOUNTING_METHODS |
| 20 | CAPITAL_GAINS_LOSSES |
| 20 | CREDITS |
| 20 | CHARITABLE |
| 19 | QBI_199A |
| 18 | REAL_ESTATE_DEPRECIATION |
| 18 | OPPORTUNITY_ZONES |
| 18 | ESTATE_GIFT_GST |
| 17 | ENTITY_SELECTION |
| 17 | M_A_AND_REORGANIZATIONS |

(Remaining 25 categories range from 10 to 17 subcategories, plus
MISCELLANEOUS with 6.)

## OBBBA coverage (inline-cited at G3; remaining cited at G4)

Inline-cited OBBBA subcategories (ready for Phase 3a evaluator MVP):

- §164(b)(6) SALT cap: `SSALT_164_SALT_CAP`, `SSALT_OBBBA_CAP_MODELING`
- §199A: `QBI_199AI_MINIMUM`, `QBI_OBBBA_PHASEIN`
- §151(f) senior deduction: `RET_OBBBA_SENIOR_DEDUCTION`
- §461(l) permanence: `LL_461L`
- §174A domestic R&E expensing: `AM_174A_DOMESTIC_RE`, `RND_174A_DOMESTIC`
- §168(k) bonus depreciation: `RED_BONUS_DEPR`
- §170 / §68 OBBBA charitable changes: `CHAR_OBBBA_05_FLOOR`,
  `CHAR_OBBBA_ABOVE_LINE`, `CHAR_OBBBA_37_CAP`,
  `CHAR_OBBBA_CORPORATE_FLOOR`
- §1202 revised regime: `QSBS_HOLDING_PERIOD`, `QSBS_OBBBA_15M_CAP`
- §2010 $15M permanent exclusion: `EGG_OBBBA_15M_EXEMPTION`
- §1062 + Notice 2026-3 farmland installment: `FRA_1062_FARMLAND_INSTALL`,
  `FRA_NOTICE_2026_3`, `CAP_NOTICE_2026_3`
- §139L agricultural lender exclusion: `FRA_139L_LENDER_EXCLUSION`
- OBBBA tip and overtime exclusions: `COMP_OBBBA_TIP_EXCLUSION`,
  `COMP_OBBBA_OT_PREMIUM_EXCLUSION`

Additional OBBBA-touched subcategories carry `obbba_touched: true` with
`statutory_cite` left for Phase 2 cross-check population.

## Sign-off

- [x] MANIFEST.yaml matches spec §3.1 line by line
- [x] 40 category YAML files present, each parsing cleanly, each
      declaring the correct category_code and category_sequence_order
- [x] 40 per-category `_SIGNOFF.md` companions present and available for
      per-category review
- [x] G2 decisions record (`_staging/CATEGORY_DECISIONS_SIGNOFF.md`) reflects
      only informational decisions carried from the master build spec
- [x] Integrity test suite green (`pytest app/tests/strategy_library/`)
- [x] Spec §3.2 schema invariants hold: no duplicate subcategory codes,
      all cross_references resolve, all merged_from values point to
      retired legacy names

Signed: Levon Galstian, CPA
Date: 2026-04-18
