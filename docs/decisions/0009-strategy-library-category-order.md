# 0009 — Strategy Library category order

- **Status:** OPEN (user deferred 2026-04-18 pending paste-back of the
  20-category list from OPEN_QUESTIONS.md)
- **Opened:** 2026-04-18
- **Phase gate:** Phase 1 entry

## Context

§18 Phase 1 builds the Strategy Library one category at a time. The
category sequence governs how engagement-valuable strategies land first.
User answered Q0.6 conditionally: will supply a reordered sequence once
the 20 categories are pasted back into chat. The default proposal from
OPEN_QUESTIONS.md Q0.6 is the fall-back if no re-order is returned.

## Default ordering criteria supplied by the user

1. April 2026 filing-season urgency.
2. Client-base applicability frequency.
3. Parameter volatility (OBBBA-touched sections first — Notices continue
   to drop).
4. Cross-category dependency (brackets and standard deduction before
   anything that references AGI or taxable-income thresholds).

## Default proposed order (Q0.6 in OPEN_QUESTIONS.md, pending user override)

1. COMPENSATION
2. QBI_199A
3. RETIREMENT
4. ENTITY_SELECTION
5. STATE_SALT (incl. CA PTET)
6. REAL_ESTATE_DEPRECIATION
7. QSBS_1202
8. TRUSTS_INCOME_SHIFTING
9. TRUSTS_WEALTH_TRANSFER
10. ESTATE_GIFT_GST
11. CHARITABLE
12. INSTALLMENT_DEFERRAL
13. CAPITAL_GAINS_LOSSES
14. LOSS_LIMIT_NAVIGATION
15. ACCOUNTING_METHODS
16. CREDITS
17. SALE_TRANSACTION
18. INTERNATIONAL
19. MISCELLANEOUS
20. COMPLIANCE_AND_PROCEDURAL

## Answer

(awaiting user paste-back / re-order or explicit "accept default")

## Implementation notes

- `strategy_library/MANIFEST.yaml` `categories` block is already
  ordered by `sequence_order` keys; Phase 1 sub-phases follow that order
  unless the user overrides.
- A re-order requires updating `sequence_order` values in MANIFEST.yaml
  and nothing else; strategy IDs remain stable.