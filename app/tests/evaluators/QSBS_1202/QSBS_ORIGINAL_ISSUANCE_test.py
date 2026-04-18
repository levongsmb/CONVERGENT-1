"""Tests for QSBS_ORIGINAL_ISSUANCE evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QSBS_1202.QSBS_ORIGINAL_ISSUANCE import Evaluator
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
    """QSBS founder has two QSBS lots (pre-OBBBA and post-OBBBA)."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["qsbs_lot_count"] == 2
    # Both lots have issuance_date, issuer_ein, and acquisition_date == issuance_date
    assert trace["passing_count"] == 2


def test_flags_missing_metadata(rules):
    """Construct a scenario with QSBS missing issuer EIN."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["qsbs_issuer_ein"] = None

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    # Model-level validators in scenario may also flag this; verify evaluator surfaces.
    pre_finding = next(f for f in trace["findings"] if f["asset_code"] == "QSBS_PRE_2022")
    assert "missing qsbs_issuer_ein" in pre_finding["issues"]
    assert pre_finding["passes_original_issuance"] is False


def test_detects_acquisition_issuance_mismatch(rules):
    """Construct a scenario with acquisition_date != issuance_date."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["acquisition_date"] = "2023-05-01"  # later than issuance 2022-03-14

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    pre_finding = next(f for f in trace["findings"] if f["asset_code"] == "QSBS_PRE_2022")
    assert any("acquisition_date" in issue for issue in pre_finding["issues"])


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QSBS_ACTIVE_BUSINESS" in result.cross_strategy_impacts
    assert "QSBS_HOLDING_PERIOD" in result.cross_strategy_impacts
    assert "ENT_QSBS_DRIVEN" in result.cross_strategy_impacts


def test_pin_cites_include_1202c1b(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1202(c)(1)(B)" in c for c in result.pin_cites)
    assert any("§1202(h)" in c for c in result.pin_cites)
    assert any("Rev. Rul. 71-572" in c for c in result.pin_cites)
