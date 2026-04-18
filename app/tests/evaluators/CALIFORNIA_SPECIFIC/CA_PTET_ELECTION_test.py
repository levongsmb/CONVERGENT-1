"""Tests for CA_PTET_ELECTION evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CALIFORNIA_SPECIFIC.CA_PTET_ELECTION import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name: str):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_outside_sb132_window(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2031)
    assert result.applicable is False
    assert "SB 132" in result.reason or "2026-2030" in result.reason


def test_not_applicable_without_ca_connection(rules):
    """Construct a scenario with non-CA domicile and non-CA entity."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_state_domicile"] = "TX"
    base["identity"]["spouse_state_domicile"] = "TX"
    for e in base["entities"]:
        e["formation_state"] = "TX"
        e["operating_states"] = ["TX"]

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_for_ca_scorp_owner_archetype(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["ptet_rate"]) == Decimal("0.093")
    # QNI = ordinary $612,000 + guaranteed $0 = $612,000
    assert Decimal(trace["qualified_net_income"]) == Decimal("612000")
    # PTET paid = $612,000 * 9.3% = $56,916
    assert Decimal(trace["ptet_paid"]) == Decimal("56916.00")
    # Gross federal savings at 37% marginal = $56,916 * 0.37 = $21,058.92
    assert Decimal(trace["fed_savings_gross"]) == Decimal("21058.92")
    assert trace["regime"] == "SB132_2026_2030"


def test_salt_cap_overlap_math_on_scorp_owner_fixture(rules):
    """Fixture SALT: state income $28,600 + property residence $16,200 = $44,800.
    SALT cap 2026 MFJ = $40,400. Total $44,800 > cap already, so already_capped=True
    and overlap_reduction should be 0."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["salt_cap_already_consumed"] is True
    assert Decimal(trace["overlap_reduction"]) == Decimal("0.00")
    # Headline = gross savings when cap is already consumed
    assert Decimal(trace["headline_savings"]) == Decimal(trace["fed_savings_gross"])


def test_overlap_reduction_applied_when_cap_has_headroom(rules):
    """Construct a scenario with low SALT (property $5K, state income $10K -> total $15K,
    base cap 2026 MFJ $40,400, headroom for PTET to overlap with cap."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["deductions"]["salt_paid_state_income"] = 10000
    base["deductions"]["salt_paid_property_residence"] = 5000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["salt_cap_already_consumed"] is False
    # Cap $40,400 - property residence $5,000 = headroom $35,400
    # PTET paid $56,916 > headroom; overlap = $35,400 * 0.37 = $13,098
    expected_overlap = (Decimal("35400") * Decimal("0.37")).quantize(Decimal("0.01"))
    assert Decimal(trace["overlap_reduction"]) == expected_overlap
    # Headline = gross $21,058.92 - overlap
    assert Decimal(trace["headline_savings"]) == (
        Decimal(trace["fed_savings_gross"]) - expected_overlap
    )


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SSALT_PTET_MODELING" in result.cross_strategy_impacts
    assert "SSALT_164_SALT_CAP" in result.cross_strategy_impacts
    assert "SSALT_OBBBA_CAP_MODELING" in result.cross_strategy_impacts


def test_pin_cites_include_sb132(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("SB 132" in c for c in result.pin_cites)
    assert any("FTB Form 3804" in c for c in result.pin_cites)
    assert any("§164(b)(6)" in c for c in result.pin_cites)


def test_reads_ptet_and_salt_cap_from_config(rules):
    calls: list = []

    class Spy:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def get(self, key, year):
            calls.append((key, year))
            return self.wrapped.get(key, year)

        @property
        def version(self):
            return self.wrapped.version

    scenario = _load("scenario_mfj_scorp_owner")
    Evaluator().evaluate(scenario, Spy(rules), year=2026)
    assert ("california/ptet", 2026) in calls
    assert ("federal/salt_cap_obbba", 2026) in calls


def test_partnership_scenario_also_applicable(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    # QNI = $340,000 ordinary + $60,000 guaranteed payments = $400,000
    assert Decimal(result.computation_trace["qualified_net_income"]) == Decimal("400000")
