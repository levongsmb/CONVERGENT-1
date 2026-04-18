"""CAP_PUSH_OUT_ELECTION — BBA push-out election mechanics under §6226."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_PUSH_OUT_ELECTION"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6226 — push-out election",
        "IRC §6226(a)(2) — 45-day window from FPAA",
        "IRC §6226(b) — partner-level adjustment statements",
        "Treas. Reg. §301.6226-1 — push-out mechanics",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnerships = [
            e for e in scenario.entities
            if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP)
        ]
        if not partnerships:
            return self._not_applicable(
                "no partnership in scenario; §6226 push-out is partnership-specific"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "FPAA issuance date (45-day clock start)",
                "reviewed-year partner list and their tax postures",
                "imputed underpayment vs partner-level tax comparison",
            ],
            assumptions=[
                "§6226 push-out passes BBA adjustment to reviewed-year "
                "partners in lieu of entity-level imputed underpayment.",
                "45-day window from FPAA is a HARD deadline — no extension "
                "absent §7508A disaster.",
                "Each reviewed-year partner files amended return for their "
                "allocated share plus interest at underpayment rate + 2%.",
            ],
            implementation_steps=[
                "Compute imputed underpayment at entity level (highest "
                "marginal rate, §6225(b)) and compare to push-out tax.",
                "Push-out is favorable when reviewed-year partners' actual "
                "rates are lower than §6225(b) highest rate.",
                "File push-out election within 45 days of FPAA; issue partner-"
                "level statements (§6226(b)).",
                "Partners file amended returns for reviewed year with "
                "adjustments plus §6226(c) interest.",
            ],
            risks_and_caveats=[
                "Push-out imposes partner-level interest at underpayment rate "
                "+ 2% penalty; entity-level imputed underpayment uses plain "
                "underpayment rate.",
                "Tiered partnerships: push-out may cascade through tiers; "
                "modeling required before electing.",
            ],
            cross_strategy_impacts=[
                "CAP_BBA_AUDIT_REGIME",
                "CAP_PR_CONTROLS",
                "CAP_EXAMS_APPEALS",
            ],
            verification_confidence="high",
        )
