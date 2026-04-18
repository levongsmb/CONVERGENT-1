"""CHAR_OBBBA_37_CAP — 35% tax-benefit cap for 37% bracket itemizers.

OBBBA amended §68 to limit the value of itemized deductions to 35%
for taxpayers in the 37% top bracket. Mechanism: itemized deductions
are reduced by 2/37ths of the lesser of (a) total itemized deductions
or (b) the amount by which taxable income plus itemized deductions
exceeds the top-bracket threshold. Effective 35% rate cap on the
itemized value that would otherwise have reduced tax at 37%.

Note §199A deduction is computed without regard to this limitation.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


_TOP_BRACKET_RATE = Decimal("0.37")
_EFFECTIVE_CAP_RATE = Decimal("0.35")
_LIMITATION_MULTIPLIER = Decimal(2) / Decimal(37)


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CHAR_OBBBA_37_CAP"
    CATEGORY_CODE = "CHARITABLE"
    PIN_CITES = [
        "IRC §68 as amended by OBBBA — 35% tax-benefit cap for 37% bracket filers",
        "IRC §1(j)(2) — 37% bracket thresholds (per Rev. Proc.)",
        "P.L. 119-21 — OBBBA §68 amendments",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        total_itemized = (
            scenario.deductions.mortgage_interest_acquisition
            + scenario.deductions.investment_interest
            + scenario.deductions.salt_paid_state_income
            + scenario.deductions.salt_paid_property_residence
            + scenario.deductions.medical_expenses
            + scenario.deductions.charitable_cash_public
            + scenario.deductions.charitable_cash_pf_non_operating
            + scenario.deductions.charitable_cash_daf
            + scenario.deductions.charitable_appreciated_public
            + scenario.deductions.charitable_appreciated_private
        )
        if total_itemized <= Decimal(0):
            return self._not_applicable(
                "no itemized deductions in scenario; §68 cap applies to itemizers"
            )

        # Approx taxable income (orchestrator refines)
        approx_income = (
            scenario.income.wages_primary + scenario.income.wages_spouse
            + scenario.income.self_employment_income
            + scenario.income.interest_ordinary
            + scenario.income.dividends_ordinary + scenario.income.dividends_qualified
            + scenario.income.capital_gains_long_term
            + scenario.income.capital_gains_short_term
            + scenario.income.rental_income_net
            + sum(
                (k1.ordinary_business_income + k1.guaranteed_payments
                 for k1 in scenario.income.k1_income),
                start=Decimal(0),
            )
        )
        approx_taxable_income = approx_income - total_itemized

        # §1(j)(2) top-bracket threshold for 2026 (from brackets YAML)
        brackets = rules.get("federal/individual_brackets", year)
        filing_status = scenario.identity.filing_status
        fs_key = "MFJ" if filing_status == FilingStatus.MFJ else (
            "SINGLE" if filing_status == FilingStatus.SINGLE else None
        )
        top_threshold = None
        if fs_key is not None:
            for p in brackets.get("parameters", []):
                c = p["coordinate"]
                if (
                    c.get("filing_status") == fs_key
                    and c.get("sub_parameter") == "bracket_breakpoints_ordinary"
                    and isinstance(p.get("value"), list)
                ):
                    # Find the 37% bracket (last row)
                    for row in p["value"]:
                        if Decimal(str(row["rate"])) == Decimal("0.37"):
                            top_threshold = Decimal(str(row["lower"]))
                            break

        if top_threshold is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"37% bracket threshold for {fs_key or filing_status.value} not populated",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
                computation_trace={"year": year, "filing_status": fs_key},
            )

        # If approx taxable income + itemized is at or below top threshold,
        # the cap does not apply to this taxpayer.
        if approx_taxable_income + total_itemized <= top_threshold:
            return self._not_applicable(
                f"taxable income plus itemized (${approx_taxable_income + total_itemized:,.0f}) "
                f"is at or below the 37% bracket threshold (${top_threshold:,.0f}); "
                "§68 cap does not apply"
            )

        excess = (approx_taxable_income + total_itemized) - top_threshold
        limitation_basis = min(total_itemized, excess)
        reduction = (limitation_basis * _LIMITATION_MULTIPLIER).quantize(Decimal("0.01"))
        # Tax cost: the reduction reduces deductions in the 37% bracket, so the
        # marginal cost = reduction × 37% (since it would have been deducted at 37%)
        tax_cost = (reduction * _TOP_BRACKET_RATE).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "projected taxable income and itemized deductions",
                "bracket threshold for 37% bracket (Rev. Proc.)",
                "§199A deduction separately (not subject to this limitation)",
            ],
            assumptions=[
                f"§1(j)(2) top-bracket threshold ({fs_key}): ${top_threshold:,.0f}",
                f"Approx taxable income (post-itemized): ${approx_taxable_income:,.2f}",
                f"Total itemized deductions: ${total_itemized:,.2f}",
                f"Excess over top threshold: ${excess:,.2f}",
                f"Limitation basis (lesser): ${limitation_basis:,.2f}",
                f"Multiplier: 2/37ths ({_LIMITATION_MULTIPLIER:.5f})",
                f"Reduction to itemized: ${reduction:,.2f}",
                f"Effective tax cost at 37%: ${tax_cost:,.2f}",
            ],
            implementation_steps=[
                "Compute the §68 reduction on the Schedule A subtotal before "
                "applying the AGI percentage limits.",
                "Note §199A deduction is computed without regard to this cap — "
                "QBI deduction is unaffected.",
                "Multi-year planning: bunching charitable and SALT into a year "
                "where the taxpayer is below the 37% bracket (e.g., retirement "
                "year, sabbatical) avoids the cap entirely.",
            ],
            risks_and_caveats=[
                "The cap interacts with the CHAR_OBBBA_05_FLOOR 0.5% disallowance; "
                "ordering of the two rules follows §170(a) as amended — the "
                "floor applies first, then the §68 cap on the reduced itemized.",
                "State tax: the §68 cap is federal only; CA does not conform "
                "and does not apply a similar cap.",
                "Approx taxable income here excludes retirement contributions, "
                "QBI, and above-the-line items; orchestrator convergence "
                "refines against actual computed taxable income.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CHAR_OBBBA_05_FLOOR",
                "CHAR_BUNCHING",
                "CHAR_DAF",
                "QBI_INCOME_COMPRESSION",
                "RET_CASH_BALANCE",
            ],
            verification_confidence="high",
            computation_trace={
                "top_bracket_threshold": str(top_threshold),
                "approx_taxable_income": str(approx_taxable_income),
                "total_itemized": str(total_itemized),
                "excess_over_threshold": str(excess),
                "limitation_basis": str(limitation_basis),
                "reduction_to_itemized": str(reduction),
                "effective_tax_cost": str(tax_cost),
            },
        )
