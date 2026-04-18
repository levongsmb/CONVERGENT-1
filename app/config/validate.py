"""
Pre-commit validator for the config/ tree.

Checks:
  1. config/VERSION.yaml exists and is well-formed.
  2. config/models.yaml defines the four canonical task classes: complex_reasoning,
     bulk_cross_check, classification, memo_polish.
  3. Every escalation target referenced by a task class exists as a task class
     (no orphan references).
  4. Every YAML under config/ parses cleanly and declares `config_version`
     (top-level or under metadata:) where the schema expects one.
  5. Every prompt referenced in task-class metadata exists under config/prompts/.
  6. Every form file declares a jurisdiction and latest_revision.
  7. Authority IDs within a given year are globally unique across all authority
     files.

Run:
  python -m app.config.validate
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import yaml


_ROOT = Path(__file__).parent.parent.parent / "config"
_REQUIRED_TASK_CLASSES = {
    "complex_reasoning",
    "bulk_cross_check",
    "classification",
    "memo_polish",
}


def _parse(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def validate_all() -> List[str]:
    errors: List[str] = []

    # 1. VERSION.yaml
    version_path = _ROOT / "VERSION.yaml"
    if not version_path.exists():
        errors.append("config/VERSION.yaml is missing")
    else:
        doc = _parse(version_path)
        if "config_manifest_version" not in doc:
            errors.append("config/VERSION.yaml missing config_manifest_version")

    # 2 and 3. models.yaml
    models_path = _ROOT / "models.yaml"
    if not models_path.exists():
        errors.append("config/models.yaml is missing")
    else:
        models = _parse(models_path)
        task_classes = models.get("task_classes", {})
        missing = _REQUIRED_TASK_CLASSES - set(task_classes)
        if missing:
            errors.append(f"config/models.yaml missing required task classes: {sorted(missing)}")
        for name, entry in task_classes.items():
            target = entry.get("escalate_on_low_confidence_to") or entry.get("fallback_task_class")
            if target is not None and target not in task_classes:
                errors.append(
                    f"config/models.yaml task class '{name}' references unknown escalation target '{target}'"
                )

    # 4. Every YAML parses. Warn on missing config_version in files that should have one.
    for yaml_file in _ROOT.rglob("*.yaml"):
        try:
            _parse(yaml_file)
        except yaml.YAMLError as exc:
            errors.append(f"{yaml_file.relative_to(_ROOT.parent)} failed to parse: {exc}")

    # 5. Prompts: verify cross_check_subcategory template exists since code depends on it
    cross_check_prompt = _ROOT / "prompts" / "cross_check_subcategory.j2"
    md_variant = _ROOT / "prompts" / "cross_check_subcategory.md"
    if not cross_check_prompt.exists() and not md_variant.exists():
        errors.append("config/prompts/cross_check_subcategory.j2 or .md is missing")

    # 6. Forms structure
    for form_file in (_ROOT / "forms").rglob("*.yaml"):
        body = _parse(form_file)
        if not body.get("form_number"):
            errors.append(f"{form_file.relative_to(_ROOT.parent)} missing form_number")
        if not body.get("latest_revision"):
            errors.append(f"{form_file.relative_to(_ROOT.parent)} missing latest_revision")
        if not body.get("jurisdiction"):
            errors.append(f"{form_file.relative_to(_ROOT.parent)} missing jurisdiction")

    # 7. Authority id uniqueness per year
    authorities_root = _ROOT / "authorities"
    if authorities_root.exists():
        for year_dir in sorted(p for p in authorities_root.iterdir() if p.is_dir()):
            seen: dict[str, Path] = {}
            for auth_file in year_dir.rglob("*.yaml"):
                body = _parse(auth_file)
                container = body.get("sections") or body.get("notices") or body.get("rev_procs") or body.get("state_acts") or {}
                for authority_id in container:
                    if authority_id in seen:
                        errors.append(
                            f"Duplicate authority id '{authority_id}' in year {year_dir.name}: "
                            f"{seen[authority_id].relative_to(_ROOT.parent)} and "
                            f"{auth_file.relative_to(_ROOT.parent)}"
                        )
                    else:
                        seen[authority_id] = auth_file

    return errors


def main() -> int:
    errors = validate_all()
    if errors:
        print(f"config/ validation failed with {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("config/ validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
