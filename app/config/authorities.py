"""
Config-driven statutory authority loader. Evaluators and report generators call
get_authority(id, year) to resolve canonical cites, amendment metadata, and
related regulation references.

Examples:
  get_authority("199A", 2026)         # from config/authorities/2026/irc_sections.yaml
  get_authority("1202", 2026)
  get_authority("SB_132", 2026)       # from config/authorities/2026/state/ca_sb_132.yaml
  get_authority("NOTICE_2026_3", 2026) # from config/authorities/2026/notices.yaml

The loader walks the authority files under config/authorities/<year>/ and its
subdirectories, building a flat id-to-record index. Authority IDs must be
globally unique within a year.
"""
from pathlib import Path
from threading import Lock
from typing import Dict, Optional
import yaml


_ROOT = Path(__file__).parent.parent.parent / "config" / "authorities"
_cache: Dict[int, Dict[str, dict]] = {}
_lock = Lock()


def _build_index(year: int) -> Dict[str, dict]:
    index: Dict[str, dict] = {}
    year_root = _ROOT / str(year)
    if not year_root.exists():
        raise FileNotFoundError(
            f"Authority cache miss for year {year}. Expected config/authorities/{year}/ to exist."
        )
    for yaml_file in sorted(year_root.rglob("*.yaml")):
        with open(yaml_file) as f:
            body = yaml.safe_load(f)
        sections = body.get("sections") or body.get("notices") or body.get("rev_procs") or body.get("state_acts")
        if not sections:
            continue
        for authority_id, record in sections.items():
            if authority_id in index:
                raise ValueError(
                    f"Duplicate authority id '{authority_id}' in year {year}: "
                    f"{index[authority_id].get('_source_file')} and {yaml_file}"
                )
            record_copy = dict(record)
            record_copy["_source_file"] = str(yaml_file.relative_to(year_root.parent.parent))
            record_copy["_authority_id"] = authority_id
            index[authority_id] = record_copy
    return index


def get_authority(authority_id: str, year: int) -> dict:
    """Return the parsed authority record for an id in a given year."""
    if year not in _cache:
        with _lock:
            if year not in _cache:
                _cache[year] = _build_index(year)
    index = _cache[year]
    if authority_id not in index:
        raise KeyError(
            f"Authority '{authority_id}' not found in year {year}. "
            f"Check config/authorities/{year}/ or cross-check the id spelling."
        )
    return index[authority_id]


def reload() -> None:
    """Force reload of all cached authority indices."""
    with _lock:
        _cache.clear()
