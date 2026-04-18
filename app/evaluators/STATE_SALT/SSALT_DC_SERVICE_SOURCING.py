"""SSALT_DC_SERVICE_SOURCING — DC sourcing of service income for
apportionment purposes."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_DC_SERVICE_SOURCING"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "D.C. Code §47-1810.02(d-1) — market-based sourcing for services",
        "27 DCMR §114 — apportionment regulations",
        "OTR Notice 2023-01 — market-based sourcing guidance",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        dc_touch = (
            scenario.identity.primary_state_domicile == StateCode.DC
            or any(
                e.formation_state == StateCode.DC
                or StateCode.DC in (e.operating_states or [])
                for e in scenario.entities
            )
        )
        if not dc_touch:
            return self._not_applicable(
                "no DC nexus; market-sourcing analysis is only relevant when "
                "DC has a claim to apportion receipts"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "service revenue by customer location",
                "customer billing addresses (proxy for benefit received)",
                "delivery / performance location by contract",
                "entity apportionment factor computation",
            ],
            assumptions=[
                "DC uses MARKET-BASED sourcing: service receipts are "
                "sourced to DC based on where the customer receives the "
                "benefit of the service.",
                "Default hierarchy: delivery location, then customer "
                "location of use, then customer billing address.",
                "Cost-of-performance is NOT the DC rule; relying on it "
                "overstates out-of-DC sourcing.",
            ],
            implementation_steps=[
                "Inventory service revenue by customer location.",
                "Apply DC sourcing hierarchy to each stream.",
                "Reconcile to prior-year apportionment factor; flag large "
                "shifts for audit preparation.",
                "Coordinate with SSALT_DC_UBFT apportionment if entity "
                "is unincorporated DC-nexus.",
            ],
            risks_and_caveats=[
                "Market-sourcing audits focus on customer-location "
                "substantiation; maintain contract + invoice records.",
                "Professional-services firms may underestimate DC nexus "
                "when billing goes through a non-DC parent but customer "
                "is in DC.",
            ],
            cross_strategy_impacts=[
                "SSALT_DC_UBFT",
                "SSALT_LOCAL_TAX_OVERLAYS",
                "SSALT_CONFORMITY_DECOUPLING",
            ],
            verification_confidence="medium",
        )
