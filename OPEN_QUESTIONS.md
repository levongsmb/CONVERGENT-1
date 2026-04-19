# Open Questions

Questions the user must answer before a blocked phase can continue.
When a question is answered, it moves to `docs/decisions/`; it is
removed here.

## Phase 0 — deferred; not blocking current work

### Q0.6 — Strategy Library category sequence (deferred on 2026-04-18)

User deferred Q0.6 on 2026-04-18 pending paste-back of a category
ordering. Phase 3b has since proceeded using the **40-category default
MANIFEST order** in `__strategy_library/subcategories/MANIFEST.yaml`
(per Decision 0010, which supersedes the legacy 20-category
`strategy_library/MANIFEST.yaml`). Sequences signed to date:
sequence 1 COMPLIANCE_AND_PROCEDURAL at G7, sequence 2 STATE_SALT
backfilled at G8, sequence 3 CALIFORNIA_SPECIFIC is next. A reorder
remains possible for not-yet-started sequences; completed categories
would not be invalidated.

Accept or reorder: send either (a) an explicit "accept default order"
or (b) a re-ordered sequence over the 40-category `__strategy_library/`
MANIFEST.

Default ordering criteria supplied with the deferral:
1. April 2026 filing-season urgency
2. Client-base applicability frequency
3. Parameter volatility (OBBBA-touched sections first)
4. Cross-category dependency (brackets and standard deduction before
   anything referencing AGI or taxable-income thresholds)

The current default order (40 categories, from
`__strategy_library/subcategories/MANIFEST.yaml`):

1. COMPLIANCE_AND_PROCEDURAL (signed G7)
2. STATE_SALT (signed G8)
3. CALIFORNIA_SPECIFIC
4. QBI_199A
5. COMPENSATION
6. SELF_EMPLOYMENT_TAX
7. RETIREMENT
8. PTE_BASIS_AND_DISTRIBUTIONS
9. ENTITY_SELECTION
10. S_CORP_SPECIAL_ISSUES
11. PARTNERSHIP_STRUCTURING
12. C_CORP_SPECIAL_ISSUES
13. ACCOUNTING_METHODS
14. LOSS_LIMIT_NAVIGATION
15. REAL_ESTATE_DEPRECIATION
16. REAL_ESTATE_DISPOSITIONS_1031
17. CAPITAL_GAINS_LOSSES
18. NIIT_1411
19. DEBT_RECAPITALIZATION
20. CREDITS
21. RESEARCH_DEV_AND_IP
22. CHARITABLE
23. SALE_TRANSACTION
24. M_A_AND_REORGANIZATIONS
25. INSTALLMENT_AND_DEFERRED_SALES
26. EXECUTIVE_COMP_AND_EQUITY
27. QSBS_1202
28. OPPORTUNITY_ZONES
29. (sequences 29-40 per MANIFEST.yaml — RESIDENCY_DOMICILE,
    APPORTIONMENT_AND_SOURCING, INTERNATIONAL_INBOUND,
    INTERNATIONAL_OUTBOUND, ESTATE_GIFT_GST,
    RELATED_PARTY_AND_FAMILY_SHIFTING, INSURANCE_RISK_TRANSFER,
    FARM_RANCH_AG, FAMILY_OFFICE_INVESTMENT_STRUCTURES,
    MISCELLANEOUS — consult MANIFEST.yaml for the authoritative
    ordering.)

Note: the legacy `strategy_library/MANIFEST.yaml` (20 categories,
187 strategy IDs) is retained as an audit artifact only and is
superseded by the 40-category `__strategy_library/` MANIFEST above.
See `strategy_library/MANIFEST.yaml` header for deprecation banner
and `docs/decisions/0010-master-build-supersession.md` for the
governing decision.

**Blocks:** nothing currently. MANIFEST `sequence_order` keys already
reflect the default above and Phase 3b is consuming them in order; a
future reorder would update
`__strategy_library/subcategories/MANIFEST.yaml` and re-sequence only
the not-yet-started categories (3-40 as of this writing).

## Phase 0 — closed since last update

The following were answered on 2026-04-18 and have been moved to the
numbered decisions in `docs/decisions/`:

- Q0.1 → Decision 0007 (review method = SIGNOFF.md companions)
- Q0.2 → Decision 0008 (narrow OBBBA Notice scope — 13 provisions)
- Q0.3 → Decision 0004 (CA PTET with SB 132 corrections)
- Q0.4 → Decision 0006 (unsigned Phase 0 installer)
- Q0.5 → Decision 0005 (Claude 4.7 / 4.6 / 4.5 family)

## Sign-off companions still outstanding

The Phase 0 acceptance gate (§18) requires every row in
`rules_cache_bootstrap/review_checklist.md` to reach the ✓ state. The
user's 2026-04-18 answer delivered confirmed values for several critical
YAMLs; remaining ◐ and ☐ rows still require further user input to
formally close Phase 0. These rows do not block current Phase 3b
evaluator work but remain on the audit ledger.
