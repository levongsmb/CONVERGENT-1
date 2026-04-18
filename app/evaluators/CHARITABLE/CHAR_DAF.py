"""CHAR_DAF — donor-advised fund bunching.

DAFs accept multi-year charitable intent up-front and disburse over
time. Pair with CHAR_BUNCHING for itemization threshold management:
fund two years of giving in a single year to clear the standard
deduction, then take the standard deduction in the off year.

Under OBBBA (effective 2026), individual charitable deductions are
subject to a 0.5% AGI floor (CHAR_OBBBA_05_FLOOR) and non-itemizers
receive an above-the-line $1,000 single / $2,000 MFJ deduction, but
contributions to DAFs and non-operating private foundations are
EXCLUDED from the above-the-line item — DAF only benefits itemizers.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


def _approx_magi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    base = (
        income.wages_primary + income.wages_spouse + income.self_employment_income
        + income.interest_ordinary + income.dividends_ordinary + income.dividends_qualified
        + income.capital_gains_long_term + income.capital_gains_short_term
        + income.rental_income_net + income.pension_ira_distributions
    )
    for k1 in income.k1_income:
        base += k1.ordinary_business_income + k1.guaranteed_payments
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CHAR_DAF"
    CATEGORY_CODE = "CHARITABLE"
    PIN_CITES = [
        "IRC §170(b)(1)(A) — 60% AGI limit for cash to public charity (including sponsoring org of DAF)",
        "IRC §170(b)(1)(C) — 30% AGI limit for appreciated long-term capital property",
        "IRC §170(f)(18) — donor-advised fund definition and substantiation",
        "IRC §170(a) as amended by OBBBA — 0.5% AGI floor (itemizers)",
        "§63(c) — standard deduction bunching baseline",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        current_charitable_cash = (
            scenario.deductions.charitable_cash_public
            + scenario.deductions.charitable_cash_daf
        )
        current_charitable_appreciated = (
            scenario.deductions.charitable_appreciated_public
            + scenario.deductions.charitable_appreciated_private
        )
        total_charitable = current_charitable_cash + current_charitable_appreciated

        if total_charitable <= Decimal(0):
            return self._not_applicable(
                "no charitable contributions in scenario; DAF planning requires "
                "active charitable intent"
            )

        magi = _approx_magi(scenario)

        # Standard deduction threshold lookup
        sd_doc = rules.get("federal/standard_deduction", year)
        sd_amount = None
        filing_status = scenario.identity.filing_status
        fs_key = "MFJ" if filing_status == FilingStatus.MFJ else (
            "HOH" if filing_status == FilingStatus.HOH else
            "MFS" if filing_status == FilingStatus.MFS else "SINGLE"
        )
        for p in sd_doc.get("parameters", []):
            c = p["coordinate"]
            if c.get("filing_status") == fs_key and c.get("sub_parameter") == "basic_amount":
                sd_amount = Decimal(str(p["value"]))
                break

        # Current itemizable deductions other than charitable (approximated as zero
        # for the DAF quick-check; full AGI + SALT modeling is in the orchestrator)
        approx_other_itemized = (
            scenario.deductions.mortgage_interest_acquisition
            + min(
                scenario.deductions.salt_paid_state_income
                + scenario.deductions.salt_paid_property_residence,
                Decimal("40400"),  # 2026 MFJ SALT cap (approximate; SSALT evaluator refines)
            )
        )
        itemized_base = approx_other_itemized + total_charitable
        bunching_benefit = None
        if sd_amount is not None and itemized_base < sd_amount * Decimal(2):
            # Bunching 2 years of charitable into one year can lift the stacked
            # itemized total above the 2-year standard-deduction floor
            two_year_charitable = total_charitable * Decimal(2)
            stacked = approx_other_itemized * Decimal(2) + two_year_charitable
            two_year_sd = sd_amount * Decimal(2)
            bunching_benefit = max(stacked - two_year_sd, Decimal(0)) - max(
                (approx_other_itemized * Decimal(2) + total_charitable * Decimal(2))
                - itemized_base * Decimal(2),
                Decimal(0),
            )

        approx_marginal = Decimal("0.32")
        estimated_fed_save = (
            total_charitable * approx_marginal
        ).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "projected multi-year charitable giving plan",
                "preference for immediate vs deferred grants to operating charities",
                "DAF sponsoring organization (Fidelity, Schwab, community foundations)",
                "appreciated securities available to fund (preferred to cash)",
            ],
            assumptions=[
                f"Current-year charitable (cash + appreciated): ${total_charitable:,.2f}",
                f"Approx MAGI: ${magi:,.0f}",
                f"Standard deduction ({fs_key}): ${sd_amount:,.0f}" if sd_amount else "standard deduction awaiting cache",
                f"Approx other itemized (mortgage + SALT): ${approx_other_itemized:,.2f}",
                f"Approx marginal rate: {approx_marginal:.0%}",
            ],
            implementation_steps=[
                "Open a DAF account with a sponsoring §170(b)(1)(A) organization.",
                "Fund with appreciated securities held > 1 year for full FMV "
                "deduction (avoids capital-gain recognition, §170(e)(1)).",
                "Bunch 2-5 years of giving into the current year to stack above "
                "the standard-deduction threshold.",
                "Grant from DAF to operating charities over subsequent years; "
                "grantees receive cash, not appreciated property.",
                "Note OBBBA 0.5% AGI floor applies to itemizers starting 2026; "
                "DAF funding reduces the unrecovered-floor drag by bunching.",
            ],
            risks_and_caveats=[
                "DAF contributions are IRREVOCABLE upon sponsor acceptance.",
                "AGI limits: 60% for cash / 30% for appreciated property to a "
                "DAF (public-charity limits apply via the sponsoring org).",
                "OBBBA above-the-line $1,000 / $2,000 deduction does NOT apply "
                "to DAF contributions; only direct cash to operating charities.",
                "The 0.5% AGI floor (CHAR_OBBBA_05_FLOOR) chips the first 0.5% "
                "of AGI of itemized charitable each year; bunching minimizes "
                "this by concentrating giving in fewer floor-years.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CHAR_BUNCHING",
                "CHAR_APPREC_SECURITIES",
                "CHAR_PRE_SALE",
                "CHAR_OBBBA_05_FLOOR",
                "CHAR_OBBBA_37_CAP",
                "CHAR_AGI_LIMITS",
            ],
            verification_confidence="high",
            computation_trace={
                "current_charitable_total": str(total_charitable),
                "current_charitable_cash": str(current_charitable_cash),
                "current_charitable_appreciated": str(current_charitable_appreciated),
                "approx_magi": str(magi),
                "standard_deduction": str(sd_amount) if sd_amount else None,
                "approx_other_itemized": str(approx_other_itemized),
                "approx_bunching_benefit_2yr": str(bunching_benefit) if bunching_benefit else None,
            },
        )
