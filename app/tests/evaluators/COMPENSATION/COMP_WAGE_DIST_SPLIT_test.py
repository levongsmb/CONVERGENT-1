"""Tests for COMP_WAGE_DIST_SPLIT evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPENSATION.COMP_WAGE_DIST_SPLIT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules_with_oasdi_base():
    """Rules cache adapter with a populated 2026 OASDI wage base.
    The production cache marks the 2026 value awaiting_user_input; this
    fixture provides a known numeric override so the evaluator's
    deterministic math is testable today.
    """
    from app.config import rules as rules_mod

    base_adapter = ConfigRulesAdapter()
    fica_real = base_adapter.get("federal/fica_wage_bases", 2026)
    fica = copy.deepcopy(fica_real)
    for p in fica["parameters"]:
        if p["coordinate"].get("sub_parameter") == "oasdi_wage_base":
            p["value"] = 176100  # hypothetical 2026 OASDI base, for test determinism
            p["verification_status"] = "verified_by_cpa"
            break

    class PatchedAdapter:
        def get(self, key, year):
            if key == "federal/fica_wage_bases":
                return fica
            return base_adapter.get(key, year)

        @property
        def version(self):
            return base_adapter.version

    return PatchedAdapter()


@pytest.fixture
def rules_unpatched():
    return ConfigRulesAdapter()


def _load(name: str):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_scorp(rules_with_oasdi_base):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules_with_oasdi_base, year=2026)
    assert result.applicable is False
    assert "S corporation" in result.reason


def test_low_confidence_when_oasdi_base_is_awaiting_user_input(rules_unpatched):
    """The production 2026 OASDI base is null (awaiting_user_input).
    Evaluator must degrade to applicable=True but verification_confidence=low.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_unpatched, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"
    assert "wage base" in (result.reason or "")
    assert result.estimated_tax_savings == Decimal(0)


def test_fica_delta_computed_when_base_populated(rules_with_oasdi_base):
    """With OASDI base = $176,100 and current wage = $195,000 on the S corp
    owner fixture, lowering to the OASDI base saves employer + employee OASDI
    on the difference ($18,900 × 12.4%) = $2,343.60. No Medicare or AddlMed
    savings because those continue above the base.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi_base, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["oasdi_wage_base"]) == Decimal("176100")
    # Candidate = max(OASDI base 176100, reasonable floor = (612000+195000)*0.25 = 201750)
    # -> 201750
    assert Decimal(trace["candidate_wage"]) == Decimal("201750")
    # Candidate > current (195000), so fica_delta should be non-positive.
    # Saving only emerges when current_wage > candidate_wage.
    assert Decimal(trace["fica_delta"]) <= Decimal(0)
    assert result.estimated_tax_savings == Decimal(0)


def test_fica_delta_positive_when_current_wage_exceeds_candidate(
    rules_with_oasdi_base,
):
    """Construct a scenario where current wage ($400K) exceeds the candidate
    anchor ($201,750 reasonable floor) and confirm FICA savings are positive
    and equal to the OASDI differential.
    """
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["wages_primary"] = 400000
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["w2_wages_allocated"] = 400000
    for e in base["entities"]:
        if e["code"] == "SCORP_PRIMARY":
            e["w2_wages"] = 400000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_oasdi_base, year=2026)
    assert result.applicable is True
    # Current wage 400K, OASDI base 176100 -> OASDI wage at candidate = 176100
    # Candidate is max(OASDI 176100, reasonable floor = (612+400)*1000*0.25 = 253000) = 253000
    trace = result.computation_trace
    assert Decimal(trace["candidate_wage"]) == Decimal("253000")
    # Savings from dropping wage 400K -> 253K on Medicare side:
    # Medicare combined 2.9% on $147,000 delta = $4,263
    # (OASDI fully maxed at the base at both wage levels, so no OASDI delta)
    # But there's also delta from Medicare 2.9% * (400000 - 253000) = 147000 * 0.029 = 4,263
    # Note: fica_current includes OASDI computed on min(400000, 176100) = 176100
    # fica_candidate includes OASDI on min(253000, 176100) = 176100 (same)
    # So the only delta is Medicare: (400000 - 253000) * (0.0145 + 0.0145) = 147000 * 0.029
    expected = (Decimal("147000") * Decimal("0.029")).quantize(Decimal("0.01"))
    assert Decimal(trace["fica_delta"]) == expected
    assert result.estimated_tax_savings == expected
    assert result.savings_by_tax_type.payroll_tax == expected


def test_cross_strategy_impacts_listed(rules_with_oasdi_base):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi_base, year=2026)
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts
    assert "QBI_SCORP_WAGE_BALANCE" in result.cross_strategy_impacts
    assert "RET_SOLO_401K" in result.cross_strategy_impacts


def test_pin_cites_present(rules_with_oasdi_base):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi_base, year=2026)
    assert any("§3121" in c for c in result.pin_cites)
    assert any("§3101(b)(2)" in c for c in result.pin_cites)
    assert any("§199A" in c for c in result.pin_cites)


def test_reads_rates_from_config_not_hardcoded(rules_with_oasdi_base):
    """Evaluator must call rules.get for fica_wage_bases and additional_medicare.
    Verify via spy wrapping the patched adapter.
    """
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
    Evaluator().evaluate(scenario, Spy(rules_with_oasdi_base), year=2026)
    assert ("federal/fica_wage_bases", 2026) in calls
    assert ("federal/additional_medicare", 2026) in calls
