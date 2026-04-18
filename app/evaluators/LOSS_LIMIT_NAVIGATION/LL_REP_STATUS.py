"""LL_REP_STATUS — Real Estate Professional status under §469(c)(7).

REP status converts rental activities from passive to nonpassive,
allowing rental losses to offset active income. Requires:
  (a) More than 50% of personal services in real-property trades or
      businesses in which the taxpayer materially participates.
  (b) At least 750 hours in real-property trades or businesses.
  (c) Material participation in the rental activity (or the activity
      is grouped with others where material participation is met).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "LL_REP_STATUS"
    CATEGORY_CODE = "LOSS_LIMIT_NAVIGATION"
    PIN_CITES = [
        "IRC §469(c)(7) — real estate professional exception",
        "IRC §469(c)(7)(B)(i) — more-than-half personal services test",
        "IRC §469(c)(7)(B)(ii) — 750-hour test",
        "Treas. Reg. §1.469-9 — REP status rules",
        "Rev. Proc. 2011-34 — late grouping election",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_rental = (
            scenario.income.rental_income_net != Decimal(0)
            or scenario.prior_year.suspended_passive_losses > Decimal(0)
        )
        if not has_rental:
            return self._not_applicable(
                "no rental activity or suspended passive loss in scenario"
            )

        # Scenario does not currently carry hours-by-activity; surface the
        # facts-to-gather list so the CPA can document the election.
        current_loss = (
            -scenario.income.rental_income_net
            if scenario.income.rental_income_net < Decimal(0)
            else Decimal(0)
        )
        potential_release = current_loss + scenario.prior_year.suspended_passive_losses

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "contemporaneous log of hours spent on real-property trades "
                "or businesses (time-tracking app, calendar, or dated diary)",
                "total personal-service hours across all activities for the "
                "50% test",
                "material participation facts per rental property (seven "
                "tests under Treas. Reg. §1.469-5T(a))",
                "§1.469-9(g) aggregation election status on file",
            ],
            assumptions=[
                "REP is evaluated annually; prior-year REP status does not "
                "carry to current year without re-qualification.",
                f"Current-year rental loss subject to release if REP qualifies: ${current_loss:,.2f}",
                f"Prior-year suspended passive loss potentially released on full taxable disposition: "
                f"${scenario.prior_year.suspended_passive_losses:,.2f}",
            ],
            implementation_steps=[
                "File (or confirm prior filing of) §1.469-9(g) election to "
                "aggregate all rental real estate as a single activity.",
                "Collect contemporaneous time logs totaling > 750 hours in "
                "real-property trades or businesses.",
                "Collect total personal-service hours; verify > 50% are in "
                "real-property trades or businesses.",
                "Apply material participation tests under §1.469-5T(a) to "
                "each aggregated rental activity.",
                "If qualified, rental losses become nonpassive on Schedule E "
                "and Form 8582; §469 disallowance does not apply.",
            ],
            risks_and_caveats=[
                "MFJ: both spouses' hours do NOT combine for the 750-hour / "
                "50% test — each spouse qualifies independently. But the "
                "aggregation election, once made, applies to both.",
                "W-2 wage earner with full-time non-real-estate employment "
                "typically cannot satisfy the 50% test without resigning or "
                "materially reducing other work.",
                "Hours spent as employee in real-property trade count only "
                "if the taxpayer owns >= 5% of the employer.",
                "IRS challenges REP status aggressively; contemporaneous "
                "documentation is essential. Post-hoc reconstruction has "
                "been rejected repeatedly (see Moss, Calvanico, Miller).",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "LL_469_PASSIVE",
                "LL_469_GROUPING",
                "LL_STR_EXCEPTION",
                "LL_SUSPENDED_LOSSES",
                "RED_PASSIVE_LOSS_INTERACT",
                "NIIT_REP_PLANNING",
            ],
            verification_confidence="high",
            computation_trace={
                "current_rental_loss": str(current_loss),
                "suspended_passive_losses": str(scenario.prior_year.suspended_passive_losses),
                "potential_release_if_qualified": str(potential_release),
            },
        )
