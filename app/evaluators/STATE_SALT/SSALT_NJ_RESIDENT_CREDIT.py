"""SSALT_NJ_RESIDENT_CREDIT — NJ resident credit optimization."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NJ_RESIDENT_CREDIT"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "N.J.S.A. 54A:4-1 — NJ resident credit for taxes paid other jurisdiction",
        "NJ Division of Taxation GIT-3W — credit for taxes paid to other states",
        "Tannenbaum v. Director, Division of Taxation, 21 N.J. Tax 372 (2004)",
        "P.L. 2021, c. 419 — aligned BAIT with resident credit rules",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        nj_resident = scenario.identity.primary_state_domicile == StateCode.NJ
        if not nj_resident:
            return self._not_applicable(
                "not a NJ resident; resident-credit optimization is a "
                "residence-state analysis"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "income sourced to non-NJ states and tax paid there",
                "NJ tax on the same income (resident-state tax)",
                "whether PTET was paid on the same income in other states",
                "prior-year NJ return to compare methodology year-over-year",
            ],
            assumptions=[
                "NJ resident credit is limited to LOWER of (a) other-state "
                "tax paid on the double-taxed income, or (b) NJ tax on "
                "that same income.",
                "Post-2021 law: NJ BAIT paid by an out-of-state entity "
                "on income of an NJ-resident owner generally qualifies "
                "for resident credit (fixing prior trap).",
                "NY convenience-rule income remains NY-sourced for NJ "
                "resident credit — NJ recognizes the NY sourcing.",
            ],
            implementation_steps=[
                "Compute the lesser-of cap per stream of multi-state income.",
                "For PTET states (NY, CA, MA): track owner's PTET credit "
                "and avoid double-counting.",
                "For convenience-rule income: claim NJ resident credit "
                "on NY-sourced wages per Tannenbaum framework.",
                "File NJ-1040 with Schedule NJ-COJ per income-source category.",
            ],
            risks_and_caveats=[
                "NJ historically denied resident credit for NY PTET; "
                "post-2021 rule correction applies but requires careful "
                "documentation of PTET paid at entity level.",
                "The lesser-of limit can produce zero credit when NJ "
                "rate exceeds the other state's.",
            ],
            cross_strategy_impacts=[
                "SSALT_RESIDENT_CREDIT",
                "SSALT_NJ_BAIT",
                "SSALT_NY_PTET",
                "SSALT_NY_CONVENIENCE_RULE",
            ],
            verification_confidence="high",
        )
