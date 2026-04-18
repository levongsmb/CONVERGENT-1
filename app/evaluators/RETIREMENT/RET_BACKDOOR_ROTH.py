"""RET_BACKDOOR_ROTH — backdoor Roth IRA conversion.

When MAGI exceeds the §408A(c)(3) Roth IRA direct-contribution phaseout,
a taxpayer can (a) make a nondeductible traditional IRA contribution
under §219 and (b) convert to Roth under §408A(d)(3). If no pre-tax
IRA balance exists, the conversion is essentially tax-free.

The §408(d)(2) pro-rata rule aggregates ALL traditional IRA balances
(and SEP / SIMPLE IRAs) for the conversion-basis calculation; the
evaluator flags when the taxpayer has other pre-tax IRA balances that
would cause partial taxability on conversion.
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
                if isinstance(v, list):
                    return tuple(Decimal(str(x)) for x in v)
                return Decimal(str(v))
            except Exception:
                return v
    return None


def _approx_magi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    base = (
        income.wages_primary
        + income.wages_spouse
        + income.self_employment_income
        + income.interest_ordinary
        + income.dividends_ordinary
        + income.dividends_qualified
        + income.capital_gains_long_term
        + income.capital_gains_short_term
        + income.rental_income_net
    )
    for k1 in income.k1_income:
        base += (
            k1.ordinary_business_income
            + k1.interest_income
            + k1.dividend_income
            + k1.capital_gain_long_term
            + k1.capital_gain_short_term
            + k1.guaranteed_payments
        )
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RET_BACKDOOR_ROTH"
    CATEGORY_CODE = "RETIREMENT"
    PIN_CITES = [
        "IRC §219 — traditional IRA contribution",
        "IRC §408(d)(2) — pro-rata rule on distributions / conversions",
        "IRC §408A(c)(3) — Roth IRA direct-contribution MAGI phaseout",
        "IRC §408A(d)(3) — traditional-to-Roth conversion",
        "IRS Notice 2014-54 — after-tax rollover bifurcation",
        "IRS Notice 2025-67 — 2026 contribution limits",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ret = rules.get("federal/retirement_limits", year)
        filing_status = scenario.identity.filing_status
        fs_key = "MFJ" if filing_status == FilingStatus.MFJ else (
            "MFS" if filing_status == FilingStatus.MFS else "SINGLE_OR_HOH"
        )

        phaseout = _param(ret, tax_year=year, filing_status=fs_key, sub_parameter="roth_ira_magi_phaseout_range")
        if phaseout is None or not isinstance(phaseout, tuple) or len(phaseout) != 2:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"Roth IRA MAGI phaseout for {year}/{fs_key} incomplete in rules cache",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
                computation_trace={"year": year, "filing_status": fs_key},
            )

        phaseout_low, phaseout_high = phaseout
        magi = _approx_magi(scenario)
        if magi <= phaseout_low:
            return self._not_applicable(
                f"MAGI ${magi:,.0f} below Roth direct-contribution phaseout "
                f"(${phaseout_low:,.0f}); direct Roth contribution is available "
                f"— see RET_BACKDOOR_ROTH not needed"
            )

        ira_contribution = _param(ret, tax_year=year, sub_parameter="section_408a_ira_contribution") or Decimal("7500")
        ira_catchup = _param(ret, tax_year=year, sub_parameter="section_219b5B_ira_catchup") or Decimal("1100")
        primary_age = year - scenario.identity.primary_dob.year
        applicable_limit = ira_contribution + (ira_catchup if primary_age >= 50 else Decimal(0))

        # Conversion amount assumed = full annual IRA contribution; dollar
        # impact = ordinary-income-tax deferred to Roth growth, not current-
        # year savings. Surface as opportunity with zero direct savings.
        approx_growth_years = max(65 - primary_age, Decimal(5))
        approx_annual_return = Decimal("0.07")
        approx_future_value = applicable_limit * ((Decimal("1") + approx_annual_return) ** int(approx_growth_years))
        approx_tax_saved_on_growth = (
            (approx_future_value - applicable_limit) * Decimal("0.24")
        ).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=approx_tax_saved_on_growth,
            savings_by_tax_type=TaxImpact(federal_income_tax=approx_tax_saved_on_growth),
            inputs_required=[
                "all pre-tax traditional IRA / SEP / SIMPLE balances (pro-rata rule)",
                "planned annual Roth conversion amount",
                "MAGI projection for the conversion year",
                "retirement age target for compounding horizon",
            ],
            assumptions=[
                f"§408A(c)(3) Roth phaseout range ({fs_key}): ${phaseout_low:,.0f} - ${phaseout_high:,.0f}",
                f"Approx MAGI: ${magi:,.0f}",
                f"IRA contribution limit: ${applicable_limit:,.0f} "
                f"(includes age-50 catch-up: {primary_age >= 50})",
                f"Assumed growth horizon: {approx_growth_years} years at "
                f"{approx_annual_return:.0%} annual return",
                "Tax-saved figure is on future growth, not current year.",
            ],
            implementation_steps=[
                "Confirm NO pre-tax traditional IRA / SEP / SIMPLE balance, OR "
                "plan to roll any pre-tax balance to a 401(k) first to clear "
                "the §408(d)(2) pro-rata denominator.",
                "Make the §219 nondeductible contribution to a traditional IRA.",
                "Wait a short period (days to weeks; IRS has not specified a "
                "required waiting period); convert under §408A(d)(3).",
                "File Form 8606 to report the nondeductible contribution AND "
                "the conversion.",
                "Track basis on Form 8606 annually.",
            ],
            risks_and_caveats=[
                "Pro-rata rule: if any pre-tax IRA balance exists as of "
                "December 31 of the conversion year, the conversion is "
                "partially taxable. This commonly catches taxpayers with old "
                "rollover IRAs or SEP / SIMPLE accounts.",
                "Step-transaction challenges have been raised but the IRS "
                "has not formally enforced them against backdoor Roth. Current "
                "guidance (2018 JCT Bluebook) tacitly blesses the strategy.",
                "For MFJ, both spouses need individual traditional IRAs; "
                "the pro-rata rule is applied per taxpayer.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RET_SOLO_401K",
                "RET_MEGA_BACKDOOR_ROTH",
                "RET_ROTH_CONVERSION",
                "RET_RMD",
            ],
            verification_confidence="high",
            computation_trace={
                "filing_status": fs_key,
                "primary_age": primary_age,
                "magi_approx": str(magi),
                "phaseout_low": str(phaseout_low),
                "phaseout_high": str(phaseout_high),
                "annual_ira_contribution_limit": str(applicable_limit),
                "approx_growth_years": str(approx_growth_years),
                "approx_future_value": str(approx_future_value.quantize(Decimal("0.01"))),
                "approx_tax_saved_on_growth": str(approx_tax_saved_on_growth),
            },
        )
