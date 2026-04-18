"""PTE_OUTSIDE_BASIS — partnership outside basis tracking.

Partnership outside basis (the partner's basis in the partnership
interest) governs (a) §704(d) loss limitation, (b) basis on
distributions under §731, (c) gain/loss on partial or complete
disposition. This evaluator surfaces the state of the taxpayer's
outside basis for each LLC-as-partnership / partnership K-1 position
and flags reconstruction needs.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "PTE_OUTSIDE_BASIS"
    CATEGORY_CODE = "PTE_BASIS_AND_DISTRIBUTIONS"
    PIN_CITES = [
        "IRC §705(a) — determination of partner basis",
        "IRC §722 — basis from contributions",
        "IRC §752 — share of partnership liabilities included in basis",
        "IRC §704(d) — loss limited to basis",
        "IRC §731 — basis effect of distributions",
        "Treas. Reg. §1.704-1(b)(2)(iv) — tax basis capital reporting",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnerships = [
            e for e in scenario.entities
            if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP)
        ]
        if not partnerships:
            return self._not_applicable(
                "no partnership entity in scenario; outside basis applies to "
                "partnership interests"
            )

        findings: list = []
        any_missing = False
        suspended_704d = scenario.prior_year.suspended_704d_carryover
        suspended_at_risk = scenario.prior_year.suspended_at_risk_carryover

        for e in partnerships:
            missing = e.outside_basis is None
            if missing:
                any_missing = True
            findings.append({
                "entity_code": e.code,
                "entity_type": e.type.value,
                "outside_basis": str(e.outside_basis) if e.outside_basis is not None else None,
                "missing_outside_basis": missing,
            })

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "partner's contribution history (cash, property, services)",
                "partner's share of partnership liabilities under §752 (recourse / nonrecourse / qualified nonrecourse)",
                "distributions received since contribution",
                "allocated income and loss history since acquisition",
                "prior §743(b) adjustments if interest purchased",
                "suspended §704(d) losses waiting on basis restoration",
            ],
            assumptions=[
                f"Partnership positions: {len(partnerships)}",
                f"Any position missing outside_basis: {any_missing}",
                f"Prior-year §704(d) suspended losses: "
                f"${suspended_704d:,.2f}",
                f"Prior-year at-risk suspended losses: "
                f"${suspended_at_risk:,.2f}",
            ],
            implementation_steps=[
                "For each partnership interest, reconstruct outside basis "
                "from acquisition date forward: start with initial contribution, "
                "add share of income, subtract share of losses and "
                "distributions, adjust for liability share under §752.",
                "Request prior-year K-1s and partnership Schedule K capital-"
                "account reconciliation (post-2020 tax basis capital reporting "
                "under §1.704-1(b)(2)(iv)).",
                "Coordinate with §754 election status: if in place, §743(b) "
                "adjustments affect inside-only basis and do NOT change "
                "outside basis.",
                "Document §752 liability allocations annually; changes in "
                "nonrecourse vs recourse allocations shift outside basis.",
                "Before any disposition, pair with PTE_754_ELECTION and "
                "SALE_751_HOT_ASSETS.",
            ],
            risks_and_caveats=[
                "§704(d) suspended losses accumulate until basis is "
                "restored. Contributions, debt allocations, or undistributed "
                "income release suspensions pro-rata.",
                "§465 at-risk limitation operates independently of §704(d); "
                "qualifying non-recourse debt counts for basis but not for "
                "at-risk amount unless §465(b)(6) qualified nonrecourse "
                "financing applies.",
                "Tax basis capital reporting is MANDATORY post-2020. "
                "Incorrect reporting triggers §6698 / §6721 penalties.",
                "On disposition, excess of amount realized over outside "
                "basis = gain. Miscomputed basis = miscomputed gain and "
                "potential audit risk.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "PTE_704D_LIMITATION",
                "PTE_DEBT_BASIS",
                "PTE_BASIS_CAPITAL_REPORTING",
                "PTE_754_ELECTION",
                "PTE_731_DISTRIBUTIONS",
                "LL_704D_BASIS",
                "LL_465_AT_RISK",
                "SALE_751_HOT_ASSETS",
            ],
            verification_confidence="high",
            computation_trace={
                "partnership_count": len(partnerships),
                "findings": findings,
                "any_missing_outside_basis": any_missing,
                "suspended_704d_carryover": str(suspended_704d),
                "suspended_at_risk_carryover": str(suspended_at_risk),
            },
        )
