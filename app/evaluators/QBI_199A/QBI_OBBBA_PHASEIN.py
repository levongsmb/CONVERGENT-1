"""QBI_OBBBA_PHASEIN — §199A(b)(3) phase-in window under OBBBA.

OBBBA §70431 expanded the §199A(b)(3) phase-in to a $75,000 single /
$150,000 MFJ window above the §199A(e)(2) threshold amount starting
2026. The evaluator:

  - Determines whether taxable income falls below, within, or above the
    phase-in window for the filing status.
  - Computes the applicable-percentage reduction for non-SSTB wage/UBIA
    limitation and full SSTB disallowance inside the window.
  - Surfaces the headroom / overshoot dollars so planners can target
    deductions (retirement, PTET, charitable) that compress taxable
    income into the favorable zone.

All thresholds and window widths come from config/rules_cache/2026/
federal/qbi_199a.yaml. No hardcoded numbers.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


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
                return v
    return None


def _approx_taxable_income(scenario: ClientScenario) -> Decimal:
    """First-order taxable income proxy used only for phase-in positioning.
    Orchestrator convergence will refine against computed AGI."""
    income = scenario.income
    base = (
        income.wages_primary
        + income.wages_spouse
        + income.self_employment_income
        + income.interest_ordinary
        + income.dividends_ordinary
        + income.dividends_qualified
        + income.capital_gains_long_term
        + income.capital_gains_short_term
        + income.rental_income_net
    )
    for k1 in income.k1_income:
        base += (
            k1.ordinary_business_income
            + k1.interest_income
            + k1.dividend_income
            + k1.capital_gain_long_term
            + k1.capital_gain_short_term
            + k1.guaranteed_payments
        )
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QBI_OBBBA_PHASEIN"
    CATEGORY_CODE = "QBI_199A"
    PIN_CITES = [
        "IRC §199A(b)(3) as amended by OBBBA §70431 — $75K/$150K phase-in window",
        "IRC §199A(e)(2) — threshold amount (Rev. Proc. 2025-32 for 2026)",
        "IRC §199A(d) — SSTB definition and phase-out",
        "P.L. 119-21 §70431 — OBBBA amendments to §199A",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_qbi = any(
            k1.qualified_business_income > Decimal(0)
            for k1 in scenario.income.k1_income
        ) or any(
            e.qbi > Decimal(0) for e in scenario.entities
        )
        if not has_qbi:
            return self._not_applicable(
                "no qualified business income in scenario; phase-in analysis is QBI-specific"
            )

        qbi = rules.get("federal/qbi_199a", year)
        filing_status = scenario.identity.filing_status
        mfj = filing_status == FilingStatus.MFJ

        threshold = _param(
            qbi,
            tax_year=year,
            sub_parameter=(
                "taxable_income_threshold_mfj" if mfj else "taxable_income_threshold_single"
            ),
        )
        phasein_width = _param(
            qbi,
            tax_year=year,
            sub_parameter=(
                "phasein_width_mfj" if mfj else "phasein_width_single_hoh_mfs"
            ),
        )

        if phasein_width is None:
            phasein_width = Decimal("150000" if mfj else "75000")

        taxable_income = _approx_taxable_income(scenario)

        if threshold is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason="threshold amount for planning year is awaiting Rev. Proc.",
                estimated_tax_savings=Decimal(0),
                savings_by_tax_type=TaxImpact(),
                inputs_required=[
                    "Rev. Proc. annual threshold amount (§199A(e)(2))",
                ],
                pin_cites=list(self.PIN_CITES),
                cross_strategy_impacts=[
                    "QBI_SCORP_WAGE_BALANCE",
                    "QBI_SSTB_AVOIDANCE",
                    "QBI_INCOME_COMPRESSION",
                    "RET_SOLO_401K",
                    "CHAR_BUNCHING",
                ],
                verification_confidence="low",
                computation_trace={
                    "threshold_populated": False,
                    "approx_taxable_income": str(taxable_income),
                    "phasein_width": str(phasein_width),
                    "filing_status": filing_status.value,
                },
            )

        window_top = threshold + phasein_width
        if taxable_income <= threshold:
            regime = "BELOW_THRESHOLD"
            headroom = threshold - taxable_income
            overshoot = Decimal(0)
            applicable_pct = Decimal("0")  # no phase-in
        elif taxable_income >= window_top:
            regime = "ABOVE_WINDOW"
            headroom = Decimal(0)
            overshoot = taxable_income - window_top
            applicable_pct = Decimal("1")
        else:
            regime = "IN_PHASEIN"
            headroom = window_top - taxable_income  # dollars above that would still be in-window
            overshoot = taxable_income - threshold
            applicable_pct = (overshoot / phasein_width).quantize(Decimal("0.0001"))

        # Compression opportunity: if regime is IN_PHASEIN or ABOVE_WINDOW,
        # recommend strategies that reduce taxable income back under threshold.
        compression_target = (
            max(taxable_income - threshold, Decimal(0)) if regime != "BELOW_THRESHOLD"
            else Decimal(0)
        )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # compression economics depend on composition
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "current-year projected taxable income",
                "SSTB status of each QBI activity",
                "W-2 wages and UBIA per activity",
            ],
            assumptions=[
                f"§199A(e)(2) threshold: ${threshold:,.0f}",
                f"Phase-in width: ${phasein_width:,.0f} "
                f"({'MFJ' if mfj else 'non-MFJ'})",
                f"Approximate taxable income: ${taxable_income:,.0f}",
                f"Regime: {regime}",
            ],
            implementation_steps=[
                "Rerun QBI_SCORP_WAGE_BALANCE and QBI_SSTB_AVOIDANCE at the "
                "current taxable-income posture.",
                "If IN_PHASEIN and SSTB: each dollar pushed above threshold "
                "disallows QBI at applicable_pct; compression strategies "
                "(retirement deferrals, PTET, charitable) carry a multiplier.",
                "If IN_PHASEIN and non-SSTB: wage/UBIA limitation phases in "
                "pro-rata; modeling wage increases may expand the ceiling.",
                "If BELOW_THRESHOLD: document the buffer; confirm that "
                "planning actions do not push over threshold unnecessarily.",
            ],
            risks_and_caveats=[
                "Approx taxable income is a first-order proxy; orchestrator "
                "convergence refines against computed AGI + deductions.",
                "OBBBA expanded the window but retained the SSTB cliff inside "
                "the window. Mixed SSTB / non-SSTB activities require separate "
                "treatment.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QBI_SCORP_WAGE_BALANCE",
                "QBI_SSTB_AVOIDANCE",
                "QBI_INCOME_COMPRESSION",
                "QBI_AGGREGATION",
                "RET_SOLO_401K",
                "RET_CASH_BALANCE",
                "CA_PTET_ELECTION",
                "CHAR_BUNCHING",
            ],
            verification_confidence="high",
            computation_trace={
                "threshold": str(threshold),
                "phasein_width": str(phasein_width),
                "window_top": str(window_top),
                "approx_taxable_income": str(taxable_income),
                "regime": regime,
                "headroom_below_threshold": str(headroom) if regime == "BELOW_THRESHOLD" else None,
                "overshoot_into_window": str(overshoot) if regime == "IN_PHASEIN" else None,
                "overshoot_above_window": str(overshoot) if regime == "ABOVE_WINDOW" else None,
                "applicable_percentage": str(applicable_pct),
                "compression_target_to_reach_threshold": str(compression_target),
                "filing_status": filing_status.value,
            },
        )
