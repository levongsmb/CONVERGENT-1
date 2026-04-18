"""SSALT_NY_PTET — New York pass-through entity tax specifics."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType, StateCode


_PTE_TYPES = {
    EntityType.S_CORP, EntityType.LLC_S_CORP,
    EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NY_PTET"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NY Tax Law §§860-866 — NY PTET",
        "NY Tax Law §867 — NYC PTET (separate election)",
        "TSB-M-21(1)C, (1)I — NY PTET guidance",
        "IRS Notice 2020-75 — federal deductibility",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ny_pte = [
            e for e in scenario.entities
            if e.type in _PTE_TYPES
            and (e.formation_state == StateCode.NY
                 or StateCode.NY in (e.operating_states or []))
        ]
        if not ny_pte:
            return self._not_applicable(
                "no NY-sourced pass-through entity; NY PTET requires NY "
                "formation or NY-sourced income"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "NY-sourced PTE taxable income",
                "partner / shareholder residency (resident vs nonresident)",
                "prior NY PTET credit carryforward at owner level",
                "NYC PTET election consideration (separate election)",
            ],
            assumptions=[
                "NY PTET election must be made by March 15 of the tax year "
                "(not the return date).",
                "For electing resident S-corps, 100% of income is included; "
                "nonresident S-corps apportion per NY-source rules.",
                "NYC PTET is separate and additive; election required "
                "separately for NYC benefit.",
                "Graduated rate: 6.85% / 9.65% / 10.3% / 10.9%.",
            ],
            implementation_steps=[
                "File NY PTET election via NY Web File by 3/15/YYYY (no "
                "extension) — missed deadline forfeits the year.",
                "If NYC-resident owners exist, file separate NYC PTET election "
                "under NY Tax Law §867.",
                "Make estimated PTET payments quarterly; final payment by "
                "return due date (3/15 for calendar year).",
                "Coordinate with SSALT_PTET_MODELING (federal benefit) and "
                "SSALT_RESIDENT_CREDIT (owner's resident state treatment).",
            ],
            risks_and_caveats=[
                "NY PTET election is IRREVOCABLE for the tax year once filed.",
                "Missed 3/15 election window cannot be cured; plan in "
                "December prior year.",
                "NY PTET credit is refundable for owners but counts as "
                "taxable federal income in the year of refund.",
            ],
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_NYC_RESIDENT",
                "SSALT_RESIDENT_CREDIT",
                "SSALT_164_SALT_CAP",
            ],
            verification_confidence="high",
            computation_trace={"ny_pte_count": len(ny_pte)},
        )
