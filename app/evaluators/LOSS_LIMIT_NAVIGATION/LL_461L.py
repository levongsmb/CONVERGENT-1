"""LL_461L — excess business loss limitation under §461(l).

OBBBA made §461(l) permanent. The limitation disallows aggregate
business losses exceeding a threshold amount (indexed); the disallowed
portion flows to a §172 NOL carryover.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


def _param(doc, **coord):
    for p in doc.get("parameters", []):
        c = p.get("coordinate", {})
        if all(c.get(k) == v for k, v in coord.items()):
            v = p.get("value")
            if v is None:
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return v
    return None


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "LL_461L"
    CATEGORY_CODE = "LOSS_LIMIT_NAVIGATION"
    PIN_CITES = [
        "IRC §461(l)(1) — excess business loss disallowance",
        "IRC §461(l)(3)(A) — threshold amount (Rev. Proc. indexed)",
        "IRC §461(l)(2) — disallowed loss flows to §172 NOL carryover",
        "OBBBA — §461(l) made permanent",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        net_business = scenario.income.self_employment_income
        for k1 in scenario.income.k1_income:
            net_business += k1.ordinary_business_income + k1.guaranteed_payments
        net_business += scenario.income.rental_income_net

        if net_business >= Decimal(0):
            return self._not_applicable(
                "no aggregate business loss; §461(l) disallowance is loss-specific"
            )

        ebl_doc = rules.get("federal/section_461l", year)
        filing_status = scenario.identity.filing_status
        mfj = filing_status == FilingStatus.MFJ
        threshold_key = (
            "threshold_mfj" if mfj else "threshold_single_hoh_mfs"
        )
        threshold = _param(ebl_doc, tax_year=year, sub_parameter=threshold_key)

        aggregate_loss = -net_business  # positive number

        if threshold is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason="§461(l) threshold amount for planning year awaiting Rev. Proc.",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
                computation_trace={
                    "aggregate_business_loss": str(aggregate_loss),
                    "threshold_populated": False,
                },
            )

        allowed = min(aggregate_loss, threshold)
        disallowed = max(aggregate_loss - threshold, Decimal(0))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "net business income / loss by activity",
                "guaranteed payments, SE income, K-1 ordinary from each pass-through",
                "rental net income / loss (if aggregated for §461(l))",
            ],
            assumptions=[
                f"§461(l) threshold for {year} ({filing_status.value}): ${threshold:,.0f}",
                f"Aggregate business loss: ${aggregate_loss:,.2f}",
                f"Allowed in current year: ${allowed:,.2f}",
                f"Disallowed (flows to §172 NOL): ${disallowed:,.2f}",
            ],
            implementation_steps=[
                "Compute §461(l) on Form 461 for the taxpayer (individual level).",
                "File Form 461 with the return; carryforward the disallowed "
                "amount as a §172 NOL item, NOT as a §461(l) carryover.",
                "Multi-year: evaluate grouping and disposition planning to "
                "release suspended losses before §461(l) applies again.",
            ],
            risks_and_caveats=[
                "§461(l) is a per-taxpayer limit (both spouses on MFJ).",
                "Pair with LL_SUSPENDED_LOSSES to avoid double-counting "
                "amounts already disallowed under §469, §465, or basis rules.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "LL_SUSPENDED_LOSSES",
                "LL_469_PASSIVE",
                "LL_465_AT_RISK",
                "LL_NOL_USAGE",
                "LL_704D_BASIS",
            ],
            verification_confidence="high",
            computation_trace={
                "net_business_income_proxy": str(net_business),
                "aggregate_business_loss": str(aggregate_loss),
                "threshold": str(threshold),
                "allowed": str(allowed),
                "disallowed_to_nol": str(disallowed),
                "filing_status": filing_status.value,
            },
        )
