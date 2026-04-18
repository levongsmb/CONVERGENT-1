"""CAP_EXAMS_APPEALS — IRS exams and Appeals defense."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_EXAMS_APPEALS"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §7602 — examination authority",
        "IRC §7121 — closing agreements",
        "IRC §7122 — offer in compromise",
        "IRC §6330 — collection due process",
        "IRM 4.10 — examination standards",
        "IRM 8 — Appeals procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "exam notice identifying issues and years",
                "agent contact and exam type (correspondence / office / field)",
                "IDR (Information Document Request) history",
                "status of unsigned Form 872 extensions",
            ],
            assumptions=[
                "Exam → 30-day letter → Appeals → 90-day letter → Tax Court.",
                "Appeals is independent from Exam and evaluates hazards of "
                "litigation (IRM 8.6.1.4).",
                "Early engagement with Appeals via Fast Track Settlement is "
                "available for many cases.",
            ],
            implementation_steps=[
                "On exam notice: file Form 2848 POA; establish taxpayer "
                "communication boundary (all through practitioner).",
                "Respond to IDRs with scope pushback; produce ONLY what is "
                "requested and relevant.",
                "At 30-day letter: file written protest for Appeals if "
                "disputed amount > $25,000.",
                "At 90-day letter: petition Tax Court within 90 days OR pay "
                "and sue for refund in district court or CFC.",
                "Evaluate Fast Track Settlement before formal Appeals.",
            ],
            risks_and_caveats=[
                "90-day letter clock is absolute — missed deadline forfeits "
                "Tax Court jurisdiction.",
                "Closing agreement under §7121 binds both parties; structure "
                "carefully to avoid unintended future-year implications.",
                "Appeals CANNOT raise new issues; taxpayer CAN raise new "
                "issues in Appeals if not precluded.",
            ],
            cross_strategy_impacts=[
                "CAP_REASONABLE_CAUSE",
                "CAP_PENALTY_ABATEMENT",
                "CAP_STATUTE_MGMT",
                "CAP_ACCOUNTING_METHOD_DEFENSE",
                "CAP_ERC_DEFENSE",
            ],
            verification_confidence="high",
        )
