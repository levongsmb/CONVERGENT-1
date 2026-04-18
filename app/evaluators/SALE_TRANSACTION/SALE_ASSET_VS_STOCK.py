"""SALE_ASSET_VS_STOCK — asset sale vs stock sale comparison.

Buyer preference is generally an asset sale (stepped-up basis on
acquired assets, §338 elections mimic the same). Seller preference is
generally a stock sale (single-layer tax for C corps, capital gain
character across the board for pass-throughs). For S corps, §338(h)(10)
or §336(e) elections can produce an asset-sale result for buyer while
preserving a single-layer tax for seller-shareholders.

The evaluator surfaces the swing dollar for a planned liquidity event
given proceeds and existing basis.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SALE_ASSET_VS_STOCK"
    CATEGORY_CODE = "SALE_TRANSACTION"
    PIN_CITES = [
        "IRC §338(h)(10) — deemed asset sale for QSP of S corp / subsidiary",
        "IRC §336(e) — deemed asset sale for qualified stock disposition",
        "IRC §1060 — residual-method allocation on asset sale",
        "IRC §1221 — capital asset definition",
        "IRC §1245 / §1250 — depreciation recapture on asset sale",
        "Rev. Rul. 2008-18 — F reorganization facilitates stock-sale structure",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        liquidity = scenario.planning.liquidity_event_planned
        if liquidity is None:
            return self._not_applicable(
                "no liquidity event planned; asset-vs-stock analysis requires "
                "a planned transaction"
            )

        proceeds_raw = liquidity.get("expected_proceeds")
        if proceeds_raw is None:
            return self._not_applicable(
                "liquidity_event_planned lacks expected_proceeds; cannot "
                "quantify the asset-vs-stock swing"
            )
        proceeds = Decimal(str(proceeds_raw))

        # Identify the target entity and its character (S corp vs C corp vs partnership)
        targets = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
            )
        ]
        if not targets:
            return self._not_applicable(
                "no operating entity suitable as a sale target in scenario"
            )

        # Use first target as the primary (orchestrator refines with
        # transaction-specific entity identification)
        target = targets[0]

        # Outside basis / stock basis for seller's tax
        seller_basis = target.stock_basis or target.outside_basis or Decimal(0)
        gross_gain = proceeds - seller_basis

        is_s_corp = target.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
        is_c_corp = target.type in (EntityType.C_CORP, EntityType.LLC_C_CORP)
        is_partnership = target.type in (
            EntityType.PARTNERSHIP,
            EntityType.LLC_PARTNERSHIP,
        )

        # Approximate tax under each structure
        ltcg_rate = Decimal("0.238")  # 20% + 3.8% NIIT on S corp / partnership gain
        ordinary_rate = Decimal("0.37")

        if is_c_corp:
            # Asset sale: entity tax 21% + shareholder LTCG on after-tax proceeds
            entity_tax = gross_gain * Decimal("0.21")
            after_entity = proceeds - entity_tax
            shareholder_gain = after_entity - seller_basis
            asset_sale_total = entity_tax + (shareholder_gain * ltcg_rate)
            # Stock sale: single-layer LTCG
            stock_sale_total = gross_gain * ltcg_rate
            swing = (asset_sale_total - stock_sale_total).quantize(Decimal("0.01"))
            narrative = "C_CORP_DOUBLE_TAX_ON_ASSET_SALE"
        elif is_s_corp:
            # Asset sale with §338(h)(10): ordinary recapture on §1245 components
            # + capital gain on other assets; assume 30% of gain is ordinary
            # recapture as a planning proxy
            ordinary_portion = gross_gain * Decimal("0.30")
            capital_portion = gross_gain - ordinary_portion
            asset_sale_total = (ordinary_portion * ordinary_rate) + (capital_portion * ltcg_rate)
            stock_sale_total = gross_gain * ltcg_rate
            swing = (asset_sale_total - stock_sale_total).quantize(Decimal("0.01"))
            narrative = "S_CORP_338_RECAPTURE_EXPOSURE"
        else:  # partnership
            # Partnership asset sale: §751 hot-asset ordinary + capital balance.
            # Stock-sale-equivalent is interest sale at capital-gain rate with
            # §751(a) ordinary portion on hot assets. Net is similar.
            ordinary_portion = gross_gain * Decimal("0.15")
            capital_portion = gross_gain - ordinary_portion
            asset_sale_total = (ordinary_portion * ordinary_rate) + (capital_portion * ltcg_rate)
            stock_sale_total = (ordinary_portion * ordinary_rate) + (capital_portion * ltcg_rate)
            swing = Decimal(0)
            narrative = "PARTNERSHIP_751_HOT_ASSET_EQUIVALENCE"

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=abs(swing),
            savings_by_tax_type=TaxImpact(
                federal_income_tax=abs(swing),
            ),
            inputs_required=[
                "buyer's preferred structure (usually asset) vs seller's preferred (usually stock)",
                "§1060 purchase-price allocation across goodwill, intangibles, hot assets",
                "§1245 and §1250 recapture components at seller level",
                "§338(h)(10) or §336(e) election facts and availability",
                "§754 election posture for partnership targets",
            ],
            assumptions=[
                f"Entity type: {target.type.value}",
                f"Expected proceeds: ${proceeds:,.0f}",
                f"Seller basis (stock or outside): ${seller_basis:,.2f}",
                f"Gross gain: ${gross_gain:,.2f}",
                f"Narrative tag: {narrative}",
                f"Illustrative asset-sale total tax: ${asset_sale_total:,.2f}",
                f"Illustrative stock-sale total tax: ${stock_sale_total:,.2f}",
                f"Swing (asset − stock): ${swing:,.2f}",
            ],
            implementation_steps=[
                "Commission a §1060 purchase-price allocation analysis "
                "from a valuation specialist to quantify recapture.",
                "For S corp: evaluate §338(h)(10) / §336(e) election availability "
                "(QSP requirement, buyer consent). Run F-reorganization "
                "(SALE_F_REORG) as a parallel structure giving buyer a step-up "
                "via Q-Sub election at close.",
                "For C corp: model rollover equity (SALE_ROLLOVER_EQUITY) to "
                "defer a portion of the seller's gain into new acquirer stock.",
                "For partnership: §754 election is baseline; §743(b) step-up "
                "at buyer's level with no shift in seller character.",
                "Coordinate with SALE_BASIS_CLEANUP, SALE_EARNOUTS, and the "
                "installment-note evaluators.",
            ],
            risks_and_caveats=[
                "Swing figures here are first-order proxies — use a deal model "
                "with actual §1060 allocation, §1245 / §1250 component detail, "
                "working-capital true-up, and escrow holdbacks.",
                "§338(h)(10): buyer gets an ordinary asset-sale treatment; "
                "seller loses capital character on depreciation recapture "
                "and is taxed on the stepped-up asset sale at entity-level "
                "gain character. Seller usually requires price premium.",
                "State tax: CA does not conform to all federal deal-structure "
                "elections; model CA separately.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SALE_F_REORG",
                "SALE_BASIS_CLEANUP",
                "SALE_338H10",
                "SALE_336E",
                "SALE_ROLLOVER_EQUITY",
                "SALE_EARNOUTS",
                "SALE_INSTALLMENT",
                "INST_STANDARD_453",
                "PS_751_HOT_ASSETS",
            ],
            verification_confidence="medium",
            computation_trace={
                "target_entity_code": target.code,
                "target_entity_type": target.type.value,
                "expected_proceeds": str(proceeds),
                "seller_basis": str(seller_basis),
                "gross_gain": str(gross_gain),
                "asset_sale_total_tax": str(asset_sale_total),
                "stock_sale_total_tax": str(stock_sale_total),
                "swing_asset_minus_stock": str(swing),
                "narrative": narrative,
            },
        )
