"""Determine which subcategories require cross-check.

Per spec Section 4: "Run against every subcategory where `priority_score`,
`entity_applicability`, `tax_type_impacted`, `jurisdiction_tags`,
`obbba_touched`, or `statutory_cite` is null."

A subcategory "needs" cross-check if ANY of those fields is absent, None,
or an empty collection. The `needs_reason` function returns the specific
fields missing so the audit log can record what the cross-check populated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ruamel.yaml import YAML


TRIGGER_FIELDS: Tuple[str, ...] = (
    "priority_score",
    "entity_applicability",
    "tax_type_impacted",
    "jurisdiction_tags",
    "obbba_touched",
    "statutory_cite",
)


_yaml = YAML(typ="rt")  # round-trip loader; preserves formatting and key order


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set, str)) and len(value) == 0:
        return True
    return False


def fields_needing_population(sub: dict) -> List[str]:
    """Return the list of trigger fields that are absent or blank on a subcategory."""
    out: List[str] = []
    for f in TRIGGER_FIELDS:
        if f not in sub or _is_blank(sub[f]):
            out.append(f)
    return out


def needs_cross_check(sub: dict) -> bool:
    return len(fields_needing_population(sub)) > 0


def already_marked_manual_or_retry(sub: dict) -> bool:
    """Re-running the protocol should skip subcategories we already
    flagged for human follow-up on a prior pass."""
    ccr = sub.get("cross_check_required")
    return ccr in ("manual", "retry")


def load_category(path: Path) -> dict:
    with open(path) as f:
        return _yaml.load(f)


def iter_library(subcategories_dir: Path) -> Iterable[Tuple[str, Path, dict]]:
    """Yield (category_code, category_file_path, parsed_body) tuples in
    MANIFEST sequence order."""
    manifest_path = subcategories_dir / "MANIFEST.yaml"
    with open(manifest_path) as f:
        manifest = _yaml.load(f)
    for entry in manifest["categories"]:
        code = entry["code"]
        p = subcategories_dir / f"{code}.yaml"
        body = load_category(p)
        yield code, p, body


def subcategories_needing_cross_check(
    subcategories_dir: Path,
    *,
    include_manual_retry: bool = False,
) -> List[Tuple[str, str, List[str]]]:
    """Return a list of (category_code, subcategory_code, missing_fields) for
    every subcategory that needs cross-check.
    """
    out: List[Tuple[str, str, List[str]]] = []
    for cat_code, _path, body in iter_library(subcategories_dir):
        for sub in body.get("subcategories", []):
            if not include_manual_retry and already_marked_manual_or_retry(sub):
                continue
            missing = fields_needing_population(sub)
            if missing:
                out.append((cat_code, sub["code"], missing))
    return out


def count_by_category(
    subcategories_dir: Path, *, include_manual_retry: bool = False
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for cat_code, sub_code, _ in subcategories_needing_cross_check(
        subcategories_dir, include_manual_retry=include_manual_retry
    ):
        counts[cat_code] = counts.get(cat_code, 0) + 1
    return counts
