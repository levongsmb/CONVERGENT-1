"""CAP_7508A_DISASTER — disaster relief postponements under §7508A."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_7508A_DISASTER"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §7508A — postponement of certain tax deadlines by reason of federally declared disaster",
        "IRC §165(i) — casualty loss election to prior year",
        "IRC §1033 — involuntary conversion replacement",
        "IRS Disaster Relief page — listed federally declared disaster areas",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "physical or business address in a federally declared disaster zone",
                "incident period and §7508A relief window from IRS announcement",
                "§165(i) prior-year casualty-loss election eligibility",
                "§1033 replacement-period facts (2 years, 4 for principal residence)",
            ],
            assumptions=[
                "§7508A relief is automatic for taxpayers within the "
                "declared zone; self-identification required if outside zone "
                "but records are within it.",
                "§165(i) election allows casualty loss to be claimed on "
                "prior-year return for faster refund.",
            ],
            implementation_steps=[
                "Confirm client address or record-location is in disaster zone.",
                "Cite the IRS announcement number on late-filed returns; penalty "
                "and interest are abated within the relief window.",
                "If casualty loss occurred, evaluate §165(i) election to claim "
                "on prior-year amended return.",
                "For involuntary conversion gain: elect §1033 deferral with "
                "replacement-property plan.",
            ],
            risks_and_caveats=[
                "§7508A does NOT extend SOL for refund claims beyond the "
                "statutory window under §6511.",
                "Only federally declared disasters qualify — not state-level "
                "declarations alone.",
                "Casualty losses for personal-use property are deductible only "
                "for federally declared disasters (post-TCJA §165(h)(5)).",
            ],
            cross_strategy_impacts=[
                "CAP_PENALTY_ABATEMENT",
                "CAP_REASONABLE_CAUSE",
                "CA_DISASTER_LOSS",
            ],
            verification_confidence="high",
        )
