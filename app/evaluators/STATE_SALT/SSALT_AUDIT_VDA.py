"""SSALT_AUDIT_VDA — state audit defense and voluntary disclosure agreements."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_AUDIT_VDA"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "Multistate Tax Commission National Nexus Program (NNP VDA)",
        "CA FTB Voluntary Disclosure Program — CA R&TC §19191",
        "NY Voluntary Disclosure and Compliance Program — NY Tax Law §1700",
        "Streamlined Sales and Use Tax Agreement — SSUTA Member VDA protocol",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_multi_state_business = any(
            len(set((e.operating_states or []) + [e.formation_state])) > 1
            for e in scenario.entities
        )
        has_multi_state_activity = any(
            item.state_sourcing is not None and len(item.state_sourcing) > 0
            for item in scenario.income.other_income
        )
        if not (scenario.entities or has_multi_state_activity):
            return self._not_applicable(
                "no multi-state business or activity; VDA analysis "
                "requires an exposure inventory"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "state-by-state nexus inventory (income, sales/use, franchise)",
                "back-years of potential exposure (typically 3-7)",
                "whether taxpayer has been contacted by any state",
                "planned restructurings that might trigger state attention",
            ],
            assumptions=[
                "VDA programs typically limit lookback (3-4 years) and "
                "waive penalty; interest usually still accrues.",
                "MTC National Nexus Program (NNP) offers multi-state VDA "
                "through a single coordinated submission.",
                "Post-contact voluntary disclosure is usually unavailable; "
                "anonymous pre-clearance is critical.",
            ],
            implementation_steps=[
                "Compile exposure quantification for each state / tax type.",
                "Prioritize states by exposure magnitude and VDA "
                "favorability (MTC member vs bilateral).",
                "Submit anonymous pre-clearance via advisor; negotiate "
                "lookback and penalty waiver before disclosing identity.",
                "For audits in progress: pivot to audit defense, including "
                "§6501-parallel state SOL defenses and apportionment challenges.",
            ],
            risks_and_caveats=[
                "VDA protection is program-specific; a signed VDA in State A "
                "does NOT bind State B.",
                "Voluntary payment without VDA does not waive penalty; "
                "always pursue formal agreement when lookback > statutory.",
            ],
            cross_strategy_impacts=[
                "SSALT_SALES_USE_EXPOSURE",
                "CAP_STATUTE_MGMT",
                "CAP_PENALTY_ABATEMENT",
                "SALE_M_AND_A_STRUCTURING",
            ],
            verification_confidence="medium",
            computation_trace={
                "multi_state_business": has_multi_state_business,
            },
        )
