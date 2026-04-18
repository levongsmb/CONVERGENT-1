"""SSALT_NJ_BAIT — NJ Business Alternative Income Tax election."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType, StateCode


_PTE_TYPES = {
    EntityType.S_CORP, EntityType.LLC_S_CORP,
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NJ_BAIT"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "N.J.S.A. 54A:12-1 to 54A:12-10 — NJ Business Alternative Income Tax",
        "NJ P.L. 2019, c. 320 — original BAIT authorization",
        "NJ P.L. 2021, c. 419 — BAIT amendments fixing owner credit and resident credit interaction",
        "IRS Notice 2020-75 — federal deductibility of entity-level SALT",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        nj_pte = [
            e for e in scenario.entities
            if e.type in _PTE_TYPES
            and (e.formation_state == StateCode.NJ
                 or StateCode.NJ in (e.operating_states or []))
        ]
        if not nj_pte:
            return self._not_applicable(
                "no NJ pass-through entity; BAIT requires NJ formation "
                "or NJ-sourced PTE income"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "NJ-sourced PTE taxable income",
                "partner / member share and residency",
                "prior-year BAIT credit carryforward at owner level",
            ],
            assumptions=[
                "BAIT is elective per tax year; election via NJ PTE-100.",
                "Graduated rates: 5.675% / 6.52% / 9.12% / 10.9% on PTE "
                "income tiers.",
                "Owner-level BAIT credit is refundable with 20-year "
                "carryforward under P.L. 2021, c. 419.",
                "BAIT federal deductibility preserved under Notice 2020-75.",
            ],
            implementation_steps=[
                "Compute projected PTE NJ-sourced income for the year.",
                "Model federal benefit (BAIT paid × marginal rate) against "
                "owner-level BAIT credit utilization.",
                "File BAIT estimates quarterly; annual PTE-100 by 3/15 "
                "(following year).",
                "Coordinate with SSALT_NJ_RESIDENT_CREDIT to avoid "
                "double-credit claims on the same income.",
            ],
            risks_and_caveats=[
                "BAIT election is annual; missing the filing deadline "
                "forfeits the year's election.",
                "NJ resident credit rules interact with BAIT; verify "
                "owner's resident-state does not deny credit for BAIT paid.",
            ],
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_NJ_RESIDENT_CREDIT",
                "SSALT_NJ_TRUST_RESIDENCY",
                "SSALT_164_SALT_CAP",
            ],
            verification_confidence="high",
            computation_trace={"nj_pte_count": len(nj_pte)},
        )
