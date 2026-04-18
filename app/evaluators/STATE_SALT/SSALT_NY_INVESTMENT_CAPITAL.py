"""SSALT_NY_INVESTMENT_CAPITAL — NY franchise tax investment capital
classification to exclude investment income from apportionment base."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType, StateCode


_CORP_TYPES = {
    EntityType.C_CORP, EntityType.LLC_C_CORP,
    EntityType.S_CORP, EntityType.LLC_S_CORP,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NY_INVESTMENT_CAPITAL"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NY Tax Law §208.5 — investment capital definition (post-2015 reform)",
        "NY Tax Law §210 — franchise tax on business income",
        "TSB-M-15(8)C — investment capital identification requirements",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ny_corps = [
            e for e in scenario.entities
            if e.type in _CORP_TYPES
            and (e.formation_state == StateCode.NY
                 or StateCode.NY in (e.operating_states or []))
        ]
        if not ny_corps:
            return self._not_applicable(
                "no NY corporate entity; §208.5 investment-capital rules "
                "apply only to NY Article 9-A filers"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "investment asset list with holding period",
                "CUSIP-level identification tagged as investment within "
                "one year of acquisition (per TSB-M-15(8)C)",
                "prior-year investment capital schedule for consistency",
                "FMV and historical basis for each investment asset",
            ],
            assumptions=[
                "Investment capital income is EXCLUDED from NY business "
                "income (no tax on qualifying investment income).",
                "Qualifying requires: (a) stock held > 6 months, (b) not "
                "held for sale to customers, (c) tagged as investment "
                "capital within 1 year of acquisition.",
                "Mark-to-market securities dealers cannot classify as "
                "investment capital.",
            ],
            implementation_steps=[
                "Establish tagging protocol at acquisition; maintain ledger.",
                "For each quarter-end, reconcile investment-capital "
                "schedule to holdings.",
                "Exclude qualifying investment income from §210 business base.",
                "Document investment intent in board minutes and investment "
                "policy statement.",
            ],
            risks_and_caveats=[
                "Missing the 1-year tagging deadline disqualifies the asset "
                "for the holding period — non-curable.",
                "NY can reclassify as business capital on audit if trading "
                "activity suggests dealer status.",
            ],
            cross_strategy_impacts=[
                "SSALT_CONFORMITY_DECOUPLING",
                "SSALT_NY_PTET",
                "ENT_CCORP_DIV_CLAWBACK",
            ],
            verification_confidence="medium",
            computation_trace={"ny_corp_count": len(ny_corps)},
        )
