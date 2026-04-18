"""
Config-driven rules cache loader. Evaluators call get_rule(key, year).

Keys are slash-delimited paths relative to config/rules_cache/<year>/ without
the .yaml extension. Examples:
  get_rule("federal/qbi_199a", 2026)
  get_rule("federal/individual_brackets", 2026)
  get_rule("california/ptet", 2026)

The returned object is the fully parsed YAML document. Consumers navigate its
structure through their own knowledge of the parameter family.
"""
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, Optional
import yaml


_ROOT = Path(__file__).parent.parent.parent / "config" / "rules_cache"
_cache: Dict[tuple, dict] = {}
_lock = Lock()


@dataclass(frozen=True)
class RuleBundle:
    year: int
    key: str
    path: Path
    body: dict
    version: Optional[str]


def _resolve(key: str, year: int) -> Path:
    return _ROOT / str(year) / f"{key}.yaml"


def get_rule(key: str, year: int) -> dict:
    """Return the parsed YAML document for a rule key in a given tax year."""
    ck = (year, key)
    if ck in _cache:
        return _cache[ck]
    with _lock:
        if ck in _cache:
            return _cache[ck]
        path = _resolve(key, year)
        if not path.exists():
            raise FileNotFoundError(
                f"Rule cache miss: {key} for year {year}. Expected at {path}. "
                f"Populate config/rules_cache/{year}/ or check the key path."
            )
        with open(path) as f:
            body = yaml.safe_load(f)
        _cache[ck] = body
        return body


def get_rule_bundle(key: str, year: int) -> RuleBundle:
    """Return a RuleBundle with provenance metadata."""
    path = _resolve(key, year)
    body = get_rule(key, year)
    version = None
    if isinstance(body, dict):
        version = body.get("config_version") or body.get("metadata", {}).get("config_version")
    return RuleBundle(year=year, key=key, path=path, body=body, version=version)


def cache_version() -> str:
    """Return the top-level config manifest version for audit logging."""
    manifest_path = Path(__file__).parent.parent.parent / "config" / "VERSION.yaml"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return yaml.safe_load(f).get("config_manifest_version", "unknown")
    return "unknown"


def reload() -> None:
    """Force reload of all cached rules. Call after in-process edits to config/rules_cache/."""
    with _lock:
        _cache.clear()
