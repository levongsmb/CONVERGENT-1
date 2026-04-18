"""RET_SOLO_401K — Solo 401(k) design for self-employed owners.

Applicable to owner-only businesses (sole prop, SMLLC, S-corp one-owner
with no non-owner-family employees). Total contribution =
  employee elective deferral (§402(g)) + employer nonelective profit sharing
  up to §415(c) annual additions cap.

For a Schedule C / sole prop:
  employer_ps = net SE earnings × 0.25 effective = 20% of net SE after
  half-SE adjustment (circular computation; IRS Pub 560 worksheet).

For an S-corp owner-employee:
  employer_ps = W-2 wages × 25% (§404(h)(1)(C) / §415(c) bound).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


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
    SUBCATEGORY_CODE = "RET_SOLO_401K"
    CATEGORY_CODE = "RETIREMENT"
    PIN_CITES = [
        "IRC §402(g)(1) — employee elective deferral limit",
        "IRC §414(v) — catch-up contribution age 50+",
        "IRC §414(v)(2)(E)(ii) — super catch-up age 60-63 (SECURE 2.0 §109)",
        "IRC §415(c) — annual additions limit",
        "IRC §401(a)(17) — compensation cap",
        "IRC §404(h)(1)(C) — employer deduction limit for SE / S corp",
        "IRS Notice 2025-67 — 2026 limits",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicable if self-employed OR single-owner S-corp
        has_se = scenario.income.self_employment_income > Decimal(0)
        single_owner_scorp = any(
            e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            and e.ownership_pct_by_taxpayer >= Decimal("100")
            for e in scenario.entities
        )
        if not has_se and not single_owner_scorp:
            return self._not_applicable(
                "no self-employment earnings and no 100%-owner S corp; "
                "Solo 401(k) requires an owner-only business"
            )

        ret = rules.get("federal/retirement_limits", year)
        employee_deferral = _param(ret, tax_year=year, sub_parameter="section_402g_employee_elective_deferral")
        catchup_50 = _param(ret, tax_year=year, sub_parameter="section_414v_catchup_age_50")
        super_catchup = _param(ret, tax_year=year, sub_parameter="section_414v_super_catchup_age_60_63")
        annual_additions = _param(ret, tax_year=year, sub_parameter="section_415c_annual_additions")
        comp_cap = _param(ret, tax_year=year, sub_parameter="section_401a17_compensation_limit")

        if employee_deferral is None or annual_additions is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason="retirement limits for planning year incomplete in rules cache",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
                computation_trace={"year": year},
            )

        # Age band: primary taxpayer DOB determines catch-up eligibility
        from datetime import date
        primary_age = year - scenario.identity.primary_dob.year
        if primary_age >= 60 and primary_age <= 63 and super_catchup is not None:
            applicable_catchup = super_catchup
            catchup_tier = "SUPER_CATCHUP_60_63"
        elif primary_age >= 50 and catchup_50 is not None:
            applicable_catchup = catchup_50
            catchup_tier = "AGE_50"
        else:
            applicable_catchup = Decimal(0)
            catchup_tier = "NONE"

        # Earnings base
        if single_owner_scorp:
            # W-2 wage base (primary taxpayer W-2 from entity)
            earnings_base = scenario.income.wages_primary
            basis = "W-2 wages from S corp"
            employer_ps_cap_pct = Decimal("0.25")
            employer_ps = min(earnings_base, comp_cap or earnings_base) * employer_ps_cap_pct
        else:
            # Schedule C SE: 20% effective of net SE after half-SE tax.
            # Quick proxy: 20% of net SE earnings (close to exact).
            earnings_base = scenario.income.self_employment_income
            basis = "Schedule C / SE net earnings (20% effective)"
            employer_ps = earnings_base * Decimal("0.20")

        max_total_before_catchup = min(
            employee_deferral + employer_ps,
            annual_additions,
        )
        max_total_with_catchup = (max_total_before_catchup + applicable_catchup).quantize(Decimal("0.01"))

        # Tax-save proxy at 32% marginal for high earners
        approx_marginal = Decimal("0.32")
        estimated_fed_save = (max_total_with_catchup * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "primary taxpayer DOB (catch-up tier)",
                "net SE earnings (Schedule C) or W-2 wages from 100%-owned S corp",
                "existing employer-sponsored plan (disqualifies Solo 401(k) if present)",
            ],
            assumptions=[
                f"§402(g) employee deferral for {year}: ${employee_deferral:,.0f}",
                f"Applicable catch-up tier ({catchup_tier}): ${applicable_catchup:,.0f}",
                f"§415(c) annual additions: ${annual_additions:,.0f}",
                f"Earnings basis: {basis} (${earnings_base:,.2f})",
                f"Employer profit-sharing contribution: ${employer_ps:,.2f}",
                f"Approx marginal rate used: {approx_marginal:.0%}",
            ],
            implementation_steps=[
                "Adopt a Solo 401(k) plan document before year-end (SECURE Act "
                "allows plan establishment up to the tax return due date for "
                "employer-side contributions for tax year 2025+).",
                "Fund employee deferral via payroll (S-corp) or as a separate "
                "contribution (SE) by the plan year-end or IRS-specified date.",
                "Fund employer profit-sharing contribution by the return due "
                "date (including extensions).",
                "File Form 5500-EZ annually once plan assets exceed $250,000.",
            ],
            risks_and_caveats=[
                "Solo 401(k) requires NO non-owner-family employees working "
                "1,000+ hours. Adding an eligible employee triggers §410(b) "
                "coverage and may require plan amendment or separate ERISA plan.",
                "Controlled-group rules under §414(b)/(c): if the taxpayer "
                "owns other businesses with employees, aggregation may "
                "disqualify Solo 401(k) treatment.",
                "S-corp employer PS cap is 25% of W-2 wages — NOT 25% of "
                "distributive share. Coordinates tightly with "
                "COMP_WAGE_DIST_SPLIT.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "COMP_WAGE_DIST_SPLIT",
                "COMP_REASONABLE_COMP",
                "RET_CASH_BALANCE",
                "RET_MEGA_BACKDOOR_ROTH",
                "RET_CTRL_GROUP",
                "QBI_SCORP_WAGE_BALANCE",
            ],
            verification_confidence="high",
            computation_trace={
                "primary_age": primary_age,
                "catchup_tier": catchup_tier,
                "applicable_catchup": str(applicable_catchup),
                "earnings_base": str(earnings_base),
                "earnings_basis": basis,
                "employee_deferral": str(employee_deferral),
                "employer_ps": str(employer_ps),
                "annual_additions_cap": str(annual_additions),
                "max_total_before_catchup": str(max_total_before_catchup),
                "max_total_with_catchup": str(max_total_with_catchup),
            },
        )
