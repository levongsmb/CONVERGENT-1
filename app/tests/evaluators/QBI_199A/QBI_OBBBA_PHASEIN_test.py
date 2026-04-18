"""Tests for QBI_OBBBA_PHASEIN evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QBI_199A.QBI_OBBBA_PHASEIN import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


@pytest.fixture
def rules_with_threshold():
    """Patched adapter with a known §199A(e)(2) threshold for 2026 so
    regime-detection math is testable."""
    base = ConfigRulesAdapter()
    qbi_real = base.get("federal/qbi_199a", 2026)
    qbi = copy.deepcopy(qbi_real)
    for p in qbi["parameters"]:
        sp = p["coordinate"].get("sub_parameter")
        if sp == "taxable_income_threshold_mfj":
            p["value"] = 400000
        if sp == "taxable_income_threshold_single":
            p["value"] = 200000

    class Patched:
        def get(self, key, year):
            return qbi if key == "federal/qbi_199a" else base.get(key, year)

        @property
        def version(self):
            return base.version

    return Patched()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_qbi(rules_with_threshold):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    assert result.applicable is False


def test_low_confidence_when_threshold_awaiting_user_input(rules):
    """Production rules cache has 2026 thresholds null -> low confidence."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"
    assert result.computation_trace["threshold_populated"] is False


def test_mfj_scorp_owner_lands_above_window(rules_with_threshold):
    """MFJ fixture has ~$947K approx taxable income, well above threshold
    $400K + phasein_width from the current rules cache.
    Note: the 2026 rules cache currently carries the pre-OBBBA $100K MFJ
    phase-in width; the $150K OBBBA-expanded width is a Phase 3b rules-
    cache follow-up. Window top at $100K width = $500K."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    trace = result.computation_trace
    assert trace["regime"] == "ABOVE_WINDOW"
    assert Decimal(trace["window_top"]) == Decimal("500000")
    assert Decimal(trace["applicable_percentage"]) == Decimal("1")
    assert Decimal(trace["compression_target_to_reach_threshold"]) > Decimal(0)


def test_single_qsbs_founder_below_threshold(rules_with_threshold):
    """Single founder fixture: wages $240K + interest $22K + div $8K + LT cap $19K
    = ~$289K which is above single threshold $200K, so IN_PHASEIN."""
    scenario = _load("scenario_qsbs_founder")
    # Founder has no QBI (C corp) -> not applicable
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    assert result.applicable is False


def test_in_phasein_detected_on_constructed_scenario(rules_with_threshold):
    """Construct an MFJ scenario with taxable income between $400K threshold
    and $500K window top (current rules cache uses $100K MFJ width)."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Drop K-1 ordinary to $120K so approx taxable income lands ~$445K
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = 120000
            k1["qualified_business_income"] = 120000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    trace = result.computation_trace
    assert trace["regime"] == "IN_PHASEIN"
    overshoot = Decimal(trace["overshoot_into_window"])
    # applicable_pct = overshoot / phasein_width (100000 in current rules cache)
    expected_pct = (overshoot / Decimal("100000")).quantize(Decimal("0.0001"))
    assert Decimal(trace["applicable_percentage"]) == expected_pct


def test_cross_strategy_impacts_listed(rules_with_threshold):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    assert "QBI_SSTB_AVOIDANCE" in result.cross_strategy_impacts
    assert "RET_CASH_BALANCE" in result.cross_strategy_impacts
    assert "CA_PTET_ELECTION" in result.cross_strategy_impacts


def test_pin_cites_include_obbba_and_code(rules_with_threshold):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_threshold, year=2026)
    assert any("§199A(b)(3)" in c for c in result.pin_cites)
    assert any("OBBBA §70431" in c for c in result.pin_cites)
    assert any("P.L. 119-21" in c for c in result.pin_cites)


def test_reads_qbi_rules(rules_with_threshold):
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
    Evaluator().evaluate(scenario, Spy(rules_with_threshold), year=2026)
    assert ("federal/qbi_199a", 2026) in calls
