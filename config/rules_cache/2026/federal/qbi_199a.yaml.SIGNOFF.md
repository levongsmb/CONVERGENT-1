# SIGNOFF — `federal/qbi_199a.yaml` (ongoing remediation log)

This file tracks post-bootstrap reviews of `qbi_199a.yaml`. The Phase 0
bootstrap audit trail lives under `rules_cache_bootstrap/` and is
frozen as-of 2026-04-18.

## Review rows

| Date | Reviewer | Parameter(s) | Change | Authority | Sign-off |
|---|---|---|---|---|---|
| 2026-04-18 | Levon Galstian, CPA | `phasein_width_mfj`, `phasein_width_single_hoh_mfs` | 100000 → 150000 (MFJ); 50000 → 75000 (SINGLE/HOH/MFS). Notes updated to reflect OBBBA §70431 widening and post-2026 inflation indexing. `verification_status: bootstrapped → verified_by_cpa`. | IRC §199A(b)(3)(B)(ii) as amended by OBBBA §70431 (P.L. 119-21) | Signed |

## Remediation context

G6 Audit Remediation Task 1. Prior values were pre-OBBBA widths that
silently misclassified MFJ taxpayers between threshold+$100K and
threshold+$150K as `ABOVE_WINDOW` when they should have been
`IN_PHASEIN`. The evaluator at
`app/evaluators/QBI_199A/QBI_OBBBA_PHASEIN.py` already cites OBBBA
§70431 and has correct fallback defaults; the YAML misalignment
prevented those fallbacks from firing.

Cross-checked against Grant Thornton, RSM, and KerberRose published
guidance on OBBBA §70431. All three confirm the $150K MFJ / $75K
SINGLE-and-others widened range effective for tax years beginning
after 12/31/2025.
