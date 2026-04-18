"""SSALT_NY_MANSION_TAX — NY real estate transfer and mansion tax for
residential conveyances."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, AssetType, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NY_MANSION_TAX"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NY Tax Law §1402 — real estate transfer tax",
        "NY Tax Law §1402-a — NY mansion tax (progressive 1% to 3.9% in NYC)",
        "NYC Admin Code §11-2101 — NYC Real Property Transfer Tax",
        "NYC Admin Code §11-2102(c) — NYC additional base tax",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ny_residential = [
            a for a in scenario.assets
            if a.asset_type == AssetType.REAL_PROPERTY_RESIDENTIAL
            and a.location_state == StateCode.NY
        ]
        liquidity = scenario.planning.liquidity_event_planned
        if not ny_residential and (liquidity is None
                                   or liquidity.get("asset_state") != "NY"):
            return self._not_applicable(
                "no NY-situs residential real property and no NY-situs "
                "liquidity event; mansion tax is consideration-based on transfer"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "NY residential asset consideration at transfer",
                "buyer vs seller allocation in contract",
                "whether property is in NYC (progressive overlay) or "
                "other NY locality",
                "prior transfers within 24 months (aggregation risk)",
            ],
            assumptions=[
                "NY state mansion tax: 1% on residential consideration > $1M.",
                "NYC progressive additional tax layered on top: 0.25% at "
                "$2M, ramping to 2.9% at $25M+.",
                "Combined NYC + NY transfer tax on a $25M+ NYC residence "
                "can exceed 6% of consideration.",
            ],
            implementation_steps=[
                "Map residential properties to their locality-specific rate.",
                "For NYC transactions: evaluate use of a transfer of a "
                "controlling entity interest (§1402 still reaches economic "
                "transfers — not a simple workaround).",
                "Allocate mansion tax contractually (buyer vs seller) and "
                "document consideration clearly to avoid IRS/NY "
                "recharacterization.",
                "Coordinate with SSALT_TRANSFER_TAX (national view) and "
                "estate-planning transfers where tax may not apply.",
            ],
            risks_and_caveats=[
                "Gifting (nominal consideration) generally avoids mansion "
                "tax but may trigger federal gift tax — coordinate with "
                "estate-planning evaluators.",
                "NY has tightened the controlling-interest rules; transfers "
                "of > 50% of entity owning the property are reached.",
            ],
            cross_strategy_impacts=[
                "SSALT_TRANSFER_TAX",
                "SSALT_NYC_RESIDENT",
                "EST_GIFT_VALUATION",
                "EST_FAMILY_LIMITED_PARTNERSHIP",
            ],
            verification_confidence="high",
        )
