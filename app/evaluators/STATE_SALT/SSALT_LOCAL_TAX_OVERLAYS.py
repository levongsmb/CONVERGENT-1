"""SSALT_LOCAL_TAX_OVERLAYS — local tax overlays (NYC UBT, SF GRT, etc.)."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


_LOCAL_OVERLAY_STATES = {
    StateCode.NY, StateCode.CA, StateCode.PA, StateCode.OH, StateCode.MI,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_LOCAL_TAX_OVERLAYS"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "NYC Admin Code §11-503 — NYC UBT (unincorporated business tax)",
        "NYC Admin Code §11-601 et seq. — NYC General Corporation Tax",
        "SF Bus. & Tax Regs. Article 12-A-1 — SF Gross Receipts Tax",
        "PA Local Earned Income Tax (Act 32)",
        "OH CAT — Ohio Commercial Activity Tax",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        exposed = set()
        for e in scenario.entities:
            if e.formation_state in _LOCAL_OVERLAY_STATES:
                exposed.add(e.formation_state)
            for s in (e.operating_states or []):
                if s in _LOCAL_OVERLAY_STATES:
                    exposed.add(s)
        if scenario.identity.primary_state_domicile in _LOCAL_OVERLAY_STATES:
            exposed.add(scenario.identity.primary_state_domicile)
        if not exposed:
            return self._not_applicable(
                "no operation or domicile in a local-overlay state; "
                "NYC UBT / SF GRT / PA EIT not implicated"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "local jurisdiction of every business and residence",
                "apportionment of receipts to local jurisdiction",
                "entity type (UBT applies to unincorporated only; GCT to corps)",
                "local NOL and credit carryforward positions",
            ],
            assumptions=[
                "NYC UBT: 4% on unincorporated trade or business net income "
                "sourced to NYC; partial §612 conformity.",
                "SF GRT is receipts-based, not income-based; quarterly "
                "installments with year-end true-up.",
                "PA Act 32 requires local EIT withholding / filing at "
                "resident and work-location jurisdictions.",
            ],
            implementation_steps=[
                "Identify every sub-state jurisdiction with filing requirements.",
                "For NYC: distinguish UBT (unincorporated) from GCT (corporate); "
                "model the UBT credit on NYC personal income tax.",
                "For SF: measure gross receipts sourced to SF; track "
                "homelessness and overpaid-executive surcharges.",
                "For PA Act 32 residents: align resident-locality EIT with "
                "work-locality withholding to prevent double payment.",
            ],
            risks_and_caveats=[
                "Local taxes often do not qualify for federal SALT deduction "
                "when imposed on the individual (cap) but DO qualify when "
                "imposed on the business (below the line).",
                "Local jurisdictions have statute-of-limitations divergence "
                "from state; multi-year exposure reviews required.",
            ],
            cross_strategy_impacts=[
                "SSALT_NYC_RESIDENT",
                "SSALT_DC_UBFT",
                "SSALT_SALES_USE_EXPOSURE",
                "SSALT_164_SALT_CAP",
            ],
            verification_confidence="medium",
            computation_trace={"exposed_states": sorted(s.value for s in exposed)},
        )
