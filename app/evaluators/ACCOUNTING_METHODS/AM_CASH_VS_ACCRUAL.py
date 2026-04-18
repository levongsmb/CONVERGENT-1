"""AM_CASH_VS_ACCRUAL — cash vs accrual method election.

Small businesses under the §448(c) gross-receipts threshold may elect
cash method, which generally accelerates deductions (bills paid) and
defers income recognition (not received). Evaluator identifies
current accounting method per entity and quantifies switching
opportunity.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


# §448(c) threshold — $30M indexed for 2025; evaluator degrades if
# rules cache parameter null. Placeholder proxy here.
_448_THRESHOLD_PROXY = Decimal("30000000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "AM_CASH_VS_ACCRUAL"
    CATEGORY_CODE = "ACCOUNTING_METHODS"
    PIN_CITES = [
        "IRC §446 — general rule for methods of accounting",
        "IRC §448 — limitation on use of cash method",
        "IRC §448(c) — gross receipts test ($30M indexed 2025)",
        "IRC §471(c) — small-business inventory simplification",
        "Rev. Proc. 2023-24 — automatic method change procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ops = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.SOLE_PROP,
            )
        ]
        if not ops:
            return self._not_applicable(
                "no operating entity; cash-vs-accrual analysis is entity-level"
            )

        candidates: list = []
        for e in ops:
            gross_proxy = e.gross_receipts_prior_3_avg or e.gross_receipts_prior_year
            under_threshold = (
                gross_proxy is not None and gross_proxy < _448_THRESHOLD_PROXY
            )
            candidates.append({
                "entity_code": e.code,
                "entity_type": e.type.value,
                "current_method": e.accounting_method,
                "inventory_method": e.inventory_method,
                "gross_receipts_proxy": str(gross_proxy) if gross_proxy else None,
                "under_448c_proxy_threshold": under_threshold,
                "switch_candidate": (
                    under_threshold and e.accounting_method == "ACCRUAL"
                ),
            })

        switch_candidates = [c for c in candidates if c["switch_candidate"]]
        if not switch_candidates:
            return self._not_applicable(
                "no entity under §448(c) threshold currently on accrual; "
                "cash method switch not indicated"
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # first-order benefit depends on A/R vs A/P delta
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "year-end accounts receivable balance",
                "year-end accounts payable balance",
                "inventory balance for §471(c) analysis",
                "recurring deferred revenue (§451(c) coordination)",
                "§481(a) adjustment estimate from method switch",
            ],
            assumptions=[
                f"§448(c) threshold proxy: ${_448_THRESHOLD_PROXY:,.0f}",
                f"Entities under threshold on accrual: {len(switch_candidates)}",
                "Cash-method adoption defers A/R recognition and accelerates "
                "A/P deduction (typical net-income-favorable in growth years).",
            ],
            implementation_steps=[
                "Compute §481(a) adjustment: A/R + inventory (if switching "
                "471(c)) − A/P. Positive = unfavorable (4-year spread); "
                "negative = favorable (immediate).",
                "File Form 3115 with automatic-consent designation number for "
                "the cash method change (DCN 233) under Rev. Proc. 2023-24.",
                "Coordinate with AM_471C_INVENTORY for the inventory "
                "simplification election if inventory currently capitalized.",
                "Coordinate with AM_451C_ADVANCE_PAYMENTS for deferred revenue "
                "treatment under cash method.",
            ],
            risks_and_caveats=[
                "§448(c) is a 3-year-average gross receipts test; growth "
                "above the threshold requires switching BACK to accrual "
                "and another §481(a) adjustment (favorable).",
                "Certain entities are ineligible for cash method regardless "
                "of size (tax shelters, farming with C corp syndicates).",
                "State conformity: most states conform to federal method "
                "elections, but some (TX franchise tax, CA LLC fee) use "
                "separate computations.",
                "Planning trap: switching in a year with very large A/R "
                "creates a large unfavorable §481(a) that spreads over 4 "
                "years — the cash method benefit may be absorbed by the "
                "spread.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "AM_448_GROSS_RECEIPTS",
                "AM_471C_INVENTORY",
                "AM_451C_ADVANCE_PAYMENTS",
                "AM_481A_PLANNING",
                "AM_263A_UNICAP",
            ],
            verification_confidence="high",
            computation_trace={
                "entity_count": len(candidates),
                "switch_candidate_count": len(switch_candidates),
                "candidates": candidates,
                "threshold_proxy": str(_448_THRESHOLD_PROXY),
            },
        )
