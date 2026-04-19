"""CAP_PROTECTIVE_ELECTIONS — protective elections and protective refund claims."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_PROTECTIVE_ELECTIONS"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6511(a) — refund claim SOL",
        "IRC §6511(b)(2) — refund-amount lookback cap",
        "IRC §6511(d)(2) — protective claim for contingent event",
        "Rev. Proc. 2015-13 — protective method-change elections",
        "§9100 relief — late or missed election (Treas. Reg. §§301.9100-1, -2, -3)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "contingent events that may entitle the taxpayer to a refund (pending litigation, regulatory change)",
                "SOL expiration dates for open refund windows",
                "elections that may or may not apply depending on future facts",
                "tax payments made within the §6511(b)(2) lookback period (3 yrs + extension if timely return; 2 yrs otherwise)",
            ],
            assumptions=[
                "Protective claim preserves SOL on refund where the right "
                "depends on a contingent event (pending case law, foreign tax "
                "credit carryback, §83(b) late election).",
                "§9100 relief may cure missed elections where facts support "
                "reasonable reliance.",
                "§6511(a) governs the filing deadline for a refund claim; "
                "§6511(b)(2) separately caps the recoverable amount to tax "
                "paid within the lookback period preceding the claim. Both "
                "tests must be satisfied for any dollar of refund.",
            ],
            implementation_steps=[
                "Identify elections whose applicability depends on unresolved "
                "contingencies; file protectively with specific facts.",
                "File protective refund claim on Form 843 or amended return "
                "(Form 1040-X / 1120X) citing the contingent event.",
                "For missed elections: evaluate §9100 relief under "
                "Treas. Reg. §301.9100-3 (discretionary) or -2 (automatic).",
            ],
            risks_and_caveats=[
                "Protective claim SOL: §6511(a) gives 3 years from return "
                "filing or 2 years from payment, whichever later. Protective "
                "claim must be filed WITHIN this window.",
                "§6511(b)(2) lookback cap: even a timely §6511(a) claim "
                "recovers $0 if no qualifying tax payments fell within the "
                "lookback window (3 yrs + extension if a return was timely "
                "filed; otherwise 2 yrs preceding the claim).",
                "§9100 relief is discretionary and time-consuming; not a "
                "substitute for timely filing.",
            ],
            cross_strategy_impacts=[
                "CAP_STATUTE_MGMT",
                "CAP_ELECTION_CALENDAR",
                "CAP_SUPERSEDING_VS_AMENDED",
            ],
            verification_confidence="high",
        )
