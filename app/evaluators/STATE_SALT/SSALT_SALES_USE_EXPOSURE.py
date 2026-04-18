"""SSALT_SALES_USE_EXPOSURE — sales and use tax exposure from restructuring."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_SALES_USE_EXPOSURE"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "South Dakota v. Wayfair, Inc., 585 U.S. 162 (2018) — economic nexus",
        "Streamlined Sales and Use Tax Agreement — conformity framework",
        "CA R&TC §6203 — CA use tax on remote sales",
        "State occasional-sale and bulk-sale exemptions (state-by-state)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_business = bool(scenario.entities)
        liquidity_event = scenario.planning.liquidity_event_planned
        if not has_business and liquidity_event is None:
            return self._not_applicable(
                "no operating business and no liquidity event; "
                "sales/use exposure is a business / restructuring risk"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "current sales/use nexus map (economic and physical)",
                "registration status per state",
                "contemplated restructuring / asset sale structure",
                "states with occasional-sale or bulk-sale exemptions",
            ],
            assumptions=[
                "Post-Wayfair, most states impose economic-nexus thresholds "
                "($100K-$500K sales or 200 transactions).",
                "Asset sales of an operating business often trigger bulk-"
                "sales-tax exposure UNLESS occasional-sale exemption applies.",
                "Stock / equity sales generally avoid sales-tax exposure but "
                "may trigger transfer tax (see SSALT_TRANSFER_TAX).",
            ],
            implementation_steps=[
                "Perform nexus review for all states with material receipts.",
                "For any planned asset sale: secure bulk-sale certificate / "
                "occasional-sale exemption documentation BEFORE closing.",
                "Quantify unregistered-state exposure and consider "
                "voluntary disclosure (see SSALT_AUDIT_VDA).",
                "Coordinate registration, collection, and remittance "
                "for any newly crossed threshold.",
            ],
            risks_and_caveats=[
                "Buyers routinely demand successor-liability protection; "
                "seller must clear pre-closing exposure via bulk-sale "
                "notice or escrow holdback.",
                "Retroactive registration attracts penalty + interest; "
                "VDA windows are state-specific and time-limited.",
            ],
            cross_strategy_impacts=[
                "SSALT_AUDIT_VDA",
                "SSALT_TRANSFER_TAX",
                "SALE_M_AND_A_STRUCTURING",
            ],
            verification_confidence="medium",
        )
