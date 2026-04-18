"""CLI entry point for the cross-check protocol.

Dry-run (default, safe, no API calls):
    python -m app.cross_check

Real run with API calls:
    python -m app.cross_check --real --today-date 2026-04-18

Include subcategories previously flagged for retry/manual review:
    python -m app.cross_check --real --include-manual-retry
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from app.cross_check.runner import run_all


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.cross_check")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Make real Anthropic API calls. Default is dry-run.",
    )
    parser.add_argument(
        "--today-date",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Date token baked into the prompt and the audit filename (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--include-manual-retry",
        action="store_true",
        help="Also process subcategories previously marked cross_check_required=manual or retry.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=50,
        help="Rewrite touched category YAML files every N processed subcategories.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-subcategory progress output.",
    )
    args = parser.parse_args(argv)

    dry_run = not args.real
    progress = None if args.quiet else (lambda msg: print(msg, file=sys.stderr))

    if dry_run:
        print("DRY-RUN mode: no API calls will be made.", file=sys.stderr)
    else:
        print("REAL mode: Anthropic API calls will be made.", file=sys.stderr)

    stats = run_all(
        today_date=args.today_date,
        dry_run=dry_run,
        include_manual_retry=args.include_manual_retry,
        checkpoint_every=args.checkpoint_every,
        progress=progress,
    )

    print()
    print("Cross-check run complete.")
    print(f"  Total subcategories in library : {stats.total_subcategories_in_library}")
    print(f"  Needing cross-check            : {stats.needing_cross_check}")
    print(f"  Processed                      : {stats.processed}")
    print(f"  ok                             : {stats.ok}")
    print(f"  escalated to complex_reasoning : {stats.escalated}")
    print(f"  json_parse_fail                : {stats.json_parse_fail}")
    print(f"  api_error                      : {stats.api_error}")
    print(f"  dry_run                        : {stats.dry_run}")
    print(f"  skipped                        : {stats.skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
