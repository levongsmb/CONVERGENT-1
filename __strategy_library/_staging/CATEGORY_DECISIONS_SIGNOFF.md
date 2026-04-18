# G2 — Category Decisions Sign-Off (Informational)

Firm: SMB CPA Group, PC
Build spec section: 3 (Phase 1b — Strategy Library Inventory) and Section 8 (Sign-Off Gates)

Per spec Section 8:

> G2 — Phase 1b category decisions —
> `__strategy_library/_staging/CATEGORY_DECISIONS_SIGNOFF.md`
> (all decisions already approved in this build spec; file is informational)

This gate is informational only. The forty-category list and all
category-level merges were approved in the master build spec itself
(Section 3.1 and 3.3). This file records the decisions for audit trail
continuity.

## Decisions carried in from the master build spec

### Final 40-category list (spec §3.1)

The list of 40 categories with `sequence_order` 1 through 40 is canonical.
`__strategy_library/subcategories/MANIFEST.yaml` mirrors §3.1 line by line.
Any future change to category composition requires a new numbered
`docs/decisions/` entry and an update to the MANIFEST.

### Category-level merges (recorded via `merged_from`)

The following legacy category names were merged into final categories
under this build. Each merged subcategory carries `merged_from: <legacy_name>`
for audit continuity. The legacy names are retired.

| Final category | merged_from legacy name | Subcategories carrying the merge flag |
|---|---|---|
| COMPLIANCE_AND_PROCEDURAL | IRS_CONTROVERSY_DEFENSE | CAP_EXAMS_APPEALS, CAP_ACCOUNTING_METHOD_DEFENSE, CAP_ERC_DEFENSE |
| COMPLIANCE_AND_PROCEDURAL | INFORMATION_REPORTING_WITHHOLDING | CAP_1099, CAP_BACKUP_WITHHOLDING, CAP_W8_W9, CAP_PAYROLL_REPORTING, CAP_K2_K3 |
| STATE_SALT | NEW_YORK_SPECIFIC | SSALT_NYC_RESIDENT, SSALT_NY_PTET, SSALT_NY_INVESTMENT_CAPITAL, SSALT_NY_CONVENIENCE_RULE, SSALT_NY_MANSION_TAX |
| STATE_SALT | NEW_JERSEY_HAWAII_DC_SPECIFIC | SSALT_NJ_BAIT, SSALT_NJ_RESIDENT_CREDIT, SSALT_NJ_TRUST_RESIDENCY, SSALT_HI_GET_INCOME, SSALT_DC_UBFT, SSALT_DC_SERVICE_SOURCING |
| COMPENSATION | EMPLOYMENT_PAYROLL_BENEFITS | COMP_FRINGE_127, COMP_FRINGE_132, COMP_FRINGE_105, COMP_FRINGE_125, COMP_DCAP, COMP_CHILDCARE_CREDIT_COORD |
| CREDITS | ENERGY_CREDITS_INCENTIVES | CR_ENERGY, CR_ENERGY_TRANSFERABILITY, CR_ENERGY_RECAPTURE, CR_ENERGY_DOMESTIC_CONTENT, CR_ENERGY_OBBBA_PHASEOUTS |
| SALE_TRANSACTION | EXIT_AND_SUCCESSION | SALE_MGMT_CARVE_OUTS, SALE_SUCCESSION_TRANSFERS |
| EXECUTIVE_COMP_AND_EQUITY | DEFERRED_COMPENSATION_409A | EXEC_409A_DEFERRED, EXEC_409A_DOCUMENT_FAILURE, EXEC_409A_OPERATIONAL_FAILURE |

No merges between current categories exist. All `merged_from` values point
to retired legacy names, verified by
`test_merged_from_references_are_legacy_only` in
`app/tests/strategy_library/test_library_parses.py`.

### Integrity invariants (tested)

- 40 categories with sequence orders 1-40, no gaps, no duplicates
- Every MANIFEST category has a corresponding YAML file; no orphan files
- Every category YAML declares `category_code` matching filename and
  `category_sequence_order` matching MANIFEST
- No duplicate subcategory codes globally across the 40 files
- Every `cross_references` entry resolves to a real category or
  category.subcategory
- Every `merged_from` refers to a legacy (retired) name, never to a current
  category code
- OBBBA-touched subcategories either carry a `statutory_cite` or leave it
  to be populated by Phase 2 cross-check
- Total subcategory count 616, within spec-referenced band of ~590

### OBBBA-touched subcategories (inline-cited at G3)

The following subcategories carry `obbba_touched: true` with a statutory
cite supplied inline in the YAML (rather than left to cross-check). These
are the highest-priority OBBBA provisions for the evaluator MVP in
Phase 3a.

- CAP_NOTICE_2026_3 (Notice 2026-3)
- SSALT_164_SALT_CAP, SSALT_OBBBA_CAP_MODELING (IRC §164(b)(6) as amended by OBBBA)
- QBI_199AI_MINIMUM, QBI_OBBBA_PHASEIN (IRC §199A(i), §199A(b)(3) as amended)
- COMP_OBBBA_TIP_EXCLUSION, COMP_OBBBA_OT_PREMIUM_EXCLUSION
- RET_OBBBA_SENIOR_DEDUCTION (IRC §151(f) as added by OBBBA)
- LL_461L (IRC §461(l) made permanent by OBBBA)
- AM_174A_DOMESTIC_RE, RND_174A_DOMESTIC (IRC §174A as added by OBBBA)
- RED_BONUS_DEPR (IRC §168(k) as restored by OBBBA)
- CHAR_OBBBA_05_FLOOR, CHAR_OBBBA_ABOVE_LINE, CHAR_OBBBA_37_CAP, CHAR_OBBBA_CORPORATE_FLOOR
- QSBS_HOLDING_PERIOD, QSBS_OBBBA_15M_CAP (IRC §1202 as amended by OBBBA §70431)
- EGG_OBBBA_15M_EXEMPTION (IRC §2010 as amended by OBBBA)
- FRA_1062_FARMLAND_INSTALL, FRA_NOTICE_2026_3, FRA_139L_LENDER_EXCLUSION
  (IRC §§ 1062, 139L as added by OBBBA; Notice 2026-3)

Other OBBBA-touched items with null `statutory_cite` are populated by
Phase 2 cross-check per spec Section 4.

## Sign-off

Informational only; no checkboxes. The master build spec (Section 3.1
and Section 3.3) is the decision record.

Prepared: 2026-04-18
Reviewer of record: Levon Galstian, CPA
