"""SSALT_PTET_MODELING — pass-through entity tax election modeling across states."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType, StateCode


_QUALIFIED_ENTITY_TYPES = {
    EntityType.S_CORP, EntityType.LLC_S_CORP,
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
}

# States with PTET regimes in scope for SMB CPA Group v1 (see spec §11)
_PTET_STATES = {
    StateCode.CA, StateCode.NY, StateCode.NJ, StateCode.MA,
    StateCode.VA, StateCode.CO,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_PTET_MODELING"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "IRS Notice 2020-75 — federal deductibility of state PTET at entity level",
        "IRC §164(b)(6) — SALT cap that PTET is designed to work around",
        "CA SB 132 (Ch. 17, Stats. 2025) — CA PTET 2026-2030 regime",
        "NY Tax Law §§ 860-866 — NY PTET",
        "NJ BAIT — N.J.S.A. 54A:12-1 et seq.",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        qualified_entities = [
            e for e in scenario.entities
            if e.type in _QUALIFIED_ENTITY_TYPES
            and (e.formation_state in _PTET_STATES
                 or any(s in _PTET_STATES for s in (e.operating_states or [])))
        ]
        if not qualified_entities:
            return self._not_applicable(
                "no qualified pass-through entity operating in a PTET-eligible "
                "state; PTET modeling requires a state-scoped election"
            )
        ptet_state_exposures = set()
        for e in qualified_entities:
            if e.formation_state in _PTET_STATES:
                ptet_state_exposures.add(e.formation_state)
            for s in (e.operating_states or []):
                if s in _PTET_STATES:
                    ptet_state_exposures.add(s)

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "entity qualified net income by state",
                "partner / shareholder state residency",
                "prior-year PTET credit carryforwards by state",
                "June 15 (CA) / March 15 (NY) / mirror dates per state",
                "owner consent mechanics per state (CA 3804, NY Web File)",
            ],
            assumptions=[
                "PTET election converts non-deductible individual SALT into "
                "deductible entity-level expense per Notice 2020-75.",
                "Federal benefit ≈ entity PTET paid × owner's marginal federal rate.",
                "State benefit: PTET credit against owner's state tax; usually "
                "dollar-for-dollar with state-specific carryforward rules.",
            ],
            implementation_steps=[
                "Identify every state where an eligible pass-through operates; "
                "compare PTET availability, rate, and timing.",
                "For each state, compute net federal saving (entity-level "
                "deduction at federal marginal rate) against PTET credit "
                "utilization at owner level.",
                "Confirm timing windows per state: CA June 15 (see "
                "CA_PTET_ELECTION), NY March 15 prepay / September 15 amended, "
                "NJ with return, MA with return.",
                "Coordinate with SSALT_164_SALT_CAP for individual-level "
                "cap position and SSALT_RESIDENT_CREDIT for resident credit "
                "optimization.",
            ],
            risks_and_caveats=[
                "PTET rules are state-by-state; composite filing may override "
                "PTET eligibility in some states.",
                "Nonresident-owner states may impose withholding obligations "
                "concurrent with PTET election — double-tracking required.",
                "Trust owners and tiered-partnership owners have state-"
                "specific eligibility constraints.",
            ],
            cross_strategy_impacts=[
                "CA_PTET_ELECTION",
                "SSALT_164_SALT_CAP",
                "SSALT_OBBBA_CAP_MODELING",
                "SSALT_RESIDENT_CREDIT",
                "SSALT_COMPOSITE_VS_WITHHOLD",
                "SSALT_NY_PTET",
                "SSALT_NJ_BAIT",
            ],
            verification_confidence="high",
            computation_trace={
                "qualified_entity_count": len(qualified_entities),
                "ptet_state_exposures": sorted(s.value for s in ptet_state_exposures),
            },
        )
