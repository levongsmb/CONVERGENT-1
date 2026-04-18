"""Phase 2 acceptance tests — cross-check protocol unit and integration tests.

Covers:
  - null detection per spec §4 trigger-field list
  - YAML merge layer preserves existing values and populates nulls
  - failure handling: JSON parse failure (retry + manual mark) and API
    error (retry mark)
  - escalation path: low verification_confidence routes to complex_reasoning
  - checkpoint-every-N mutation safety
  - audit log JSONL shape and hashing
  - dry-run mode produces audit entries without API calls
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

import pytest
from ruamel.yaml import YAML

from app.cross_check import merge, null_detection
from app.cross_check.audit import AuditLog, sha16
from app.cross_check.runner import LLMClient, RunStats, run_all


_yaml = YAML(typ="rt")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_library(tmp_path):
    """Materialize a miniature strategy library under tmp_path with two
    categories, four subcategories, and realistic null patterns."""
    subs_dir = tmp_path / "subcategories"
    subs_dir.mkdir()

    manifest = """\
manifest_version: "test"
categories:
  - {sequence_order: 1, code: CAT_A}
  - {sequence_order: 2, code: CAT_B}
"""
    (subs_dir / "MANIFEST.yaml").write_text(manifest)

    cat_a = """\
category_code: CAT_A
category_sequence_order: 1
subcategories:
  - {code: CAT_A_SUB_1, short_label: "Fully nulled subcategory"}
  - code: CAT_A_SUB_2
    short_label: "Has inline cite"
    statutory_cite: "IRC §199A inline"
    priority_score: 10
    obbba_touched: true
    entity_applicability: [S_CORP]
    tax_type_impacted: [FEDERAL_INCOME_TAX]
    jurisdiction_tags: [FEDERAL]
"""
    (subs_dir / "CAT_A.yaml").write_text(cat_a)

    cat_b = """\
category_code: CAT_B
category_sequence_order: 2
subcategories:
  - {code: CAT_B_SUB_1, short_label: "Only statutory_cite", statutory_cite: "IRC §61"}
  - {code: CAT_B_SUB_2, short_label: "Previously flagged manual", cross_check_required: manual}
