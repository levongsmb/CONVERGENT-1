"""SALE_F_REORG — F reorganization pre-sale structuring.

An F reorganization converts a historic S corp into a holding
corporation (NewCo) owning the target as a Qualified Subchapter S
Subsidiary (Q-Sub). At closing, the buyer acquires 100% of the target
(now a Q-Sub) as a deemed asset purchase via the single-member
disregarded-entity regime, while the selling shareholders recognize
capital gain on stock of NewCo. The buyer gets the step-up; the seller
gets the capital-gain character. Rev. Rul. 2008-18 endorses this path.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SALE_F_REORG"
    CATEGORY_CODE = "SALE_TRANSACTION"
    PIN_CITES = [
        "IRC §368(a)(1)(F) — F reorganization mere change in form",
        "IRC §1361(b)(3) — Q-Sub election",
        "Rev. Rul. 2008-18 — F reorganization + Q-Sub pre-sale structure",
        "PLR 200836002 — F reorg followed by sale of Q-Sub",
        "Treas. Reg. §1.368-2(m) — F reorganization requirements",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        liquidity = scenario.planning.liquidity_event_planned
        if liquidity is None:
            return self._not_applicable(
                "no liquidity event planned; F reorganization is pre-sale "
                "structuring for a known transaction"
            )

        # Applicable when the target is an S corp
        scorp_targets = [
            e for e in scenario.entities
            if e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
        ]
        if not scorp_targets:
            return self._not_applicable(
                "no S corp target in scenario; F reorganization is S-corp-specific"
            )

        target = scorp_targets[0]
        proceeds_raw = liquidity.get("expected_proceeds")
        proceeds = Decimal(str(proceeds_raw)) if proceeds_raw is not None else Decimal(0)
        seller_basis = target.stock_basis or Decimal(0)
        gross_gain = max(proceeds - seller_basis, Decimal(0))

        # Simulated savings: F-reorg flip avoids the asset-sale recapture
        # drag on the seller side by converting the transaction to a stock
        # sale at the NewCo level while buyer acquires asset-basis via Q-Sub
        # disregarded regime. Proxy: 30% of gain avoids ordinary recapture
        # (37% rate) vs. capital (23.8% rate) differential.
        avoided_ordinary = gross_gain * Decimal("0.30")
        saving_vs_338h10 = (
            avoided_ordinary * (Decimal("0.37") - Decimal("0.238"))
        ).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=saving_vs_338h10,
            savings_by_tax_type=TaxImpact(federal_income_tax=saving_vs_338h10),
            inputs_required=[
                "S corp history (single historic entity or prior F reorganizations)",
                "buyer's preference for asset vs stock treatment",
                "existing shareholder debt and ownership structure",
                "state LLC conversion filing requirements (CA, DE)",
                "target close date (F reorg typically executed 30-60 days before close)",
            ],
            assumptions=[
                f"S corp target: {target.code} ({target.type.value})",
                f"Expected proceeds: ${proceeds:,.0f}",
                f"Seller stock basis: ${seller_basis:,.2f}",
                f"Gross gain on sale: ${gross_gain:,.2f}",
                f"Proxy 30% recapture component at ordinary 37%: "
                f"${avoided_ordinary:,.2f}",
                f"Estimated saving vs §338(h)(10) path: ${saving_vs_338h10:,.2f}",
            ],
            implementation_steps=[
                "Form NewCo as a new state corporation; elect S status "
                "(Form 2553).",
                "Merge historic S corp into NewCo (F reorganization under "
                "§368(a)(1)(F), Rev. Rul. 2008-18).",
                "File Q-Sub election (Form 8869) for the subsidiary "
                "(formerly the historic S corp).",
                "Convert the Q-Sub to an LLC via state filing so it is "
                "disregarded for federal tax purposes.",
                "Close the sale: buyer acquires 100% of the LLC interests "
                "(disregarded regime → deemed asset purchase for buyer "
                "with stepped-up basis; NewCo shareholders recognize capital "
                "gain).",
                "Retain F-reorg documentation: merger certificate, tax-free "
                "reorganization continuity-of-interest representations, "
                "business-purpose statement.",
            ],
            risks_and_caveats=[
                "Treas. Reg. §1.368-2(m) requires six F-reorg conditions. "
                "All must be satisfied; one common trap is the 'same assets' "
                "requirement in the new corporation.",
                "Buyer representations: buyer typically requires reps and "
                "warranties on the F-reorg execution and Q-Sub election to "
                "protect the asset-sale basis step-up.",
                "State conformity: confirm CA, DE, and any other state of "
                "operation conforms to the F-reorg treatment. CA uses "
                "federal S corporation rules but the LLC conversion "
                "requires separate CA filings.",
                "Pair with SALE_BASIS_CLEANUP before the F-reorg to ensure "
                "AAA / OAA / basis is clean; post-F-reorg is too late.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SALE_ASSET_VS_STOCK",
                "SALE_BASIS_CLEANUP",
                "SALE_338H10",
                "SALE_336E",
                "SALE_ROLLOVER_EQUITY",
                "SCSI_F_REORG_SALE",
                "MA_F_REORG",
            ],
            verification_confidence="medium",
            computation_trace={
                "target_entity_code": target.code,
                "expected_proceeds": str(proceeds),
                "seller_basis": str(seller_basis),
                "gross_gain": str(gross_gain),
                "proxy_recapture_portion_at_ordinary": str(avoided_ordinary),
                "estimated_saving_vs_338h10": str(saving_vs_338h10),
            },
        )
