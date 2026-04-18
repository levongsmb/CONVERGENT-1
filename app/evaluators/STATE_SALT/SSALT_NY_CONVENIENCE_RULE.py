"""SSALT_NY_CONVENIENCE_RULE — NY convenience of employer rule for
nonresident remote workers."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NY_CONVENIENCE_RULE"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "20 NYCRR §132.18(a) — NY convenience of employer rule",
        "TSB-M-06(5)I — NY guidance on convenience rule",
        "Zelinsky v. Tax Appeals Tribunal, 1 N.Y.3d 85 (2003) — upheld the rule",
        "Huckaby v. New York State Div. of Tax Appeals, 4 N.Y.3d 427 (2005)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        wages = scenario.income.wages_primary + scenario.income.wages_spouse
        ny_domicile = scenario.identity.primary_state_domicile == StateCode.NY
        if wages <= Decimal(0):
            return self._not_applicable(
                "no W-2 wages; convenience rule applies to wages sourced "
                "to NY for remote employment"
            )
        if ny_domicile:
            return self._not_applicable(
                "NY resident; NY convenience rule targets NONRESIDENT "
                "employees working remotely for NY employers"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "employer's office state (is it NY?)",
                "number of days physically worked in NY vs remote",
                "whether remote work is for employer necessity vs convenience",
                "prior-year filings establishing remote-work pattern",
            ],
            assumptions=[
                "If employer is NY-based and remote work is for employee "
                "convenience (not employer necessity), NY sources 100% of "
                "wages to NY regardless of physical presence.",
                "Exception: bona fide employer office in another state "
                "that satisfies the 10-factor test shifts sourcing.",
                "Resident-state credit may not fully offset NY tax on the "
                "same wages, creating double taxation.",
            ],
            implementation_steps=[
                "Document employer necessity justification (bona fide "
                "branch office, employer requirement, client meeting logs).",
                "For taxpayers with remote flexibility, consider a formal "
                "reassignment to a bona fide non-NY office satisfying the "
                "10-factor test.",
                "Track days actually worked in NY; file NY IT-203 "
                "(nonresident) with appropriate allocation.",
                "Coordinate with resident-state credit for partial relief.",
            ],
            risks_and_caveats=[
                "CT and PA grant reverse credit on NY-sourced wages; other "
                "states may not fully credit, causing double tax.",
                "Connecticut adopted its own convenience rule effective 2024 "
                "mirroring NY — check resident state's reciprocal treatment.",
            ],
            cross_strategy_impacts=[
                "SSALT_RESIDENT_CREDIT",
                "SSALT_NYC_RESIDENT",
                "SSALT_NONRESIDENT_WH",
            ],
            verification_confidence="high",
        )
