"""SSALT_NONRESIDENT_WH — nonresident withholding minimization."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType


_PTE_TYPES = {
    EntityType.S_CORP, EntityType.LLC_S_CORP,
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NONRESIDENT_WH"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "CA FTB Form 592 / 592-B / 592-PTE — nonresident and PTE withholding",
        "CA R&TC §18662 — CA nonresident withholding authority",
        "NY Tax Law §658(c)(4) — NY partnership withholding on nonresident partners",
        "Various state nonresident withholding reduction / waiver forms",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        pte = [e for e in scenario.entities if e.type in _PTE_TYPES]
        if not pte:
            return self._not_applicable(
                "no pass-through entity; nonresident withholding is a PTE mechanic"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "owner residency by state",
                "entity sourcing of income by state",
                "availability of waiver / reduction forms per state",
                "prior-year actual owner state liability (basis for waiver)",
            ],
            assumptions=[
                "Most states require PTE to withhold on nonresident owners "
                "unless the owner opts into composite OR submits a waiver.",
                "CA permits a reduced-withholding waiver (FTB Form 589/588) "
                "tied to prior-year actual liability.",
                "Withholding is a prepayment; excess refunds on the owner's "
                "nonresident return but creates cash-flow drag.",
            ],
            implementation_steps=[
                "For each nonresident owner, request state-specific waiver "
                "where available and economically justified.",
                "Align withholding rate to prior-year actual liability ratio "
                "rather than statutory default.",
                "Coordinate with composite election decision "
                "(SSALT_COMPOSITE_VS_WITHHOLD) — composite usually supersedes "
                "withholding.",
                "Track per-owner 592-B / K-1 withholding attribution for "
                "downstream personal-return credit.",
            ],
            risks_and_caveats=[
                "Failure to withhold exposes the PTE to penalty and interest; "
                "waivers must be on file before the distribution date.",
                "PTET election often eliminates the nonresident withholding "
                "obligation — confirm per state.",
            ],
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_COMPOSITE_VS_WITHHOLD",
                "SSALT_RESIDENT_CREDIT",
            ],
            verification_confidence="high",
        )
