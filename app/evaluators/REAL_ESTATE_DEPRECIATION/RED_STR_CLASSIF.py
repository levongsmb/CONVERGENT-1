"""RED_STR_CLASSIF — short-term rental classification exception.

Short-term rental activities (average rental period ≤ 7 days under
Treas. Reg. §1.469-1T(e)(3)(ii)(A)) are NOT rental activities for §469
purposes. The taxpayer may treat an STR as a non-passive trade or
business with material participation, releasing the rental-loss cage
without needing REP status.

Applicable when scenario flags a rental activity whose average rental
period may qualify. The current schema does not carry per-property
average rental period; this evaluator surfaces the question and lists
inputs required.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RED_STR_CLASSIF"
    CATEGORY_CODE = "REAL_ESTATE_DEPRECIATION"
    PIN_CITES = [
        "Treas. Reg. §1.469-1T(e)(3)(ii)(A) — 7-day average rental period exception",
        "Treas. Reg. §1.469-1T(e)(3)(ii)(B) — 30-day average plus significant personal services",
        "Treas. Reg. §1.469-5T(a) — material participation tests",
        "Rev. Rul. 2019-08 — nonpassive treatment",
        "Bailey v. Commissioner, T.C. Memo 2001-296 — STR material participation",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        rental_assets = [
            a for a in scenario.assets
            if a.asset_type
            in (AssetType.REAL_PROPERTY_RESIDENTIAL, AssetType.REAL_PROPERTY_COMMERCIAL)
            and "rental" in (a.description or "").lower()
        ]
        has_rental_activity = (
            scenario.income.rental_income_net != Decimal(0)
            or len(rental_assets) > 0
        )
        if not has_rental_activity:
            return self._not_applicable(
                "no rental activity in scenario; STR classification is "
                "rental-specific"
            )

        current_rental_net = scenario.income.rental_income_net
        rental_loss = (
            -current_rental_net if current_rental_net < Decimal(0) else Decimal(0)
        )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "average rental period per property (days of bookings / number of rentals)",
                "personal-use days per property (§280A)",
                "material-participation hour log (§1.469-5T(a) seven tests)",
                "significant personal services provided to renters if average period > 7 days",
            ],
            assumptions=[
                f"Candidate rental assets: {len(rental_assets)}",
                f"Current-year rental loss (aggregate): ${rental_loss:,.2f}",
                "STR exception releases loss from passive cage only if taxpayer "
                "materially participates (seven tests under §1.469-5T(a)).",
            ],
            implementation_steps=[
                "Compute average rental period per property: total days rented "
                "divided by number of distinct rental periods. Exception "
                "applies at ≤ 7 days average.",
                "If average is > 7 but ≤ 30 days, the alternative rule under "
                "§1.469-1T(e)(3)(ii)(B) requires significant personal services.",
                "Document material participation hours (500+ hours OR 100+ "
                "hours and more than any other participant under "
                "§1.469-5T(a)(3)).",
                "If STR qualifies and taxpayer materially participates: losses "
                "are nonpassive, offset ordinary income, and are not subject "
                "to §469 suspension.",
                "Losses remain subject to §461(l) excess business loss limit.",
            ],
            risks_and_caveats=[
                "STR losses are NONPASSIVE for §469 but remain subject to "
                "§461(l), §465 at-risk, and §1366(d) / §704(d) basis rules.",
                "Material participation must be documented contemporaneously. "
                "IRS routinely challenges hour logs reconstructed after the "
                "fact (Moss, Bailey, Lucero, Tolin).",
                "The STR exception does NOT convert rental income to earned "
                "income for SE tax. §1402(a)(1) rental exclusion continues to "
                "apply unless the taxpayer is a dealer (§1221).",
                "Personal-use days under §280A interact: if personal use > 14 "
                "days or 10% of rental days, the residence rules under "
                "§280A(c)(5) limit deductions.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "LL_469_PASSIVE",
                "LL_REP_STATUS",
                "LL_SUSPENDED_LOSSES",
                "RED_COST_SEG",
                "RED_PASSIVE_LOSS_INTERACT",
                "NIIT_REP_PLANNING",
            ],
            verification_confidence="high",
            computation_trace={
                "candidate_rental_asset_count": len(rental_assets),
                "current_rental_loss": str(rental_loss),
                "str_exception_conditions": [
                    "avg rental period <= 7 days (no personal services required)",
                    "avg rental period <= 30 days with significant personal services",
                ],
            },
        )
