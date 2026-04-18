"""SSALT_RESIDENT_CREDIT — resident credit optimization for multi-state taxpayers."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_RESIDENT_CREDIT"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "State resident-credit statutes (CA R&TC §18001; NY Tax Law §620; NJ N.J.S.A. 54A:4-1)",
        "Wynne v. Maryland Comptroller, 575 U.S. 542 (2015) — dormant Commerce Clause limits",
        "FTB Publication 1031 — CA resident credit guidance",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        multi_state_income = any(
            (item.state_sourcing is not None and len(item.state_sourcing) > 1)
            for item in scenario.income.other_income
        )
        has_nonresident_tax = any(
            k1.state_pte_credit_attributable for k1 in scenario.income.k1_income
        )
        if not multi_state_income and not has_nonresident_tax:
            return self._not_applicable(
                "no multi-state income sourcing or nonresident PTE credit; "
                "resident credit analysis needs multi-state exposure"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "nonresident state tax paid and sourcing",
                "resident state tax on same income",
                "PTET credit coordination (can complicate or eliminate resident credit)",
                "state-specific credit computation rules",
            ],
            assumptions=[
                "Resident-state credit generally limited to LOWER of "
                "nonresident state tax actually paid OR resident-state tax "
                "on the same income.",
                "PTET paid at the entity level may or may not qualify for "
                "resident credit depending on state (CA explicitly treats "
                "PTET-credit-claimed income as ineligible for further resident "
                "credit on same income stream).",
                "Post-Wynne, states must grant resident credit on nonresident "
                "income tax to avoid discrimination.",
            ],
            implementation_steps=[
                "Compute nonresident-state tax actually paid on each out-of-"
                "state income stream.",
                "Compute resident-state tax attributable to the same income.",
                "Apply resident-state statutory limit to determine credit.",
                "Coordinate with PTET elections — PTET credit at owner level "
                "and resident credit are mutually exclusive for the same "
                "income in most states.",
            ],
            risks_and_caveats=[
                "Common trap: claiming both PTET credit (from other state) "
                "AND resident credit on the same income at the resident "
                "level — states are tightening enforcement.",
                "Composite return participation can forfeit resident credit.",
            ],
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_COMPOSITE_VS_WITHHOLD",
                "SSALT_NONRESIDENT_WH",
                "SSALT_NJ_RESIDENT_CREDIT",
            ],
            verification_confidence="high",
        )
