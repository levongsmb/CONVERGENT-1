"""SALE_BASIS_CLEANUP — pre-sale basis, AAA, and shareholder-account cleanup.

In the 1-2 years before a planned liquidity event, clean up:
  - Shareholder loans (documentation, AFR interest, repayment vs contribution).
  - AAA / OAA / E&P balances for S corps (distribute AAA before close to
    reduce stock basis and increase stock gain at LT vs ordinary).
  - Suspended losses under §1366(d) / §704(d) basis limitations.
  - Post-termination transition period (PTTP) distributions for S corp
    conversions to C.
  - §754 / §743(b) election posture for partnership targets.
  - §263A and §471(c) method postures that buyer due diligence will surface.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SALE_BASIS_CLEANUP"
    CATEGORY_CODE = "SALE_TRANSACTION"
    PIN_CITES = [
        "IRC §1366(d) — S corp shareholder basis limitation on losses",
        "IRC §1368 — S corp distribution ordering",
        "IRC §1371(e) — post-termination transition period",
        "IRC §704(d) — partner basis limitation",
        "IRC §754 — partnership basis adjustment election",
        "IRC §743(b) — transferee basis adjustment",
        "IRC §7872 — below-market loans (AFR on shareholder loans)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        liquidity = scenario.planning.liquidity_event_planned
        if liquidity is None:
            return self._not_applicable(
                "no liquidity event planned; basis cleanup is pre-sale work"
            )

        target_close = liquidity.get("target_close_date")
        if target_close is None:
            return self._not_applicable(
                "liquidity_event_planned lacks target_close_date"
            )

        targets = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
            )
        ]
        if not targets:
            return self._not_applicable(
                "no operating entity that requires basis cleanup"
            )

        findings: list = []
        for t in targets:
            is_scorp = t.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            is_partnership = t.type in (
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP
            )

            items = []
            if is_scorp:
                if t.aaa_balance is not None and t.aaa_balance > Decimal(0):
                    items.append(
                        f"AAA balance ${t.aaa_balance:,.2f} — consider pre-sale "
                        f"distribution to reduce stock basis and shift gain "
                        f"composition"
                    )
                if t.accumulated_ep is not None and t.accumulated_ep > Decimal(0):
                    items.append(
                        f"Accumulated E&P ${t.accumulated_ep:,.2f} from C history — "
                        f"§1375 passive-income tax risk; consider distributions "
                        f"to drain AE&P"
                    )
                if t.stock_basis is None:
                    items.append("stock_basis not populated — basis reconstruction required before close")
                if t.debt_basis is None:
                    items.append("debt_basis not populated — review shareholder loans and AFR")
            if is_partnership:
                if t.outside_basis is None:
                    items.append("outside_basis not populated — §704(d) posture unknown")
                items.append("§754 election: if not yet filed, evaluate for buyer's §743(b) step-up")

            if scenario.prior_year.suspended_704d_carryover > Decimal(0):
                items.append(
                    f"Suspended §704(d) carryover ${scenario.prior_year.suspended_704d_carryover:,.2f} — "
                    f"may require basis restoration before disposition"
                )
            if scenario.prior_year.suspended_passive_losses > Decimal(0):
                items.append(
                    f"Suspended passive losses ${scenario.prior_year.suspended_passive_losses:,.2f} — "
                    f"§469(g) releases on fully-taxable disposition"
                )

            findings.append({
                "entity_code": t.code,
                "entity_type": t.type.value,
                "cleanup_items": items,
                "item_count": len(items),
            })

        total_items = sum(f["item_count"] for f in findings)

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "S corp AAA / OAA / AE&P reconciliation through close date",
                "shareholder loan ledger and AFR accrual",
                "§754 election history for partnership targets",
                "suspended loss carryforwards under §469, §704(d), §1366(d), §461(l)",
                "§263A / §471(c) method postures",
                "prior Form 1120-S / 1065 returns for buyer's due diligence",
            ],
            assumptions=[
                f"Target close: {target_close}",
                f"Entities requiring cleanup review: {len(findings)}",
                f"Total cleanup items identified: {total_items}",
            ],
            implementation_steps=[
                "Schedule basis reconstruction at least 12 months before close.",
                "For S corps: distribute AAA through the §1368(a) ordering "
                "rule before close; reconcile shareholder basis on Form 7203.",
                "For S corps with C history: drain AE&P via distributions "
                "to mitigate §1375 passive-income-tax and §1374 BIG "
                "exposure.",
                "For partnerships: file §754 election if not in place; "
                "run the §743(b) step-up model on the target transaction.",
                "Document shareholder loans with promissory notes and AFR "
                "interest accrual (§7872).",
                "Coordinate with SALE_F_REORG — F-reorg execution must "
                "happen AFTER basis cleanup but before buyer's due "
                "diligence window.",
            ],
            risks_and_caveats=[
                "AAA distributions are a ONE-WAY door. If the sale falls "
                "through, the distributed cash is gone. Balance liquidity "
                "needs against the tax benefit.",
                "§1371(e) post-termination distributions apply ONLY during "
                "the PTTP following an S election termination; pre-sale "
                "distributions follow normal §1368 ordering.",
                "Suspended passive losses release on a FULLY TAXABLE "
                "disposition (§469(g)); stock sale may not be 'fully "
                "taxable' if rollover equity or installment deferral "
                "components exist.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SALE_F_REORG",
                "SALE_ASSET_VS_STOCK",
                "PTE_OUTSIDE_BASIS",
                "PTE_AAA_TRACKING",
                "PTE_754_ELECTION",
                "LL_SUSPENDED_LOSSES",
                "LL_DISPOSITION_FREE_SL",
                "SCSI_AAA_TRACKING",
                "SCSI_BIG_1374",
            ],
            verification_confidence="high",
            computation_trace={
                "target_close_date": str(target_close),
                "findings": findings,
                "total_cleanup_items": total_items,
            },
        )
