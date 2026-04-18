"""CAP_8275_DISCLOSURE — disclosure statements Form 8275 / 8275-R."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_8275_DISCLOSURE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6662(d) — substantial understatement penalty",
        "IRC §6662(d)(2)(B) — reduced to 20% if disclosed and reasonable basis",
        "IRC §6694 — preparer penalty coordination",
        "Treas. Reg. §1.6662-4(f) — adequate disclosure standard",
        "Rev. Proc. 2023-14 — items treated as adequately disclosed without Form 8275",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "positions taken with less than substantial authority",
                "regulation-contrary positions (Form 8275-R required)",
                "preparer's assessment of position strength under §6694",
            ],
            assumptions=[
                "Form 8275 (regular): position with reasonable basis but "
                "without substantial authority avoids §6662 accuracy "
                "penalty on disclosure.",
                "Form 8275-R: required when position is CONTRARY to a "
                "regulation — disclosure preserves the reasonable-basis "
                "defense but does not preempt regulation.",
                "Rev. Proc. 2023-14 lists items treated as adequately "
                "disclosed via return entries without Form 8275.",
            ],
            implementation_steps=[
                "Identify every position with less than substantial authority "
                "or contrary to a regulation.",
                "For contrary-to-regulation positions: file Form 8275-R with "
                "return.",
                "For below-substantial-authority positions: file Form 8275 OR "
                "rely on Rev. Proc. 2023-14 adequate-disclosure items where "
                "applicable.",
                "Document preparer's §6694 reasonable-basis and disclosure "
                "opinion in workpapers.",
            ],
            risks_and_caveats=[
                "Disclosure preserves NO defense for tax-shelter positions "
                "(§6662(d)(2)(C)) or reportable transactions.",
                "Filing 8275 is a signal to the IRS that may increase audit "
                "risk; balance against penalty avoidance.",
                "Preparer §6694 requires disclosure if tax preparer does not "
                "have substantial authority.",
            ],
            cross_strategy_impacts=[
                "CAP_REASONABLE_CAUSE",
                "CAP_EXAMS_APPEALS",
                "CAP_STATUTE_MGMT",
            ],
            verification_confidence="high",
        )
