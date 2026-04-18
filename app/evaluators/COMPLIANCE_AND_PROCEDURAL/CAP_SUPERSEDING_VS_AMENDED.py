"""CAP_SUPERSEDING_VS_AMENDED — superseding vs amended returns."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_SUPERSEDING_VS_AMENDED"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6511 — amended return SOL",
        "IRC §6501 — assessment SOL",
        "Rev. Rul. 77-289 — superseding return treated as original",
        "Haggar Co. v. Helvering, 308 U.S. 389 (1940) — superseding return doctrine",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "original return filing date",
                "extended due date for the tax year",
                "nature of the correction (election change, math error, new facts)",
                "whether any affected elections are irrevocable post-due-date",
            ],
            assumptions=[
                "Superseding return: filed BEFORE extended due date, "
                "treated as the original. Elections may be modified.",
                "Amended return: filed AFTER extended due date, subject to "
                "§6511 SOL; irrevocable elections cannot be changed.",
            ],
            implementation_steps=[
                "Determine whether current date is before or after extended "
                "due date.",
                "If before due date: file a superseding return (same form, "
                "indicate 'Superseding' on 1040-X box or the entity return).",
                "If after due date: file Form 1040-X / 1120-X / 1065-X with "
                "changed items; note any elections that cannot be revised.",
                "Track §6501 assessment SOL if the correction increases tax.",
            ],
            risks_and_caveats=[
                "Some elections (§168(k)(7) bonus election-out, §754 election) "
                "are irrevocable once made; superseding return is the only "
                "chance to change.",
                "Amended return starts a new audit-exposure window limited to "
                "the adjusted items.",
            ],
            cross_strategy_impacts=[
                "CAP_STATUTE_MGMT",
                "CAP_PROTECTIVE_ELECTIONS",
                "CAP_ELECTION_CALENDAR",
            ],
            verification_confidence="high",
        )
