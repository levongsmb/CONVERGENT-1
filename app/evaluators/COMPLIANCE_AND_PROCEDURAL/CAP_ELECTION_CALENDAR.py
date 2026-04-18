"""CAP_ELECTION_CALENDAR — consistency elections and annual election calendar."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_ELECTION_CALENDAR"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "Treas. Reg. §301.9100-1 through -3 — election relief",
        "IRC §754 — once-made irrevocable",
        "IRC §1362 — S election",
        "IRC §168(k)(7) — bonus election-out",
        "Rev. Proc. 2023-24 — automatic method-change DCNs",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "complete roster of elections in force by entity and year",
                "due dates for current-year elections (Form 2553, 8716, 8832, 3115, 8716)",
                "elections requiring annual renewal vs one-time",
                "§9100 relief windows for any missed elections",
            ],
            assumptions=[
                "Annual elections: §163(j)(7)(B) real-property election (irrevocable); §754 (irrevocable); §168(k)(7) bonus election-out (per class per year).",
                "Due dates typically run with the original return including extensions.",
                "§9100 relief is discretionary; not all missed elections qualify.",
            ],
            implementation_steps=[
                "Maintain a firm-level elections matrix: per client per entity "
                "per year, track election name, form number, due date, status.",
                "Run the matrix monthly against upcoming due dates; confirm "
                "each election either filed or intentionally not filed.",
                "For missed elections: evaluate §9100 relief path.",
                "Document elections in permanent-file binders.",
            ],
            risks_and_caveats=[
                "§754 election is irrevocable once made; revocation requires "
                "Commissioner consent.",
                "§1362 S election terminates on certain ineligibility events; "
                "Form 2553 re-election may be blocked for 5 years.",
                "Confusing revocable election with irrevocable election is a "
                "common trap — classify each before filing.",
            ],
            cross_strategy_impacts=[
                "CAP_PROTECTIVE_ELECTIONS",
                "CAP_3115_METHOD_CHANGE",
                "CAP_SUPERSEDING_VS_AMENDED",
            ],
            verification_confidence="high",
        )
