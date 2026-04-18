"""CAP_FORM_8308 — Form 8308 partnership interest sale reporting."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_FORM_8308"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6050K — partnership §751 exchange reporting",
        "Treas. Reg. §1.6050K-1 — Form 8308 requirements",
        "Form 8308 instructions — §751(a) hot-asset transfers",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnerships = [
            e for e in scenario.entities
            if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP)
        ]
        if not partnerships:
            return self._not_applicable(
                "no partnership in scenario; Form 8308 is partnership-specific"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "transferor / transferee details for any partnership interest sales",
                "§751(a) hot-asset computation (unrealized receivables, inventory)",
                "due date (with Form 1065 by 3/15; copies to transferor and transferee by 1/31)",
            ],
            assumptions=[
                "Form 8308 required for any §751(a) transfer (sale of a "
                "partnership interest with hot assets).",
                "Partnership must report transfer even if it is not the "
                "party receiving payment.",
            ],
            implementation_steps=[
                "On any notice of partnership interest transfer, compute "
                "§751(a) ordinary-income portion.",
                "Prepare Form 8308 with Parts I-IV completed.",
                "Distribute copies: to transferor and transferee by January 31.",
                "File Form 8308 with partnership return (Form 1065) by 3/15.",
            ],
            risks_and_caveats=[
                "Missed Form 8308 is a common trap; §6721 / §6722 penalties "
                "apply.",
                "New §751(a) reporting requirements expanded under Reg. "
                "§1.6050K-1 beginning with 2023 returns.",
            ],
            cross_strategy_impacts=[
                "PS_751_HOT_ASSETS",
                "PTE_754_ELECTION",
                "SALE_751_HOT_ASSETS",
            ],
            verification_confidence="high",
        )
