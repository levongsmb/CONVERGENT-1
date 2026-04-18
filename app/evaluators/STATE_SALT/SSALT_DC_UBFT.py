"""SSALT_DC_UBFT — DC Unincorporated Business Franchise Tax."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType, StateCode


_UBFT_EXPOSED_TYPES = {
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
    EntityType.LLC_DISREGARDED, EntityType.SOLE_PROP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_DC_UBFT"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "D.C. Code §47-1808.01 et seq. — DC Unincorporated Business Franchise Tax",
        "D.C. Code §47-1808.03 — UBFT personal services exception",
        "D.C. Code §47-1810.02 — apportionment",
        "OTR Notice 2025-series — current UBFT guidance",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        dc_unincorporated = [
            e for e in scenario.entities
            if e.type in _UBFT_EXPOSED_TYPES
            and (e.formation_state == StateCode.DC
                 or StateCode.DC in (e.operating_states or []))
        ]
        if not dc_unincorporated:
            return self._not_applicable(
                "no DC unincorporated business; UBFT applies only to DC-nexus "
                "partnerships, LLCs taxed as partnerships, disregarded entities, "
                "and sole proprietorships"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "DC gross receipts of each exposed entity",
                "apportionment factors (sales, payroll, property)",
                "analysis of personal-services exception under §47-1808.03 "
                "(80% personal-services income threshold)",
                "DC NOL and credit carryforwards at entity level",
            ],
            assumptions=[
                "UBFT is 8.25% of apportioned DC taxable income of the "
                "unincorporated business.",
                "Personal-services exception: if > 80% of gross income is "
                "from personal services of the members and capital is NOT "
                "a material income-producing factor, UBFT does not apply.",
                "UBFT is a tax on the entity; DC still taxes the individual "
                "owners on distributive share (partial double tax).",
            ],
            implementation_steps=[
                "For each exposed entity, compute DC-apportioned income.",
                "Test personal-services exception and document compliance "
                "(partner services, capital role, billing patterns).",
                "File DC Form D-30 if exception fails.",
                "Coordinate with DC individual income tax (D-40) to align "
                "owner distributive share with entity filing.",
            ],
            risks_and_caveats=[
                "Personal-services exception is fact-intensive and audited "
                "on close examination of capital role.",
                "DC does not honor PTET-type elections; UBFT is not a PTET "
                "and does not benefit from Notice 2020-75 entity-level "
                "federal deductibility argument.",
            ],
            cross_strategy_impacts=[
                "SSALT_DC_SERVICE_SOURCING",
                "SSALT_PTET_MODELING",
                "SSALT_LOCAL_TAX_OVERLAYS",
            ],
            verification_confidence="high",
        )
