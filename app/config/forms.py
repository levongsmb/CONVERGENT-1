"""
Config-driven form metadata loader. Report generators and workflow prompts call
get_form(id, year) to resolve form numbers, current revisions, filing due dates,
and election mechanisms without hardcoding any of this in Python.

Lookup identifiers are the YAML filename stem (lowercase, no extension). The
jurisdiction is inferred from the subdirectory.

Examples:
  get_form("3804", 2026, jurisdiction="california")
  get_form("1040", 2026, jurisdiction="federal")
"""
from pathlib import Path
from threading import Lock
from typing import Dict, Optional
import yaml


_ROOT = Path(__file__).parent.parent.parent / "config" / "forms"
_cache: Dict[tuple, dict] = {}
_lock = Lock()


def _resolve(form_id: str, jurisdiction: str) -> Path:
    return _ROOT / jurisdiction / f"{form_id}.yaml"


def get_form(form_id: str, year: int, *, jurisdiction: str) -> dict:
    """Return parsed form metadata. Raises if form does not apply to the requested year."""
    ck = (jurisdiction, form_id, year)
    if ck in _cache:
        return _cache[ck]
    with _lock:
        if ck in _cache:
            return _cache[ck]
        path = _resolve(form_id, jurisdiction)
        if not path.exists():
            raise FileNotFoundError(
                f"Form metadata not found: {jurisdiction}/{form_id}. Expected at {path}."
            )
        with open(path) as f:
            body = yaml.safe_load(f)
        applies_to = body.get("applies_to_tax_years")
        if applies_to is not None and str(year) not in [str(y) for y in applies_to]:
            raise ValueError(
                f"Form {jurisdiction}/{form_id} is not configured for tax year {year}. "
                f"Declared applicable years: {applies_to}."
            )
        _cache[ck] = body
        return body


def reload() -> None:
    """Force reload of all cached form metadata."""
    with _lock:
        _cache.clear()
