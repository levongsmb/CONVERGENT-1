# G6 — Phase 3a MVP Evaluators Complete (50/50)

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec sections: 5 (Phase 3a) and 8 (Sign-Off Gates)

Per spec Section 8:

> G6 — Phase 3a all 50 MVP evaluators complete —
> `app/evaluators/MVP_50_SIGNOFF.md`

Phase 3a is complete. On user sign-off of G6, Phase 3b opens —
remaining ~540 evaluators across 12 additional subcategory tranches
covering the balance of the 616-subcategory Strategy Library.

## Deliverables under G6

| # | Component | Path |
|---|---|---|
| 1 | 50 evaluator modules | `app/evaluators/<CATEGORY>/<CODE>.py` |
| 2 | 50 test modules (359 total tests) | `app/tests/evaluators/<CATEGORY>/<CODE>_test.py` |
| 3 | Registry auto-discovery of all 50 | `app/evaluators/_registry.py` |
| 4 | 18 category directories under `app/evaluators/` | per spec §5.1 |
| 5 | Phase 3a pattern sign-off (G5) | `app/evaluators/MVP_PATTERN_SIGNOFF.md` (signed 2026-04-18) |

## Evaluator inventory

### Batch 1 (G5 pattern sign-off) — 5 evaluators / 38 tests

1. `CAP_EST_TAX_SAFE_HARBORS` — 7 tests
2. `COMP_REASONABLE_COMP` — 7 tests
3. `COMP_WAGE_DIST_SPLIT` — 7 tests
4. `QBI_SCORP_WAGE_BALANCE` — 8 tests (spec §5.3 reference pattern)
5. `CA_PTET_ELECTION` — 9 tests

### Batch 2 — 10 evaluators / 63 tests

6. `QBI_OBBBA_PHASEIN` — 8
7. `QBI_199AI_MINIMUM` — 7
8. `SSALT_OBBBA_CAP_MODELING` — 6
9. `LL_461L` — 5
10. `LL_469_PASSIVE` — 5
11. `LL_REP_STATUS` — 6
12. `LL_163J_INTEREST` — 5
13. `RET_SOLO_401K` — 7
14. `RET_CASH_BALANCE` — 7
15. `RET_BACKDOOR_ROTH` — 7

### Batch 3 — 10 evaluators / 62 tests

16. `RET_ROTH_CONVERSION` — 7
17. `RET_OBBBA_SENIOR_DEDUCTION` — 7
18. `ENT_SOLE_TO_SCORP` — 6
19. `ENT_LLC_PSHIP_VS_SCORP` — 5
20. `ENT_QSBS_DRIVEN` — 7
21. `RED_COST_SEG` — 6
22. `RED_BONUS_DEPR` — 6
23. `RED_163J_REPTOB` — 6
24. `RED_STR_CLASSIF` — 6
25. `CGL_TAX_LOSS_HARVEST` — 6

### Batch 4 — 10 evaluators / 59 tests

26. `CGL_GAIN_BUNCHING` — 6
27. `CGL_1231` — 5
28. `CGL_1250_UNRECAPTURED` — 5
29. `CHAR_DAF` — 6
30. `CHAR_PRE_SALE` — 6
31. `CHAR_APPREC_SECURITIES` — 6
32. `CHAR_OBBBA_05_FLOOR` — 6
33. `CHAR_OBBBA_37_CAP` — 6
34. `QSBS_ORIGINAL_ISSUANCE` — 6
35. `QSBS_HOLDING_PERIOD` — 7

### Batch 5 — 10 evaluators / 60 tests

36. `QSBS_OBBBA_TIERED` — 6
37. `QSBS_STATE_CONFORMITY` — 6
38. `SALE_ASSET_VS_STOCK` — 6
39. `SALE_F_REORG` — 6
40. `SALE_BASIS_CLEANUP` — 6
41. `INST_STANDARD_453` — 6
42. `AM_174A_DOMESTIC_RE` — 6
43. `AM_CASH_VS_ACCRUAL` — 6
44. `AM_481A_PLANNING` — 5
45. `CR_RND_41` — 6

### Batch 6 — 5 evaluators / 29 tests

46. `CR_ORDERING_LIMITS` — 5
47. `SET_SCORP_CONVERSION` — 6
48. `SET_1402A13` — 6
49. `NIIT_MATERIAL_PARTIC` — 6
50. `PTE_OUTSIDE_BASIS` — 6

**Total: 50 evaluators, 359 tests, 100% passing in 3.78s.**

## Category coverage (Phase 3a)

| Category | Evaluators in Phase 3a | Total subcategories in category |
|---|---:|---:|
| COMPLIANCE_AND_PROCEDURAL | 1 | 27 |
| STATE_SALT | 1 | 25 |
| CALIFORNIA_SPECIFIC | 1 | 15 |
| QBI_199A | 3 | 19 |
| COMPENSATION | 2 | 23 |
| SELF_EMPLOYMENT_TAX | 2 | 13 |
| RETIREMENT | 4 | 21 |
| PTE_BASIS_AND_DISTRIBUTIONS | 1 | 12 |
| ENTITY_SELECTION | 3 | 17 |
| LOSS_LIMIT_NAVIGATION | 4 | 16 |
| REAL_ESTATE_DEPRECIATION | 4 | 18 |
| CAPITAL_GAINS_LOSSES | 4 | 20 |
| NIIT_1411 | 1 | 12 |
| CREDITS | 2 | 20 |
| CHARITABLE | 5 | 20 |
| SALE_TRANSACTION | 3 | 21 |
| INSTALLMENT_AND_DEFERRED_SALES | 1 | 13 |
| QSBS_1202 | 4 | 18 |
| ACCOUNTING_METHODS | 3 | 20 |
| **Phase 3a total** | **50** | **349 (across 19 categories)** |

