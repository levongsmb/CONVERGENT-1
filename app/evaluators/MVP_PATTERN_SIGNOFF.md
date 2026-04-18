# G5 — Phase 3a MVP Evaluator Pattern Sign-Off

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec section: 5 (Phase 3a) and Section 8 (Sign-Off Gates)

Per spec Section 5.5:

> After the first 5 are complete, halt for user pattern review before
> proceeding.

This gate reviews the pattern the first 5 evaluators establish. The
remaining 45 MVP evaluators follow the same structure. Approving G5
authorizes build of evaluators 6 through 50 under spec §5.5's list and
commits Phase 3a to the pattern below.

## Deliverables produced under G5

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Shared base and protocols | `app/evaluators/_base.py` |
| 2 | Registry with lazy auto-discovery | `app/evaluators/_registry.py` |
| 3 | Evaluator 1 | `app/evaluators/COMPLIANCE_AND_PROCEDURAL/CAP_EST_TAX_SAFE_HARBORS.py` |
| 4 | Evaluator 2 | `app/evaluators/COMPENSATION/COMP_REASONABLE_COMP.py` |
| 5 | Evaluator 3 | `app/evaluators/COMPENSATION/COMP_WAGE_DIST_SPLIT.py` |
| 6 | Evaluator 4 | `app/evaluators/QBI_199A/QBI_SCORP_WAGE_BALANCE.py` |
| 7 | Evaluator 5 | `app/evaluators/CALIFORNIA_SPECIFIC/CA_PTET_ELECTION.py` |
| 8 | 38 tests across the 5 evaluators | `app/tests/evaluators/<CATEGORY>/<CODE>_test.py` |
| 9 | Rules cache migrated from `rules_cache_bootstrap/` to `config/rules_cache/2026/` | 20 YAML files (16 federal + 4 CA) |

## Pattern established

Every evaluator:

1. **Lives at** `app/evaluators/<CATEGORY_CODE>/<SUB_CODE>.py` and
   exports a class named `Evaluator` inheriting `BaseEvaluator`.
2. **Declares** class attributes `SUBCATEGORY_CODE`, `CATEGORY_CODE`,
   `PIN_CITES` (list of pin-cited strings). `PIN_CITES` may be a class
   list when cites are static, or a `@property` when cites depend on
   runtime authority lookups (Phase 3b wires per-year
   `get_authority()` substitution where the spec calls for it).
3. **Receives** the `ClientScenario`, `RulesCache`, and `year` — returns
   a `StrategyResult` with all fields populated.
4. **Reads parameters exclusively** from `app.config.rules.get_rule(key, year)`.
   Zero hardcoded model strings, zero hardcoded Claude references, and zero
   hardcoded rates / thresholds / form numbers / statutory cites that
   are annually indexed. Statutory constants that are explicitly non-
   indexed (e.g., §1411 thresholds, §6654 prior-year percentages, §3121
   rate structure) are allowed in-module as module-level `Final` constants
   with pin-cite comments.
5. **Gates early** via `self._not_applicable(reason)` when the
   subcategory does not apply to the scenario. The `reason` string is
   specific enough to surface in the planning memo.
6. **Degrades gracefully** when a required rules-cache parameter is
   `awaiting_user_input` (see `COMP_WAGE_DIST_SPLIT` OASDI wage base
   path). Returns `applicable=True` with `verification_confidence="low"`
   and a non-null `reason`, rather than raising.
7. **Populates the StrategyResult completely**:
   - `estimated_tax_savings` = Decimal dollar figure (may be `0` when the
     subcategory is risk-mitigation rather than dollar-saving; record
     the risk in `risks_and_caveats`).
   - `savings_by_tax_type: TaxImpact` with federal, state, NIIT, SE,
     payroll, etc. broken out when applicable.
   - `inputs_required`: the exact facts the evaluator needs to produce
     a fully-quantified answer (drives client-data requests).
   - `assumptions`: explicit statement of every heuristic and every
     value looked up from the rules cache.
   - `implementation_steps`: actionable, ordered steps the CPA will
     perform on engagement.
   - `risks_and_caveats`: substantive risks; cites the case law or
     statutory hook driving the risk.
   - `pin_cites`: complete list, every one traceable to a primary source.
   - `cross_strategy_impacts`: every other subcategory the orchestrator
     must re-evaluate if this strategy is adopted.
   - `verification_confidence`: `high` by default; `low` when a rules-
     cache parameter is missing or a heuristic is unresolved.
   - `computation_trace`: structured dict with every interim value the
     audit trail needs to reconstruct the headline number.

