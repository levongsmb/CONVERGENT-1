# SIGNOFF — `california/ptet.yaml`

**Reviewer:** (awaiting CPA initials)
**Review date:** 2026-04-18 (answer date; initials pending)
**Target YAML:** `ptet.yaml`
**Decision reference:** `docs/decisions/0004-ptet-ca-current-rule-confirmation.md`

## Signed-off parameters (per Decision 0004 answer 2026-04-18)

All parameters below were explicitly confirmed or explicitly corrected
in the user's Q0.3 answer.

- `regime` = `SB132_2026_2030` — **signed_off**
- `tax_rate` = 9.3% — **signed_off**
- `credit_treatment` = `NONREFUNDABLE_5YR_CARRYFORWARD` — **signed_off**
- `election_and_balance_due_date` = `ORIGINAL_DUE_DATE_OF_ENTITY_RETURN`
  (calendar-year March 15; fiscal-year original due date of 565/568/100S)
  — **corrected** (replaces single-field election_deadline)
- `election_minimum_prepayment_date` = June 15 — **corrected**
  (new field added)
- `election_minimum_prepayment_amount_rule` = greater of 50% prior-year
  PTET or $1,000 — **corrected** (new field added)
- `election_minimum_prepayment_floor` = $1,000 — **corrected** (new)
- `election_minimum_prepayment_pct_of_prior_year` = 50% — **corrected** (new)
- `june15_shortfall_invalidates_election` = false — **signed_off**
- `june15_shortfall_credit_reduction_basis` = `SHORTFALL_AMOUNT`
  — **corrected** (clarifies "not pro rata")
- `june15_shortfall_credit_reduction_pct` = 12.5% — **signed_off**
- `june15_shortfall_credit_reduction_measurement_date` = return filing date
  — **corrected** (new field added)
- `regime_effective_window_start` = 2026-01-01 — **signed_off**
- `regime_effective_window_end` = 2030-12-31 — **signed_off**

## needs_review parameters

- `qualified_entity_types` — **needs_review**: carried from AB 150
  framework; confirm SB 132 did not modify.
- `qualified_taxpayer_exclusions` — **needs_review**: same.

## Authority correction

- **Primary:** SB 132 (Ch. 17, Stats. 2025, signed 2025-06-27).
- **Secondary:** FTB Form 3804 Instructions; FTB PTET FAQ (updating).
- **Do NOT cite RTC §§19900 et seq.** for 2026+ — that framework
  applies to 2021–2025.

## Pitfall Library coordination

`authority_layer/pitfalls.yaml` entry updated:
- Old ID: `ca_ptet_june15_short_payment_credit_reduction`
- New ID: `ca_ptet_june15_shortfall_credit_reduction`
- Narrative now reflects SHORTFALL-based mechanic (not pro rata) and
  SB 132 primary authority.

## Overall sign-off

```
Reviewed and approved: (awaiting CPA countersignature) — <initials>
```
