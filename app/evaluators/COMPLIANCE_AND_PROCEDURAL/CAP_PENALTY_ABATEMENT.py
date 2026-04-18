"""CAP_PENALTY_ABATEMENT — late-filing and late-payment penalty abatement.

§6651 imposes late-filing (5%/month up to 25%) and late-payment
(0.5%/month up to 25%) penalties. Abatement is available through
reasonable-cause (§6651(a)), first-time-abatement administrative
waiver, or procedural relief (§7508A disaster). Applicable to any
scenario with prior-year IRS notice activity or known filing delays.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_PENALTY_ABATEMENT"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6651(a)(1) — late-filing penalty 5%/month",
        "IRC §6651(a)(2) — late-payment penalty 0.5%/month",
        "IRC §6651(c) — stacking limitation",
        "IRM 20.1.1.3 — reasonable cause standards",
        "IRM 20.1.1.3.6.1 — first-time-abate administrative waiver",
        "Rev. Proc. 2019-46 — first-time-abate procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "IRS notice(s) received identifying assessed penalties",
                "filing history for prior three years (first-time-abate eligibility)",
                "reasonable-cause facts and supporting documentation",
                "§7508A disaster designation status if applicable",
            ],
            assumptions=[
                "First-time abate available if no penalties in prior 3 years "
                "and current-year compliance is complete.",
                "Reasonable cause requires written substantiation of "
                "ordinary business care and prudence.",
            ],
            implementation_steps=[
                "Pull IRS transcript (Form 2848 POA + transcript request) to "
                "identify all assessed penalties.",
                "Test first-time-abate eligibility (IRM 20.1.1.3.6.1): clean "
                "prior 3 years AND current compliance.",
                "If FTA denied, file reasonable-cause statement on Form 843 "
                "citing specific facts under IRM 20.1.1.3.",
                "If §7508A disaster relief covers the period, request "
                "procedural abatement rather than reasonable-cause.",
            ],
            risks_and_caveats=[
                "FTA is one-per-taxpayer-per-type; use it on the largest "
                "single-year penalty first.",
                "Reasonable-cause denials are common; structure the facts "
                "statement under IRM criteria (death, serious illness, "
                "unavoidable absence, destruction of records, reliance on "
                "professional advice).",
                "§6662 accuracy penalties are NOT abatable via FTA; require "
                "reasonable-cause + substantial-authority defense.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CAP_FIRST_TIME_ABATE",
                "CAP_REASONABLE_CAUSE",
                "CAP_7508A_DISASTER",
                "CAP_EXAMS_APPEALS",
            ],
            verification_confidence="high",
            computation_trace={},
        )
