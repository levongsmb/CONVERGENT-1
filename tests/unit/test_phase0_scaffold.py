"""Phase 0 smoke tests — the scaffold imports cleanly and the bootstrap
runner surfaces the rules-cache review plan.

These tests establish the minimum bar that Phase 0 is structurally sound.
They don't exercise tax computation; that arrives in Phase 5.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_package_version_present():
    import convergent

    assert convergent.__version__.startswith("0.1.0-phase0")


def test_decimal_setup_roundtrip():
    from convergent.util.decimal_tax import PENNY, to_penny

    assert to_penny(Decimal("1.005")) == Decimal("1.01")
    assert to_penny("3.333") == Decimal("3.33")
    assert PENNY == Decimal("0.01")


def test_engagement_schema_tables_named():
    from convergent.persistence.engagement_db import metadata

    names = set(metadata.tables.keys())
    expected_subset = {
        "engagement",
        "taxpayer",
        "family_member",
        "income_source",
        "entity",
        "entity_ownership",
        "retirement_plan",
        "balance_sheet_item",
        "estate_posture",
        "election_in_force",
        "ingested_document",
        "prior_year_snapshot",
        "reconciliation_entry",
        "goals_inventory",
        "scenario",
        "authority_artifact",
        "memo_artifact",
        "cost_estimate",
        "override_log",
        "audit_trail",
    }
    missing = expected_subset - names
    assert not missing, f"Missing tables: {missing}"


def test_rules_cache_schema_tables_named():
    from convergent.persistence.rules_cache_db import metadata

    names = set(metadata.tables.keys())
    assert {
        "rules_cache_snapshot",
        "rule_parameter",
        "obbba_notice",
        "listed_transaction",
        "reportable_transaction",
    }.issubset(names)


def test_authority_cache_schema_tables_named():
    from convergent.persistence.authority_cache_db import metadata

    names = set(metadata.tables.keys())
    assert {
        "authority_snapshot",
        "statute",
        "regulation",
        "published_guidance",
        "court_opinion",
        "mapping_section_to_guidance",
        "mapping_strategy_to_authority",
        "commentary_cache",
    }.issubset(names)


def test_manifest_yaml_parses_and_enumerates_categories():
    import yaml

    manifest_path = REPO / "strategy_library" / "MANIFEST.yaml"
    data = yaml.safe_load(manifest_path.read_text())

    assert data["total_strategies"] >= 120
    keys = {c["key"] for c in data["categories"]}
    expected_20 = {
        "COMPENSATION",
        "QBI_199A",
        "RETIREMENT",
        "ENTITY_SELECTION",
        "STATE_SALT",
        "REAL_ESTATE_DEPRECIATION",
        "QSBS_1202",
        "TRUSTS_INCOME_SHIFTING",
        "TRUSTS_WEALTH_TRANSFER",
        "ESTATE_GIFT_GST",
        "CHARITABLE",
        "INSTALLMENT_DEFERRAL",
        "CAPITAL_GAINS_LOSSES",
        "LOSS_LIMIT_NAVIGATION",
        "ACCOUNTING_METHODS",
        "CREDITS",
        "SALE_TRANSACTION",
        "INTERNATIONAL",
        "MISCELLANEOUS",
        "COMPLIANCE_AND_PROCEDURAL",
    }
    assert keys == expected_20

    # No duplicate strategy IDs across the Library.
    all_ids: list[str] = []
    for cat in data["categories"]:
        all_ids.extend(s["id"] for s in cat["strategies"])
    assert len(all_ids) == len(set(all_ids)), "Duplicate strategy IDs in MANIFEST.yaml"


def test_rules_cache_bootstrap_files_parse():
    import yaml

    root = REPO / "rules_cache_bootstrap"
    assert root.exists()
    for y in root.rglob("*.yaml"):
        yaml.safe_load(y.read_text())  # does not raise


def test_pitfalls_yaml_parses_and_has_ca_ptet_entry():
    import yaml

    pitfalls = yaml.safe_load((REPO / "authority_layer" / "pitfalls.yaml").read_text())
    ids = {p["id"] for p in pitfalls["pitfalls"]}
    assert "ca_ptet_june15_short_payment_credit_reduction" in ids
    assert "listed_transaction_match" in ids
    assert "scorp_reasonable_comp_low_ratio" in ids


def test_bootstrap_runner_surfaces_review_plan():
    result = subprocess.run(
        [sys.executable, "-m", "convergent.authority_layer.statutory_mining.bootstrap"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0
    assert "Phase 0 review plan" in result.stdout
    assert "rules_cache_bootstrap" in result.stdout


def test_main_version_flag():
    result = subprocess.run(
        [sys.executable, "-m", "convergent", "--version"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0
    assert "0.1.0-phase0" in result.stdout
