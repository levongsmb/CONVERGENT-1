# Open Questions

Questions the user must answer before a blocked phase can continue. Unlike
`docs/decisions.md`, which records *every* tax-judgment fork including the
resolved ones, this file is strictly the **current blocking queue**. When a
question is answered, it moves to `docs/decisions/`; it is removed here.

## Phase 0 — blocking Phase 0 acceptance

### Q0.1 — Rules cache bootstrap sign-off workflow

How would you like to review the bootstrapped rules cache?

- (a) In-person screen share — Claude Code walks you through each
  parameter category
- (b) Markdown-rendered per-category review files that you sign off in
  the file itself (`rules_cache_bootstrap/<category>.yaml` + a
  companion `<category>.SIGNOFF.md`)
- (c) A single master checklist at `rules_cache_bootstrap/review_checklist.md`
  that references the YAML values and you annotate in-place

**Blocks:** Phase 1 entry.

### Q0.2 — OBBBA interpretive Notices to bootstrap

Which IRS Notices in the OBBBA interpretive series do you want included in
the Day-1 cache? Claude Code proposes pulling every Notice citing Public Law
119-21 that has been published as of the snapshot date. If you want a
different scope (e.g., "only Notices on §461(l), §199A, §1202, and SALT cap"),
say so before Phase 0 bootstrap runs.

**Blocks:** Rules cache bootstrap run.

### Q0.3 — CA PTET parameters verbatim confirmation

Three sub-questions in `docs/decisions/0004-ptet-ca-current-rule-confirmation.md`.
Short-form: (i) confirm parameters exactly as in §11, (ii) confirm March 15
election deadline, (iii) confirm the authority cite of record.

**Blocks:** CA rules cache YAML and CA PTET strategies.

### Q0.4 — Windows signing certificate

§3.3 says "bundle a code-signing certificate if provided (future: user
supplies a signing cert; initial builds are unsigned and will trigger
Windows SmartScreen warning on first run — document this in README)."

Do you have a code-signing certificate ready for Phase 0, or should the
Phase 0 installer build ship unsigned with the SmartScreen warning
documented? If the cert arrives later, we switch during Phase 10.

**Blocks:** Installer stub build (unsigned build is fine to start, but we
need to know which path to wire the Inno Setup script against).

### Q0.5 — Claude model pinning for Authority Layer

§3.3 specifies "Claude Sonnet 4.5 default, Claude Opus 4.5 for
Authority-Layer commentary generation." As of today (2026-04-18), the
current model family is Claude 4.X — Opus 4.7, Sonnet 4.6, Haiku 4.5. Do
you want to:

- (a) Pin the specification exactly as written (Sonnet 4.5 / Opus 4.5)
- (b) Use the current Claude model family (Sonnet 4.6 default, Opus 4.7
  for commentary)
- (c) Make the models configurable in Settings, shipping with the current
  family as default

**Blocks:** Phase 7 entry; does not block Phase 0 acceptance but should be
answered early.

### Q0.6 — Strategy Library initial coverage priority order

§12.2 lists 20 categories; §18 requires ≥120 strategies in the MANIFEST.
The user is an S-corp specialist. Priority order for Phase 1 sub-phase
sequencing — confirm or re-order:

1. COMPENSATION (reasonable comp, accountable plans, Augusta, HRA/ICHRA, S-corp >2% health, hire-your-child)
2. QBI_199A
3. RETIREMENT
4. ENTITY_SELECTION
5. STATE_SALT (incl. CA PTET)
6. REAL_ESTATE_DEPRECIATION (cost seg, §469, §1031)
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

**Blocks:** Phase 1 ordering.
