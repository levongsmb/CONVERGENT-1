"""ENT_SOLE_TO_SCORP — sole proprietor to S corp conversion.

Converts a Schedule C sole prop (or SMLLC disregarded) to an S corp
election to reduce SECA exposure. Net SE earnings above the OASDI wage
base still attract 2.9% Medicare + 0.9% AddlMed; below the base, SECA
is 15.3%. The S corp election converts the K-1 distributive share to
non-SE-tax treatment; only the reasonable-comp W-2 portion carries FICA.

Breakeven analysis: additional compliance cost (payroll tax filings,
annual 1120-S, reasonable comp study, extra state fee) must be offset
by SECA savings.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_COMPLIANCE_COST_FLOOR = Decimal("3500")  # firm-level annual incremental cost estimate
_MIN_SE_NET_FOR_BREAKEVEN = Decimal("60000")  # heuristic


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "ENT_SOLE_TO_SCORP"
    CATEGORY_CODE = "ENTITY_SELECTION"
    PIN_CITES = [
        "IRC §1361 — S corporation definition and eligibility",
        "IRC §1362 — election of small business corporation",
        "IRC §1402(a) — SECA on net earnings from SE",
        "IRC §3121(d) — employee status for FICA",
        "IRC §162 — reasonable comp as §1.162-7 compensation",
        "Rev. Rul. 59-221 — S corp pass-through NOT subject to SECA",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        se_income = scenario.income.self_employment_income
        sole_props = [
            e for e in scenario.entities
            if e.type in (EntityType.SOLE_PROP, EntityType.LLC_DISREGARDED)
        ]
        has_scorp_already = any(
            e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
            for e in scenario.entities
        )

        if has_scorp_already:
            return self._not_applicable(
                "scenario already has an S corp; ENT_SOLE_TO_SCORP is a "
                "conversion evaluator for non-S entities"
            )
        if not sole_props and se_income == Decimal(0):
            return self._not_applicable(
                "no sole prop / SMLLC disregarded and no SE income; "
                "S corp election is not applicable"
            )

        if se_income < _MIN_SE_NET_FOR_BREAKEVEN and se_income > Decimal(0):
            return self._not_applicable(
                f"SE net earnings ${se_income:,.0f} below ${_MIN_SE_NET_FOR_BREAKEVEN:,.0f} "
                f"breakeven heuristic; S corp conversion typically not cost-justified"
            )

        fica = rules.get("federal/fica_wage_bases", year)
        oasdi_base_raw = None
        se_multiplier = Decimal("0.9235")
        for p in fica.get("parameters", []):
            sp = p["coordinate"].get("sub_parameter")
            if sp == "oasdi_wage_base":
                oasdi_base_raw = p.get("value")
            elif sp == "se_earnings_multiplier" and p.get("value") is not None:
                se_multiplier = Decimal(str(p["value"]))

        if oasdi_base_raw is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"OASDI wage base for {year} awaiting SSA fact sheet",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
            )

        oasdi_base = Decimal(str(oasdi_base_raw))

        # Net SE earnings subject to SECA (post 0.9235 multiplier)
        se_net = se_income * se_multiplier

        # Assume reasonable comp = 40% of SE net as a first-order anchor.
        # Actual comp set by COMP_REASONABLE_COMP; this is breakeven only.
        assumed_reasonable_comp = (se_net * Decimal("0.40")).quantize(Decimal("0.01"))

        # Current SE tax
        se_oasdi = min(se_net, oasdi_base) * Decimal("0.124")
        se_medicare = se_net * Decimal("0.029")
        current_se_tax = (se_oasdi + se_medicare).quantize(Decimal("0.01"))

        # Post-conversion FICA on reasonable comp only
        rc_oasdi = min(assumed_reasonable_comp, oasdi_base) * Decimal("0.124")
        rc_medicare = assumed_reasonable_comp * Decimal("0.029")
        post_conversion_fica = (rc_oasdi + rc_medicare).quantize(Decimal("0.01"))

        gross_savings = (current_se_tax - post_conversion_fica).quantize(Decimal("0.01"))
        net_savings = (gross_savings - _COMPLIANCE_COST_FLOOR).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(net_savings, Decimal(0)),
            savings_by_tax_type=TaxImpact(
                self_employment_tax=current_se_tax,
                payroll_tax=-post_conversion_fica,  # paid at entity level
            ),
            inputs_required=[
                "SE net earnings projection (Schedule C line 31)",
                "reasonable compensation study (see COMP_REASONABLE_COMP)",
                "state S corp fee and minimum tax (CA: $800 + 1.5% or min)",
                "existing entity formation state and election deadline (Form 2553)",
            ],
            assumptions=[
                f"OASDI wage base: ${oasdi_base:,.0f}",
                f"SE earnings multiplier: {se_multiplier}",
                f"Current SE net: ${se_net:,.2f}",
                f"Reasonable comp anchor (40% of SE net): ${assumed_reasonable_comp:,.2f}",
                f"Incremental compliance cost assumed: ${_COMPLIANCE_COST_FLOOR:,.0f}/year",
                f"Gross SECA → FICA savings: ${gross_savings:,.2f}",
                f"Net savings after compliance cost: ${net_savings:,.2f}",
            ],
            implementation_steps=[
                "Form the entity (if SMLLC, file state election; if sole prop, "
                "form LLC first).",
                "File Form 2553 within 75 days of election effective date.",
                "Establish payroll with a provider; set up §1.162-7 reasonable "
                "comp documentation.",
                "Coordinate with COMP_REASONABLE_COMP for the compensation study.",
                "File Form 1120-S for the S corp in addition to Form 1040.",
            ],
            risks_and_caveats=[
                "Reasonable compensation is the audit frontier. Mulcahy / "
                "Watson require the officer wage to pass a three-factor test; "
                "a 40% heuristic is a planning anchor, not a defense.",
                "CA: 1.5% S corp franchise tax + $800 minimum. Factor into "
                "breakeven.",
                "SE-tax retirement contribution base changes: Solo 401(k) "
                "employer PS at 25% of W-2 wages for S corp vs 20% of SE net "
                "for sole prop. Coordinate with RET_SOLO_401K.",
                "QBI at S corp reduces by officer wage dollar-for-dollar; "
                "coordinate with QBI_SCORP_WAGE_BALANCE.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "COMP_REASONABLE_COMP",
                "COMP_WAGE_DIST_SPLIT",
                "QBI_SCORP_WAGE_BALANCE",
                "SET_SCORP_CONVERSION",
                "RET_SOLO_401K",
                "CA_LLC_FEE_MIN",
            ],
            verification_confidence="high",
            computation_trace={
                "se_income": str(se_income),
                "se_net_after_multiplier": str(se_net),
                "assumed_reasonable_comp": str(assumed_reasonable_comp),
                "current_se_tax": str(current_se_tax),
                "post_conversion_fica": str(post_conversion_fica),
                "gross_savings": str(gross_savings),
                "compliance_cost_assumed": str(_COMPLIANCE_COST_FLOOR),
                "net_savings": str(net_savings),
            },
        )
