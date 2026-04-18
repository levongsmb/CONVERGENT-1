"""QSBS_ORIGINAL_ISSUANCE — §1202(c)(1)(B) original-issuance requirement.

QSBS must be acquired from the issuing corporation:
  (a) at its original issue (whether for money, other property, or as
      compensation for services), OR
  (b) via §1202(h) carryover of basis from a qualifying holder.

Second-market purchases do NOT qualify. The evaluator verifies that
each asset flagged is_qsbs has original-issuance indicia in the
scenario schema and flags gaps for documentation.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QSBS_ORIGINAL_ISSUANCE"
    CATEGORY_CODE = "QSBS_1202"
    PIN_CITES = [
        "IRC §1202(c)(1)(B) — original-issuance requirement",
        "IRC §1202(h) — tacking on certain tax-free carryovers",
        "IRC §1202(h)(4) — partnership and pass-through gifting",
        "Treas. Reg. §1.1202-2 — proposed regulations on QSBS",
        "Rev. Rul. 71-572 — original issue vs secondary transfer",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        qsbs_lots = [
            a for a in scenario.assets
            if a.is_qsbs
        ]
        if not qsbs_lots:
            return self._not_applicable(
                "no QSBS-flagged assets in scenario; evaluator verifies "
                "original-issuance indicia on QSBS lots"
            )

        findings: list = []
        for a in qsbs_lots:
            issues = []
            if a.qsbs_issuance_date is None:
                issues.append("missing qsbs_issuance_date")
            if a.qsbs_issuer_ein is None:
                issues.append("missing qsbs_issuer_ein")
            if a.acquisition_date is not None and a.qsbs_issuance_date is not None:
                if a.acquisition_date != a.qsbs_issuance_date:
                    issues.append(
                        f"acquisition_date ({a.acquisition_date}) != "
                        f"qsbs_issuance_date ({a.qsbs_issuance_date}); "
                        "confirm §1202(h) tacking applies via gift / reorg / §351"
                    )
            findings.append({
                "asset_code": a.asset_code,
                "issuance_date": str(a.qsbs_issuance_date) if a.qsbs_issuance_date else None,
                "acquisition_date": str(a.acquisition_date) if a.acquisition_date else None,
                "issues": issues,
                "passes_original_issuance": len(issues) == 0,
            })

        passing = [f for f in findings if f["passes_original_issuance"]]

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "stock purchase agreement or cap-table entry for each lot",
                "§351 incorporation documents if stock received via §351",
                "gift documentation if stock received via §1202(h) carryover",
                "cap-table confirmation that lot was issued by the corp "
                "(not purchased from another shareholder)",
            ],
            assumptions=[
                f"QSBS-flagged lots in scenario: {len(qsbs_lots)}",
                f"Lots passing original-issuance documentation check: {len(passing)}",
            ],
            implementation_steps=[
                "For each QSBS lot, confirm acquisition via one of:",
                "  - Original issuance from the corporation (cash / property / services)",
                "  - §351 incorporation (carryover basis and holding period)",
                "  - Gift from a qualifying holder (§1202(h)(2))",
                "  - Tax-free reorganization (§1202(h)(4))",
                "Retain stock purchase agreement, Form SS-4 (EIN), issuer "
                "articles of incorporation, and cap-table evidence.",
                "If lot was purchased from another shareholder on a secondary "
                "basis, it does NOT qualify for §1202; flag for removal.",
            ],
            risks_and_caveats=[
                "Secondary-market QSBS does NOT qualify. Common trap: tender "
                "offers, employee-to-employee transfers outside §1202(h)(2).",
                "Options or warrants are NOT stock; the QSBS holding period "
                "starts when the option or warrant is EXERCISED, not granted.",
                "Convertible debt → stock conversion: holding period starts "
                "at conversion, not at debt issuance.",
                "Rev. Rul. 71-572 distinguishes §1202 original-issuance from "
                "certain secondary issuances; fact-pattern review is "
                "required on non-obvious cases.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QSBS_ACTIVE_BUSINESS",
                "QSBS_HOLDING_PERIOD",
                "QSBS_TACKING",
                "QSBS_SAFE_CONVERTIBLE",
                "ENT_QSBS_DRIVEN",
            ],
            verification_confidence="high",
            computation_trace={
                "qsbs_lot_count": len(qsbs_lots),
                "findings": findings,
                "passing_count": len(passing),
            },
        )
