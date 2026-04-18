"""Evaluator registry. Discovers every module under `app.evaluators.<CAT>`
that exports a class named `Evaluator` and indexes it by SUBCATEGORY_CODE.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

from app.evaluators._base import BaseEvaluator


_registry: Dict[str, Type[BaseEvaluator]] = {}
_registered = False


def register_all() -> None:
    """Walk the evaluators package tree, import every submodule, and
    index any class named `Evaluator`. Idempotent — repeated calls are
    cheap."""
    global _registered
    if _registered:
        return

    import app.evaluators as pkg

    for _finder, module_name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if not is_pkg:
            continue
        if module_name.startswith("_"):
            continue
        subpkg = importlib.import_module(f"app.evaluators.{module_name}")
        for _sf, sub_module_name, sub_is_pkg in pkgutil.iter_modules(subpkg.__path__):
            if sub_is_pkg:
                continue
            if sub_module_name.startswith("_"):
                continue
            mod = importlib.import_module(
                f"app.evaluators.{module_name}.{sub_module_name}"
            )
            if hasattr(mod, "Evaluator"):
                ev_cls = getattr(mod, "Evaluator")
                _registry[ev_cls.SUBCATEGORY_CODE] = ev_cls

    _registered = True


def reset() -> None:
    """Test hook — forget registered evaluators."""
    global _registered
    _registry.clear()
    _registered = False


def get(subcategory_code: str) -> Type[BaseEvaluator]:
    register_all()
    return _registry[subcategory_code]


def all_evaluators() -> Dict[str, Type[BaseEvaluator]]:
    register_all()
    return dict(_registry)
