# Open Questions

Questions the user must answer before a blocked phase can continue.
When a question is answered, it moves to `docs/decisions/`; it is
removed here.

## Phase 0 — deferred; not blocking current work

### Q0.6 — Strategy Library category sequence (deferred on 2026-04-18)

User deferred Q0.6 on 2026-04-18 pending paste-back of the 20-category
list. Phase 3b has since proceeded using the default MANIFEST order
(`__strategy_library/subcategories/MANIFEST.yaml`) — sequence 1
COMPLIANCE_AND_PROCEDURAL signed at G7, sequence 2 STATE_SALT
backfilled at G8, sequence 3 CALIFORNIA_SPECIFIC next. A reorder
remains possible if priorities shift; completed categories would not
be invalidated.

Accept or reorder: send either (a) an explicit "accept default order"
or (b) a re-ordered sequence.

Default ordering criteria supplied with the deferral:
1. April 2026 filing-season urgency
2. Client-base applicability frequency
3. Parameter volatility (OBBBA-touched sections first)
4. Cross-category dependency (brackets and standard deduction before
   anything referencing AGI or taxable-income thresholds)

The 20 categories (current default order from `strategy_library/MANIFEST.yaml`):

1. COMPENSATION — §162 / §1366 / §119 / §132 / §105 / §106 / §125 (officer comp and fringe benefits)
2. QBI_199A — §199A qualified business income optimization
3. RETIREMENT — qualified and non-qualified retirement plan optimization
4. ENTITY_SELECTION — choice of entity and entity conversion
5. STATE_SALT — state tax and PTET optimization including CA
6. REAL_ESTATE_DEPRECIATION — depreciation and real-estate structural planning
7. QSBS_1202 — §1202 original issuance, gifting, and rollover
8. TRUSTS_INCOME_SHIFTING — non-grantor trust income shifting and related
9. TRUSTS_WEALTH_TRANSFER — wealth-transfer trust structures
10. ESTATE_GIFT_GST — estate, gift, and GST planning
11. CHARITABLE — charitable giving structures and timing
12. INSTALLMENT_DEFERRAL — §453 and deferral structures
13. CAPITAL_GAINS_LOSSES — capital gain / loss timing and character
14. LOSS_LIMIT_NAVIGATION — §461(l) / §163(j) / §465 / §469 planning
15. ACCOUNTING_METHODS — method elections and changes
16. CREDITS — federal business and incentive credits
17. SALE_TRANSACTION — liquidity-event planning
18. INTERNATIONAL — cross-border
19. MISCELLANEOUS — remaining high-impact strategies
20. COMPLIANCE_AND_PROCEDURAL — procedural and penalty-mitigation

**Blocks:** nothing currently. MANIFEST `sequence_order` keys already
reflect the default above and Phase 3b is consuming them in order; a
future reorder would update `__strategy_library/subcategories/MANIFEST.yaml`
and re-sequence only the not-yet-started categories (4-40 as of this
writing).

## Phase 0 — closed since last update

The following were answered on 2026-04-18 and have been moved to the
numbered decisions in `docs/decisions/`:

- Q0.1 → Decision 0007 (review method = SIGNOFF.md companions)
- Q0.2 → Decision 0008 (narrow OBBBA Notice scope — 13 provisions)
- Q0.3 → Decision 0004 (CA PTET with SB 132 corrections)
- Q0.4 → Decision 0006 (unsigned Phase 0 installer)
- Q0.5 → Decision 0005 (Claude 4.7 / 4.6 / 4.5 family)

## Sign-off companions still outstanding

The Phase 0 acceptance gate (§18) additionally requires every row in
`rules_cache_bootstrap/review_checklist.md` to reach the ✓ state. The
user's 2026-04-18 answer delivered confirmed values for several critical
YAMLs; remaining ◐ and ☐ rows require further user input before Phase 0
fully closes. Claude Code does **not** advance to Phase 1 until the
master sign-off line is added to the review checklist.
