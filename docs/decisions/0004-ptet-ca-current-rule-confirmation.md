# 0004 — CA PTET current rule confirmation

- **Status:** OPEN
- **Opened:** 2026-04-18
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

(awaiting user)
