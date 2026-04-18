"""CAP_K2_K3 — partnership Schedule K-2 and K-3 reporting."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_K2_K3"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "Schedule K-2 / K-3 instructions (Form 1065 / 1120-S)",
        "IRS FAQ on K-2/K-3 Domestic Filing Exception",
        "Treas. Reg. §1.6031(a)-1 — partnership return filing requirements",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        flow_through = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
            )
        ]
        if not flow_through:
            return self._not_applicable(
                "no partnership / S corp in scenario; K-2 / K-3 apply to "
                "flow-through entities"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "foreign activity status of the entity (foreign income, "
                "foreign taxes paid, foreign partners)",
                "all-domestic-activity attestation documentation",
                "partner / shareholder notifications for domestic filing exception",
                "timely partner / shareholder responses to notification",
            ],
            assumptions=[
                "Domestic Filing Exception (DFE) eliminates K-2 / K-3 filing "
                "if: (a) no foreign activity, (b) all owners are US persons, "
                "(c) timely partner notification given, (d) no partner "
                "requests Schedule K-3.",
                "Even under DFE, if one partner requests K-3, full K-2 / K-3 "
                "filing becomes mandatory.",
            ],
            implementation_steps=[
                "Test DFE eligibility: no foreign activity + all-US owners.",
                "Send notification to partners / shareholders by the one-"
                "month before filing date.",
                "If any partner requests K-3: prepare Schedule K-2 at entity "
                "level and K-3 per partner.",
                "File K-2 / K-3 electronically with Form 1065 / 1120-S.",
            ],
            risks_and_caveats=[
                "Partner right to request K-3 is broad; a single foreign-"
                "invested partner triggers full reporting.",
                "K-2 / K-3 penalty exposure is large: §6698 late-filing + "
                "§6722 information-return penalty stack.",
            ],
            cross_strategy_impacts=[
                "IO_5471_5472",
                "IO_FTC_BASKETS",
                "CR_FTC",
                "CAP_1099",
            ],
            verification_confidence="high",
        )
