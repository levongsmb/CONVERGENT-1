"""
Config-driven prompt loader and renderer. Prompts never live in Python string
literals. Prompts live in Jinja2 templates under config/prompts/. Callers
pass template name and variables; this module returns the rendered prompt.

Template name is the filename stem without extension. Both .j2 and .md
extensions are accepted to support Markdown-format prompts for task classes
that prefer that representation.

Example:
  from app.config.prompts import render
  prompt = render("cross_check_subcategory", parent_category=cat, sub=sub, today_date=today)
"""
from pathlib import Path
from typing import Dict
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


_ROOT = Path(__file__).parent.parent.parent / "config" / "prompts"


def _build_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_ROOT)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )


_env: Environment | None = None


def _resolve_template_name(template_name: str) -> str:
    """Accept `name`, `name.j2`, or `name.md` and return the concrete filename."""
    if template_name.endswith(".j2") or template_name.endswith(".md"):
        return template_name
    for ext in (".j2", ".md"):
        candidate = _ROOT / f"{template_name}{ext}"
        if candidate.exists():
            return f"{template_name}{ext}"
    raise FileNotFoundError(
        f"Prompt template '{template_name}' not found under {_ROOT}. "
        f"Expected a file named {template_name}.j2 or {template_name}.md."
    )


def render(template_name: str, **variables) -> str:
    """Return the rendered prompt string."""
    global _env
    if _env is None:
        _env = _build_env()
    resolved = _resolve_template_name(template_name)
    template = _env.get_template(resolved)
    return template.render(**variables)


def reload() -> None:
    """Force reload of the Jinja environment (picks up edits on disk)."""
    global _env
    _env = None
