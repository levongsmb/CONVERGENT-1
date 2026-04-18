"""
Config-driven LLM routing. Code references task classes; config maps to models.
Swap models in config/models.yaml without touching code.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "models.yaml"
_cache: Optional[dict] = None


@dataclass(frozen=True)
class LLMConfig:
    task_class: str
    provider: str
    model: str
    max_tokens: int
    temperature: float
    top_p: float
    fallback_task_class: Optional[str]
    escalate_on_low_confidence_to: Optional[str]
    description: str


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_CONFIG_PATH) as f:
            _cache = yaml.safe_load(f)
    return _cache


def reload() -> None:
    """Force reload of config from disk. Call after in-process edits to config/models.yaml."""
    global _cache
    _cache = None


def get_llm_config(task_class: str) -> LLMConfig:
    config = _load()
    if task_class not in config["task_classes"]:
        raise KeyError(f"Unknown task class: {task_class}. Defined: {list(config['task_classes'])}")
    entry = config["task_classes"][task_class]
    return LLMConfig(
        task_class=task_class,
        provider=entry["provider"],
        model=entry["model"],
        max_tokens=entry["max_tokens"],
        temperature=entry["temperature"],
        top_p=entry.get("top_p", 1.0),
        fallback_task_class=entry.get("fallback_task_class"),
        escalate_on_low_confidence_to=entry.get("escalate_on_low_confidence_to"),
        description=entry.get("description", ""),
    )


def get_defaults() -> dict:
    return _load().get("defaults", {})
