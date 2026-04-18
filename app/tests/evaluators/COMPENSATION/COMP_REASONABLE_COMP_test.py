"""Tests for COMP_REASONABLE_COMP evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators.COMPENSATION.COMP_REASONABLE_COMP import Evaluator
from app.evaluators._base import ConfigRulesAdapter
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name: str):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_scorp(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "S corporation" in result.reason


def test_applicable_with_scorp_owner_fixture(rules):
    """Primary SMB archetype fixture has $195K officer wage + $612K K-1 ordinary.
    Ratio = 195000 / (195000 + 612000) = 24.16% -> DEFENSIBLE band.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert len(trace["classifications"]) == 1
    c = trace["classifications"][0]
    assert c["entity_code"] == "SCORP_PRIMARY"
    assert c["classification"] == "DEFENSIBLE"
    assert Decimal(c["ratio"]) > Decimal("0.20")
    assert Decimal(c["ratio"]) < Decimal("0.70")


def test_detects_low_ratio_risk_posture(rules):
    """Construct a scenario with wage 10% of total -> RISK classification."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Force low-wage posture: $60K wage on $600K K-1 ordinary
    base["income"]["wages_primary"] = 60000
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["w2_wages_allocated"] = 60000
            k1["ordinary_business_income"] = 600000
            k1["qualified_business_income"] = 600000
    for e in base["entities"]:
        if e["code"] == "SCORP_PRIMARY":
            e["w2_wages"] = 60000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["any_risk"] is True
    assert trace["any_excessive"] is False
    assert trace["classifications"][0]["classification"] == "RISK"
    # Risk narrative must mention Mulcahy or Watson
    assert any("Mulcahy" in r or "Watson" in r for r in result.risks_and_caveats)


def test_detects_excessive_ratio_and_quantifies_fica_savings(rules):
    """Construct a scenario with wage 90% of total -> EXCESSIVE classification,
    and verify the FICA-saved figure is 7.65% of the over-ceiling wage."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Force high-wage posture: $500K wage on $50K K-1 ordinary -> ratio ~0.91
    base["income"]["wages_primary"] = 500000
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["w2_wages_allocated"] = 500000
            k1["ordinary_business_income"] = 50000
            k1["qualified_business_income"] = 50000
    for e in base["entities"]:
        if e["code"] == "SCORP_PRIMARY":
            e["w2_wages"] = 500000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["any_excessive"] is True
    assert trace["any_risk"] is False
    # Target ratio ceiling = 70%; target wage = (500+50)*0.70 = 385K
    # Excess wage = 500K - 385K = 115K; FICA saved = 115K * 7.65% = $8,797.50
    expected_fica = (Decimal(115000) * Decimal("0.0765")).quantize(Decimal("0.01"))
    assert Decimal(trace["fica_saved_if_excessive_corrected"]) == expected_fica
    assert result.savings_by_tax_type.payroll_tax == expected_fica
    assert result.estimated_tax_savings == expected_fica


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QBI_SCORP_WAGE_BALANCE" in result.cross_strategy_impacts
    assert "COMP_WAGE_DIST_SPLIT" in result.cross_strategy_impacts
    assert "NIIT_SCORP_MIX" in result.cross_strategy_impacts


def test_pin_cites_present(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("Mulcahy" in c for c in result.pin_cites)
    assert any("§1.162-7" in c for c in result.pin_cites)
    assert any("§31.3121" in c for c in result.pin_cites)


def test_reads_from_config_rules_cache(rules, monkeypatch):
    """Evaluator must call rules.get('federal/fica_wage_bases', year).
    Verify by using a spy rules cache that records keys accessed."""
    calls: list = []

    class Spy:
        def get(self, key, year):
            calls.append((key, year))
            return rules.get(key, year)

        @property
        def version(self):
            return rules.version

    scenario = _load("scenario_mfj_scorp_owner")
    Evaluator().evaluate(scenario, Spy(), year=2026)
    assert ("federal/fica_wage_bases", 2026) in calls