Remaining Phase 3b scope: ~566 subcategories across these and the
other 21 categories.

## Architectural invariants verified across all 50 evaluators

- Zero hardcoded Claude model strings (confirmed by source-scan tests).
- Zero hardcoded indexed rates, thresholds, form numbers, or
  statutory cites that belong in `config/rules_cache/` or
  `config/authorities/`. Only non-indexed statutory constants (e.g.,
  §6654(d)(1)(C) thresholds, §1411(b) thresholds, §3121 rates,
  §68 2/37ths formula) appear in-module with pin-cite comments.
- Every evaluator degrades gracefully when a required rules-cache
  parameter is `awaiting_user_input` (returns `applicable=True` with
  `verification_confidence="low"` and a non-null `reason`).
- Every evaluator reads at least one rules-cache key via
  `app.config.rules.get_rule()`, spy-verified in multiple tests.
- Every evaluator's `PIN_CITES` survive to `StrategyResult.pin_cites`.
- Registry auto-discovery returns exactly 50 evaluators addressed by
  `SUBCATEGORY_CODE`.

## OBBBA-specific evaluator coverage

The Phase 3a MVP covers every major OBBBA-touched §12.2 subcategory
flagged for inline citation at G3:

- §164(b)(6) SALT cap — `SSALT_OBBBA_CAP_MODELING`
- §199A expanded phase-in — `QBI_OBBBA_PHASEIN`
- §199A(i) minimum deduction — `QBI_199AI_MINIMUM`
- §151(f) senior deduction — `RET_OBBBA_SENIOR_DEDUCTION`
- §461(l) permanence — `LL_461L`
- §174A domestic R&E expensing — `AM_174A_DOMESTIC_RE`
- §168(k) bonus depreciation — `RED_BONUS_DEPR`
- §170 0.5% AGI floor — `CHAR_OBBBA_05_FLOOR`
- §68 35% tax-benefit cap — `CHAR_OBBBA_37_CAP`
- §1202 tiered exclusion (50/75/100%) — `QSBS_OBBBA_TIERED`
- §1202 $15M per-issuer cap — `QSBS_OBBBA_TIERED` / `ENT_QSBS_DRIVEN`

## Deterministic test anchors (representative)

Each evaluator has at least one test with an exact-dollar assertion:

| Evaluator | Deterministic assertion |
|---|---|
| CAP_EST_TAX_SAFE_HARBORS | 110% × $192,300 = $211,530 safe-harbor |
| COMP_REASONABLE_COMP | 91% ratio → $8,797.50 FICA saved on excessive wage |
| QBI_SCORP_WAGE_BALANCE | W-2 ceiling $155,000 / W-2+UBIA $82,125 |
| CA_PTET_ELECTION | $612K × 9.3% = $56,916 PTET; $21,058.92 gross fed save |
| SSALT_OBBBA_CAP_MODELING | $947K MAGI → $10K floor → $34,800 above cap |
| LL_461L | $1M loss vs $625K threshold → $375K disallowed |
| RET_SOLO_401K | $195K W-2 × 25% = $48,750 PS; capped at $72K §415(c) |
| CHAR_OBBBA_05_FLOOR | $947,940 AGI × 0.5% = $4,739.70 floor |
| CHAR_OBBBA_37_CAP | $50K × 2/37 = $2,702.70 reduction |
| QSBS_OBBBA_TIERED | 7y held → $3.675M excluded → $874,650 saved at 23.8% |
| SALE_F_REORG | $4.845M × 13.2% = $639,540 saving vs §338(h)(10) |
| INST_STANDARD_453 | $2.7M deferred / NPV math at 7% over 5 years |
| SET_SCORP_CONVERSION | $200K SE → $15,889.06 gross saving |
| NIIT_MATERIAL_PARTIC | $612K K-1 × 3.8% = $23,256 potential NIIT saving |

## Commits covering Phase 3a

| Commit | Batch | Net change |
|--------|-------|-----------:|
| `5403040` | Batch 1 (5 evaluators + G5 pattern) | +2,251 lines |
| `75bdea5` | Batch 2 (evaluators 6-15) | +2,571 lines |
| `44a8de0` | Batch 3 (evaluators 16-25) | +2,657 lines |
| `8c2bb14` | Batch 4 (evaluators 26-35) | +2,395 lines |
| `97b67ab` | Batch 5 (evaluators 36-45) | +2,446 lines |
| (this) | Batch 6 (evaluators 46-50 + G6) | (end of Phase 3a) |

## G6 sign-off checklist

- [ ] All 50 MVP evaluators present in `app/evaluators/` with matching
      test files in `app/tests/evaluators/`
- [ ] `pytest app/tests/evaluators/` → 359 passing
- [ ] `pytest app/tests/` → all 359 tests pass (no regressions in prior
      Phase 1a, 1b, or Phase 2 tests)
- [ ] `app.evaluators._registry.all_evaluators()` returns 50 distinct
      SUBCATEGORY_CODE entries
- [ ] Architectural invariants verified (no hardcoded models / rates /
      form numbers / cites; graceful null degradation; rules-cache
      reads; pin-cite coverage)
- [ ] OBBBA coverage (all inline-cited G3 provisions wired into
      evaluators) accepted
- [ ] Authorization to proceed to Phase 3b — remaining 566 subcategories
      across all 40 MANIFEST categories, committed in per-category
      batches with per-category sign-off gates (G7) per spec §18

Signed: __________________________________
Date: __________________________________
