"""RET_OBBBA_SENIOR_DEDUCTION — §151(f) senior deduction (2025-2028).

OBBBA added a $6,000 per-qualifying-taxpayer deduction for taxpayers
age 65+, with a 6% phaseout above $75K MAGI Single / $150K MFJ. The
evaluator quantifies the available deduction, the phaseout posture,
and the compression target to recover deduction where applicable.
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
    SUBCATEGORY_CODE = "RET_OBBBA_SENIOR_DEDUCTION"
    CATEGORY_CODE = "RETIREMENT"
    PIN_CITES = [
        "IRC §151(f) as added by OBBBA — $6,000 senior deduction (2025-2028)",
        "IRC §151(f) — 6% MAGI phaseout above $75K single / $150K MFJ",
        "OBBBA P.L. 119-21 — senior deduction sunset 2028",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        if year < 2025 or year > 2028:
            return self._not_applicable(
                f"§151(f) senior deduction applies 2025-2028; scenario year is {year}"
            )

        primary_age = year - scenario.identity.primary_dob.year
        spouse_age = None
        if scenario.identity.spouse_dob is not None:
            spouse_age = year - scenario.identity.spouse_dob.year

        qualifying_count = 0
        if primary_age >= 65:
            qualifying_count += 1
        if (
            scenario.identity.filing_status in (FilingStatus.MFJ, FilingStatus.QSS)
            and spouse_age is not None
            and spouse_age >= 65
        ):
            qualifying_count += 1

        if qualifying_count == 0:
            return self._not_applicable(
                "no qualifying taxpayer age 65 or older; §151(f) deduction is age-gated"
            )

        senior = rules.get("federal/obbba_senior_deduction_151f", year)
        per_taxpayer = None
        phaseout_mfj = None
        phaseout_single = None
        phaseout_rate = None
        for p in senior.get("parameters", []):
            sp = p["coordinate"].get("sub_parameter")
            fs = p["coordinate"].get("filing_status")
            v = p.get("value")
            if v is None:
                continue
            if sp == "per_qualifying_taxpayer_amount":
                per_taxpayer = Decimal(str(v))
            elif sp == "phaseout_magi_threshold" and fs == "MFJ":
                phaseout_mfj = Decimal(str(v))
            elif sp == "phaseout_magi_threshold" and fs == "SINGLE":
                phaseout_single = Decimal(str(v))
            elif sp == "phaseout_rate":
                phaseout_rate = Decimal(str(v))

        if per_taxpayer is None or phaseout_rate is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason="§151(f) parameters incomplete in rules cache",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
            )

        mfj = scenario.identity.filing_status == FilingStatus.MFJ
        threshold = phaseout_mfj if mfj else phaseout_single
        magi = _approx_magi(scenario)

        gross_deduction = per_taxpayer * qualifying_count
        if threshold is None or magi <= threshold:
            allowed_deduction = gross_deduction
            phaseout_reduction = Decimal(0)
        else:
            phaseout_reduction = min(
                (magi - threshold) * phaseout_rate,
                gross_deduction,
            ).quantize(Decimal("0.01"))
            allowed_deduction = (gross_deduction - phaseout_reduction).quantize(Decimal("0.01"))

        approx_marginal = Decimal("0.22")
        estimated_fed_save = (allowed_deduction * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "qualifying taxpayer ages (primary and spouse if MFJ)",
                "current-year MAGI",
                "compression strategies available (retirement deferrals, charitable, PTET)",
            ],
            assumptions=[
                f"Qualifying taxpayers age 65+: {qualifying_count}",
                f"Per-taxpayer deduction: ${per_taxpayer:,.0f}",
                f"Gross deduction: ${gross_deduction:,.2f}",
                f"Phaseout threshold ({'MFJ' if mfj else 'Single'}): ${threshold:,.0f}" if threshold else "no threshold",
                f"Approx MAGI: ${magi:,.0f}",
                f"Phaseout reduction: ${phaseout_reduction:,.2f}",
                f"Allowed deduction: ${allowed_deduction:,.2f}",
                f"Approx marginal rate: {approx_marginal:.0%}",
            ],
            implementation_steps=[
                "Claim the deduction on the 2026 return (above-the-line per §151(f)).",
                "If MAGI is in or near phaseout, evaluate compression via: "
                "increased retirement deferrals, PTET election, charitable "
                "bunching, defer capital gain harvesting.",
                "Multi-year plan: the deduction sunsets after 2028; model pre- "
                "and post-sunset years separately.",
            ],
            risks_and_caveats=[
                "§151(f) sunsets after 2028 unless extended. Multi-year plans "
                "crossing 2029 must model the cliff.",
                "Phaseout uses MAGI, not AGI; confirm the MAGI definition "
                "aligns with §151(f) technical guidance.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RET_ROTH_CONVERSION",
                "RET_RMD",
                "CHAR_BUNCHING",
                "CA_PTET_ELECTION",
                "QBI_INCOME_COMPRESSION",
            ],
            verification_confidence="high",
            computation_trace={
                "primary_age": primary_age,
                "spouse_age": spouse_age,
                "qualifying_count": qualifying_count,
                "per_taxpayer_amount": str(per_taxpayer),
                "gross_deduction": str(gross_deduction),
                "phaseout_threshold": str(threshold) if threshold else None,
                "magi": str(magi),
                "phaseout_reduction": str(phaseout_reduction),
                "allowed_deduction": str(allowed_deduction),
            },
        )
