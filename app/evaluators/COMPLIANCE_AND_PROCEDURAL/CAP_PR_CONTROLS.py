"""CAP_PR_CONTROLS — partnership representative controls under §6223."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_PR_CONTROLS"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6223(a) — partnership representative designation",
        "IRC §6223(b) — binding authority over partnership and partners",
        "Treas. Reg. §301.6223-1 — eligibility and designation",
        "Treas. Reg. §301.6223-2 — resignation and revocation",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnerships = [
            e for e in scenario.entities
            if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP)
        ]
        if not partnerships:
            return self._not_applicable(
                "no partnership in scenario; PR controls are partnership-specific"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "current PR designation on Form 1065 Part III",
                "PR succession plan (resignation / revocation procedures)",
                "partnership agreement PR-related provisions",
                "designated individual (DI) for entity PRs",
            ],
            assumptions=[
                "PR has BINDING authority over partnership and partners in "
                "BBA audit actions.",
                "PR must have substantial US presence; if entity, PR must "
                "designate an individual (DI).",
                "PR may be changed annually via Form 1065 filing; off-cycle "
                "change requires revocation procedures under §301.6223-2.",
            ],
            implementation_steps=[
                "Designate PR on each year's Form 1065, Part III.",
                "Amend partnership agreement to specify PR selection, "
                "succession, indemnification, and partner-communication "
                "obligations.",
                "Maintain DI documentation for entity PRs; DI must be natural "
                "person with substantial US presence.",
                "On PR change: file Form 8979 Revocation of PR + designate "
                "replacement.",
            ],
            risks_and_caveats=[
                "PR's binding authority is near-unilateral; partners lose "
                "TEFRA-era participation rights.",
                "Disagreement between partners and PR is adjudicated within "
                "the partnership agreement framework, not tax procedure.",
                "Without a valid PR, IRS designates one unilaterally.",
            ],
            cross_strategy_impacts=[
                "CAP_BBA_AUDIT_REGIME",
                "CAP_PUSH_OUT_ELECTION",
                "CAP_EXAMS_APPEALS",
            ],
            verification_confidence="high",
        )
