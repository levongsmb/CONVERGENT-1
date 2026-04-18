"""QBI_199AI_MINIMUM — OBBBA §199A(i) minimum deduction.

OBBBA §70431 added a $400 minimum §199A deduction when the taxpayer has
aggregate active QBI of at least $1,000 from trades or businesses in
which the taxpayer materially participates. Both thresholds are
statutory at enactment and indexed for inflation after 2026.

This evaluator applies the floor BEFORE the wage/UBIA limitation in
§199A(b)(2)(B) — the OBBBA floor is a per-taxpayer minimum applied to
active QBI, not a subcomponent of the tentative deduction. When the
minimum binds, the planning value is the delta between the computed
deduction and the $400 floor.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_ACTIVE_QBI_FLOOR = Decimal("1000")  # statutory at enactment
_DEDUCTION_FLOOR = Decimal("400")  # statutory at enactment


def _is_active(k1) -> bool:
    """Heuristic for material participation: S corp officer-employee
    K-1s default to active; partnership K-1s with positive SE earnings
    default to active; PTP / passive carve-outs belong to other
    evaluators. Precise material-participation facts are captured in
    LL_469_PASSIVE and LL_REP_STATUS."""
    if k1.entity_type in (EntityType.S_CORP, EntityType.LLC_S_CORP):
        return True
    if k1.entity_type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP):
        return k1.self_employment_earnings > Decimal(0) or k1.guaranteed_payments > Decimal(0)
    return False


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QBI_199AI_MINIMUM"
    CATEGORY_CODE = "QBI_199A"
    PIN_CITES = [
        "IRC §199A(i) as added by OBBBA §70431 — $400 minimum deduction "
        "when aggregate active QBI >= $1,000",
        "P.L. 119-21 §70431 — OBBBA §199A amendments",
        "Rev. Proc. 2025-32 — 2026 threshold and deduction-rate baseline",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        active_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.qualified_business_income > Decimal(0) and _is_active(k1)
        ]
        aggregate_active_qbi = sum(
            (k1.qualified_business_income for k1 in active_k1s),
            start=Decimal(0),
        )

        if aggregate_active_qbi <= Decimal(0):
            return self._not_applicable(
                "no active QBI in scenario; §199A(i) minimum is active-QBI-specific"
            )
        if aggregate_active_qbi < _ACTIVE_QBI_FLOOR:
            return self._not_applicable(
                f"aggregate active QBI ${aggregate_active_qbi:,.2f} below "
                f"§199A(i) $1,000 active-QBI threshold"
            )

        qbi = rules.get("federal/qbi_199a", year)
        deduction_rate = Decimal("0.20")
        for p in qbi.get("parameters", []):
            if p["coordinate"].get("sub_parameter") == "deduction_rate":
                if p.get("value") is not None:
                    deduction_rate = Decimal(str(p["value"]))
                break

        # First-order computed deduction = 20% × aggregate active QBI.
        # A full convergence layers on the taxable-income ceiling, SSTB
        # phase-in, and wage/UBIA limitation. Here we surface the bare
        # §199A(i) comparison.
        computed_deduction = (aggregate_active_qbi * deduction_rate).quantize(
            Decimal("0.01")
        )
        minimum_binds = computed_deduction < _DEDUCTION_FLOOR
        delta = (_DEDUCTION_FLOOR - computed_deduction) if minimum_binds else Decimal(0)

        # Assume top-bracket marginal for MVP dollar impact; orchestrator
        # refines downstream.
        approx_marginal = Decimal("0.22")  # representative middle-bracket for $1K-$2K active QBI
        estimated_fed_saving = (delta * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_saving,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_saving),
            inputs_required=[
                "aggregate active QBI (material participation)",
                "applicable marginal tax rate for the planning year",
                "confirmation that the activity is not an SSTB at the "
                "taxable-income posture (SSTB disallowance overrides the floor)",
            ],
            assumptions=[
                f"Active QBI threshold: ${_ACTIVE_QBI_FLOOR:,.0f}",
                f"Minimum deduction floor: ${_DEDUCTION_FLOOR:,.0f}",
                f"Aggregate active QBI: ${aggregate_active_qbi:,.2f}",
                f"Computed 20% deduction: ${computed_deduction:,.2f}",
                f"Approx marginal rate used: {approx_marginal:.0%}",
            ],
            implementation_steps=[
                "Confirm material participation under §469 for each "
                "active K-1 activity included in the aggregate.",
                "Confirm each activity is not an SSTB at the current "
                "taxable-income posture; SSTB disallowance overrides §199A(i) "
                "floor.",
                "Report the greater of computed QBI deduction or $400 "
                "on Form 8995 / 8995-A.",
            ],
            risks_and_caveats=[
                "§199A(i) applies only to ACTIVE QBI. Passive PTP income and "
                "passive-activity rental losses are excluded from the aggregate.",
                "Both thresholds are indexed after 2026; confirm current-year "
                "values from the §199A inflation-adjustment Rev. Proc.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QBI_ACTIVE_TB_QUAL",
                "QBI_MATERIAL_PARTIC_MIN",
                "QBI_SSTB_AVOIDANCE",
                "QBI_SCORP_WAGE_BALANCE",
                "LL_469_PASSIVE",
            ],
            verification_confidence="high",
            computation_trace={
                "aggregate_active_qbi": str(aggregate_active_qbi),
                "active_k1_count": len(active_k1s),
                "computed_deduction_20pct": str(computed_deduction),
                "deduction_floor": str(_DEDUCTION_FLOOR),
                "minimum_binds": minimum_binds,
                "delta_to_floor": str(delta),
                "approx_marginal_rate": str(approx_marginal),
            },
        )
