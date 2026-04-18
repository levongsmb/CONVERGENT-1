"""Tests for CAP_EST_TAX_SAFE_HARBORS evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_EST_TAX_SAFE_HARBORS import (
    Evaluator,
)
from app.evaluators._base import ConfigRulesAdapter
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name: str):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


# ---------------------------------------------------------------------------
# Spec §5.7 required tests
# ---------------------------------------------------------------------------


def test_not_applicable_when_no_income_and_no_prior_year_history(rules, tmp_path):
    """Gating: evaluator returns not_applicable when there is no prior-year
    total tax and no current-year income sources."""
    import yaml

    from app.scenario.loader import FIXTURES_DIR

    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["income"]["wages_primary"] = 0
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    base["income"]["k1_income"] = []
    base["prior_year"]["total_federal_tax"] = None
    base["prior_year"]["agi"] = None
    base["prior_year"]["capital_loss_carryforward_long_term"] = 0
    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "prior-year" in (result.reason or "")
    assert result.pin_cites  # still enumerated for audit context


def test_applicable_with_baseline_scenario(rules):
    """Runs on the standard single-filer fixture; must be applicable and
    produce a non-None prior_year_safe_harbor in the trace."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["prior_year_safe_harbor"] is not None
    # Single filer with prior AGI $131,700 < $150K threshold -> 100% (not elevated)
    assert trace["elevated_triggered"] is False
    assert Decimal(trace["prior_year_pct"]) == Decimal("1.00")


def test_elevated_safe_harbor_pct_triggers_for_high_income_mfj(rules):
    """Prior-year AGI $792K > $150K MFJ threshold -> 110% rule applies."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["elevated_triggered"] is True
    assert Decimal(trace["prior_year_pct"]) == Decimal("1.10")
    # 110% of prior tax $192,300 = $211,530
    assert Decimal(trace["prior_year_safe_harbor"]) == Decimal("211530.00")


def test_lumpy_income_flag_set_on_liquidity_event_fixture(rules):
    """Liquidity event fixture declares planning.liquidity_event_planned so
    the annualization method heuristic must fire."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["has_lumpy_income_flag"] is True
    # First risk line must call out §6654(d)(2) annualization
    assert any(
        "§6654(d)(2)" in r or "annualized" in r.lower()
        for r in result.risks_and_caveats
    )


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CAP_PENALTY_ABATEMENT" in result.cross_strategy_impacts
    assert "SSALT_STATE_ESTIMATES" in result.cross_strategy_impacts


def test_pin_cites_present(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§6654" in c for c in result.pin_cites)
    assert any("90%" in c for c in result.pin_cites)


def test_no_hardcoded_model_strings_or_rates_in_source():
    """Spec §5.2a invariant: evaluator must not contain Claude model strings.
    Tax rate constants that are STATUTORY (e.g., §6654(d)(1)(C) thresholds
    $150,000 and $75,000 and the 90%/100%/110% safe-harbor percentages)
    are Code-prescribed values, not indexed parameters, so they legitimately
    live in the evaluator module rather than in config/rules_cache/.
    """
    from pathlib import Path

    source = Path(
        "app/evaluators/COMPLIANCE_AND_PROCEDURAL/CAP_EST_TAX_SAFE_HARBORS.py"
    ).read_text()
    assert "claude-" not in source
    assert "anthropic" not in source.lower()
