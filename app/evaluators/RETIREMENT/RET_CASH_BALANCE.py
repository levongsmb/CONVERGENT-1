"""RET_CASH_BALANCE — cash balance plan layered on Solo 401(k).

Cash balance plans are §414(j) defined benefit plans with participant
hypothetical account balances. They STACK on top of a 401(k) /
profit-sharing plan to produce deductible contributions well above the
§415(c) DC limit. Target fit: 45-65 year-old owners with consistent
income who can commit to multi-year funding.

Deductible contribution depends on actuarial assumptions and age-based
§415(b) annual benefit limit. The evaluator produces an ORDER-OF-
MAGNITUDE feasibility signal rather than a precise contribution number
(precise numbers require an actuary).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


# Age-band rough contribution targets (order of magnitude; an actuary
# produces the actual schedule). These are planning heuristics, not
# statutory values.
_AGE_BAND_TARGET_CONTRIBUTION = [
    (35, 45, Decimal("75000")),
    (45, 55, Decimal("150000")),
    (55, 60, Decimal("225000")),
    (60, 65, Decimal("300000")),
    (65, 70, Decimal("225000")),
]


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RET_CASH_BALANCE"
    CATEGORY_CODE = "RETIREMENT"
    PIN_CITES = [
        "IRC §414(j) — defined benefit plan",
        "IRC §415(b) — annual benefit limit",
        "IRC §404(a)(1)(A) — deductible contribution to DB plan (actuarially determined)",
        "Rev. Rul. 2002-42 — cash balance plan qualification",
        "Treas. Reg. §1.411(b)(5) — hybrid plan rules",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_se = scenario.income.self_employment_income > Decimal("250000")
        high_earning_scorp = any(
            e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            and e.ownership_pct_by_taxpayer >= Decimal("100")
            and scenario.income.wages_primary > Decimal("175000")
            for e in scenario.entities
        )
        if not has_se and not high_earning_scorp:
            return self._not_applicable(
                "income base is too low to justify DB/CB plan; requires "
                "at least $175K W-2 (S corp 100% owner) or $250K SE earnings"
            )

        primary_age = year - scenario.identity.primary_dob.year
        if primary_age < 35:
            return self._not_applicable(
                "primary taxpayer age < 35; DB / CB plan economics typically "
                "unfavorable at this age tier"
            )
        if primary_age > 70:
            return self._not_applicable(
                "primary taxpayer age > 70; DB / CB plan at this tier triggers "
                "RMD and reduced §415(b) window"
            )

        target_contribution = Decimal(0)
        age_band = "NONE"
        for low, high, amount in _AGE_BAND_TARGET_CONTRIBUTION:
            if low <= primary_age < high:
                target_contribution = amount
                age_band = f"{low}-{high}"
                break

        approx_marginal = Decimal("0.35")
        estimated_fed_save = (target_contribution * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "primary taxpayer age and retirement age target",
                "at least 3 years of consistent income history",
                "existing 401(k) / profit-sharing plan posture",
                "willingness to fund for minimum 3-5 years",
                "actuary-produced benefit formula and contribution schedule",
            ],
            assumptions=[
                f"Primary age: {primary_age} ({age_band} band)",
                f"Order-of-magnitude annual contribution target: ${target_contribution:,.0f}",
                f"Approx marginal rate: {approx_marginal:.0%}",
                "Actual deductible contribution determined annually by plan actuary.",
            ],
            implementation_steps=[
                "Engage a pension actuary to design the plan (cash balance pay "
                "credit, interest credit, retirement age assumption).",
                "Adopt plan document before end of the plan year (defined "
                "benefit plans can be adopted by the tax return due date for "
                "year-end funding).",
                "Run a combined-plan analysis against existing Solo 401(k) or "
                "traditional 401(k): the §404(a)(7) combined deduction limit "
                "applies (~31% of eligible compensation, with carve-outs).",
                "Establish a trust and trustee; coordinate Form 5500 filing and "
                "actuarial valuation schedule.",
                "Commit to 3-5 years of minimum funding under §412 or face "
                "plan termination penalties.",
            ],
            risks_and_caveats=[
                "Minimum required contribution under §412 is MANDATORY once "
                "the plan is adopted. Variable-income taxpayers must model "
                "downside years.",
                "Plan must be designed for substantial and recurring benefit "
                "accruals — §1.401-1(b)(2). IRS scrutinizes plans that only "
                "fund the owner.",
                "Pair with a Solo 401(k): combined §404(a)(7) deduction "
                "limit applies. RET_SOLO_401K + RET_CASH_BALANCE combined "
                "cap is ~31% of eligible compensation plus DB contribution.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RET_SOLO_401K",
                "RET_COMBO_PLANS",
                "RET_CTRL_GROUP",
                "COMP_REASONABLE_COMP",
                "COMP_WAGE_DIST_SPLIT",
            ],
            verification_confidence="medium",
            computation_trace={
                "primary_age": primary_age,
                "age_band": age_band,
                "target_contribution_rough": str(target_contribution),
                "approx_marginal_rate": str(approx_marginal),
            },
        )
