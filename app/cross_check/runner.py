"""Cross-check runner — orchestrates the bulk_cross_check pass across every
subcategory whose metadata has nulls in the trigger fields.

Operating modes:
  - dry_run: no API calls, no YAML writes. Emits one `status: dry_run`
    audit entry per subcategory that would be processed. Used for cost
    estimation and for G4 sign-off on the planned scope.
  - real: calls the Anthropic API via the task-class-resolved model,
    writes responses back into category YAMLs, checkpoints every 50
    subcategories.

Failure handling (spec §4.3):
  - JSON parse failure on first call: retry once with same parameters.
    Second failure: mark cross_check_required="manual" and continue.
  - API error (HTTP / timeout / rate limit): log and mark
    cross_check_required="retry". Do not crash the whole run.
  - Checkpoint every 50 subcategories: rewrite each touched category YAML
    so crash recovery loses at most 50 subcategories of work.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from ruamel.yaml.comments import CommentedMap

from app.config.prompts import render
from app.config.router import LLMConfig, get_defaults, get_llm_config
from app.cross_check.audit import AuditEntry, AuditLog, sha16
from app.cross_check.merge import (
    apply_cross_check_response,
    find_subcategory,
    load_category_yaml,
    mark_needs_manual,
    mark_needs_retry,
    write_category_yaml,
)
from app.cross_check.null_detection import (
    already_marked_manual_or_retry,
    fields_needing_population,
    iter_library,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUBS_DIR = REPO_ROOT / "__strategy_library" / "subcategories"
DEFAULT_AUDIT_DIR = REPO_ROOT / "__strategy_library" / "_audit"


@dataclass
class RunStats:
    total_subcategories_in_library: int = 0
    needing_cross_check: int = 0
    processed: int = 0
    ok: int = 0
    escalated: int = 0
    json_parse_fail: int = 0
    api_error: int = 0
    dry_run: int = 0
    skipped: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# LLM call abstraction (unit-testable, swappable for mocks)
# ---------------------------------------------------------------------------


class LLMClient:
    """Thin wrapper around the Anthropic SDK. Injected into `run_all()` so
    tests can substitute a deterministic fake."""

    def __init__(self):
        self._client = None

    def _ensure(self):
        if self._client is None:
            try:
                from anthropic import Anthropic  # noqa: WPS433 — deferred import
            except ImportError as exc:
                raise RuntimeError(
                    "anthropic SDK is required for real cross-check runs. "
                    "Install with `pip install anthropic` and ensure "
                    "ANTHROPIC_API_KEY is in the environment or Windows "
                    "Credential Manager via keyring."
                ) from exc
            self._client = Anthropic()
        return self._client

    def call(self, cfg: LLMConfig, prompt: str) -> str:
        """Make a single message request and return the model's text content."""
        client = self._ensure()
        response = client.messages.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        # Expect a single text block
        return response.content[0].text


# ---------------------------------------------------------------------------
# Core per-subcategory cross-check logic
# ---------------------------------------------------------------------------


def cross_check_one(
    parent_category: str,
    sub: CommentedMap,
    *,
    today_date: str,
    llm_client: LLMClient,
) -> Tuple[dict, str, bool]:
    """Call the LLM against one subcategory. Returns (parsed_response, model_used, did_escalate).

    Raises json.JSONDecodeError on parse failure (after internal retries are
    exhausted). Raises the Anthropic SDK's exceptions on API errors.
    """
    cfg = get_llm_config("bulk_cross_check")
    prompt = render(
        "cross_check_subcategory",
        parent_category=parent_category,
        sub=sub,
        today_date=today_date,
    )
    response_text = llm_client.call(cfg, prompt)
    parsed = json.loads(response_text)  # raises JSONDecodeError on malformed output
    did_escalate = False

    if (
        parsed.get("verification_confidence") == "low"
        and cfg.escalate_on_low_confidence_to is not None
    ):
        escalated_cfg = get_llm_config(cfg.escalate_on_low_confidence_to)
        escalated_text = llm_client.call(escalated_cfg, prompt)
        parsed = json.loads(escalated_text)
        did_escalate = True
        return parsed, escalated_cfg.model, did_escalate

    return parsed, cfg.model, did_escalate


# ---------------------------------------------------------------------------
# Full-run orchestrator
# ---------------------------------------------------------------------------


