"""QSBS_STATE_CONFORMITY — state conformity to §1202 (CA focus).

California repealed §1202 conformity effective 2013. A CA-resident
QSBS holder pays CA tax at ordinary rates (up to 12.3% plus 1%
Mental Health Services Tax on income above $1M) on the FULL gain —
the federal exclusion does not flow through.

The evaluator quantifies the CA tax drag and surfaces residency-
planning options (CA domicile break before the sale year) per
Decision 0009 and RD_CA_DOMICILE_BREAK.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, StateCode


# CA ordinary top rate (excluding MHST). Non-indexed in the rules
# cache; refresh when RTC §17041 brackets move. Surface as a
# module-level constant for now; Phase 3b wires a lookup into
# config/rules_cache/2026/california/brackets.yaml once added.
_CA_TOP_ORDINARY_RATE = Decimal("0.123")
_CA_MHST_RATE = Decimal("0.01")
_CA_MHST_THRESHOLD = Decimal("1000000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QSBS_STATE_CONFORMITY"
    CATEGORY_CODE = "QSBS_1202"
    PIN_CITES = [
        "CA R&TC §18152.5 (pre-2013) — former §1202 conformity, repealed",
        "CA R&TC §17041 — CA ordinary income tax rates",
        "CA R&TC §17043 — Mental Health Services Tax (1% over $1M)",
        "FTB Legal Ruling 1998-4 — sourcing of gain on intangibles",
        "Cutler v. FTB, 208 Cal. App. 4th 1247 (2012) — prior CA §1202 litigation",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        qsbs_lots = [
            a for a in scenario.assets
            if a.is_qsbs
            and a.fmv is not None
            and a.adjusted_basis is not None
            and (a.fmv - a.adjusted_basis) > Decimal(0)
        ]
        if not qsbs_lots:
            return self._not_applicable(
                "no appreciated QSBS lots in scenario; state conformity "
                "analysis requires QSBS with gain"
            )

        ca_connected = (
            scenario.identity.primary_state_domicile == StateCode.CA
            or scenario.identity.spouse_state_domicile == StateCode.CA
        )
        if not ca_connected:
            return self._not_applicable(
                "no CA domicile in scenario; QSBS_STATE_CONFORMITY focuses on "
                "CA nonconformity. Other non-conforming states (HI, MA, NJ, "
                "PA partial) are handled by future state-specific evaluators"
            )

        total_gain = sum(
            (a.fmv - a.adjusted_basis for a in qsbs_lots),
            start=Decimal(0),
        )

        ca_ordinary_tax = (total_gain * _CA_TOP_ORDINARY_RATE).quantize(Decimal("0.01"))
        mhst = Decimal(0)
        if total_gain > _CA_MHST_THRESHOLD:
            mhst = ((total_gain - _CA_MHST_THRESHOLD) * _CA_MHST_RATE).quantize(Decimal("0.01"))
        total_ca_tax = (ca_ordinary_tax + mhst).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # this evaluator surfaces exposure
            savings_by_tax_type=TaxImpact(state_income_tax=total_ca_tax),
            inputs_required=[
                "CA resident status on sale date",
                "potential CA domicile break facts (see RD_CA_DOMICILE_BREAK)",
                "state residency in year of issuance vs year of sale",
                "installment sale structure (CA §1031 clawback analog)",
            ],
            assumptions=[
                f"Aggregate QSBS gain: ${total_gain:,.2f}",
                f"CA top ordinary rate applied: {_CA_TOP_ORDINARY_RATE:.1%}",
                f"CA MHST: 1% above $1,000,000 income",
                f"CA ordinary tax: ${ca_ordinary_tax:,.2f}",
                f"CA MHST component: ${mhst:,.2f}",
                f"Total CA tax on QSBS gain: ${total_ca_tax:,.2f}",
                "Federal §1202 exclusion does NOT reduce the CA base.",
            ],
            implementation_steps=[
                "Model CA tax at sale year vs hypothetical post-domicile-break "
                "year. If the taxpayer credibly breaks CA domicile before the "
                "sale, the entire gain avoids CA tax.",
                "Document domicile-break facts per RD_CA_DOMICILE_BREAK: "
                "physical presence, driver's license, voter registration, "
                "physician of record, professional licensure, family, "
                "business contacts.",
                "Installment sale under §453 does not defer CA tax on the "
                "characterization year; sourcing and CA residency at payment "
                "receipt matter.",
                "If CA-residence at sale is unavoidable, quantify the drag "
                "in the memo and consider accelerating the sale into a year "
                "where federal §1202 exclusion is at the 50% or 75% tier "
                "(some CA tax vs. much less federal tax tradeoff).",
            ],
            risks_and_caveats=[
                "CA does not recognize §1045 rollover either; any rollover is "
                "a federal-only deferral.",
                "Part-year residency: CA taxes the portion of the gain "
                "sourced to CA residency. Sourcing of intangible-property "
                "gain follows domicile at date of sale per FTB Legal Ruling "
                "1998-4.",
                "CA 4-year lookback: post-domicile-break sales are audited "
                "aggressively for 'convenience' residency changes. Retain "
                "robust evidence.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CA_NONCONFORMITY_QSBS",
                "RD_CA_DOMICILE_BREAK",
                "RD_DAY_COUNT_SUBSTANT",
                "QSBS_HOLDING_PERIOD",
                "QSBS_OBBBA_TIERED",
                "QSBS_1045_ROLLOVER",
            ],
            verification_confidence="high",
            computation_trace={
                "total_qsbs_gain": str(total_gain),
                "ca_top_ordinary_rate": str(_CA_TOP_ORDINARY_RATE),
                "ca_ordinary_tax": str(ca_ordinary_tax),
                "ca_mhst_threshold": str(_CA_MHST_THRESHOLD),
                "ca_mhst": str(mhst),
                "total_ca_tax_on_qsbs_gain": str(total_ca_tax),
            },
        )
