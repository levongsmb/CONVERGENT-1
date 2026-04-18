"""Phase 0 rules cache bootstrap runner.

Per Decision 0001 (Option C): populate a first-pass rules cache with values
for which we can produce a current pin cite from primary authority. Where a
value requires not-yet-released Rev. Procs, depends on an open user-judgment
decision, or falls inside the OBBBA sunset-watch list, the entry is
explicit: ``verification_status = awaiting_user_input`` with the specific
authority the value will come from once available.

This runner does not hit the network. It reads the curated YAML files
under ``rules_cache_bootstrap/`` and materializes them as a
``rules_cache_snapshot`` row plus per-parameter rows. The YAML files are the
artifact the user personally reviews for Phase 0 sign-off.

Usage (from the dev console or the installer post-install step):

    python -m convergent.authority_layer.statutory_mining.bootstrap

This is a Phase 0 **scaffold** — the materialization logic is stubbed until
Phase 2 (when the rules cache DB session manager is real).
"""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_root() -> Path:
    """Repo-relative fallback when running from source; installer path otherwise.

    Path traversal (running from source):
      __file__ = <repo>/convergent/authority_layer/statutory_mining/bootstrap.py
      parents[0] = statutory_mining/
      parents[1] = authority_layer/
      parents[2] = convergent/
      parents[3] = <repo>/
    """
    here = Path(__file__).resolve()
    repo_candidate = here.parents[3] / "rules_cache_bootstrap"
    if repo_candidate.exists():
        return repo_candidate
    # Installed path (set by `convergent.config.rules_cache_seed_dir()` in Phase 2).
    from convergent import config

    return config.rules_cache_seed_dir()


def enumerate_yaml_files(root: Path) -> list[Path]:
    """List every bootstrapped-parameter YAML under the root."""
    return sorted(p for p in root.rglob("*.yaml") if not p.name.startswith("_"))


def run() -> int:
    """CLI entry point. Phase 0: prints the bootstrap review plan."""
    root = bootstrap_root()
    if not root.exists():
        print(f"Rules cache bootstrap directory not found: {root}", file=sys.stderr)
        return 1

    files = enumerate_yaml_files(root)
    print(f"Convergent rules cache bootstrap — Phase 0 review plan")
    print(f"Source: {root}")
    print(f"Files enumerated: {len(files)}\n")
    for f in files:
        print(f"  - {f.relative_to(root)}")
    print()
    print("Phase 0 gate: the user must personally sign off every parameter")
    print("in these files before Phase 1 begins. See")
    print("rules_cache_bootstrap/review_checklist.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