"""
    (subs_dir / "CAT_B.yaml").write_text(cat_b)

    return subs_dir


class FakeLLM(LLMClient):
    """Deterministic fake returning scripted JSON strings. No API call."""

    def __init__(self, script: Dict[str, str]):
        super().__init__()
        self.script = script  # key: (model, prompt_sha16) -> response text
        self.calls: List[tuple] = []

    def call(self, cfg, prompt):
        key = sha16(prompt)
        self.calls.append((cfg.model, key))
        # Allow both (model, key) and key-only lookups
        if (cfg.model, key) in self.script:
            return self.script[(cfg.model, key)]
        if key in self.script:
            return self.script[key]
        if "*" in self.script:
            return self.script["*"]
        raise AssertionError(f"FakeLLM: no script entry for model={cfg.model} key={key}")


# ---------------------------------------------------------------------------
# null_detection
# ---------------------------------------------------------------------------


def test_fields_needing_population_all_six_when_bare(tmp_library):
    body = _yaml.load((tmp_library / "CAT_A.yaml").read_text())
    sub = body["subcategories"][0]  # CAT_A_SUB_1
    missing = null_detection.fields_needing_population(sub)
    assert set(missing) == {
        "priority_score", "entity_applicability", "tax_type_impacted",
        "jurisdiction_tags", "obbba_touched", "statutory_cite",
    }


def test_fields_needing_population_empty_when_complete(tmp_library):
    body = _yaml.load((tmp_library / "CAT_A.yaml").read_text())
    sub = body["subcategories"][1]  # CAT_A_SUB_2
    assert null_detection.fields_needing_population(sub) == []


def test_already_marked_manual_or_retry(tmp_library):
    body = _yaml.load((tmp_library / "CAT_B.yaml").read_text())
    sub = body["subcategories"][1]  # CAT_B_SUB_2
    assert null_detection.already_marked_manual_or_retry(sub) is True


def test_subcategories_needing_cross_check_skips_manual_flag(tmp_library):
    out = null_detection.subcategories_needing_cross_check(tmp_library)
    # Manual-flagged entry excluded; fully populated entry excluded; others in
    codes = [code for _cat, code, _missing in out]
    assert "CAT_A_SUB_1" in codes
    assert "CAT_B_SUB_1" in codes
    assert "CAT_A_SUB_2" not in codes  # fully populated
    assert "CAT_B_SUB_2" not in codes  # manual-flagged


def test_count_by_category(tmp_library):
    counts = null_detection.count_by_category(tmp_library)
    assert counts == {"CAT_A": 1, "CAT_B": 1}


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------


def test_apply_cross_check_response_populates_nulls_only(tmp_library):
    body = merge.load_category_yaml(tmp_library / "CAT_B.yaml")
    sub = merge.find_subcategory(body, "CAT_B_SUB_1")
    response = {
        "short_label": "Model-rewritten label",
        "detailed_description": "New description",
        "statutory_cite": "IRC §179",  # should NOT overwrite inline cite
        "priority_score": 8,
        "entity_applicability": ["INDIVIDUAL"],
        "tax_type_impacted": ["FEDERAL_INCOME_TAX"],
        "jurisdiction_tags": ["FEDERAL"],
        "obbba_touched": False,
        "verification_confidence": "high",
    }
    populated = merge.apply_cross_check_response(sub, response, model_used="claude-sonnet-4-6")
    # Inline cite wins; model-supplied cite ignored
    assert sub["statutory_cite"] == "IRC §61"
    # Short label was already present; preserved
    assert sub["short_label"] == "Only statutory_cite"
    # Nulls populated
    assert sub["priority_score"] == 8
    assert sub["entity_applicability"] == ["INDIVIDUAL"]
    assert sub["cross_check_model"] == "claude-sonnet-4-6"
    assert sub["cross_check_required"] is False
    assert "cross_check_utc" in sub
    assert "priority_score" in populated
    assert "statutory_cite" not in populated  # preserved, not populated


def test_apply_cross_check_response_sets_audit_fields_even_with_no_new_data(tmp_library):
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub = merge.find_subcategory(body, "CAT_A_SUB_2")  # fully populated
    populated = merge.apply_cross_check_response(sub, {}, model_used="claude-sonnet-4-6")
    assert populated == []
    assert sub["cross_check_model"] == "claude-sonnet-4-6"
    assert sub["cross_check_required"] is False


def test_mark_needs_manual_and_retry(tmp_library):
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub = merge.find_subcategory(body, "CAT_A_SUB_1")
    merge.mark_needs_manual(sub)
    assert sub["cross_check_required"] == "manual"
    assert "cross_check_utc" in sub

    merge.mark_needs_retry(sub)
    assert sub["cross_check_required"] == "retry"


def test_yaml_write_round_trip_preserves_existing_subcategory(tmp_library, tmp_path):
    # Write, read, confirm inline entries unchanged
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    out_path = tmp_path / "roundtrip.yaml"
    merge.write_category_yaml(out_path, body)
    rebody = merge.load_category_yaml(out_path)
    assert rebody["category_code"] == "CAT_A"
    assert len(rebody["subcategories"]) == 2
    # Second sub still carries its inline values
    sub2 = merge.find_subcategory(rebody, "CAT_A_SUB_2")
    assert sub2["statutory_cite"] == "IRC §199A inline"
    assert sub2["priority_score"] == 10


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


def test_audit_log_append_and_counts(tmp_path):
    log = AuditLog(tmp_path, run_date="2026-04-18")
    from app.cross_check.audit import AuditEntry
    log.append(AuditEntry(
        timestamp_utc="t",
        category="C",
        subcategory="S",
        model="m",
        prompt_hash="abc",
        response_hash="def",
        verification_confidence="high",
        status="ok",
    ))
    log.append(AuditEntry(
        timestamp_utc="t",
        category="C",
        subcategory="S2",
        model="m",
        prompt_hash="abc",
        response_hash=None,
        verification_confidence=None,
        status="api_error",
    ))
    assert log.total() == 2
    assert log.count_by_status() == {"ok": 1, "api_error": 1}


def test_sha16_deterministic():
    assert sha16("hello") == sha16("hello")
    assert sha16("hello") != sha16("world")
    assert len(sha16("hello")) == 16


# ---------------------------------------------------------------------------
# run_all — dry-run mode
# ---------------------------------------------------------------------------


def test_run_all_dry_run_counts_and_no_yaml_mutation(tmp_library, tmp_path):
    audit_dir = tmp_path / "audit"
    # Capture original YAML to confirm no mutation
    cat_a_before = (tmp_library / "CAT_A.yaml").read_text()
    cat_b_before = (tmp_library / "CAT_B.yaml").read_text()

    stats = run_all(
        today_date="2026-04-18",
        dry_run=True,
        subcategories_dir=tmp_library,
        audit_dir=audit_dir,
        llm_client=FakeLLM({}),  # never called
    )
    assert stats.total_subcategories_in_library == 4
    assert stats.needing_cross_check == 2  # SUB_1 in CAT_A and SUB_1 in CAT_B
    assert stats.dry_run == 2
    assert stats.ok == 0
    assert stats.processed == 2
    assert stats.skipped == 1  # CAT_B_SUB_2

    # YAML files untouched in dry-run
    assert (tmp_library / "CAT_A.yaml").read_text() == cat_a_before
    assert (tmp_library / "CAT_B.yaml").read_text() == cat_b_before

    # Audit file exists with two dry-run entries and one skipped entry
    log = AuditLog(audit_dir, run_date="2026-04-18")
    by_status = log.count_by_status()
    assert by_status.get("dry_run") == 2
    assert by_status.get("skipped") == 1


# ---------------------------------------------------------------------------
# run_all — real mode with fake LLM
# ---------------------------------------------------------------------------


def _valid_response(confidence="high", **overrides):
    base = {
        "short_label": "Model-generated label",
        "detailed_description": "Model-generated description",
        "statutory_cite": "N/A",
        "entity_applicability": ["INDIVIDUAL"],
        "tax_type_impacted": ["FEDERAL_INCOME_TAX"],
        "jurisdiction_tags": ["FEDERAL"],
        "priority_score": 5,
        "obbba_touched": False,
        "obbba_change_summary": None,
        "current_law_flags": [],
        "verification_confidence": confidence,
        "open_questions": [],
    }
    base.update(overrides)
    return json.dumps(base)


def test_run_all_real_path_populates_subcategories(tmp_library, tmp_path):
    fake = FakeLLM({"*": _valid_response()})
    stats = run_all(
        today_date="2026-04-18",
        dry_run=False,
        subcategories_dir=tmp_library,
        audit_dir=tmp_path / "audit",
        llm_client=fake,
        checkpoint_every=1,
    )
    assert stats.ok == 2
    assert stats.processed == 2
    assert stats.skipped == 1
    assert len(fake.calls) == 2  # no escalation

    # YAMLs mutated with cross_check metadata
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub1 = merge.find_subcategory(body, "CAT_A_SUB_1")
    assert sub1["priority_score"] == 5
    assert sub1["cross_check_model"] == "claude-sonnet-4-6"
    assert sub1["cross_check_required"] is False


def test_run_all_escalates_on_low_confidence(tmp_library, tmp_path):
    # First call (sonnet) returns low confidence; second call (opus) returns high.
    # Since prompt content is identical across calls, route by model not key.
    responses = {
        ("claude-sonnet-4-6", "*"): _valid_response(confidence="low"),
        ("claude-opus-4-7", "*"): _valid_response(confidence="high", priority_score=7),
    }
    # Build a FakeLLM that dispatches on model first
    class ModelAwareFake(FakeLLM):
        def call(self, cfg, prompt):
            self.calls.append((cfg.model, sha16(prompt)))
            return responses[(cfg.model, "*")]

    fake = ModelAwareFake({"*": ""})
    stats = run_all(
        today_date="2026-04-18",
        dry_run=False,
        subcategories_dir=tmp_library,
        audit_dir=tmp_path / "audit",
        llm_client=fake,
    )
    assert stats.escalated == 2
    assert stats.ok == 0
    # Each processed subcategory triggered two calls (sonnet + opus)
    assert len(fake.calls) == 4
    # The populated priority_score comes from the escalated response
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub1 = merge.find_subcategory(body, "CAT_A_SUB_1")
    assert sub1["priority_score"] == 7
    assert sub1["cross_check_model"] == "claude-opus-4-7"


def test_run_all_json_parse_failure_retries_then_marks_manual(tmp_library, tmp_path):
    # Both attempts return malformed JSON; subcategory must be marked manual
    class AlwaysBadJSON(FakeLLM):
        def call(self, cfg, prompt):
            self.calls.append((cfg.model, sha16(prompt)))
            return "not json at all"
    fake = AlwaysBadJSON({})
    stats = run_all(
        today_date="2026-04-18",
        dry_run=False,
        subcategories_dir=tmp_library,
        audit_dir=tmp_path / "audit",
        llm_client=fake,
    )
    assert stats.json_parse_fail == 2
    # Two attempts per processed subcategory
    assert len(fake.calls) == 4
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub1 = merge.find_subcategory(body, "CAT_A_SUB_1")
    assert sub1["cross_check_required"] == "manual"


def test_run_all_api_error_marks_retry(tmp_library, tmp_path):
    class AlwaysThrowing(FakeLLM):
        def call(self, cfg, prompt):
            self.calls.append((cfg.model, sha16(prompt)))
            raise RuntimeError("simulated API error")
    fake = AlwaysThrowing({})
    stats = run_all(
        today_date="2026-04-18",
        dry_run=False,
        subcategories_dir=tmp_library,
        audit_dir=tmp_path / "audit",
        llm_client=fake,
    )
    assert stats.api_error == 2
    body = merge.load_category_yaml(tmp_library / "CAT_A.yaml")
    sub1 = merge.find_subcategory(body, "CAT_A_SUB_1")
    assert sub1["cross_check_required"] == "retry"
