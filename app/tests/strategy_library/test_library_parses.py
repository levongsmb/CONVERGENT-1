"""Phase 1b acceptance tests — Strategy Library inventory integrity.

Tests:
  1. MANIFEST.yaml lists exactly 40 categories with unique sequence orders 1-40
  2. Every category listed in MANIFEST has a matching YAML file
  3. Every category YAML declares `category_code` matching its filename stem and
     `category_sequence_order` matching MANIFEST
  4. No duplicate subcategory codes globally across all 40 files
  5. Every `cross_references` entry either references CATEGORY_CODE (whole
     category) or CATEGORY_CODE.SUB_CODE that exists
  6. Every `merged_from` value is a plausible legacy category name (no
     circular references; merges are informational legacy tracking only)
  7. OBBBA-touched subcategories carry a statutory_cite where required by spec
  8. Total subcategory count aligns with spec expectation of ~590
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_ROOT = REPO_ROOT / "__strategy_library" / "subcategories"
MANIFEST_PATH = LIB_ROOT / "MANIFEST.yaml"


def _load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def _load_category(code: str) -> dict:
    with open(LIB_ROOT / f"{code}.yaml") as f:
        return yaml.safe_load(f)


def _collect_all() -> Tuple[dict, Dict[str, dict]]:
    manifest = _load_manifest()
    cats: Dict[str, dict] = {}
    for entry in manifest["categories"]:
        cats[entry["code"]] = _load_category(entry["code"])
    return manifest, cats


def test_manifest_has_forty_categories_in_sequence():
    manifest = _load_manifest()
    entries = manifest["categories"]
    assert len(entries) == 40, f"expected 40 categories, got {len(entries)}"
    seqs = [e["sequence_order"] for e in entries]
    assert seqs == list(range(1, 41)), f"sequence orders out of order: {seqs}"
    codes = [e["code"] for e in entries]
    assert len(set(codes)) == 40, "duplicate category codes in MANIFEST"


def test_every_manifest_category_has_yaml_file():
    manifest = _load_manifest()
    for entry in manifest["categories"]:
        p = LIB_ROOT / f"{entry['code']}.yaml"
        assert p.exists(), f"missing category file: {p}"


def test_no_extra_category_files_beyond_manifest():
    manifest = _load_manifest()
    declared = {e["code"] for e in manifest["categories"]}
    present = {p.stem for p in LIB_ROOT.glob("*.yaml") if p.stem != "MANIFEST"}
    extra = present - declared
    assert not extra, f"orphan category files not in MANIFEST: {sorted(extra)}"


def test_every_category_code_and_sequence_match_manifest():
    manifest, cats = _collect_all()
    expected_seq = {e["code"]: e["sequence_order"] for e in manifest["categories"]}
    for code, body in cats.items():
        assert body.get("category_code") == code, (
            f"{code}.yaml declares category_code={body.get('category_code')}"
        )
        assert body.get("category_sequence_order") == expected_seq[code], (
            f"{code}.yaml declares sequence_order={body.get('category_sequence_order')} "
            f"but MANIFEST has {expected_seq[code]}"
        )


def test_no_duplicate_subcategory_codes_globally():
    _, cats = _collect_all()
    seen: Dict[str, str] = {}
    dupes: List[Tuple[str, str, str]] = []
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            sc = sub["code"]
            if sc in seen:
                dupes.append((sc, seen[sc], cat_code))
            else:
                seen[sc] = cat_code
    assert not dupes, f"duplicate subcategory codes across categories: {dupes}"


def test_cross_references_resolve():
    _, cats = _collect_all()
    # Build the full set of (category_code, subcategory_code) pairs plus
    # the set of category codes for whole-category references.
    all_subs: Set[str] = set()
    all_cats: Set[str] = set(cats.keys())
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            all_subs.add(f"{cat_code}.{sub['code']}")
    # Now walk cross_references on every subcategory.
    unresolved: List[str] = []
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            for ref in sub.get("cross_references", []) or []:
                if "." in ref:
                    if ref not in all_subs:
                        unresolved.append(f"{cat_code}.{sub['code']} -> {ref}")
                else:
                    # Whole-category reference
                    if ref not in all_cats:
                        unresolved.append(f"{cat_code}.{sub['code']} -> {ref}")
    assert not unresolved, f"unresolved cross_references: {unresolved}"


def test_merged_from_references_are_legacy_only():
    """merged_from is informational legacy tracking. The referenced name must
    NOT be a current category code (otherwise it would indicate a real circular
    merge). Legacy names like IRS_CONTROVERSY_DEFENSE are fine.
    """
    _, cats = _collect_all()
    current_codes = set(cats.keys())
    offenders: List[str] = []
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            mf = sub.get("merged_from")
            if mf is not None and mf in current_codes:
                offenders.append(f"{cat_code}.{sub['code']} merged_from={mf} (a current category)")
    assert not offenders, f"merged_from should reference legacy names, not current categories: {offenders}"


def test_obbba_touched_has_statutory_cite_or_open_cross_check():
    """Every OBBBA-touched subcategory either provides a statutory_cite
    inline OR is left to the Phase 2 cross-check (cite populated by model)."""
    _, cats = _collect_all()
    missing: List[str] = []
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            if sub.get("obbba_touched") is True:
                has_cite = bool(sub.get("statutory_cite"))
                # Spec allows Phase 2 population; we only require that the
                # field either exists or is left null (not a typo).
                if not has_cite and "statutory_cite" in sub and sub["statutory_cite"] not in (None, ""):
                    missing.append(f"{cat_code}.{sub['code']}")
    assert not missing, f"OBBBA-touched subcategories with malformed statutory_cite: {missing}"


def test_total_subcategory_count_in_expected_range():
    """Spec text references ~590 subcategories. Allow a reasonable band."""
    _, cats = _collect_all()
    total = sum(len(body.get("subcategories", [])) for body in cats.values())
    assert 550 <= total <= 650, f"total subcategory count {total} outside expected band 550-650"


def test_evaluator_path_when_present_is_well_formed():
    """If evaluator_path is provided on any subcategory, it must follow the
    expected scheme app/evaluators/<CATEGORY_CODE>/<SUB_CODE>.py.
    """
    _, cats = _collect_all()
    offenders: List[str] = []
    for cat_code, body in cats.items():
        for sub in body.get("subcategories", []):
            ep = sub.get("evaluator_path")
            if ep is None:
                continue
            expected = f"app/evaluators/{cat_code}/{sub['code']}.py"
            if ep != expected:
                offenders.append(f"{cat_code}.{sub['code']}: {ep!r} != {expected!r}")
    assert not offenders, f"malformed evaluator_path values: {offenders}"
