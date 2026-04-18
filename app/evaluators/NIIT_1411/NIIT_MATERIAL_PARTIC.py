"""NIIT_MATERIAL_PARTIC — §1411 material participation carve-out.

Under §1411, net investment income includes income from passive trade
or businesses but EXCLUDES income from nonpassive trades or businesses
in which the taxpayer materially participates. Flipping a trade or
business from passive to nonpassive — via grouping under Treas. Reg.
§1.469-4 or meeting one of the seven material-participation tests
under §1.469-5T(a) — removes the 3.8% NIIT.

Applicable when the scenario has K-1 ordinary business income
(positive) AND the taxpayer's MAGI is above the §1411(b) threshold.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType, FilingStatus


def _param(doc: dict, **coord) -> Optional[Decimal]:
    for p in doc.get("parameters", []):
        c = p.get("coordinate", {})
        if all(c.get(k) == v for k, v in coord.items()):
            v = p.get("value")
            if v is None:
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return None
    return None


def _approx_magi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    base = (
        income.wages_primary + income.wages_spouse
        + income.self_employment_income
        + income.interest_ordinary
        + income.dividends_ordinary + income.dividends_qualified
        + income.capital_gains_long_term + income.capital_gains_short_term
        + income.rental_income_net + income.pension_ira_distributions
    )
    for k1 in income.k1_income:
        base += k1.ordinary_business_income + k1.guaranteed_payments
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "NIIT_MATERIAL_PARTIC"
    CATEGORY_CODE = "NIIT_1411"
    PIN_CITES = [
        "IRC §1411(a) — 3.8% NIIT rate",
        "IRC §1411(b) — MAGI thresholds ($250K MFJ / $200K single; statutory)",
        "IRC §1411(c)(2) — nonpassive trade or business exclusion",
        "Treas. Reg. §1.1411-5 — active trade or business treatment",
        "Treas. Reg. §1.469-5T(a) — seven material-participation tests",
        "Treas. Reg. §1.469-4 — grouping rules",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        k1s_with_income = [
            k1 for k1 in scenario.income.k1_income
            if k1.ordinary_business_income > Decimal(0)
            and k1.entity_type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
            )
        ]
        if not k1s_with_income:
            return self._not_applicable(
                "no partnership / S corp K-1 with positive ordinary business "
                "income; §1411 material-participation carve-out is trade-or-"
                "business-income-specific"
            )

        niit = rules.get("federal/niit", year)
        filing_status = scenario.identity.filing_status
        fs_key = (
            "MFJ" if filing_status == FilingStatus.MFJ else
            "MFS" if filing_status == FilingStatus.MFS else
            "HOH" if filing_status == FilingStatus.HOH else "SINGLE"
        )
        threshold = _param(
            niit, tax_year=year, filing_status=fs_key, sub_parameter="magi_threshold"
        )

        magi = _approx_magi(scenario)
        if threshold is not None and magi <= threshold:
            return self._not_applicable(
                f"MAGI ${magi:,.0f} at or below §1411(b) threshold "
                f"${threshold:,.0f} ({fs_key}); NIIT does not apply"
            )

        rate = _param(niit, tax_year=year, filing_status="ANY", sub_parameter="rate") or Decimal("0.038")

        # Protect income potentially exposed to NIIT that could be carved
        # out via material participation. First-order proxy: all partnership
        # ordinary income passive-to-active could save 3.8%.
        at_risk_income = sum(
            (k1.ordinary_business_income for k1 in k1s_with_income),
            start=Decimal(0),
        )
        potential_niit_saving = (at_risk_income * rate).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=potential_niit_saving,
            savings_by_tax_type=TaxImpact(niit=potential_niit_saving),
            inputs_required=[
                "hours worked per activity (seven §1.469-5T(a) tests)",
                "§1.469-4 grouping elections in place",
                "taxpayer's role in each entity (officer, manager, silent)",
                "K-1 Box 1 / Box 2 income nature per activity",
            ],
            assumptions=[
                f"Approx MAGI: ${magi:,.0f}",
                f"§1411(b) threshold ({fs_key}): "
                f"${threshold:,.0f}" if threshold else "threshold null",
                f"NIIT rate: {rate:.1%}",
                f"K-1 positions with ordinary income: {len(k1s_with_income)}",
                f"Aggregate at-risk income: ${at_risk_income:,.2f}",
                f"Potential NIIT saving if all activities nonpassive: "
                f"${potential_niit_saving:,.2f}",
            ],
            implementation_steps=[
                "Document material participation hours per activity "
                "(contemporaneous log — IRS challenges post-hoc logs).",
                "Apply the seven §1.469-5T(a) tests: 500 hours, substantially "
                "all participation, 100+ hours and more than anyone else, "
                "significant-participation aggregate 500+, 5 of last 10 years, "
                "personal-service activity, facts-and-circumstances test.",
                "File §1.469-4 grouping election for related activities where "
                "aggregation helps reach a test threshold.",
                "For active S-corp shareholder-employees, material "
                "participation is generally clear; partnership limited "
                "partners may need to shift economic role.",
                "Coordinate with SET_SOROBAN_RISK for §1402(a)(13) interaction.",
            ],
            risks_and_caveats=[
                "Contemporaneous documentation is critical. Courts have "
                "rejected reconstructed logs in Moss, Tolin, and others.",
                "§1411 active test for S-corp shareholders: must materially "
                "participate under §469 regs. Working officer generally "
                "qualifies; silent shareholder does not.",
                "Self-charged interest and rent between taxpayer and flow-"
                "through entities require careful §1411 analysis under "
                "§1.1411-4(g).",
                "Spouses' hours combine for §469 material participation "
                "(MFJ), but not for §1402 SE tax purposes.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "NIIT_GROUPING",
                "NIIT_SCORP_MIX",
                "NIIT_REP_PLANNING",
                "NIIT_BUSINESS_VS_INVEST",
                "LL_469_PASSIVE",
                "LL_469_GROUPING",
                "LL_REP_STATUS",
                "SET_1402A13",
            ],
            verification_confidence="high",
            computation_trace={
                "magi_approx": str(magi),
                "threshold": str(threshold) if threshold else None,
                "threshold_populated": threshold is not None,
                "filing_status": fs_key,
                "niit_rate": str(rate),
                "k1_positions": len(k1s_with_income),
                "at_risk_income": str(at_risk_income),
                "potential_niit_saving_if_nonpassive": str(potential_niit_saving),
            },
        )
