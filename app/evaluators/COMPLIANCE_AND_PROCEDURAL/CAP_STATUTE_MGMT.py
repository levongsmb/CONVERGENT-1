"""CAP_STATUTE_MGMT — statute management and consent strategy."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_STATUTE_MGMT"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6501 — assessment SOL (3 years default; 6 years if 25%+ gross income omission; unlimited for fraud or no return)",
        "IRC §6511 — refund claim SOL",
        "IRC §6501(c)(4) — extension by consent (Form 872)",
        "IRC §6501(c)(8) — foreign information return 3-year hold",
        "IRM 25.6.22 — statute-of-limitations procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "open tax years and their assessment SOL dates",
                "open refund claim SOL dates (3 years from filing / 2 from payment)",
                "any Form 872 consent extensions signed",
                "foreign information return filings (Form 5471, 8865, 8938, FBAR)",
            ],
            assumptions=[
                "§6501(a) default assessment SOL is 3 years after return "
                "filed (or due date if later).",
                "§6501(e)(1) extends SOL to 6 years if taxpayer omits more "
                "than 25% of gross income.",
                "§6501(c)(1) unlimited SOL for fraud or no return.",
                "§6501(c)(8) keeps SOL open until 3 years after required "
                "foreign information return is actually filed.",
            ],
            implementation_steps=[
                "Build a statute-tracking log with each open year's "
                "assessment SOL, refund SOL, and any outstanding Form 872.",
                "For years approaching SOL with favorable positions not yet "
                "claimed: file protective or amended return before SOL.",
                "For years where exam activity is ongoing: evaluate Form 872 "
                "consent to extension; NEVER sign blanket extensions — "
                "limit by issue and year.",
                "For foreign information returns: confirm all Form 5471 / "
                "8865 / 8938 / FBAR filings are current.",
            ],
            risks_and_caveats=[
                "Signing Form 872 waives the SOL; negotiate a restricted "
                "consent that limits extension to specific issues.",
                "§6501(c)(8) is a trap for taxpayers with foreign items; the "
                "SOL may remain open indefinitely until the required form is "
                "filed.",
            ],
            cross_strategy_impacts=[
                "CAP_PROTECTIVE_ELECTIONS",
                "CAP_EXAMS_APPEALS",
                "IO_FBAR_FATCA",
                "IO_5471_5472",
            ],
            verification_confidence="high",
        )
