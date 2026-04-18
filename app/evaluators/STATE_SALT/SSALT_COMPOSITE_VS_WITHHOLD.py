"""SSALT_COMPOSITE_VS_WITHHOLD — composite return vs nonresident
withholding election analysis for pass-through entities."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType


_PTE_TYPES = {
    EntityType.S_CORP, EntityType.LLC_S_CORP,
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_COMPOSITE_VS_WITHHOLD"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "CA FTB Form 592 / 592-PTE — nonresident withholding and PTE withholding",
        "NY Form IT-203-GR — group nonresident return (composite equivalent)",
        "Multistate Tax Compact — composite filing traditions",
        "Rev. Rul. 91-32 — not directly on point but informs state positions",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        pte_entities = [e for e in scenario.entities if e.type in _PTE_TYPES]
        multistate_pte = [
            e for e in pte_entities
            if len(set((e.operating_states or []) + [e.formation_state])) > 1
        ]
        if not pte_entities:
            return self._not_applicable(
                "no pass-through entity; composite vs withholding election "
                "is a PTE-level mechanic"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "nonresident owner residency states",
                "state-by-state composite return availability and rate",
                "withholding rates for each state",
                "PTET election status (composite and PTET often mutually exclusive)",
                "owner preference: filing footprint vs cash-flow timing",
            ],
            assumptions=[
                "Composite returns eliminate owner-level filing but taxed at "
                "top marginal rate with no personal deductions or credits.",
                "Nonresident withholding provides a prepayment credit against "
                "the owner's personal nonresident return, preserving "
                "individual deductions/credits at owner level.",
                "Electing PTET usually disqualifies both composite and "
                "withholding for the same income stream.",
            ],
            implementation_steps=[
                "For each state where a nonresident owner exists: compare "
                "(a) owner's personal nonresident tax, (b) composite rate, "
                "(c) withholding rate + owner credit.",
                "Select the lowest-cost mechanism per owner-state pair.",
                "Coordinate PTET election first (see SSALT_PTET_MODELING); "
                "composite/withholding decisions follow PTET scope.",
                "Document owner consent for composite / withholding opt-in.",
            ],
            risks_and_caveats=[
                "Composite elections are often irrevocable for the year.",
                "Some states (e.g., NY) require group election per owner; "
                "mixed elections within one entity require separate tracking.",
                "Withholding timing: quarterly prepayments vs return-due; "
                "missed deposits incur state penalty.",
            ],
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_NONRESIDENT_WH",
                "SSALT_RESIDENT_CREDIT",
            ],
            verification_confidence="high",
            computation_trace={
                "pte_entity_count": len(pte_entities),
                "multistate_pte_count": len(multistate_pte),
            },
        )
