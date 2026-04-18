"""CR_ORDERING_LIMITS — general business credit §38 ordering and 25%-of-tax limit.

§38 aggregates most business credits (§41 R&D, §45, §48, §45W, §45X,
WOTC, etc.). The aggregate credit is limited each year to:

  Tax liability minus (greater of tentative minimum tax OR 25% of the
  net regular tax liability in excess of $25,000)

Unused credits carry BACK 1 year and FORWARD 20 years under §39.
Ordering of credits when multiple generated: §38(d) specifies order;
first in, first out within any category.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CR_ORDERING_LIMITS"
    CATEGORY_CODE = "CREDITS"
    PIN_CITES = [
        "IRC §38(a) — general business credit aggregation",
        "IRC §38(c)(1) — 25%-of-tax limitation",
        "IRC §38(d) — ordering of credits within aggregate",
        "IRC §39(a) — carryback / carryforward (1 year back, 20 years forward)",
        "IRC §55(c) — AMT interaction and the §38(c) tentative minimum tax floor",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        carryforwards = scenario.prior_year.credit_carryforwards
        has_carryforwards = len(carryforwards) > 0

        # Applicable when there is meaningful federal tax (to which the
        # §38 limit applies) or carryforward credits to utilize.
        prior_fed_tax = scenario.prior_year.total_federal_tax or Decimal(0)
        if prior_fed_tax < Decimal("10000") and not has_carryforwards:
            return self._not_applicable(
                "insufficient federal tax context and no carryforward credits; "
                "§38 ordering analysis requires meaningful tax liability or "
                "a credit inventory"
            )

        total_carryforward_amount = Decimal(0)
        for c in carryforwards:
            amt = c.get("amount")
            if amt is not None:
                total_carryforward_amount += Decimal(str(amt))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "projected current-year regular tax liability",
                "tentative minimum tax (Form 6251 for individuals)",
                "carryforward credit inventory by type and origin year",
                "projected §41, §45, §48 generation this year",
                "affiliated-group / aggregation posture under §38(c)(5)",
            ],
            assumptions=[
                f"Prior-year total federal tax: ${prior_fed_tax:,.2f}",
                f"Credit carryforwards tracked: {len(carryforwards)}",
                f"Aggregate carryforward amount: ${total_carryforward_amount:,.2f}",
                "§38 limit: tax − greater of (TMT or 25% × (tax − $25,000)).",
                "Unused GBC carries back 1 year, forward 20 years.",
            ],
            implementation_steps=[
                "Build the aggregate GBC schedule on Form 3800 Part I: "
                "list each component credit by source.",
                "Compute the §38(c) limitation: tax liability minus the "
                "greater of (TMT, 25%-of-excess).",
                "Apply §38(d) ordering within aggregate (specified priority).",
                "If current-year credits exceed the limit, file Form 3800 "
                "Part IV with the carryforward amount per originating year.",
                "Evaluate elective carryback under §39(a)(1) — often valuable "
                "when prior year had high tax and carryback is fungible.",
            ],
            risks_and_caveats=[
                "20-year carryforward is a firm wall. Credits expiring unused "
                "are permanently lost.",
                "§38(c) limitation interacts with AMT: the TMT floor prevents "
                "credits from reducing tax below AMT. For taxpayers in AMT "
                "territory, a credit may be effectively deferred.",
                "BBA partnerships: §38 credits flow through; partner-level "
                "§38(c) limitation applies. Document credits on K-1 Line 15.",
                "§38 limit applies separately to the §41(h) startup payroll "
                "offset (cross-reference CR_RND_41 and "
                "CR_STARTUP_PAYROLL_OFFSET).",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CR_RND_41",
                "CR_STARTUP_PAYROLL_OFFSET",
                "CR_GBC_CARRYFWD",
                "CR_ENERGY",
                "CR_ENERGY_TRANSFERABILITY",
                "CR_FTC",
                "CR_280C_INTERACT",
            ],
            verification_confidence="high",
            computation_trace={
                "prior_year_federal_tax": str(prior_fed_tax),
                "carryforward_count": len(carryforwards),
                "aggregate_carryforward_amount": str(total_carryforward_amount),
                "has_carryforwards": has_carryforwards,
            },
        )
