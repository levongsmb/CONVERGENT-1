"""Shared evaluator base classes and protocols per spec Section 5.2.

Every Layer 3 evaluator is a subclass of `BaseEvaluator` that overrides
`evaluate()`. The orchestrator passes a `ClientScenario`, a `RulesCache`
accessor, and a tax year; the evaluator returns a `StrategyResult` with
deterministic dollar figures, implementation steps, pin cites,
cross-strategy impacts, and verification confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Literal, Optional, Protocol

from app.scenario.models import ClientScenario


VerificationConfidence = Literal["high", "medium", "low"]


@dataclass
class TaxImpact:
    federal_income_tax: Decimal = Decimal(0)
    state_income_tax: Decimal = Decimal(0)
    niit: Decimal = Decimal(0)
    self_employment_tax: Decimal = Decimal(0)
    payroll_tax: Decimal = Decimal(0)
    estate_gift_tax: Decimal = Decimal(0)
    capital_gains_tax: Decimal = Decimal(0)

    @property
    def total(self) -> Decimal:
        return (
            self.federal_income_tax
            + self.state_income_tax
            + self.niit
            + self.self_employment_tax
            + self.payroll_tax
            + self.estate_gift_tax
            + self.capital_gains_tax
        )


@dataclass
class StrategyResult:
    subcategory_code: str
    applicable: bool
    reason: Optional[str] = None
    estimated_tax_savings: Decimal = Decimal(0)
    savings_by_tax_type: TaxImpact = field(default_factory=TaxImpact)
    inputs_required: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    risks_and_caveats: List[str] = field(default_factory=list)
    pin_cites: List[str] = field(default_factory=list)
    cross_strategy_impacts: List[str] = field(default_factory=list)
    verification_confidence: VerificationConfidence = "high"
    computation_trace: Dict = field(default_factory=dict)


class RulesCache(Protocol):
    def get(self, key: str, year: int) -> Dict: ...

    @property
    def version(self) -> str: ...


class Evaluator(Protocol):
    SUBCATEGORY_CODE: str
    CATEGORY_CODE: str
    PIN_CITES: List[str]

    def evaluate(
        self, scenario: ClientScenario, rules: RulesCache, year: int
    ) -> StrategyResult: ...


class BaseEvaluator:
    """Default implementation. Subclasses override `evaluate()` and set
    `SUBCATEGORY_CODE` and `CATEGORY_CODE` class attributes. `PIN_CITES`
    may be a class attribute or a dynamic property that resolves through
    `app.config.authorities.get_authority`.
    """

    SUBCATEGORY_CODE: str = ""
    CATEGORY_CODE: str = ""
    PIN_CITES: List[str] = []

    def evaluate(
        self, scenario: ClientScenario, rules: RulesCache, year: int
    ) -> StrategyResult:
        raise NotImplementedError

    def _not_applicable(self, reason: str) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=False,
            reason=reason,
            pin_cites=list(self.PIN_CITES),
        )


# ---------------------------------------------------------------------------
# Convenience adapter: wrap app.config.rules.get_rule behind RulesCache
# ---------------------------------------------------------------------------


class ConfigRulesAdapter:
    """Thin adapter so evaluators accept any RulesCache-compatible object.

    Tests may substitute a fake rules cache; production uses this adapter
    pointing at `app.config.rules`.
    """

    def get(self, key: str, year: int) -> Dict:
        from app.config.rules import get_rule

        return get_rule(key, year)

    @property
    def version(self) -> str:
        from app.config.rules import cache_version

        return cache_version()
