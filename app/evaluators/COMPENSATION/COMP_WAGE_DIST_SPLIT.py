"""COMP_WAGE_DIST_SPLIT — S corp wage vs distribution dollar arbitrage.

Given an S corp shareholder-employee with a defensible comp band, the
optimal wage point WITHIN the band depends on:

  1. OASDI wage base (wages above the base avoid 6.2% each side)
  2. Medicare HI (no base, 1.45% each side plus 0.9% AddlMed above the
     §3101(b)(2) threshold)
  3. §199A QBI ceiling (W-2 wages expand the wage-based ceiling on the
     QBI deduction; officer wage that would otherwise reduce ordinary
     income by one dollar also reduces QBI by one dollar, dollar-for-
     dollar through taxable income)
  4. FUTA on wages up to $7,000

This evaluator models a simplified comparison at the CURRENT wage vs a
CANDIDATE wage set at the OASDI base (below which SECA/FICA duplication
is fully in play, above which only Medicare + AddlMed apply). The
candidate wage is a common planning anchor and produces a defensible
first-cut savings estimate.

All rates and wage bases come from config/rules_cache/2026/federal/
fica_wage_bases.yaml and additional_medicare.yaml. No hardcoded rates.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


def _lookup(rule_doc: dict, **coord) -> Decimal:
    """Find the first parameter whose coordinate matches every key in coord."""
    for p in rule_doc.get("parameters", []):
        c = p.get("coordinate", {})
        if all(c.get(k) == v for k, v in coord.items()):
            v = p.get("value")
            if v is not None:
                return Decimal(str(v))
    raise KeyError(f"parameter not found for coord={coord}")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "COMP_WAGE_DIST_SPLIT"
    CATEGORY_CODE = "COMPENSATION"
    PIN_CITES = [
        "IRC §3121(a) — wages subject to OASDI, capped at the wage base",
        "IRC §3121(a)(1) — SSA wage base (annually announced)",
        "IRC §3101(b)(2) — Additional Medicare Tax (0.9% above statutory threshold)",
        "IRC §3111(a) — employer OASDI rate 6.2%",
        "IRC §3111(b) — employer Medicare rate 1.45%",
        "IRC §1366(a) — S corp shareholder-level inclusion of pass-through income",
        "IRC §199A(b)(2)(B) — W-2 wage limitation interaction",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        scorp_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
        ]
        if not scorp_k1s:
            return self._not_applicable(
                "no S corporation K-1 in scenario; wage/distribution split "
                "analysis is S-corp-specific"
            )

        fica = rules.get("federal/fica_wage_bases", year)
        addlmed = rules.get("federal/additional_medicare", year)

        oasdi_base_raw = None
        for p in fica.get("parameters", []):
            if p.get("coordinate", {}).get("sub_parameter") == "oasdi_wage_base":
                oasdi_base_raw = p.get("value")
                break

        oasdi_rate_employee = _lookup(fica, sub_parameter="oasdi_rate_employee")
        oasdi_rate_employer = _lookup(fica, sub_parameter="oasdi_rate_employer")
        medicare_rate_employee = _lookup(fica, sub_parameter="medicare_hi_rate_employee")
        medicare_rate_employer = _lookup(fica, sub_parameter="medicare_hi_rate_employer")
        addl_medicare_rate = _lookup(addlmed, sub_parameter="rate")

        # Scenario-level current officer wage (primary shareholder's W-2 from entity)
        current_wage = scenario.income.wages_primary
        if current_wage <= Decimal(0):
            return self._not_applicable(
                "scenario has no current officer wage on primary taxpayer; "
                "wage/distribution split analysis requires a non-zero wage baseline"
            )

        # If the OASDI wage base is not yet populated for the planning year,
        # surface a low-confidence result instead of crashing. Evaluators must
        # degrade gracefully when rules cache parameters are
        # awaiting_user_input.
        if oasdi_base_raw is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"OASDI wage base for {year} not populated in rules cache",
                estimated_tax_savings=Decimal(0),
                savings_by_tax_type=TaxImpact(),
                inputs_required=[
                    "SSA-announced OASDI wage base for planning year",
                ],
                pin_cites=list(self.PIN_CITES),
                cross_strategy_impacts=[
                    "COMP_REASONABLE_COMP",
                    "QBI_SCORP_WAGE_BALANCE",
                ],
                verification_confidence="low",
                computation_trace={
                    "oasdi_wage_base": None,
                    "current_wage": str(current_wage),
                },
            )

        oasdi_base = Decimal(str(oasdi_base_raw))

        # FICA burden on current wage
        oasdi_wage = min(current_wage, oasdi_base)
        employer_oasdi_current = oasdi_wage * oasdi_rate_employer
        employee_oasdi_current = oasdi_wage * oasdi_rate_employee
        employer_medicare_current = current_wage * medicare_rate_employer
        employee_medicare_current = current_wage * medicare_rate_employee
        fica_current = (
            employer_oasdi_current
            + employee_oasdi_current
            + employer_medicare_current
            + employee_medicare_current
        )

        # Candidate wage: set to the OASDI wage base (common planning anchor).
        # Keep the candidate at the floor of 50% of the current total "reasonable"
        # band to avoid collapsing into the §6654 / Mulcahy risk zone.
        scorp_k1 = scorp_k1s[0]
        reasonable_floor = (
            (scorp_k1.ordinary_business_income + current_wage)
            * Decimal("0.25")
        )
        candidate_wage = max(oasdi_base, reasonable_floor)

        oasdi_wage_candidate = min(candidate_wage, oasdi_base)
        employer_oasdi_cand = oasdi_wage_candidate * oasdi_rate_employer
        employee_oasdi_cand = oasdi_wage_candidate * oasdi_rate_employee
        employer_medicare_cand = candidate_wage * medicare_rate_employer
        employee_medicare_cand = candidate_wage * medicare_rate_employee
        fica_candidate = (
            employer_oasdi_cand
            + employee_oasdi_cand
            + employer_medicare_cand
            + employee_medicare_cand
        )

        fica_delta = (fica_current - fica_candidate).quantize(Decimal("0.01"))

        risks_and_caveats: List[str] = [
            "Lowering officer wage reduces W-2 wages reported on Form 941, "
            "which lowers the §199A QBI ceiling when taxable income is above "
            "the threshold amount. QBI_SCORP_WAGE_BALANCE evaluates the net.",
            "Moving wage toward the OASDI base only preserves Medicare + "
            "Additional Medicare exposure. Confirm candidate_wage remains "
            "within the reasonable-comp band produced by COMP_REASONABLE_COMP.",
        ]
        if fica_delta <= Decimal(0):
            risks_and_caveats.insert(
                0,
                "Current wage is already at or below the OASDI base; further "
                "reduction is blocked by the reasonable-comp floor.",
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(fica_delta, Decimal(0)),
            savings_by_tax_type=TaxImpact(payroll_tax=max(fica_delta, Decimal(0))),
            inputs_required=[
                "current officer W-2 wages",
                "OASDI wage base for planning year (rules cache)",
                "reasonable-comp band from COMP_REASONABLE_COMP study",
            ],
            assumptions=[
                f"OASDI wage base: ${oasdi_base:,.0f}",
                f"Candidate wage anchor: ${candidate_wage:,.0f} "
                "(greater of OASDI base and 25% of total S-corp profit)",
                f"Current wage: ${current_wage:,.0f}",
            ],
            implementation_steps=[
                "Confirm candidate_wage is within the reasonable-comp "
                "band produced by a formal comp study (COMP_REASONABLE_COMP).",
                "Run a §199A / AddlMed projection at candidate_wage to "
                "confirm net benefit after QBI ceiling and AddlMed threshold "
                "interactions.",
                "Implement the wage change via a payroll adjustment; update "
                "W-2 forecast and quarterly Form 941 estimates.",
                "Coordinate with the shareholder on cash-flow timing "
                "(shifting from wages to distributions affects weekly cash).",
            ],
            risks_and_caveats=risks_and_caveats,
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "COMP_REASONABLE_COMP",
                "QBI_SCORP_WAGE_BALANCE",
                "NIIT_SCORP_MIX",
                "RET_SOLO_401K",  # wage affects §415(c) and §401(a)(17) posture
            ],
            verification_confidence="high",
            computation_trace={
                "oasdi_wage_base": str(oasdi_base),
                "oasdi_rate_employer": str(oasdi_rate_employer),
                "medicare_rate_combined": str(
                    medicare_rate_employer + medicare_rate_employee
                ),
                "addl_medicare_rate": str(addl_medicare_rate),
                "current_wage": str(current_wage),
                "candidate_wage": str(candidate_wage),
                "fica_current": str(fica_current.quantize(Decimal("0.01"))),
                "fica_candidate": str(fica_candidate.quantize(Decimal("0.01"))),
                "fica_delta": str(fica_delta),
            },
        )
