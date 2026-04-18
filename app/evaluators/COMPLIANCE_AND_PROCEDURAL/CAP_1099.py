"""CAP_1099 — 1099 reporting including 1099-K."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_1099"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6041 — information returns for $600+ payments",
        "IRC §6041A — independent contractor reporting",
        "IRC §6050W — 1099-K third-party network payments",
        "IRS Notice 2024-85 — 1099-K transition thresholds ($5K 2024, $2.5K 2025, $600 2026)",
        "IRC §6721 — information return penalties",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        operating = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.SOLE_PROP,
            )
        ]
        if not operating:
            return self._not_applicable(
                "no operating entity; 1099 reporting applies to payor entities"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "vendor payment log for the tax year ($600+ to non-corp payees)",
                "W-9 collection status per vendor",
                "1099-NEC vs 1099-MISC classification per payment type",
                "third-party network processor activity (for 1099-K reconciliation)",
            ],
            assumptions=[
                "1099-NEC: $600+ nonemployee compensation; file by January 31.",
                "1099-MISC: $600+ rents, royalties, other; file by February 28 "
                "(paper) or March 31 (e-file).",
                "1099-K threshold phases from $20K/200 transactions (pre-2024) "
                "to $600 (2026 per Notice 2024-85).",
                "Corporate payees are generally exempt (except attorneys).",
            ],
            implementation_steps=[
                "Collect Form W-9 from every vendor BEFORE first payment.",
                "Scrub payee list monthly against payment ledger to maintain "
                "current classification.",
                "File 1099-NEC by January 31 (e-file required if 10+ returns "
                "post-T.D. 9972).",
                "Reconcile 1099-K received against the same receipts on "
                "Schedule C / business return to avoid mismatched reporting.",
            ],
            risks_and_caveats=[
                "§6721 per-return penalties up to $310 / $630 (small) "
                "intentional; scale with number of returns.",
                "1099-K threshold creep requires recipient reporting of "
                "personal-use transactions; exclude non-business transactions "
                "via Schedule 1 Line 8u / 8v.",
                "Starting with 10+ returns, e-file is mandatory; paper filings "
                "bear penalties.",
            ],
            cross_strategy_impacts=[
                "CAP_BACKUP_WITHHOLDING",
                "CAP_W8_W9",
                "CAP_PAYROLL_REPORTING",
                "COMP_WORKER_CLASSIFICATION",
            ],
            verification_confidence="high",
        )
