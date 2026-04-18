"""SSALT_CONFORMITY_DECOUPLING — state conformity and decoupling analysis."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_CONFORMITY_DECOUPLING"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "CA R&TC §17024.5 — IRC conformity date (selective)",
        "CA decoupling from bonus depreciation (no conformity with §168(k))",
        "CA decoupling from §199A (no state QBI deduction)",
        "NY Tax Law §612 conformity adjustments",
        "State-by-state OBBBA conformity matrices (rolling vs static)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicable whenever taxpayer has state tax exposure (any state
        # liability in prior year or current-year sourcing).
        prior_state_tax = any(
            amt > 0 for amt in scenario.prior_year.total_state_tax_by_state.values()
        )
        if not prior_state_tax:
            return self._not_applicable(
                "no state tax exposure; conformity / decoupling analysis "
                "requires an active state filing posture"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "federal positions taken that may be decoupled at state level "
                "(bonus depreciation, §179, §163(j), §174A, §199A, §1202, §168(k))",
                "state conformity dates and rolling/static posture",
                "state-specific nonconformity schedules (CA Schedule CA, NY IT-225)",
                "basis tracking state-by-state for assets with bonus decoupling",
            ],
            assumptions=[
                "CA has permanent decoupling from §168(k) bonus depreciation; "
                "state basis > federal basis by bonus amount.",
                "CA does not allow §199A QBI deduction; add-back at state level.",
                "OBBBA provisions (§174A, §1202 tiered, §168(k) restoration, "
                "§164(b)(6) modifications) flow to states per each state's "
                "conformity statute — rolling states adopt automatically; "
                "static states require legislative update.",
            ],
            implementation_steps=[
                "Map every federal deduction / exclusion to the state "
                "conformity matrix for each state of filing.",
                "For nonconforming items: maintain separate state basis "
                "and tracking schedules (CA Schedule D-1 for §1031, etc.).",
                "Quantify state-level income pickup from decoupling "
                "(commonly material for CA on §168(k), §199A, §1202).",
                "Coordinate with SSALT_NOL_CREDIT_CARRYFWD for state NOL "
                "restatements driven by decoupling adjustments.",
            ],
            risks_and_caveats=[
                "State conformity lag can create retroactive adjustments "
                "when states adopt mid-year.",
                "CA §1202 decoupling is significant: CA recognizes 100% of "
                "QSBS gain that federal treats as excluded.",
            ],
            cross_strategy_impacts=[
                "SSALT_NOL_CREDIT_CARRYFWD",
                "SSALT_OBBBA_CAP_MODELING",
                "ENT_QSBS_DRIVEN",
                "AM_BONUS_DEPRECIATION",
            ],
            verification_confidence="high",
        )