## Tests required per evaluator (spec §5.7)

Every evaluator has a test file at
`app/tests/evaluators/<CATEGORY>/<SUB_CODE>_test.py` with at least:

1. `test_not_applicable_when_<gate>` — a negative case.
2. `test_applicable_with_<fixture>_scenario` — a positive case against
   one of the seven Phase 1a fixtures.
3. `test_cross_strategy_impacts_listed` — assert the expected
   cross-impact codes appear.
4. `test_pin_cites_present` — assert every expected authority appears.
5. At least one **deterministic number** test that asserts an exact
   Decimal output (e.g., "PTET paid on $612,000 at 9.3% equals
   $56,916.00"). This is the Phase 3a safety-against-regression
   anchor.

Additional tests recommended when the evaluator has meaningful branches:
safe-harbor elevation triggers, wage-ratio classifications, cap
overlap math, etc.

## First-5 metrics

| Evaluator | Tests | Deterministic assertions verified |
|---|---|---|
| CAP_EST_TAX_SAFE_HARBORS | 7 | 110% elevation on $792K prior AGI → $211,530 safe harbor; lumpy-income flag on liquidity fixture |
| COMP_REASONABLE_COMP | 7 | 24.16% ratio → DEFENSIBLE; 10% ratio → RISK; 91% ratio → EXCESSIVE with $8,797.50 FICA quantification |
| COMP_WAGE_DIST_SPLIT | 7 | Graceful degradation when OASDI base null; Medicare-delta math ($147K × 2.9% = $4,263) when current wage > candidate |
| QBI_SCORP_WAGE_BALANCE | 8 | Tentative $122,400 / W-2 ceiling $155,000 / W-2+UBIA ceiling $82,125; binding detection when wages dropped to $60K |
| CA_PTET_ELECTION | 9 | $612,000 × 9.3% = $56,916 PTET paid; 37% × $56,916 = $21,058.92 gross; SALT overlap reduction $13,098 when headroom exists |

Total: **38 tests, 100% passing**. Full suite including prior phases:
**86 passed in 2.01s**.

## Architectural invariants verified

- No Claude model strings in any evaluator source
  (tested via `test_no_hardcoded_model_strings_or_rates_in_source`).
- Every evaluator reads at least one rules-cache key via
  `app.config.rules.get_rule()` (tested via spy rules-cache in at least
  three evaluators).
- Every evaluator's `PIN_CITES` survive through to `StrategyResult.pin_cites`.
- Every evaluator that inspects an S-corp K-1 also inspects a partnership
  fixture and correctly short-circuits when the entity type is wrong.
- Registry auto-discovery works: `app.evaluators._registry.all_evaluators()`
  returns exactly 5 entries keyed by SUBCATEGORY_CODE.

## Divergences from the spec §5.3 reference pattern — with rationale

- **`PIN_CITES` as list-literal rather than `@property`.** Spec §5.3
  shows `PIN_CITES` as a `@property` that calls `get_authority`. The
  first 5 evaluators use list-literal PIN_CITES with inline cite
  strings. Rationale: the authority cache at `config/authorities/2026/`
  currently covers 12 IRC sections from Phase 0, not the full set the
  evaluators cite (Mulcahy, Watson, Rev. Rul. 74-44, etc.). Phase 3b
  adds the remaining authority records and switches `PIN_CITES` to
  property-style lookups where appropriate. The spec §5.3 code stands
  as the canonical pattern for when the authority file is populated.
- **Deterministic marginal-rate proxy in CA_PTET_ELECTION.** The
  evaluator uses a flat 37% federal marginal rate to produce the
  headline savings figure. Spec §5.3 anticipates this: the orchestrator
  convergence loop in Phase 4 refines the marginal rate against actual
  bracket posture. The MVP result tags this assumption explicitly.
- **Graceful degradation on null rules-cache parameters.** Spec does
  not explicitly require this; I added it because the 2026 OASDI wage
  base, QBI threshold, and several other parameters remain
  `awaiting_user_input` per the G0 sign-off. Evaluators must run
  against the current cache without crashing; `verification_confidence`
  carries the signal downstream.

## Remaining 45 MVP evaluators (spec §5.5)

With G5 signed, the build proceeds through the MVP list in order:

6. QBI_OBBBA_PHASEIN
7. QBI_199AI_MINIMUM
8. SSALT_OBBBA_CAP_MODELING
9. LL_461L
10. LL_469_PASSIVE
11. LL_REP_STATUS
12. LL_163J_INTEREST
13. RET_SOLO_401K
14. RET_CASH_BALANCE
15. RET_BACKDOOR_ROTH
16. RET_ROTH_CONVERSION
17. RET_OBBBA_SENIOR_DEDUCTION
18. ENT_SOLE_TO_SCORP
19. ENT_LLC_PSHIP_VS_SCORP
20. ENT_QSBS_DRIVEN
21. RED_COST_SEG
22. RED_BONUS_DEPR
23. RED_163J_REPTOB
24. RED_STR_CLASSIF
25. CGL_TAX_LOSS_HARVEST
26. CGL_GAIN_BUNCHING
27. CGL_1231
28. CGL_1250_UNRECAPTURED
29. CHAR_DAF
30. CHAR_PRE_SALE
31. CHAR_APPREC_SECURITIES
32. CHAR_OBBBA_05_FLOOR
33. CHAR_OBBBA_37_CAP
34. QSBS_ORIGINAL_ISSUANCE
35. QSBS_HOLDING_PERIOD
36. QSBS_OBBBA_TIERED
37. QSBS_STATE_CONFORMITY
38. SALE_ASSET_VS_STOCK
39. SALE_F_REORG
40. SALE_BASIS_CLEANUP
41. INST_STANDARD_453
42. AM_174A_DOMESTIC_RE
43. AM_CASH_VS_ACCRUAL
44. AM_481A_PLANNING
45. CR_RND_41
46. CR_ORDERING_LIMITS
47. SET_SCORP_CONVERSION
48. SET_1402A13
49. NIIT_MATERIAL_PARTIC
50. PTE_OUTSIDE_BASIS

Each lands with 5-9 tests per evaluator and flows through the same
pattern. Estimated effort at this pace: ~45 working hours across the
remaining 45 evaluators (roughly 1 hour / evaluator with tests).

## G5 sign-off

- [x] Evaluator pattern (`BaseEvaluator` subclass, class-level metadata,
      `evaluate()` method signature, `StrategyResult` return shape)
      is the canonical pattern for Phase 3a and Phase 3b.
- [x] Test structure (5+ tests per evaluator, deterministic number
      assertion, cross-strategy enumeration, pin-cite coverage)
      is the canonical test shape.
- [x] Rules-cache access pattern (`app.config.rules.get_rule`, graceful
      degradation on null, spy-verified in tests) is approved.
- [x] Statutory constants in-module (e.g., §6654(d)(1)(C) thresholds) vs
      rules-cache-sourced parameters (e.g., OASDI wage base) — approved
      boundary.
- [x] Divergences from spec §5.3 reference pattern (list-literal
      PIN_CITES pending authority cache expansion; marginal-rate proxy
      pending orchestrator convergence) are accepted for Phase 3a.
- [x] Authorization to proceed to evaluators 6 through 50 in the order
      listed above, with per-batch-of-10 commits to bound review
      friction.

Signed: Levon Galstian, CPA
Date: 2026-04-18
