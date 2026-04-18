"""LL_469_PASSIVE — §469 passive activity loss rules.

Detects scenarios where passive losses are suspended and surfaces
planning opportunities to release them via disposition, grouping, or
real estate professional status (see LL_REP_STATUS).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "LL_469_PASSIVE"
    CATEGORY_CODE = "LOSS_LIMIT_NAVIGATION"
    PIN_CITES = [
        "IRC §469 — passive activity loss rules",
        "IRC §469(c)(1) — passive activity definition",
        "IRC §469(c)(7) — real estate professional exception",
        "IRC §469(g) — release on fully taxable disposition",
        "Treas. Reg. §1.469-4 — grouping rules",
        "Rev. Proc. 2019-38 — rental real estate safe harbor",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        suspended = scenario.prior_year.suspended_passive_losses
        current_rental_net = scenario.income.rental_income_net

        has_suspended = suspended > Decimal(0)
        has_current_rental_loss = current_rental_net < Decimal(0)
        if not has_suspended and not has_current_rental_loss:
            return self._not_applicable(
                "no suspended passive losses and no current-year rental loss in scenario"
            )

        # Release opportunities
        rental_loss = -current_rental_net if current_rental_net < Decimal(0) else Decimal(0)
        total_suspended = suspended + rental_loss

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "suspended passive loss carryover by activity",
                "current-year passive income / loss by activity",
                "disposition facts for any activity planned for sale",
                "material participation hours by activity (for grouping / REP)",
            ],
            assumptions=[
                f"Prior-year suspended passive losses: ${suspended:,.2f}",
                f"Current-year rental net: ${current_rental_net:,.2f}",
                f"Aggregate passive losses awaiting release: ${total_suspended:,.2f}",
            ],
            implementation_steps=[
                "Evaluate real estate professional status election under "
                "§469(c)(7); if qualified, rental losses become nonpassive.",
                "Evaluate the short-term rental exception (average rental "
                "period <= 7 days) for any property qualifying.",
                "Review §1.469-4 grouping of related trades and businesses "
                "to unlock previously-suspended losses.",
                "Identify any planned disposition of a passive activity; "
                "§469(g) releases ALL suspended losses on full taxable sale.",
            ],
            risks_and_caveats=[
                "§469 applies AT THE TAXPAYER LEVEL. MFJ combines both spouses' "
                "hours for material participation.",
                "Grouping elections are permanent; revocation requires a "
                "material change in facts and circumstances.",
                "Related-party disposition rules under §469(g)(1)(B) deny "
                "release on sales to related parties.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "LL_469_GROUPING",
                "LL_REP_STATUS",
                "LL_STR_EXCEPTION",
                "LL_DISPOSITION_FREE_SL",
                "LL_SUSPENDED_LOSSES",
                "RED_PASSIVE_LOSS_INTERACT",
            ],
            verification_confidence="high",
            computation_trace={
                "prior_suspended_passive_losses": str(suspended),
                "current_rental_net": str(current_rental_net),
                "current_rental_loss": str(rental_loss),
                "aggregate_passive_losses_awaiting_release": str(total_suspended),
            },
        )
