"""Tests for QSBS_OBBBA_TIERED evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QSBS_1202.QSBS_OBBBA_TIERED import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_qsbs(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_qsbs_founder_fixture(rules):
    """Founder fixture has two QSBS lots. Pre-OBBBA 2022 with $3.675M gain,
    but only 4.8y held → 0% exclusion. Post-OBBBA 2025-09 with $1.05M gain,
    1.3y held → 0% exclusion. Total taxable at 28%."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    # Both lots under holding period → 100% taxable at 28%
    assert Decimal(trace["total_excluded"]) == Decimal(0)
    # Total gain = 3,675,000 + 1,050,000 = 4,725,000
    assert Decimal(trace["total_taxable_at_28_pct"]) == Decimal("4725000")


def test_full_exclusion_when_5y_held(rules):
    """Shift pre-OBBBA issuance to 2019 → 7y held → 100% PRE exclusion."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["qsbs_issuance_date"] = "2019-03-14"
            a["acquisition_date"] = "2019-03-14"
        if a["asset_code"] == "QSBS_POST_2025":
            # Remove post-OBBBA lot for simpler math
            a["is_qsbs"] = False

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["lot_count"] == 1
    # PRE lot gain $3.675M fully excluded
    assert Decimal(trace["total_excluded"]) == Decimal("3675000")
    assert Decimal(trace["total_taxable_at_28_pct"]) == Decimal(0)
    # Saved at 23.8% on $3.675M = $874,650
    assert Decimal(trace["saved_on_excluded"]) == Decimal("874650.00")


def test_post_obbba_50_pct_tier(rules):
    """Post-OBBBA lot at 3y+ → 50% tier."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    # Remove pre-OBBBA for clarity, shift post to 2023 → 3.3y by end-2026
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["is_qsbs"] = False
        if a["asset_code"] == "QSBS_POST_2025":
            a["qsbs_issuance_date"] = "2023-06-01"
            a["acquisition_date"] = "2023-06-01"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    # Gain $1,050,000 × 50% = $525,000 excluded; $525,000 taxable at 28%
    assert Decimal(trace["total_excluded"]) == Decimal("525000.00")
    assert Decimal(trace["total_taxable_at_28_pct"]) == Decimal("525000.00")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QSBS_HOLDING_PERIOD" in result.cross_strategy_impacts
    assert "QSBS_STATE_CONFORMITY" in result.cross_strategy_impacts
    assert "QSBS_STACKING" in result.cross_strategy_impacts


def test_pin_cites_include_obbba_and_cap(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§70431" in c for c in result.pin_cites)
    assert any("§1202(b)(1)(A)" in c for c in result.pin_cites)
    assert any("§1(h)(4)" in c for c in result.pin_cites)
