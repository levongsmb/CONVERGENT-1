"""Tests for QSBS_HOLDING_PERIOD evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QSBS_1202.QSBS_HOLDING_PERIOD import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_qsbs_lots(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_pre_obbba_lot_under_5y_has_zero_exclusion(rules):
    """QSBS founder fixture: QSBS_PRE_2022 issued 2022-03-14.
    At end of 2026: ~4.8 years held. Under PRE regime, strict 5-year.
    Current exclusion should be 0% and next vest date ≈ 2027-03-14."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    pre_lot = next(d for d in trace["lot_details"] if d["asset_code"] == "QSBS_PRE_2022")
    assert pre_lot["regime"] == "PRE"
    assert Decimal(pre_lot["current_exclusion_pct"]) == Decimal("0.00")
    assert pre_lot["next_tier_vest_date"] is not None


def test_pre_obbba_lot_over_5y_has_full_exclusion(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    # Shift pre-OBBBA lot issuance to 2019 so 7+ years held in 2026
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["qsbs_issuance_date"] = "2019-03-14"
            a["acquisition_date"] = "2019-03-14"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    pre_lot = next(d for d in trace["lot_details"] if d["asset_code"] == "QSBS_PRE_2022")
    assert Decimal(pre_lot["current_exclusion_pct"]) == Decimal("1.00")
    assert pre_lot["next_tier_vest_date"] is None


def test_post_obbba_lot_between_3y_and_4y_triggers_50_pct(rules):
    """Post-OBBBA lot issued 2023-01-01 → 4 years held end of 2026 → 75%."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    # Construct a post-OBBBA lot with ~3.5y held at end of 2026
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_POST_2025":
            a["qsbs_issuance_date"] = "2023-06-01"
            a["acquisition_date"] = "2023-06-01"
            a["qsbs_pre_or_post_obbba"] = "POST"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    post_lot = next(d for d in trace["lot_details"] if d["asset_code"] == "QSBS_POST_2025")
    assert post_lot["regime"] == "POST"
    # 3.58 years held → 50% tier, next vest at 4y
    assert Decimal(post_lot["current_exclusion_pct"]) == Decimal("0.50")


def test_post_obbba_lot_under_3y_has_zero_exclusion(rules):
    """Use fixture as-is: QSBS_POST_2025 issued 2025-09-20. At end 2026 ~1.3y → 0%."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    post_lot = next(d for d in trace["lot_details"] if d["asset_code"] == "QSBS_POST_2025")
    assert Decimal(post_lot["current_exclusion_pct"]) == Decimal("0.00")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QSBS_ORIGINAL_ISSUANCE" in result.cross_strategy_impacts
    assert "QSBS_1045_ROLLOVER" in result.cross_strategy_impacts
    assert "QSBS_STATE_CONFORMITY" in result.cross_strategy_impacts
    assert "CA_NONCONFORMITY_QSBS" in result.cross_strategy_impacts


def test_pin_cites_include_1202a_and_obbba(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1202(a)(1)" in c for c in result.pin_cites)
    assert any("§1202(h)(1)" in c for c in result.pin_cites)
    assert any("§70431" in c for c in result.pin_cites)
