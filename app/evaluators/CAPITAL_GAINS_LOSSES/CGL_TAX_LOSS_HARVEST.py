"""CGL_TAX_LOSS_HARVEST — tax-loss harvesting.

Identifies unrealized losses in taxable accounts that can offset
current-year realized gains (or carry forward at $3K/year against
ordinary income). The scenario schema models asset FMV and cost basis
per lot, allowing direct identification of harvest candidates.

Not in scope: specific-lot identification inside brokerage accounts
(requires custodian integration). The evaluator produces candidate
lots and dollar-at-risk identification.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
from typing import List

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario


_TAXABLE_SECURITY_TYPES = {
    AssetType.STOCK_PUBLIC,
    AssetType.STOCK_PRIVATE,
    AssetType.CRYPTO,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CGL_TAX_LOSS_HARVEST"
    CATEGORY_CODE = "CAPITAL_GAINS_LOSSES"
    PIN_CITES = [
        "IRC §1211 — limitation on capital losses",
        "IRC §1212 — capital loss carryover (indefinite for individuals)",
        "IRC §1091 — wash-sale rule (30-day window)",
        "IRC §1222 — short- vs long-term characterization",
        "Treas. Reg. §1.1012-1 — specific-lot identification",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        taxable_lots = [
            a for a in scenario.assets
            if a.asset_type in _TAXABLE_SECURITY_TYPES
            and a.fmv is not None
            and a.adjusted_basis is not None
        ]
        if not taxable_lots:
            return self._not_applicable(
                "no taxable securities with FMV + basis data in scenario; "
                "tax-loss harvesting requires per-lot cost basis visibility"
            )

        unrealized_losses: List[dict] = []
        total_unrealized_loss = Decimal(0)
        for lot in taxable_lots:
            gain = lot.fmv - lot.adjusted_basis
            if gain < Decimal(0):
                unrealized_losses.append({
                    "asset_code": lot.asset_code,
                    "description": lot.description,
                    "basis": str(lot.adjusted_basis),
                    "fmv": str(lot.fmv),
                    "loss": str(-gain),
                })
                total_unrealized_loss += -gain

        if total_unrealized_loss == Decimal(0):
            return self._not_applicable(
                "all taxable securities in scenario are at or above basis; "
                "no harvestable losses"
            )

        # Realized gains on current year
        realized_st_gain = scenario.income.capital_gains_short_term
        realized_lt_gain = scenario.income.capital_gains_long_term
        total_realized_gains = realized_st_gain + realized_lt_gain
        carryover_st = scenario.prior_year.capital_loss_carryforward_short_term
        carryover_lt = scenario.prior_year.capital_loss_carryforward_long_term
        total_existing_carryover = carryover_st + carryover_lt

        # Rough fed savings: assume harvested loss offsets LT gain at 23.8%
        # (20% LTCG + 3.8% NIIT) up to realized LT; any excess offsets $3K
        # ordinary at 32% marginal; rest banks as carryover (no current saving).
        offset_against_lt = min(total_unrealized_loss, realized_lt_gain)
        ordinary_offset_cap = Decimal("3000")
        remaining = total_unrealized_loss - offset_against_lt
        offset_ordinary = min(remaining, ordinary_offset_cap)

        saving_on_lt = offset_against_lt * Decimal("0.238")
        saving_on_ordinary = offset_ordinary * Decimal("0.32")
        headline_save = (saving_on_lt + saving_on_ordinary).quantize(Decimal("0.01"))
        deferred_loss = (
            total_unrealized_loss - offset_against_lt - offset_ordinary
        ).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=headline_save,
            savings_by_tax_type=TaxImpact(
                capital_gains_tax=saving_on_lt.quantize(Decimal("0.01")),
                federal_income_tax=saving_on_ordinary.quantize(Decimal("0.01")),
            ),
            inputs_required=[
                "per-lot cost basis (already populated in scenario schema)",
                "custodian position data for wash-sale window",
                "identified replacement positions (or 31-day wait strategy)",
                "realized gains already booked year-to-date",
            ],
            assumptions=[
                f"Unrealized losses identified: {len(unrealized_losses)}",
                f"Aggregate unrealized loss: ${total_unrealized_loss:,.2f}",
                f"Current-year realized LT gain: ${realized_lt_gain:,.2f}",
                f"Current-year realized ST gain: ${realized_st_gain:,.2f}",
                f"Existing capital-loss carryover (ST+LT): ${total_existing_carryover:,.2f}",
                f"LT-offset rate assumed: 23.8% (20% + 3.8% NIIT)",
                f"Ordinary-offset cap: ${ordinary_offset_cap:,.0f} × 32%",
                f"Loss banked to future carryover: ${deferred_loss:,.2f}",
            ],
            implementation_steps=[
                "Request custodian transaction file for past 30 days and the "
                "upcoming 30 days to identify wash-sale exposure.",
                "Select replacement security that is not 'substantially "
                "identical' under §1091 (broad index fund, different ETF "
                "issuer / methodology, or 31+ day wait).",
                "Execute the sell + replacement buy in the same trading day "
                "to minimize market exposure.",
                "Document specific-lot identification under Treas. Reg. "
                "§1.1012-1; issue written identification to custodian by "
                "trade settlement.",
                "Harvest before year-end; cash-basis accounting applies to "
                "securities but the trade-date rule under §453(g) timing "
                "requirements locks the loss in the settlement year.",
            ],
            risks_and_caveats=[
                "§1091 wash-sale: disallows the loss if a substantially "
                "identical security is purchased within 30 days before OR "
                "after the sale. The disallowed loss is added to the basis "
                "of the replacement security (deferred, not lost).",
                "IRA / 401(k) account purchases trigger wash-sale disallowance "
                "per Rev. Rul. 2008-5; the disallowed loss is permanently lost.",
                "Spouse's trades (MFJ) are attributed to the taxpayer for "
                "wash-sale purposes.",
                "Short-term losses are more valuable than long-term losses "
                "because they offset ordinary income at the top marginal rate "
                "(via §1211 ordering). Consider harvesting ST lots first.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CGL_WASH_SALES",
                "CGL_CARRYFORWARDS",
                "CGL_NETTING",
                "CGL_DIRECT_INDEXING",
                "NIIT_CAP_GAIN_HARVEST",
            ],
            verification_confidence="high",
            computation_trace={
                "unrealized_losses": unrealized_losses,
                "total_unrealized_loss": str(total_unrealized_loss),
                "realized_lt_gain": str(realized_lt_gain),
                "realized_st_gain": str(realized_st_gain),
                "existing_carryover_total": str(total_existing_carryover),
                "offset_against_lt": str(offset_against_lt),
                "offset_against_ordinary": str(offset_ordinary),
                "deferred_loss_to_carryforward": str(deferred_loss),
                "saving_on_lt": str(saving_on_lt.quantize(Decimal("0.01"))),
                "saving_on_ordinary": str(saving_on_ordinary.quantize(Decimal("0.01"))),
            },
        )