def run_all(
    *,
    today_date: str,
    dry_run: bool = True,
    subcategories_dir: Path = DEFAULT_SUBS_DIR,
    audit_dir: Path = DEFAULT_AUDIT_DIR,
    llm_client: Optional[LLMClient] = None,
    include_manual_retry: bool = False,
    checkpoint_every: int = 50,
    progress: Optional[Callable[[str], None]] = None,
) -> RunStats:
    """Execute the cross-check pass. See module docstring for behavior."""
    llm = llm_client if llm_client is not None else LLMClient()
    defaults = get_defaults()
    audit = AuditLog(audit_dir, run_date=today_date)
    stats = RunStats()

    batch_counter = 0
    dirty_paths: Set[Path] = set()
    bodies: Dict[Path, CommentedMap] = {}

    def _flush_checkpoint():
        for p in dirty_paths:
            write_category_yaml(p, bodies[p])
        dirty_paths.clear()

    for cat_code, path, body in iter_library(subcategories_dir):
        bodies[path] = body
        for sub in body.get("subcategories", []):
            stats.total_subcategories_in_library += 1

            if not include_manual_retry and already_marked_manual_or_retry(sub):
                stats.skipped += 1
                audit.append(AuditEntry(
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    category=cat_code,
                    subcategory=sub["code"],
                    model=None,
                    prompt_hash=None,
                    response_hash=None,
                    verification_confidence=None,
                    status="skipped",
                    notes=f"cross_check_required={sub.get('cross_check_required')!r}",
                ))
                continue

            missing = fields_needing_population(sub)
            if not missing:
                continue  # no-op subcategory; not logged

            stats.needing_cross_check += 1
            stats.by_category[cat_code] = stats.by_category.get(cat_code, 0) + 1

            # Prompt is cheap to render even in dry-run mode; we want the hash.
            prompt = render(
                "cross_check_subcategory",
                parent_category=cat_code,
                sub=sub,
                today_date=today_date,
            )
            prompt_h = sha16(prompt)

            if dry_run:
                stats.dry_run += 1
                stats.processed += 1
                audit.append(AuditEntry(
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    category=cat_code,
                    subcategory=sub["code"],
                    model=get_llm_config("bulk_cross_check").model,
                    prompt_hash=prompt_h,
                    response_hash=None,
                    verification_confidence=None,
                    status="dry_run",
                    fields_populated=missing,
                    notes=f"would populate: {missing}",
                ))
                if progress:
                    progress(f"[dry] {cat_code}.{sub['code']} missing={len(missing)}")
                continue

            # Real call path
            start = time.monotonic()
            parse_attempts = 0
            while True:
                parse_attempts += 1
                try:
                    parsed, model_used, did_escalate = cross_check_one(
                        cat_code, sub, today_date=today_date, llm_client=llm,
                    )
                    break
                except json.JSONDecodeError as exc:
                    if parse_attempts >= 2:
                        mark_needs_manual(sub)
                        dirty_paths.add(path)
                        stats.json_parse_fail += 1
                        stats.processed += 1
                        audit.append(AuditEntry(
                            timestamp_utc=datetime.now(timezone.utc).isoformat(),
                            category=cat_code,
                            subcategory=sub["code"],
                            model=get_llm_config("bulk_cross_check").model,
                            prompt_hash=prompt_h,
                            response_hash=None,
                            verification_confidence=None,
                            status="json_parse_fail",
                            fields_populated=[],
                            duration_ms=int((time.monotonic() - start) * 1000),
                            notes=f"{type(exc).__name__}: {exc}",
                        ))
                        if progress:
                            progress(f"[manual] {cat_code}.{sub['code']} JSON parse failed twice")
                        parsed = None
                        break
                    # single retry, no delay for deterministic tests
                    continue
                except Exception as exc:  # API error / network / rate limit
                    mark_needs_retry(sub)
                    dirty_paths.add(path)
                    stats.api_error += 1
                    stats.processed += 1
                    audit.append(AuditEntry(
                        timestamp_utc=datetime.now(timezone.utc).isoformat(),
                        category=cat_code,
                        subcategory=sub["code"],
                        model=get_llm_config("bulk_cross_check").model,
                        prompt_hash=prompt_h,
                        response_hash=None,
                        verification_confidence=None,
                        status="api_error",
                        fields_populated=[],
                        duration_ms=int((time.monotonic() - start) * 1000),
                        notes=f"{type(exc).__name__}: {exc}",
                    ))
                    if progress:
                        progress(f"[retry] {cat_code}.{sub['code']} API error: {exc}")
                    parsed = None
                    break

            if parsed is None:
                # Already logged + marked. Move on.
                pass
            else:
                response_h = sha16(json.dumps(parsed, sort_keys=True))
                populated = apply_cross_check_response(
                    sub, parsed, model_used=model_used,
                )
                dirty_paths.add(path)
                stats.processed += 1
                if did_escalate:
                    stats.escalated += 1
                else:
                    stats.ok += 1
                audit.append(AuditEntry(
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    category=cat_code,
                    subcategory=sub["code"],
                    model=model_used,
                    prompt_hash=prompt_h,
                    response_hash=response_h,
                    verification_confidence=parsed.get("verification_confidence"),
                    status="escalated" if did_escalate else "ok",
                    fields_populated=populated,
                    duration_ms=int((time.monotonic() - start) * 1000),
                ))
                if progress:
                    progress(
                        f"[{'esc' if did_escalate else 'ok'}] {cat_code}.{sub['code']} "
                        f"+{len(populated)} fields"
                    )

            # Rate limiting + checkpoint
            batch_counter += 1
            if defaults.get("batch_size") and batch_counter % defaults["batch_size"] == 0:
                if defaults.get("batch_delay_seconds"):
                    time.sleep(defaults["batch_delay_seconds"])
            if batch_counter % checkpoint_every == 0:
                _flush_checkpoint()

    _flush_checkpoint()
    return stats
