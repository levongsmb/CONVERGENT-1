# 0004 — CA PTET current rule confirmation

- **Status:** ANSWERED with corrections
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 0 — rules cache review

## Context

§11 of the prompt is explicit about the current CA PTET rule. Quoting verbatim:

> **Current FTB rule controlling 2026 and beyond — bake into all PTET
> logic, do not regress to pre-2026 treatment:** for taxable years beginning
> on or after January 1, 2026 and before January 1, 2031, a missed or short
> June 15 prepayment does not invalidate the election. The qualifying
> entity may still make a valid PTET election for the year; however, the
> qualified taxpayer's PTET credit is reduced by 12.5% of the pro rata
> share of the unpaid amount that was due on June 15. The PTET credit is
> **nonrefundable** at the qualified-taxpayer level, and any unused
> portion **carries forward five taxable years**.

This is the controlling rule for every engagement Convergent will handle.
It must appear in:

- The rules cache (`rules_cache_bootstrap/california/ptet.yaml`)
- The CA tax computation module (`convergent/engine/tax/california.py`)
- Every CA PTET strategy in the Strategy Library
- The Pitfall Library ("PTET timing pitfalls" entry in §12A.10)
- The memo generator's CA PTET narrative

## What the user must confirm

1. The parameters as stated in §11 are current as of 2026-04-18. Specifically:
   - Effective window: TY beginning 2026-01-01 through 2030-12-31 (i.e.,
     2026, 2027, 2028, 2029, 2030 — this covers a "before 2031" cutoff)
   - Credit reduction: 12.5% of pro rata unpaid amount
   - Credit treatment: nonrefundable, 5-year carryforward
   - Election still valid even if June 15 prepayment missed or short
2. The PTET election deadline remains March 15 (same as the return due
   date for calendar-year pass-throughs) or has that changed under the
   current rule?
3. Is there an FTB Notice, Legal Ruling, or published regulation number the
   user wants cited as the authority of record for the above, or does
   Form 3804 Instructions + FTB PTET FAQ continue to be the canonical cite?

## Recommendation

Claude Code will pre-populate the rules cache with the parameters exactly
as stated in §11 and pin the authority to "RTC §§ 19900 et seq.; FTB Form
3804 (2026) Instructions; FTB PTET FAQ as of snapshot date". The user's
confirmation on the three items above closes this decision.

## Answer

**2026-04-18:** Confirmed with several corrections. Summary:

1. **Tax rate 9.3% — CONFIRMED.**
2. **Credit-reduction mechanic:** 12.5% of the *shortfall amount* (the
   unpaid portion of the June 15 minimum payment), measured as of the
   return filing date — **not** 12.5% of the "pro rata share" phrasing
   from the prompt. Example: required $100,000, paid $60,000 →
   shortfall $40,000 → credit reduction $5,000.
3. **Nonrefundable with 5-year carryforward — CONFIRMED.**
4. **Effective window:** TY beginning 2026-01-01 through
   2030-12-31 — CONFIRMED.
5. **Deadlines — REPLACE single field with two fields:**
   - `election_and_balance_due_date` — Form 3804 filed with timely-filed
     original return of the electing entity; calendar-year PTEs
     March 15; fiscal-year filers, original due date of Form 565 / 568 /
     100S; balance of PTE elective tax due with the return.
   - `election_minimum_prepayment_date` — June 15 of the taxable year;
     amount = greater of 50% of prior year PTET or $1,000; the 12.5%
     haircut attaches to the June 15 shortfall measured at filing, not
     to a missed March 15.
6. **Authority of record — CORRECTED:**
   - Primary: **SB 132 (Ch. 17, Stats. 2025, signed 2025-06-27).** SB 132
     added new RTC sections parallel to §§19900–19906 to govern the
     2026–2030 regime. Do NOT cite RTC §§19900 et seq. as primary
     authority for 2026+ (that framework applies to 2021–2025 only).
   - Secondary: FTB Form 3804 Instructions; FTB PTET FAQ (both
     updating).

## Implementation notes

- `rules_cache_bootstrap/california/ptet.yaml` rewritten to match this
  answer verbatim.
- Pitfall entry `ca_ptet_june15_short_payment_credit_reduction` updated
  in `authority_layer/pitfalls.yaml` to reflect the shortfall-based
  mechanic and SB 132 primary authority.
