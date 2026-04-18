"""SSALT_NYC_RESIDENT — NYC resident personal income tax overlay."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NYC_RESIDENT"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NYC Admin Code §11-1701 — NYC resident personal income tax",
        "NY Tax Law §1304 — authority for NYC resident PIT",
        "Matter of Gaied v. New York State Tax Appeals Tribunal, "
        "22 N.Y.3d 592 (2014) — statutory residency test",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ny_domicile = scenario.identity.primary_state_domicile == StateCode.NY
        spouse_ny = scenario.identity.spouse_state_domicile == StateCode.NY
        if not (ny_domicile or spouse_ny):
            return self._not_applicable(
                "no NY domicile; NYC resident overlay requires NYC residency "
                "(domicile or 183-day statutory test)"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "days spent in NYC (for 183-day statutory residency test)",
                "permanent-place-of-abode status in NYC",
                "domicile-change documentation if planning to change",
                "trust residency if holding via trust",
            ],
            assumptions=[
                "NYC residency is independent of NY state residency — "
                "a NY state nonresident can be NYC statutory resident.",
                "Gaied requires that the permanent place of abode be "
                "actually USED by the taxpayer; pure ownership is insufficient.",
                "NYC top rate stacks on NY state top rate; combined can "
                "exceed 14.8% on high earners.",
            ],
            implementation_steps=[
                "Maintain day-count log and credible documentation "
                "(EZ-Pass, credit cards, flight records).",
                "For domicile change: execute the eight-factor test "
                "(home, business, family, time, near-and-dear, driver's "
                "license, vehicle, bank).",
                "Consider PTET to shift NYC-taxable income to entity level "
                "(see SSALT_NY_PTET).",
                "For trust-held NYC sourced income: evaluate resident trust "
                "vs nonresident trust filing.",
            ],
            risks_and_caveats=[
                "NY statutory-residency audits are aggressive; day-count "
                "mis-logging is the most common audit failure.",
                "NYC does not allow resident credit for tax paid to other "
                "states on NYC-taxable income — ironic but binding.",
            ],
            cross_strategy_impacts=[
                "SSALT_NY_PTET",
                "SSALT_NY_CONVENIENCE_RULE",
                "SSALT_RESIDENT_CREDIT",
                "SSALT_LOCAL_TAX_OVERLAYS",
            ],
            verification_confidence="medium",
        )
