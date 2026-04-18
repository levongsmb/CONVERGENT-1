"""Fixture loader for ClientScenario YAML files.

Evaluator tests and the orchestrator load scenarios through this module so
the YAML-to-model boundary is exercised in a single canonical way.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from app.scenario.models import ClientScenario


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_scenario(path: Path | str) -> ClientScenario:
    """Load a single ClientScenario from a YAML path."""
    p = Path(path)
    with open(p) as f:
        body = yaml.safe_load(f)
    return ClientScenario.model_validate(body)


def load_all_fixtures() -> List[ClientScenario]:
    """Load every YAML fixture under app/scenario/fixtures/."""
    out: List[ClientScenario] = []
    for f in sorted(FIXTURES_DIR.glob("*.yaml")):
        out.append(load_scenario(f))
    return out


def fixture_paths() -> List[Path]:
    return sorted(FIXTURES_DIR.glob("*.yaml"))
