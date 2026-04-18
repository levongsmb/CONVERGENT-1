"""CHAR_OBBBA_05_FLOOR — 0.5% AGI floor on itemized charitable deductions.

OBBBA amended §170 effective 2026 to disallow the first 0.5% of AGI
in individual itemized charitable contributions. The disallowed amount
is NOT lost — it increases the 5-year carryforward balance subject to
the same floor in future years.

The evaluator quantifies the floor impact for the current year and
surfaces the multi-year carryforward math.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


def _approx_agi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    base = (
        income.wages_primary + income.wages_spouse + income.self_employment_income
        + income.interest_ordinary + income.dividends_ordinary + income.dividends_qualified
        + income.capital_gains_long_term + income.capital_gains_short_term
        + income.rental_income_net + income.pension_ira_distributions
    )
    for k1 in income.k1_income:
        base += k1.ordinary_business_income + k1.guaranteed_payments
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CHAR_OBBBA_05_FLOOR"
    CATEGORY_CODE = "CHARITABLE"
    PIN_CITES = [
        "IRC §170(a) as amended by OBBBA — 0.5% AGI floor for individual itemizers",
        "IRC §170(d) — 5-year carryforward for disallowed amount",
        "P.L. 119-21 — OBBBA §170 amendments",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        if year < 2026:
            return self._not_applicable(
                f"§170 0.5% AGI floor effective 2026; scenario year is {year}"
            )

        total_charitable = (
            scenario.deductions.charitable_cash_public
            + scenario.deductions.charitable_cash_pf_non_operating
            + scenario.deductions.charitable_cash_daf
            + scenario.deductions.charitable_appreciated_public
            + scenario.deductions.charitable_appreciated_private
        )
        if total_charitable <= Decimal(0):
            return self._not_applicable(
                "no itemized charitable contributions in scenario"
            )

        agi = _approx_agi(scenario)
        floor_amount = (agi * Decimal("0.005")).quantize(Decimal("0.01"))
        disallowed_current_year = min(total_charitable, floor_amount).quantize(Decimal("0.01"))
        allowed_current_year = (total_charitable - disallowed_current_year).quantize(Decimal("0.01"))

        approx_marginal = Decimal("0.32")
        current_tax_drag = (disallowed_current_year * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # floor disallowance is a cost, not a saving
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "projected AGI for each year of the multi-year giving plan",
                "existing charitable carryforward from prior years",
                "ability to bunch via DAF (CHAR_DAF) to reduce years-with-floor",
            ],
            assumptions=[
                f"Approx AGI: ${agi:,.0f}",
                f"0.5% AGI floor: ${floor_amount:,.2f}",
                f"Total itemized charitable: ${total_charitable:,.2f}",
                f"Disallowed in current year (added to carryforward): ${disallowed_current_year:,.2f}",
                f"Allowed current-year deduction: ${allowed_current_year:,.2f}",
                f"Approx marginal rate: {approx_marginal:.0%}",
                f"Current-year tax drag from floor: ${current_tax_drag:,.2f}",
            ],
            implementation_steps=[
                "File Schedule A with the floor applied before the AGI-percentage limits.",
                "Track the disallowed amount on Schedule A carryforward worksheet; "
                "the 5-year §170(d) carryforward applies.",
                "Bunching strategy (CHAR_DAF) concentrates giving into fewer "
                "years, reducing the number of years where the floor takes a bite.",
                "Multi-year plan: if planning two years of giving, bunching $20K "
                "into one year costs 0.5% AGI once; splitting $10K + $10K costs "
                "0.5% AGI twice.",
            ],
            risks_and_caveats=[
                "Disallowed amount becomes a carryforward subject to the SAME "
                "floor in subsequent years. In a flat-giving-year pattern, the "
                "0.5% floor is essentially a permanent drag.",
                "Corporate §170 floor under OBBBA is 1% of taxable income; "
                "coordinate with CHAR_OBBBA_CORPORATE_FLOOR for C corp donors.",
                "The OBBBA above-the-line charitable deduction ($1,000 single / "
                "$2,000 MFJ) is NOT subject to the 0.5% floor (it applies to "
                "itemizers only) and DAF contributions do not qualify for the "
                "above-the-line amount.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CHAR_BUNCHING",
                "CHAR_DAF",
                "CHAR_OBBBA_37_CAP",
                "CHAR_OBBBA_ABOVE_LINE",
                "CHAR_OBBBA_CORPORATE_FLOOR",
                "CHAR_AGI_LIMITS",
            ],
            verification_confidence="high",
            computation_trace={
                "approx_agi": str(agi),
                "floor_pct": "0.005",
                "floor_amount": str(floor_amount),
                "total_itemized_charitable": str(total_charitable),
                "disallowed_to_carryforward": str(disallowed_current_year),
                "allowed_current_year": str(allowed_current_year),
                "current_year_tax_drag": str(current_tax_drag),
            },
        )
