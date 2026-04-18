# Rules Cache Review Checklist — Phase 0 Master

Navigation index for Decision 0007's per-file SIGNOFF.md companion
system. This file does **not** duplicate sign-off records — it points
to them.

Legend:
- ✓ = SIGNOFF.md companion exists, every parameter is `signed_off` or `corrected`
- ◐ = SIGNOFF.md companion exists, at least one `needs_review` parameter remains
- ☐ = SIGNOFF.md companion not yet created (review not started)

## Federal

- ◐ `federal/individual_brackets.yaml` — Single + MFJ signed; MFS/HoH/trusts awaiting PDF copy
- ✓ `federal/standard_deduction.yaml` — all 2026 values signed
- ✓ `federal/amt_individual.yaml` — all 2026 values signed (50% phaseout rate confirmed)
- ✓ `federal/obbba_senior_deduction_151f.yaml` — $6,000 / 75k-150k / 6% / 2025–2028 signed
- ✓ `federal/niit.yaml` — statutory parameters bootstrapped
- ✓ `federal/additional_medicare.yaml` — statutory parameters bootstrapped
- ◐ `federal/fica_wage_bases.yaml` — rates signed, 2026 OASDI wage base pending SSA Fact Sheet
- ◐ `federal/futa.yaml` — rates signed, 2026 credit-reduction-state list pending DOL
- ◐ `federal/retirement_limits.yaml` — all values signed via Notice 2025-67 **except** §415(b) DB benefit limit (populate from Notice 2025-67 directly)
- ✓ `federal/estate_gift_gst.yaml` — $15M / $19,000 signed; §2523(i) non-citizen-spouse pending PDF copy
- ✓ `federal/salt_cap_obbba.yaml` — full OBBBA schedule signed
- ◐ `federal/qbi_199a.yaml` — mechanics signed; 2026 indexed threshold amount pending Rev. Proc.
- ◐ `federal/section_461l.yaml` — sunset through 2030 signed; 2026 indexed threshold pending Rev. Proc.
- ✓ `federal/section_1202.yaml` — full OBBBA and pre-OBBBA regimes signed
- ✓ `federal/capital_gain_brackets.yaml` — rates signed; 0/15/20% breakpoints pending PDF copy
- ✓ `federal/misc_2026_indexed.yaml` — FEIE, EITC, §179, adoption, §132(f), §125(i) signed; 2026 §24 CTC indexed amount pending PDF copy

## California

- ✓ `california/ptet.yaml` — SB 132 regime fully signed per Decision 0004; entity-type / qualified-taxpayer carryover pending verification
- ☐ `california/mental_health_services_tax.yaml` — values bootstrapped, not yet sign-off reviewed
- ☐ `california/franchise_tax.yaml` — values bootstrapped, not yet sign-off reviewed
- ☐ `california/conformity_adjustments.yaml` — flags bootstrapped, not yet sign-off reviewed

## Top-level

- ✓ `obbba_notices.yaml` — narrow scope (13 provisions) signed per Decision 0008
- ☐ `listed_transactions.yaml` — seed designations awaiting currency verification
- ☐ `reportable_transactions.yaml` — seed designations awaiting currency verification

## Master sign-off

Phase 0 acceptance requires every row above at ✓. Remaining open
items are ◐ and ☐. When every row is ✓, add:

```
Signed off: <YYYY-MM-DD> — <initials>
```
