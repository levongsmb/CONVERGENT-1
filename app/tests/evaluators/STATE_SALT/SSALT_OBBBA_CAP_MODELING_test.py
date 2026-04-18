"""Tests for SSALT_OBBBA_CAP_MODELING evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_OBBBA_CAP_MODELING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_salt_paid(rules):
    """Construct a scenario with zero SALT payments."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["deductions"]["salt_paid_state_income"] = 0
    base["deductions"]["salt_paid_property_personal"] = 0
    base["deductions"]["salt_paid_property_residence"] = 0
    base["deductions"]["salt_paid_sales_tax"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_phaseout_applies_on_high_magi_mfj_fixture(rules):
    """MFJ S corp owner fixture: MAGI ~$947K > $505K threshold.
    Phaseout reduction = ($947,940 - $505,000) * 30% = $132,882.
    Effective cap = $40,400 - $132,882 = negative -> floor $10K.
    SALT paid = 28,600 + 16,200 = $44,800.
    SALT above cap = $44,800 - $10,000 = $34,800.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["base_cap"]) == Decimal("40400")
    assert Decimal(trace["effective_cap"]) == Decimal("10000")
    assert Decimal(trace["salt_above_cap"]) == Decimal("34800.00")


def test_effective_cap_preserved_when_magi_below_threshold(rules):
    """Single fixture: wages $142,500 + small investment income ~$7,860 = MAGI ~$150K.
    Threshold for single MFJ-or-nonMFS = $505K MFJ only; single uses $252,500
    (actually config has per-filing-status threshold). Single wouldn't hit
    phaseout here, so effective cap == base cap."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["phaseout_reduction"]) == Decimal("0")
    # For single filing status the rules cache uses MFJ key in our data;
    # evaluator maps SINGLE -> MFJ for base_cap lookup via the non-MFS path.
    # Base cap still comes out as $40,400.
    assert Decimal(trace["effective_cap"]) == Decimal(trace["base_cap"])


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CA_PTET_ELECTION" in result.cross_strategy_impacts
    assert "CHAR_BUNCHING" in result.cross_strategy_impacts
    assert "QBI_INCOME_COMPRESSION" in result.cross_strategy_impacts


def test_pin_cites_include_obbba_salt(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§164(b)(6)" in c for c in result.pin_cites)
    assert any("2030 sunset" in c for c in result.pin_cites)


def test_reads_salt_cap_rules(rules):
    calls = []

    class Spy:
        def __init__(self, w):
            self.w = w

        def get(self, k, y):
            calls.append((k, y))
            return self.w.get(k, y)

        @property
        def version(self):
            return self.w.version

    scenario = _load("scenario_mfj_scorp_owner")
    Evaluator().evaluate(scenario, Spy(rules), year=2026)
    assert ("federal/salt_cap_obbba", 2026) in calls
