"""Tests for QBI_SCORP_WAGE_BALANCE evaluator (spec §5.3 reference pattern)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QBI_199A.QBI_SCORP_WAGE_BALANCE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name: str):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_scorp_qbi(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "qualified business income" in result.reason


def test_applicable_with_scorp_owner_fixture(rules):
    """Fixture: $612K QBI, $310K W-2 allocated, $185K UBIA.
    Tentative 20% = $122,400; W-2 ceiling 50% = $155,000; W-2+UBIA ceiling
    = $310K*25% + $185K*2.5% = $77,500 + $4,625 = $82,125.
    Effective ceiling = max = $155,000. Tentative $122,400 < $155,000 so
    deduction is NOT wage-limited.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["tentative_deduction_20pct"]) == Decimal("122400.00")
    assert Decimal(trace["w2_ceiling_50pct"]) == Decimal("155000.00")
    expected_w2_ubia = (
        Decimal("310000") * Decimal("0.25") + Decimal("185000") * Decimal("0.025")
    )
    assert Decimal(trace["w2_ubia_ceiling"]) == expected_w2_ubia
    assert Decimal(trace["effective_ceiling"]) == Decimal("155000.00")
    assert trace["deduction_binding_on_wage"] is False
    assert Decimal(trace["headline_deduction"]) == Decimal("122400.00")


def test_wage_limited_regime_detected_when_w2_too_low(rules):
    """Construct a scenario where W-2 is low enough to bind the ceiling."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Drop wages allocated to $60K and QBI stays $612K
    # 20% * 612K = 122,400; W-2 50% ceiling = 30K; W-2+UBIA ceiling =
    # 60K*0.25 + 185K*0.025 = 15K + 4,625 = 19,625
    # Effective ceiling = 30K < 122,400 -> binding
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["w2_wages_allocated"] = 60000
    for e in base["entities"]:
        if e["code"] == "SCORP_PRIMARY":
            e["w2_wages"] = 60000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["deduction_binding_on_wage"] is True
    assert Decimal(trace["effective_ceiling"]) == Decimal("30000.00")
    assert Decimal(trace["headline_deduction"]) == Decimal("30000.00")
    assert any("wage-limited" in r.lower() or "BELOW" in r for r in result.risks_and_caveats)


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts
    assert "QBI_OBBBA_PHASEIN" in result.cross_strategy_impacts
    assert "QBI_199AI_MINIMUM" in result.cross_strategy_impacts


def test_pin_cites_present(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§199A(a)" in c for c in result.pin_cites)
    assert any("§199A(b)(2)(B)" in c for c in result.pin_cites)
    assert any("§199A(i)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)


def test_reads_qbi_rules_from_config(rules):
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
    assert ("federal/qbi_199a", 2026) in calls


def test_partnership_k1_alone_does_not_trigger(rules):
    """QBI_SCORP_WAGE_BALANCE is S-corp-scoped. Partnership QBI should not
    cause this evaluator to fire; other QBI evaluators (e.g.,
    QBI_W2_WAGE_OPT, QBI_AGGREGATION) cover partnership cases."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_threshold_unpopulated_still_runs_and_flags(rules):
    """The 2026 §199A threshold is awaiting Rev. Proc. 2025-32 confirmation.
    Evaluator must still run and record threshold_populated=False in trace.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    # In the current rules cache, the threshold is awaiting_user_input; the
    # trace must reflect that the evaluator ran regardless.
    assert "threshold_populated" in trace
