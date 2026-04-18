"""CAP_NOTICE_2026_3 — estimated tax penalty relief for §1062 farmland
installment elections under IRS Notice 2026-3.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, AssetType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_NOTICE_2026_3"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "Notice 2026-3 (December 22, 2025) — §1062 estimated-tax penalty relief",
        "IRC §1062 as added by OBBBA — qualified farmland four-year installment",
        "IRC §6654 — individual estimated tax penalty",
        "IRC §6655 — corporate estimated tax penalty",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicable when scenario has farmland and a potential §1062 election
        farmland_candidates = [
            a for a in scenario.assets
            if a.asset_type == AssetType.REAL_PROPERTY_FARMLAND
        ]
        if not farmland_candidates:
            return self._not_applicable(
                "no farmland asset in scenario; Notice 2026-3 relief is §1062-specific"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "qualified farmland sale facts (buyer qualifies as qualified farmer)",
                "year of sale for the §1062 election",
                "estimated tax posture for the sale year",
            ],
            assumptions=[
                "Notice 2026-3 provides that only 25% of net tax "
                "liability attributable to the §1062 farmland sale is "
                "included in the §6654 / §6655 required annual payment "
                "for the sale year.",
                "This relief aligns estimated-tax obligations with the "
                "four-year installment payment schedule.",
            ],
            implementation_steps=[
                "Confirm §1062 election eligibility: qualified farmland, "
                "qualified farmer buyer, sale in taxable year after 2025-07-04.",
                "Compute estimated tax under Notice 2026-3 factor (25% of "
                "attributable net tax in required-annual-payment calc).",
                "Cite Notice 2026-3 on Form 2210 Part III if penalty is "
                "nonetheless assessed.",
            ],
            risks_and_caveats=[
                "Notice 2026-3 reduces penalty EXPOSURE but not the underlying "
                "tax obligation; installments 2-4 remain due on statutory "
                "dates per §1062.",
                "Notice may be superseded by final regulations; track IRS "
                "guidance on §1062 implementation.",
            ],
            cross_strategy_impacts=[
                "FRA_1062_FARMLAND_INSTALL",
                "FRA_NOTICE_2026_3",
                "CAP_EST_TAX_SAFE_HARBORS",
                "CAP_PENALTY_ABATEMENT",
            ],
            verification_confidence="high",
        )
