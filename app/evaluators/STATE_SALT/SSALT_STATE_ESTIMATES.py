"""SSALT_STATE_ESTIMATES — state estimated tax optimization and safe harbors."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_STATE_ESTIMATES"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "CA R&TC §19136 — CA estimated tax safe harbor (110% rule for high earners)",
        "NY Tax Law §685(c) — NY estimated tax",
        "NJ N.J.S.A. 54A:9-6 — NJ estimates",
        "State-by-state safe harbor rules (varying prior-year / current-year thresholds)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        prior_state_tax = scenario.prior_year.total_state_tax_by_state
        if not prior_state_tax or all(v <= Decimal(0) for v in prior_state_tax.values()):
            return self._not_applicable(
                "no prior-year state tax liability across any state; "
                "estimated tax safe-harbor analysis needs a baseline"
            )
        exposed_states = sorted(s.value for s, amt in prior_state_tax.items() if amt > 0)
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "prior-year state liability by state",
                "current-year projected state liability",
                "prior-year AGI (for 110% high-earner trigger in CA and others)",
                "PTET credit carryforward application to current-year estimates",
            ],
            assumptions=[
                "CA imposes 110% prior-year safe harbor for AGI > $150K "
                "($75K MFS) and front-loads estimates 30%/40%/0%/30%.",
                "NY uses 110% prior-year for AGI > $150K; 4 equal quarterly.",
                "Applying PTET credit to current-year estimates reduces "
                "owner-level cash estimates but watch state rules on "
                "credit application timing.",
            ],
            implementation_steps=[
                "Compute prior-year state tax safe-harbor amount per state.",
                "Project current-year liability; compare to 90% current-year "
                "safe harbor threshold.",
                "Apply PTET credit carryforwards (see "
                "SSALT_PTET_MODELING) to reduce required estimates.",
                "For CA: front-load per §19136 schedule; "
                "set quarterly diary dates (4/15, 6/15, 9/15, 1/15).",
            ],
            risks_and_caveats=[
                "Underpayment penalty rates are state-specific and reset "
                "quarterly; missing a front-loaded quarter (CA Q1) is "
                "expensive and cannot be cured by overpayment in later Qs.",
                "PTET payments themselves may require separate entity-level "
                "estimates on different dates (CA prepayment by 6/15).",
            ],
            cross_strategy_impacts=[
                "CAP_EST_TAX_SAFE_HARBORS",
                "SSALT_PTET_MODELING",
                "SSALT_OBBBA_CAP_MODELING",
            ],
            verification_confidence="high",
            computation_trace={"exposed_states": exposed_states},
        )
