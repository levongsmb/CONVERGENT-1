"""RET_ROTH_CONVERSION — multi-year Roth conversion timing.

Converts pre-tax IRA / 401(k) balances to Roth in years when marginal
rate is lower than projected future rate (retirement / RMD year /
post-sale / pre-QCD-eligibility). Pairs with §151(f) senior deduction
phase-out threshold: keeping MAGI just below $150K MFJ / $75K single
preserves the $6,000 senior deduction.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


def _approx_magi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    total = (
        income.wages_primary + income.wages_spouse + income.self_employment_income
        + income.interest_ordinary + income.dividends_ordinary + income.dividends_qualified
        + income.capital_gains_long_term + income.capital_gains_short_term
        + income.rental_income_net + income.pension_ira_distributions
    )
    for k1 in income.k1_income:
        total += k1.ordinary_business_income + k1.guaranteed_payments
    return total


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RET_ROTH_CONVERSION"
    CATEGORY_CODE = "RETIREMENT"
    PIN_CITES = [
        "IRC §408A(d)(3) — traditional-to-Roth conversion",
        "IRC §408A(d)(3)(F) — five-year holding rule for converted amounts",
        "IRC §401(a)(9) — RMDs and required distribution year",
        "IRC §151(f) as added by OBBBA — senior deduction MAGI phaseout",
        "Rev. Rul. 2023-2 — basis recovery on conversions",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        pension_distributions = scenario.income.pension_ira_distributions
        primary_age = year - scenario.identity.primary_dob.year

        # Applicable when the taxpayer has pre-tax retirement balances
        # (approximated here by either (a) current-year distributions,
        # (b) age 50+, where pre-retirement balances are common, OR
        # (c) explicit pension_ira_distributions > 0 in the scenario).
        # A richer balance-sheet schema lands in Phase 3b.
        if pension_distributions == Decimal(0) and primary_age < 50:
            return self._not_applicable(
                "taxpayer under 50 with no pension / IRA distribution signal; "
                "Roth conversion analysis requires pre-tax retirement balance"
            )

        magi = _approx_magi(scenario)
        filing_status = scenario.identity.filing_status
        mfj = filing_status == FilingStatus.MFJ

        # Senior-deduction phaseout thresholds come from rules cache
        senior = rules.get("federal/obbba_senior_deduction_151f", year)
        senior_threshold = None
        for p in senior.get("parameters", []):
            fs = p["coordinate"].get("filing_status")
            sp = p["coordinate"].get("sub_parameter")
            if sp == "phaseout_magi_threshold":
                if (mfj and fs == "MFJ") or (not mfj and fs == "SINGLE"):
                    senior_threshold = Decimal(str(p["value"]))
                    break

        # Identify the conversion-window character:
        #   SUPER_WINDOW: retired, pre-RMD (age 60-72), low MAGI — best conditions
        #   RMD_WINDOW: post-73, forced distributions already — convert to manage RMDs
        #   PRE_RETIREMENT: still working, use Roth conversions opportunistically
        if primary_age >= 73:
            window = "POST_RMD"
        elif primary_age >= 60:
            window = "SUPER_WINDOW"
        elif primary_age >= 50:
            window = "PRE_RETIREMENT"
        else:
            window = "EARLY"

        # Headroom under senior deduction threshold (if age 65+)
        senior_headroom = Decimal(0)
        if primary_age >= 65 and senior_threshold is not None and magi < senior_threshold:
            senior_headroom = senior_threshold - magi

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "traditional IRA / 401(k) balance by account",
                "current-year marginal rate vs projected retirement marginal rate",
                "RMD start date (age 73 or 75 per SECURE 2.0 §107)",
                "state of residence at conversion year vs expected retirement state",
                "planned QCD utilization (reduces pre-tax IRA balance tax-free after 70½)",
            ],
            assumptions=[
                f"Primary age: {primary_age}",
                f"Window classification: {window}",
                f"Approx MAGI: ${magi:,.0f}",
                f"Senior-deduction threshold ({filing_status.value}): "
                f"${senior_threshold:,.0f}" if senior_threshold else "senior threshold not populated",
                f"Senior-deduction headroom (if age 65+): ${senior_headroom:,.0f}",
            ],
            implementation_steps=[
                "Project 5-year marginal rate path including RMDs, Social "
                "Security taxability, and IRMAA brackets.",
                "Identify low-rate years (pre-RMD, post-sale, sabbatical, "
                "retirement year) and size the conversion to fill the "
                "current-year bracket without crossing the next.",
                "For age 65+: size the conversion to keep MAGI under the "
                "§151(f) senior deduction threshold.",
                "Execute the conversion via trustee-to-trustee or same-trustee "
                "transfer; fund estimated tax from taxable accounts, not the "
                "converted amount.",
                "File Form 8606 to report the conversion and track basis.",
            ],
            risks_and_caveats=[
                "§408A(d)(3)(F) five-year clock applies to converted amounts; "
                "distributions before five years may be subject to 10% penalty "
                "if under 59½.",
                "IRMAA (Medicare Part B/D) brackets kick in two years after the "
                "conversion year; MAGI spikes can trigger higher premiums for "
                "two years.",
                "State tax: if the taxpayer plans to move from CA to a zero-tax "
                "state, deferring the conversion until after the move preserves "
                "~9-13% state tax.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RET_BACKDOOR_ROTH",
                "RET_MEGA_BACKDOOR_ROTH",
                "RET_RMD",
                "RET_QCD",
                "RET_OBBBA_SENIOR_DEDUCTION",
                "NIIT_ROTH_INTERACT",
                "RD_CA_DOMICILE_BREAK",
            ],
            verification_confidence="high",
            computation_trace={
                "primary_age": primary_age,
                "window": window,
                "approx_magi": str(magi),
                "senior_threshold": str(senior_threshold) if senior_threshold else None,
                "senior_headroom": str(senior_headroom),
                "pension_ira_distributions": str(pension_distributions),
            },
        )
