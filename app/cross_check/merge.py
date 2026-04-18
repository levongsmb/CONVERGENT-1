"""Merge cross-check LLM responses back into category YAML files.

Principles:
  1. Never overwrite a field that already has a non-null value. The
     cross-check populates nulls; inline-cited cites (e.g., CA_PTET_ELECTION
     `statutory_cite`) are the source of truth and remain.
  2. Set cross_check_utc and cross_check_model every time the cross-check
     runs, regardless of whether any fields were populated.
  3. Use ruamel.yaml round-trip to preserve flow style and comments on
     untouched entries. Subcategories that gain new fields will transition
     to block style automatically.
  4. `cross_check_required: false` is set after a successful parse; if the
     LLM returned `verification_confidence: low` and we escalated, a note
     is attached.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


_yaml = YAML(typ="rt")
_yaml.preserve_quotes = True
_yaml.width = 4096  # keep long lines on one line


# Fields the LLM populates (matches the prompt's JSON schema).
_LLM_OUTPUT_FIELDS = (
    "short_label",
    "detailed_description",
    "statutory_cite",
    "entity_applicability",
    "tax_type_impacted",
    "jurisdiction_tags",
    "priority_score",
    "obbba_touched",
    "obbba_change_summary",
    "current_law_flags",
    "verification_confidence",
    "open_questions",
)


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set, str)) and len(value) == 0:
        return True
    return False


def apply_cross_check_response(
    sub: CommentedMap,
    response: dict,
    *,
    model_used: str,
    utc_timestamp: Optional[str] = None,
) -> List[str]:
    """Merge LLM response into subcategory dict. Returns list of populated field names."""
    populated: List[str] = []
    utc = utc_timestamp or datetime.now(timezone.utc).isoformat()

    for field_name in _LLM_OUTPUT_FIELDS:
        if field_name not in response:
            continue
        new_value = response[field_name]
        if _is_blank(new_value):
            continue
        current = sub.get(field_name)
        if _is_blank(current):
            sub[field_name] = new_value
            populated.append(field_name)
        # If current is non-blank, we preserve it (existing inline cite wins)

    sub["cross_check_utc"] = utc
    sub["cross_check_model"] = model_used
    sub["cross_check_required"] = False

    return populated


def mark_needs_manual(sub: CommentedMap, utc_timestamp: Optional[str] = None) -> None:
    """Flag a subcategory for human review after two JSON parse failures."""
    sub["cross_check_utc"] = utc_timestamp or datetime.now(timezone.utc).isoformat()
    sub["cross_check_required"] = "manual"


def mark_needs_retry(sub: CommentedMap, utc_timestamp: Optional[str] = None) -> None:
    """Flag a subcategory for next-run retry after a transient API error."""
    sub["cross_check_utc"] = utc_timestamp or datetime.now(timezone.utc).isoformat()
    sub["cross_check_required"] = "retry"


def load_category_yaml(path: Path) -> CommentedMap:
    with open(path) as f:
        return _yaml.load(f)


def write_category_yaml(path: Path, body: CommentedMap) -> None:
    with open(path, "w") as f:
        _yaml.dump(body, f)


def find_subcategory(body: CommentedMap, sub_code: str) -> Optional[CommentedMap]:
    for sub in body.get("subcategories", []):
        if sub.get("code") == sub_code:
            return sub
    return None
