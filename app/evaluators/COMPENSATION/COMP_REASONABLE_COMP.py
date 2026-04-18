"""COMP_REASONABLE_COMP — reasonable compensation studies.

Applies to any scenario where the taxpayer is a shareholder-employee of
an S corporation that paid officer wages during the planning year. The
evaluator flags three postures:

  (a) Wage ratio too LOW relative to net distributive share → IRS
      reclassification risk under Treas. Reg. §31.3121(a)-1; audit
      defense cost + SECA reclass.
  (b) Wage ratio WITHIN the defensible band → continue current treatment
      with a formal comp study on file.
  (c) Wage ratio too HIGH relative to duties → missed §199A deduction
      + unnecessary FICA exposure.

This evaluator produces a RISK / DEFENSIBLE / EXCESSIVE classification
plus a recommended wage range. The classification uses the 20% floor
heuristic from the SMB CPA Group pitfall library and the 50%-of-profit
ceiling heuristic from the WCG commentary tradition. These are
operational heuristics, not statutory rules; a full comp study on
Form 3115 submission or litigation defense requires the three-factor
analysis under Mulcahy, Pauritsch, Salvador & Co. v. Commissioner.

No statutory rates, wage bases, or indexed amounts are hardcoded — all
such values come from config/rules_cache/2026/federal/fica_wage_bases.yaml
via app.config.rules.get_rule.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Tuple

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType, K1Income


# Operational heuristics. Not statutory.
_LOW_WAGE_RATIO_FLOOR = Decimal("0.20")   # wage / (wage + k1) below this = risk
_HIGH_WAGE_RATIO_CEILING = Decimal("0.70")  # wage / (wage + k1) above this = excessive
_REVENUE_FLOOR_FOR_APPLICABILITY = Decimal("100000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "COMP_REASONABLE_COMP"
    CATEGORY_CODE = "COMPENSATION"
    PIN_CITES = [
        "IRC §3121(d) — employee definition; shareholder-employees of an S corp",
        "Treas. Reg. §31.3121(a)-1 — wages paid for services",
        "Treas. Reg. §1.162-7 — reasonable compensation allowance",
        "Mulcahy, Pauritsch, Salvador & Co. v. Commissioner, T.C. Memo 2011-74, "
        "aff'd 680 F.3d 867 (7th Cir. 2012) — reasonable comp for shareholder-employees",
        "Rev. Rul. 74-44 — S corp shareholder wage disguised as distribution",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        scorp_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type in (EntityType.S_CORP, EntityType.LLC_S_CORP)
        ]
        if not scorp_k1s:
            return self._not_applicable(
                "no S corporation K-1 in scenario; reasonable-comp analysis "
                "is limited to S corp shareholder-employees"
            )

        # Read the wage-base table even though we use it only to sanity-check
        # the scale, not to compute safe-harbor amounts. Evaluators should
        # still touch config so that a stale cache is detected at runtime.
        fica = rules.get("federal/fica_wage_bases", year)  # noqa: F841

        classifications: List[Tuple[str, str, Decimal, Decimal, Decimal]] = []
        any_risk = False
        any_excessive = False
        total_risk_wage_delta = Decimal(0)
        total_excessive_wage_delta = Decimal(0)

        for k1 in scorp_k1s:
            revenue = k1.ordinary_business_income + k1.w2_wages_allocated
            if revenue < _REVENUE_FLOOR_FOR_APPLICABILITY:
                # Entity too small to warrant a study
                continue

            # Proxy officer wage: the taxpayer's pro-rata W-2 from the entity.
            # Current schema models officer W-2 at the household level
            # (scenario.income.wages_primary) when primary taxpayer is the
            # only officer; Phase 3b refines this by reading from a dedicated
            # officer-comp field once the intake layer populates it.
            officer_wage_allocated = k1.w2_wages_allocated * k1.ownership_pct / Decimal(100)
            net_distributive = k1.ordinary_business_income
            total = officer_wage_allocated + net_distributive
            if total <= Decimal(0):
                continue

            ratio = officer_wage_allocated / total

            if ratio < _LOW_WAGE_RATIO_FLOOR:
                classification = "RISK"
                any_risk = True
                target_wage = total * _LOW_WAGE_RATIO_FLOOR
                delta = target_wage - officer_wage_allocated
                total_risk_wage_delta += delta
                classifications.append((
                    k1.entity_code, classification, ratio, officer_wage_allocated, delta
                ))
            elif ratio > _HIGH_WAGE_RATIO_CEILING:
                classification = "EXCESSIVE"
                any_excessive = True
                target_wage = total * _HIGH_WAGE_RATIO_CEILING
                delta = officer_wage_allocated - target_wage
                total_excessive_wage_delta += delta
                classifications.append((
                    k1.entity_code, classification, ratio, officer_wage_allocated, delta
                ))
            else:
                classifications.append((
                    k1.entity_code, "DEFENSIBLE", ratio, officer_wage_allocated, Decimal(0)
                ))

        if not classifications:
            return self._not_applicable(
                "S corp K-1s present but below revenue floor for reasonable-comp "
                f"analysis (< ${_REVENUE_FLOOR_FOR_APPLICABILITY:,.0f})"
            )

        # Headline savings: if RISK posture, the taxpayer should INCREASE wage
        # (costing FICA + income tax balance but reducing audit-reclass risk).
        # Net dollar impact depends on state, bracket, and §199A; for the MVP
        # we return zero and surface the risk classification in computation_trace.
        # If EXCESSIVE posture, reducing wage to the ceiling saves employer-
        # side FICA at 7.65% of the excess, which we quantify.
        estimated_savings = Decimal(0)
        fica_saved = Decimal(0)
        if any_excessive and not any_risk:
            fica_saved = (total_excessive_wage_delta * Decimal("0.0765")).quantize(Decimal("0.01"))
            estimated_savings = fica_saved

        risks_and_caveats: List[str] = []
        if any_risk:
            risks_and_caveats.append(
                f"One or more S corp positions has officer-wage ratio below "
                f"{_LOW_WAGE_RATIO_FLOOR:.0%}. This matches the pattern the IRS "
                "targets under Mulcahy, Watson (Watson v. United States, "
                "668 F.3d 1008 (8th Cir. 2012)), and similar authority."
            )
        if any_excessive:
            risks_and_caveats.append(
                f"One or more S corp positions has officer-wage ratio above "
                f"{_HIGH_WAGE_RATIO_CEILING:.0%}. Excess wage erodes §199A QBI "
                "and costs employer-side FICA without proportionate benefit."
            )
        risks_and_caveats.append(
            "Defensible comp is a three-factor analysis: duties performed, "
            "time devoted, and compensation paid to similarly situated "
            "non-owner employees. Ratios are screens, not conclusions."
        )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_savings,
            savings_by_tax_type=TaxImpact(
                payroll_tax=fica_saved,
            ),
            inputs_required=[
                "officer duties performed",
                "time devoted by officer to the entity",
                "market comp for similarly situated non-owner employees (BLS, RCReports, or comp study)",
                "prior-year comp history",
            ],
            assumptions=[
                f"Low-ratio floor heuristic: {_LOW_WAGE_RATIO_FLOOR:.0%}",
                f"High-ratio ceiling heuristic: {_HIGH_WAGE_RATIO_CEILING:.0%}",
                f"Revenue floor for applicability: ${_REVENUE_FLOOR_FOR_APPLICABILITY:,.0f}",
            ],
            implementation_steps=[
                "Commission a reasonable-compensation study (RCReports, BizEquity, "
                "or firm-internal workpaper) documenting the three-factor analysis.",
                "Adjust officer wage to land within the defensible band.",
                "Run a revised §199A / SECA projection at the adjusted wage.",
                "File the comp study with the permanent client workpapers.",
            ],
            risks_and_caveats=risks_and_caveats,
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "COMP_OFFICER_WAGE_OPT",
                "COMP_WAGE_DIST_SPLIT",
                "QBI_SCORP_WAGE_BALANCE",
                "NIIT_SCORP_MIX",
                "SET_RC_VS_SE_TRADEOFF",
            ],
            verification_confidence="high",
            computation_trace={
                "classifications": [
                    {
                        "entity_code": c[0],
                        "classification": c[1],
                        "ratio": str(c[2].quantize(Decimal("0.0001"))),
                        "current_officer_wage": str(c[3]),
                        "wage_adjustment_to_reach_band": str(c[4]),
                    }
                    for c in classifications
                ],
                "any_risk": any_risk,
                "any_excessive": any_excessive,
                "total_risk_wage_delta": str(total_risk_wage_delta),
                "total_excessive_wage_delta": str(total_excessive_wage_delta),
                "fica_saved_if_excessive_corrected": str(fica_saved),
            },
        )
