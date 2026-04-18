"""CAP_EST_TAX_SAFE_HARBORS — estimated tax safe harbors and annualization.

Recommends an estimated-tax payment schedule that clears §6654 (individual)
safe harbors with minimum cash outlay. The safe harbors are:

  (a) 90% of current-year tax, or
  (b) 100% of prior-year tax (110% if prior-year AGI > $150,000 MFJ,
      $75,000 MFS per §6654(d)(1)(C)), or
  (c) the §6654(d)(2) annualized income installment method (applied
      item-by-item; this evaluator flags eligibility but does not
      compute the full annualization).

Applicability: every scenario where prior-year total federal tax is
known or projected current-year tax is known. Not applicable when the
taxpayer owes no tax (prior-year tax == 0 AND no current-year projected
tax).
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


# §6654(d)(1)(C) prior-year-tax safe-harbor percentage elevation
# thresholds. Statutory, not indexed. Cited from IRC §6654(d)(1)(C).
_PRIOR_AGI_ELEVATED_THRESHOLD_NONMFJ = Decimal("150000")
_PRIOR_AGI_ELEVATED_THRESHOLD_MFS = Decimal("75000")
_ELEVATED_PCT = Decimal("1.10")
_BASE_PRIOR_YEAR_PCT = Decimal("1.00")
_CURRENT_YEAR_SAFE_HARBOR_PCT = Decimal("0.90")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_EST_TAX_SAFE_HARBORS"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6654(d)(1)(B) — 90% of current-year tax safe harbor",
        "IRC §6654(d)(1)(C) — 100% / 110% prior-year tax safe harbor",
        "IRC §6654(d)(2) — annualized income installment method",
        "IRC §6654(e) — exceptions and estimated-tax threshold",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        prior_agi = scenario.prior_year.agi
        prior_tax = scenario.prior_year.total_federal_tax

        if prior_tax is None and scenario.income.wages_primary == Decimal(0) \
                and scenario.income.wages_spouse == Decimal(0) \
                and scenario.income.self_employment_income == Decimal(0) \
                and not scenario.income.k1_income:
            return self._not_applicable(
                "no prior-year tax history and no current-year income sources"
            )

        # Elevated-pct trigger
        elevated_threshold = (
            _PRIOR_AGI_ELEVATED_THRESHOLD_MFS
            if scenario.identity.filing_status == FilingStatus.MFS
            else _PRIOR_AGI_ELEVATED_THRESHOLD_NONMFJ
        )
        elevated_triggered = (
            prior_agi is not None and prior_agi > elevated_threshold
        )
        prior_year_pct = _ELEVATED_PCT if elevated_triggered else _BASE_PRIOR_YEAR_PCT
        prior_year_safe_harbor = (
            (prior_tax * prior_year_pct) if prior_tax is not None else None
        )

        # Annualization eligibility flag
        has_lumpy_income = self._income_pattern_is_lumpy(scenario)

        assumptions: List[str] = [
            f"Filing status: {scenario.identity.filing_status.value}",
            f"Prior-year AGI {'>' if elevated_triggered else '<='} ${elevated_threshold:,.0f}, "
            f"so prior-year safe-harbor percentage = "
            f"{int(prior_year_pct * 100)}% of prior-year tax",
        ]
        if prior_tax is not None:
            assumptions.append(
                f"Prior-year safe-harbor dollar amount: ${prior_year_safe_harbor:,.2f}"
            )

        implementation_steps: List[str] = [
            "Compute 90% of projected current-year tax.",
            "Compute prior-year safe-harbor dollar amount "
            f"(prior tax × {int(prior_year_pct * 100)}%).",
            "Select the lower of the two as the required annual payment.",
            "Divide the required annual payment into four equal installments "
            "due April 15, June 15, September 15, and January 15 of the following year.",
        ]

        risks_and_caveats: List[str] = [
            "If current-year income is front-loaded (e.g., Q1 liquidity event), "
            "the annualized income installment method under §6654(d)(2) may reduce "
            "the Q2/Q3 installments without triggering a penalty.",
            "State estimated-tax safe harbors operate independently; CA FTB safe "
            "harbors differ materially from §6654.",
        ]

        if has_lumpy_income:
            risks_and_caveats.insert(
                0,
                "Income pattern suggests lumpy / back-loaded receipts; evaluate "
                "the §6654(d)(2) annualized income installment method on Form 2210 "
                "Schedule AI before locking the installment schedule.",
            )

        # Skeleton dollar output: this subcategory produces penalty-avoidance
        # value rather than a direct tax saving. Record zero dollar savings
        # but mark applicable so it surfaces in planning memos when relevant.
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "prior-year total federal tax",
                "prior-year AGI",
                "projected current-year tax",
                "quarterly income timing if annualizing",
            ],
            assumptions=assumptions,
            implementation_steps=implementation_steps,
            risks_and_caveats=risks_and_caveats,
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CAP_PENALTY_ABATEMENT",
                "SSALT_STATE_ESTIMATES",
            ],
            verification_confidence="high",
            computation_trace={
                "prior_year_pct": str(prior_year_pct),
                "prior_year_safe_harbor": (
                    str(prior_year_safe_harbor) if prior_year_safe_harbor is not None
                    else None
                ),
                "elevated_triggered": elevated_triggered,
                "has_lumpy_income_flag": has_lumpy_income,
            },
        )

    @staticmethod
    def _income_pattern_is_lumpy(scenario: ClientScenario) -> bool:
        """Heuristic: large one-time items (§1202 gain, capital gains,
        planned liquidity event) indicate lumpy income pattern that
        warrants considering the annualization method."""
        if scenario.planning.liquidity_event_planned is not None:
            return True
        if scenario.income.section_1202_gain_gross > Decimal(0):
            return True
        # Treat LT cap gain above 25% of wages as lumpy
        wages_total = scenario.income.wages_primary + scenario.income.wages_spouse
        if (
            wages_total > Decimal(0)
            and scenario.income.capital_gains_long_term > (wages_total * Decimal("0.25"))
        ):
            return True
        return False
