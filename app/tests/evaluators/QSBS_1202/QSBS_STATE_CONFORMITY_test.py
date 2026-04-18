"""Tests for QSBS_STATE_CONFORMITY evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QSBS_1202.QSBS_STATE_CONFORMITY import Evaluator
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


def test_not_applicable_without_ca_domicile(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    base["identity"]["primary_state_domicile"] = "TX"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_qsbs_founder_with_ca_domicile(rules):
    """QSBS founder fixture: CA-domiciled with gain $3,675K pre + $1,050K post = $4,725K total.
    CA tax at 12.3% = $581,175; MHST on excess over $1M = $37,250; total $618,425.
    """
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["total_qsbs_gain"]) == Decimal("4725000")
    # 4,725,000 × 12.3% = 581,175
    assert Decimal(trace["ca_ordinary_tax"]) == Decimal("581175.00")
    # MHST: (4,725,000 - 1,000,000) × 1% = 37,250
    assert Decimal(trace["ca_mhst"]) == Decimal("37250.00")
    assert Decimal(trace["total_ca_tax_on_qsbs_gain"]) == Decimal("618425.00")


def test_no_mhst_when_gain_under_1m(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    # Lower both lots so total gain < $1M
    for a in base["assets"]:
        if a["asset_code"] == "QSBS_PRE_2022":
            a["fmv"] = 700000  # gain = 700K - 525K = 175K
        if a["asset_code"] == "QSBS_POST_2025":
            a["fmv"] = 600000  # gain = 600K - 200K = 400K
    # Total gain = 575K

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["total_qsbs_gain"]) == Decimal("575000")
    assert Decimal(trace["ca_mhst"]) == Decimal(0)
    assert Decimal(trace["ca_ordinary_tax"]) == Decimal("70725.00")  # 575K × 12.3%


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RD_CA_DOMICILE_BREAK" in result.cross_strategy_impacts
    assert "CA_NONCONFORMITY_QSBS" in result.cross_strategy_impacts
    assert "QSBS_OBBBA_TIERED" in result.cross_strategy_impacts


def test_pin_cites_include_rtc_and_cutler(rules):
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§18152.5" in c for c in result.pin_cites)
    assert any("§17043" in c for c in result.pin_cites)
    assert any("Cutler" in c for c in result.pin_cites)
