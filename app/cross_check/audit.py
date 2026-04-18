"""JSONL audit log for the cross-check protocol per spec Section 4.2.

Each line records one subcategory touch:
  {
    "timestamp_utc": "...",
    "category": "CODE",
    "subcategory": "CODE",
    "model": "claude-sonnet-4-6",
    "prompt_hash": "<sha256[:16]>",
    "response_hash": "<sha256[:16]>",
    "verification_confidence": "high" | "medium" | "low",
    "status": "ok" | "escalated" | "json_parse_fail" | "api_error" | "dry_run" | "skipped",
    "fields_populated": [...],
    "duration_ms": int,
    "notes": str | null
  }
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass
class AuditEntry:
    timestamp_utc: str
    category: str
    subcategory: str
    model: Optional[str]
    prompt_hash: Optional[str]
    response_hash: Optional[str]
    verification_confidence: Optional[str]
    status: str
    fields_populated: List[str] = field(default_factory=list)
    duration_ms: int = 0
    notes: Optional[str] = None


class AuditLog:
    """Append-only JSONL audit log scoped to a single cross-check run."""

    def __init__(self, audit_dir: Path, run_date: Optional[str] = None):
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        date_token = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.path = audit_dir / f"cross_check_{date_token}.jsonl"

    def append(self, entry: AuditEntry) -> None:
        with open(self.path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def count_by_status(self) -> dict:
        counts: dict = {}
        if not self.path.exists():
            return counts
        with open(self.path) as f:
            for line in f:
                row = json.loads(line)
                counts[row["status"]] = counts.get(row["status"], 0) + 1
        return counts

    def total(self) -> int:
        if not self.path.exists():
            return 0
        with open(self.path) as f:
            return sum(1 for _ in f)
