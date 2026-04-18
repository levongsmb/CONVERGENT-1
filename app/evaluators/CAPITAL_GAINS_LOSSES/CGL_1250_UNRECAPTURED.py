"""CGL_1250_UNRECAPTURED — 25% rate on unrecaptured §1250 gain.

When real property with straight-line depreciation is sold, the
depreciation portion of the gain is "unrecaptured §1250 gain" taxed at
a maximum 25% rate under §1(h)(6). Planning: manage the interaction
with §1031 deferral, installment sale spreading, and §121 exclusion.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CGL_1250_UNRECAPTURED"
    CATEGORY_CODE = "CAPITAL_GAINS_LOSSES"
    PIN_CITES = [
        "IRC §1(h)(6) — 25% maximum rate on unrecaptured §1250 gain",
        "IRC §1250 — depreciation recapture on real property",
        "IRC §453 — installment sale spreading",
        "IRC §1031 — like-kind exchange deferral",
        "IRC §121 — principal residence exclusion",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        direct = scenario.income.unrecaptured_1250_gain
        k1_1250 = sum(
            (k1.unrecaptured_1250_gain for k1 in scenario.income.k1_income),
            start=Decimal(0),
        )
        total = direct + k1_1250
        if total <= Decimal(0):
            return self._not_applicable(
                "no unrecaptured §1250 gain in scenario; evaluator is "
                "real-property-disposition-specific"
            )

        # Rate differential vs 20% LTCG + 3.8% NIIT = 23.8% on LTCG
        # §1250 unrecaptured is capped at 25%. The tax cost above LTCG
        # portion is 25% - 23.8% = 1.2% (assuming top-bracket NIIT).
        # But §1411 NIIT also applies to §1250 unrecaptured component.
        niit_component = total * Decimal("0.038")
        base_1250_tax = total * Decimal("0.25")
        total_fed_on_gain = (base_1250_tax + niit_component).quantize(Decimal("0.01"))

        # Planning value: deferral or acceleration windows
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # planning surfaces the exposure
            savings_by_tax_type=TaxImpact(capital_gains_tax=total_fed_on_gain),
            inputs_required=[
                "accumulated depreciation taken on each real-property asset sold",
                "§1031 replacement property identification window (45 + 180 days)",
                "§453A interest accrual posture if installment receivable > $5M",
                "§121 principal-residence exclusion availability",
            ],
            assumptions=[
                f"Aggregate unrecaptured §1250 gain: ${total:,.2f}",
                f"§1(h)(6) maximum rate: 25%",
                f"§1411 NIIT stacking: 3.8% where MAGI threshold exceeded",
                f"Base §1250 federal tax: ${base_1250_tax:,.2f}",
                f"NIIT component (if MAGI above threshold): ${niit_component:,.2f}",
                f"Total federal tax on §1250 unrecaptured gain: ${total_fed_on_gain:,.2f}",
            ],
            implementation_steps=[
                "For a planned real-property sale, quantify the accumulated "
                "depreciation component BEFORE the sale — the seller often "
                "focuses on economic gain and misses the §1250 piece.",
                "Evaluate §1031 like-kind exchange to defer the entire gain "
                "(including §1250 unrecaptured). Coordinate with RED1031_* "
                "evaluators on execution.",
                "Evaluate installment-sale spreading under §453 to smooth "
                "the §1250 rate impact; watch §453A interest on large notes.",
                "If the property qualifies for §121, the exclusion reduces "
                "§1250 unrecaptured pro-rata; document §121(a) use and "
                "ownership tests.",
            ],
            risks_and_caveats=[
                "§1250 unrecaptured gain is a §1(h) rate characterization, "
                "NOT ordinary-income recapture. Full recapture of §1250 is "
                "only for accelerated depreciation, which is not used on "
                "post-1986 realty under §168 straight-line.",
                "CA does not apply preferential capital-gain rates: §1250 "
                "gain is taxed at ordinary CA rates up to ~13.3% plus MHST.",
                "§453A interest applies if the installment note exceeds $5M.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RED_RECAPTURE_PLAN",
                "RED_INSTALL_RECAPTURE",
                "RED1031_FORWARD",
                "INST_STANDARD_453",
                "CGL_1231",
                "NIIT_INSTALL_TIMING",
            ],
            verification_confidence="high",
            computation_trace={
                "direct_1250": str(direct),
                "k1_1250": str(k1_1250),
                "total_1250": str(total),
                "base_1250_tax_at_25pct": str(base_1250_tax),
                "niit_component_at_3_8pct": str(niit_component),
                "total_fed_on_1250": str(total_fed_on_gain),
            },
        )
