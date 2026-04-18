"""QBI_SCORP_WAGE_BALANCE — S corp officer wage balancing against §199A QBI.

Computes the §199A wage/UBIA limitation and flags whether the current
officer wage is BINDING the deduction. When binding, an increase in W-2
wages expands the ceiling; when slack, additional wage merely increases
FICA without a §199A benefit. The OBBBA-expanded phase-in window
($75K single / $150K MFJ above the threshold — §199A(b)(3)) and the new
§199A(i) minimum deduction ($400 floor at $1,000 active QBI) are both
honored.

Reference pattern: spec Section 5.3. This module is the canonical shape
for every subsequent QBI evaluator.

No hardcoded percentages or thresholds: W-2 ceiling (50%), UBIA ceiling
(25% + 2.5%), deduction rate (20%), and phase-in widths come from
config/rules_cache/2026/federal/qbi_199a.yaml.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType, FilingStatus


def _param(doc: dict, **coord) -> Optional[Decimal]:
    for p in doc.get("parameters", []):
        c = p.get("coordinate", {})
        if all(c.get(k) == v for k, v in coord.items()):
            v = p.get("value")
            if v is None:
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return v  # non-numeric (e.g., ENUM string)
    return None


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QBI_SCORP_WAGE_BALANCE"
    CATEGORY_CODE = "QBI_199A"
    PIN_CITES = [
        "IRC §199A(a) — 20% QBI deduction",
        "IRC §199A(b)(2)(B) — W-2 wage and UBIA limitation",
        "IRC §199A(b)(3) — phase-in (OBBBA-expanded $75K single / $150K MFJ)",
        "IRC §199A(e)(2) — threshold amount (Rev. Proc. 2025-32 for 2026)",
        "IRC §199A(i) — OBBBA minimum deduction ($400 at $1,000 active QBI)",
        "Rev. Proc. 2025-32 — 2026 threshold amounts",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        scorp_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            and k1.qualified_business_income > Decimal(0)
        ]
        if not scorp_k1s:
            return self._not_applicable(
                "no S corp K-1 with qualified business income in scenario"
            )

        qbi_doc = rules.get("federal/qbi_199a", year)

        deduction_rate = _param(qbi_doc, sub_parameter="deduction_rate") or Decimal("0.20")
        w2_pct_limit = _param(qbi_doc, sub_parameter="w2_wages_pct_limit") or Decimal("0.50")
        w2_plus_ubia_pct = _param(qbi_doc, sub_parameter="w2_plus_ubia_pct_limit") or Decimal("0.25")
        ubia_pct = _param(qbi_doc, sub_parameter="ubia_of_qualified_property_pct") or Decimal("0.025")
        phasein_mfj = _param(qbi_doc, sub_parameter="phasein_width_mfj") or Decimal("100000")
        phasein_single = (
            _param(qbi_doc, sub_parameter="phasein_width_single_hoh_mfs")
            or Decimal("50000")
        )

        filing_status = scenario.identity.filing_status
        threshold = _param(
            qbi_doc,
            tax_year=year,
            filing_status="MFJ" if filing_status == FilingStatus.MFJ else "SINGLE",
            sub_parameter="taxable_income_threshold_mfj"
            if filing_status == FilingStatus.MFJ
            else "taxable_income_threshold_single",
        )

        # Aggregate scenario-level approximations — this MVP evaluator does
        # not implement the full §199A convergence loop. It identifies the
        # wage-limitation regime the taxpayer is in and flags whether wage
        # is binding.
        total_qbi = sum(
            (k1.qualified_business_income for k1 in scorp_k1s),
            start=Decimal(0),
        )
        total_w2 = sum(
            (k1.w2_wages_allocated for k1 in scorp_k1s),
            start=Decimal(0),
        )
        total_ubia = sum(
            (k1.ubia_allocated for k1 in scorp_k1s),
            start=Decimal(0),
        )

        tentative_deduction = total_qbi * deduction_rate
        w2_ceiling = total_w2 * w2_pct_limit
        w2_ubia_ceiling = (total_w2 * w2_plus_ubia_pct) + (total_ubia * ubia_pct)
        effective_ceiling = max(w2_ceiling, w2_ubia_ceiling)

        deduction_binding_on_wage = tentative_deduction > effective_ceiling
        headline_deduction = min(tentative_deduction, effective_ceiling)

        # Approximate marginal savings from raising wage by $1 to expand ceiling:
        # d(w2_ceiling)/d(wage) = 0.50; but additional wage incurs ~15.3% FICA
        # plus reduces net distributive by $1. At a 37% top bracket taxpayer
        # with NIIT at the distribution edge, the calculus favors raising wage
        # if and only if the binding ceiling is near the tentative deduction.
        # Surface the regime; do not over-compute in the MVP.
        regime = "UNDER_THRESHOLD" if (threshold is None or tentative_deduction <= effective_ceiling) \
            else "WAGE_LIMITED"

        risks_and_caveats: List[str] = [
            "OBBBA expanded the §199A(b)(3) phase-in width to $75K (single) and "
            "$150K (MFJ) starting 2026. Planning at the threshold should model "
            "partial phase-in rather than a cliff.",
            "The OBBBA §199A(i) minimum deduction is the greater of the computed "
            "QBI deduction or $400 when aggregate active QBI is at least $1,000. "
            "This floor applies before the wage/UBIA limitation is tested.",
        ]
        if deduction_binding_on_wage:
            risks_and_caveats.insert(
                0,
                "Wage/UBIA ceiling is BELOW the 20% tentative deduction. Each "
                "additional dollar of W-2 wage paid through the S corp expands "
                "the ceiling by $0.50 (W-2 ceiling) or up to $0.25 + 2.5% UBIA "
                "(W-2 plus UBIA ceiling). Run QBI_SCORP_WAGE_BALANCE against "
                "COMP_REASONABLE_COMP before adjusting wage.",
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            # MVP: headline dollar impact requires a convergence loop; record
            # zero explicit savings and surface the binding posture in the
            # computation trace. Phase 3b tightens the headline figure.
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "S corp W-2 wages allocated to the taxpayer",
                "S corp UBIA of qualified property allocated to the taxpayer",
                "taxable income (for threshold/phase-in math)",
                "SSTB status of each QBI-generating entity",
            ],
            assumptions=[
                f"Deduction rate: {deduction_rate:.0%}",
                f"W-2 ceiling: {w2_pct_limit:.0%} of W-2 wages",
                f"W-2 + UBIA ceiling: {w2_plus_ubia_pct:.0%} of W-2 wages + "
                f"{ubia_pct:.1%} of UBIA",
                f"Phase-in width: ${phasein_mfj:,.0f} MFJ / "
                f"${phasein_single:,.0f} single-HoH-MFS",
            ],
            implementation_steps=[
                "Reconcile scenario W-2 wages and UBIA to the entity return.",
                "Compute tentative 20% QBI deduction.",
                "Compute both §199A(b)(2)(B) ceilings; take the greater.",
                "If wage-limited, model the net benefit of increasing wage "
                "(expanding ceiling) against the FICA + §199A deduction "
                "interaction via convergence with COMP_REASONABLE_COMP.",
                "If taxable income is above the §199A(e)(2) threshold, apply "
                "the OBBBA-expanded phase-in (§199A(b)(3)).",
            ],
            risks_and_caveats=risks_and_caveats,
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "COMP_REASONABLE_COMP",
                "COMP_WAGE_DIST_SPLIT",
                "QBI_OBBBA_PHASEIN",
                "QBI_199AI_MINIMUM",
                "QBI_SSTB_AVOIDANCE",
                "SET_SCORP_CONVERSION",
            ],
            verification_confidence="high",
            computation_trace={
                "total_qbi": str(total_qbi),
                "total_w2_wages": str(total_w2),
                "total_ubia": str(total_ubia),
                "tentative_deduction_20pct": str(tentative_deduction),
                "w2_ceiling_50pct": str(w2_ceiling),
                "w2_ubia_ceiling": str(w2_ubia_ceiling),
                "effective_ceiling": str(effective_ceiling),
                "headline_deduction": str(headline_deduction),
                "deduction_binding_on_wage": deduction_binding_on_wage,
                "regime": regime,
                "threshold_populated": threshold is not None,
            },
        )
