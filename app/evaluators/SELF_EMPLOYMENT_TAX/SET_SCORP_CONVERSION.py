"""SET_SCORP_CONVERSION — SE tax reduction via S corp conversion.

Companion to ENT_SOLE_TO_SCORP (entity-selection angle). This evaluator
focuses on the SE tax arithmetic: SECA on SE earnings is 15.3% up to
the OASDI wage base, 2.9% above it (plus 0.9% AddlMed over threshold).
S corp conversion subjects ONLY the reasonable comp to FICA, with the
K-1 distributive share NOT subject to SECA (Rev. Rul. 59-221).

Applicable when taxpayer has material SE income and no S corp already.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_MIN_SE_INCOME_FOR_APPLICABILITY = Decimal("60000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SET_SCORP_CONVERSION"
    CATEGORY_CODE = "SELF_EMPLOYMENT_TAX"
    PIN_CITES = [
        "IRC §1402(a) — self-employment income definition",
        "IRC §1402(a)(2) — S corp distributive share excluded from SECA",
        "Rev. Rul. 59-221 — S corp pass-through not SE income",
        "IRC §3101 / §3111 — FICA on wages",
        "IRC §3101(b)(2) — Additional Medicare tax 0.9%",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        se_income = scenario.income.self_employment_income
        already_scorp = any(
            e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            for e in scenario.entities
        )
        if already_scorp:
            return self._not_applicable(
                "taxpayer already has an S corp; SET_SCORP_CONVERSION applies "
                "to conversion from sole prop / partnership to S status"
            )
        if se_income < _MIN_SE_INCOME_FOR_APPLICABILITY:
            return self._not_applicable(
                f"SE income ${se_income:,.0f} below ${_MIN_SE_INCOME_FOR_APPLICABILITY:,.0f} "
                f"heuristic; S corp conversion is cost-justified above threshold"
            )

        fica = rules.get("federal/fica_wage_bases", year)
        addlmed = rules.get("federal/additional_medicare", year)

        oasdi_base_raw = None
        se_mult = Decimal("0.9235")
        for p in fica.get("parameters", []):
            sp = p["coordinate"].get("sub_parameter")
            if sp == "oasdi_wage_base":
                oasdi_base_raw = p.get("value")
            elif sp == "se_earnings_multiplier" and p.get("value") is not None:
                se_mult = Decimal(str(p["value"]))

        if oasdi_base_raw is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"OASDI wage base for {year} awaiting SSA fact sheet",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
            )

        oasdi_base = Decimal(str(oasdi_base_raw))
        se_net = se_income * se_mult

        # Current SE tax
        oasdi_portion = min(se_net, oasdi_base) * Decimal("0.124")
        medicare_portion = se_net * Decimal("0.029")
        current_se = (oasdi_portion + medicare_portion).quantize(Decimal("0.01"))

        # Post-conversion reasonable comp anchor 40%, FICA on that only
        rc = (se_net * Decimal("0.40")).quantize(Decimal("0.01"))
        rc_oasdi = min(rc, oasdi_base) * Decimal("0.124")
        rc_medicare = rc * Decimal("0.029")
        post_fica = (rc_oasdi + rc_medicare).quantize(Decimal("0.01"))

        gross_saving = (current_se - post_fica).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(gross_saving, Decimal(0)),
            savings_by_tax_type=TaxImpact(
                self_employment_tax=current_se,
                payroll_tax=-post_fica,
            ),
            inputs_required=[
                "projected SE net earnings (Schedule C line 31 × 0.9235)",
                "reasonable compensation band from COMP_REASONABLE_COMP",
                "state S-corp fee and minimum tax posture",
                "entity formation status (need LLC / corp shell first)",
            ],
            assumptions=[
                f"OASDI wage base: ${oasdi_base:,.0f}",
                f"SE multiplier: {se_mult}",
                f"SE income: ${se_income:,.2f}",
                f"SE net after multiplier: ${se_net:,.2f}",
                f"Current SE tax: ${current_se:,.2f}",
                f"Reasonable comp anchor (40% of SE net): ${rc:,.2f}",
                f"Post-conversion FICA on reasonable comp: ${post_fica:,.2f}",
                f"Gross SECA → FICA saving: ${gross_saving:,.2f}",
            ],
            implementation_steps=[
                "Pair with COMP_REASONABLE_COMP for a formal defensible "
                "compensation study.",
                "Coordinate with ENT_SOLE_TO_SCORP for the mechanical "
                "conversion path and Form 2553 timing.",
                "Model net-of-compliance-cost break-even — typical firm cost "
                "add-on is $3-5K/year; SE tax saving must exceed.",
                "If the taxpayer is in the 0.9% Additional Medicare zone, "
                "coordinate with SET_1402A13 variants for additional nuance.",
            ],
            risks_and_caveats=[
                "Reasonable compensation is the audit frontier for S corps. "
                "The 40% anchor is a planning proxy, not a defense. "
                "Document the three-factor analysis (Mulcahy, Watson).",
                "Retirement plan contribution capacity changes: Solo 401(k) "
                "employer PS at 25% of W-2 wages for S corp vs 20% of SE net "
                "for sole prop.",
                "QBI: S-corp officer wage reduces QBI dollar-for-dollar; "
                "coordinate with QBI_SCORP_WAGE_BALANCE.",
                "CA: 1.5% S-corp tax + $800 minimum. Factor into the "
                "breakeven.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "ENT_SOLE_TO_SCORP",
                "COMP_REASONABLE_COMP",
                "COMP_WAGE_DIST_SPLIT",
                "QBI_SCORP_WAGE_BALANCE",
                "RET_SOLO_401K",
                "SET_1402A13",
                "CA_LLC_FEE_MIN",
            ],
            verification_confidence="high",
            computation_trace={
                "se_income": str(se_income),
                "se_net": str(se_net),
                "current_se_tax": str(current_se),
                "reasonable_comp_anchor": str(rc),
                "post_conversion_fica": str(post_fica),
                "gross_saving": str(gross_saving),
            },
        )
