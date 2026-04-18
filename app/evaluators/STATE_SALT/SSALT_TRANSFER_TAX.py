"""SSALT_TRANSFER_TAX — state/local real estate transfer, mansion,
and documentary stamp tax planning."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, AssetType


_REAL_PROPERTY_TYPES = {
    AssetType.REAL_PROPERTY_RESIDENTIAL,
    AssetType.REAL_PROPERTY_COMMERCIAL,
    AssetType.REAL_PROPERTY_LAND,
    AssetType.REAL_PROPERTY_FARMLAND,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_TRANSFER_TAX"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NY Tax Law §1402 — NY real estate transfer tax",
        "NY Tax Law §1402-a — NY mansion tax (1% > $1M, progressive to 3.9%)",
        "CA R&TC §11911 et seq. — CA documentary transfer tax",
        "LA Measure ULA — LA mansion tax on sales > $5M (4%) / > $10M (5.5%)",
        "NJ mansion tax N.J.S.A. 46:15-7.2 (1% > $1M)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        real_property_assets = [
            a for a in scenario.assets if a.asset_type in _REAL_PROPERTY_TYPES
        ]
        liquidity = scenario.planning.liquidity_event_planned
        if not real_property_assets and liquidity is None:
            return self._not_applicable(
                "no real property assets and no liquidity event; "
                "transfer-tax planning needs a transfer event"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "each real property: location, FMV, basis, encumbrances",
                "projected sale price and sale date",
                "buyer / seller allocation of transfer tax",
                "availability of controlling-interest transfer rules as workaround",
            ],
            assumptions=[
                "NY mansion tax is progressive above $1M residential; "
                "up to 3.9% at > $25M in NYC.",
                "LA Measure ULA applies 4% > $5M and 5.5% > $10M "
                "on LA City properties (affects Burbank/LA metro).",
                "Transfer tax base is typically CONSIDERATION, not FMV; "
                "planning around installment or contingent consideration "
                "may defer but rarely eliminates the tax.",
            ],
            implementation_steps=[
                "Survey every property by location; map to local transfer "
                "tax rates and any mansion-tax thresholds.",
                "For transfers among entities / family: evaluate "
                "controlling-interest transfer exemptions.",
                "Evaluate timing vs mansion-tax rate change windows.",
                "For LA properties > $5M: model Measure ULA impact BEFORE "
                "listing decision.",
            ],
            risks_and_caveats=[
                "NY and NJ also impose tax on transfers of controlling "
                "entity interests — stock sales do not always avoid transfer tax.",
                "Some states (NC, VA) impose documentary stamps on DEEDS OF "
                "TRUST (mortgages), not just transfers — tracking is easily missed.",
            ],
            cross_strategy_impacts=[
                "SSALT_NY_MANSION_TAX",
                "SSALT_SALES_USE_EXPOSURE",
                "SALE_M_AND_A_STRUCTURING",
                "EST_GIFT_VALUATION",
            ],
            verification_confidence="medium",
        )
