# 0008 — OBBBA Notice narrow bootstrap scope

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 0 rules cache bootstrap

## Context

Q0.2 asked whether to bootstrap every IRS Notice citing P.L. 119-21 or
narrow to specific sections with return-line compute impact.

## Answer

**2026-04-18:** Narrow. Bootstrap Notices only for these thirteen
provisions:

1. IRC §199A (including SSTB parameters)
2. IRC §461(l) excess business loss
3. IRC §1202 QSBS
4. IRC §164(b)(6) SALT cap
5. IRC §168(k) bonus depreciation (permanent restoration)
6. IRC §174 domestic R&E restoration
7. IRC §151(f) senior deduction
8. Qualified tip income exclusion
9. Overtime premium exclusion
10. IRC §24 CTC amendments
11. IRC §68 itemized deduction tax-benefit limitation for 37% bracket
12. IRC §55 AMT phaseout changes
13. IRC §2010 estate basic exclusion

Exclude: Notices addressing only transition relief, procedural penalty
waivers, or employer withholding mechanics that do not touch a return
line.

## Implementation notes

- `rules_cache_bootstrap/obbba_notices.yaml` `scope_filter` block
  enumerates the thirteen provisions above; Statutory Mining OBBBA
  pollers (in `convergent/authority_layer/statutory_mining/sources/irs.py`
  when wired in Phase 7) honor this filter.
- Notices outside the filter are cached in the general authority cache
  if retrieved during broader polls, but do not trigger rules-cache
  diff alerts or OBBBA-scoped commentary.
- If a future engagement implicates an OBBBA provision outside the
  thirteen, the user can expand scope by editing this decision and the
  `scope_filter` block.