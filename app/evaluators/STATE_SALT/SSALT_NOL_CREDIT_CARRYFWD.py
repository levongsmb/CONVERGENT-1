"""SSALT_NOL_CREDIT_CARRYFWD — state NOL and credit carryforward preservation."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NOL_CREDIT_CARRYFWD"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "CA R&TC §17276 — CA NOL computation and carryforward",
        "CA R&TC §24416 — CA NOL for corporations; 2024-2026 suspension under AB 176 / SB 167",
        "NY Tax Law §208.9(f) — NY franchise NOL conversion",
        "IRC §382 — federal ownership change limits informing state parallels",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        py = scenario.prior_year
        has_nol_cf = bool(py.nol_carryforwards) or py.suspended_passive_losses > 0
        has_credit_cf = bool(py.credit_carryforwards) or bool(py.pte_credit_carryforwards)
        if not (has_nol_cf or has_credit_cf):
            return self._not_applicable(
                "no state NOL or credit carryforward in prior-year context; "
                "preservation analysis needs an existing attribute"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "year-by-year NOL balance by state",
                "credit carryforward balance with expiration dates",
                "state suspension rules in effect for current year",
                "projected state taxable income to estimate utilization",
            ],
            assumptions=[
                "CA NOLs for business entities are suspended for tax years "
                "2024-2026 under SB 167; carryforward period is extended "
                "by the suspension period.",
                "Federal IRC §382 ownership-change limitations generally "
                "flow through to state NOL computations by conformity.",
                "PTE credit carryforwards expire state-by-state (CA 5 years "
                "under SB 132; NY 5 years; NJ 20 years).",
            ],
            implementation_steps=[
                "Reconcile federal NOL to each state's decoupled NOL "
                "(different computation, different carryforward period).",
                "Sequence NOL and credit usage to honor expiration "
                "(credits with near-term expiration first).",
                "For CA suspension years (2024-2026), confirm any "
                "small-business exceptions (< $1M CA AGI) before applying.",
                "Coordinate with SSALT_CONFORMITY_DECOUPLING to avoid "
                "double-counting state-specific adjustments.",
            ],
            risks_and_caveats=[
                "Lost credits from non-application (e.g., attributing PTET "
                "credit to a composite return) are often non-recoverable.",
                "Mergers / restructurings may trigger state §382-parallel "
                "limitation reset; pre-transaction modeling is mandatory.",
            ],
            cross_strategy_impacts=[
                "SSALT_CONFORMITY_DECOUPLING",
                "SSALT_PTET_MODELING",
                "CAP_PROTECTIVE_ELECTIONS",
            ],
            verification_confidence="high",
        )
