"""CAP_FIRST_TIME_ABATE — first-time abatement administrative waiver."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_FIRST_TIME_ABATE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRM 20.1.1.3.6.1 — first-time-abate administrative waiver",
        "Rev. Proc. 2019-46 — FTA procedures",
        "IRC §6651 / §6654 — covered penalties",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "prior 3-year penalty history",
                "current-year filing / payment status (must be compliant)",
                "IRS notice identifying assessed penalty",
            ],
            assumptions=[
                "FTA is one-per-taxpayer-per-penalty-type; spend it on the "
                "largest single-year assessment.",
                "Clean prior-3-year record required; minor penalties for "
                "other taxes can still allow FTA.",
            ],
            implementation_steps=[
                "Request FTA by calling IRS Practitioner Priority Service or "
                "by filing Form 843 with FTA indicator.",
                "If agent denies verbally, request written denial for appeal "
                "preservation.",
                "If FTA denied on clean-record test, identify which year "
                "broke compliance and address separately.",
            ],
            risks_and_caveats=[
                "FTA does NOT cover §6662 accuracy penalties.",
                "FTA applies separately to each tax type (income, employment, "
                "excise). Can be claimed on multiple types in same year.",
            ],
            cross_strategy_impacts=[
                "CAP_PENALTY_ABATEMENT",
                "CAP_REASONABLE_CAUSE",
            ],
            verification_confidence="high",
        )
