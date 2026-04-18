"""Statutory Mining refresh scheduler.

Launched as an asyncio background task at app startup. Per §12A.5 /
§12A.6:

- Daily: IRS newsroom, Tax Court opinions, FTB news, Federal Register
- Weekly: Listed/Reportable indices, regs.gov docket, eCFR diffs,
  govinfo CFR Title 26 monthly snapshot check
- Monthly: IRC statutory text from govinfo USCODE bulk
- Annually: indexed-amount Rev. Proc. refresh (Nov/Oct)

The refresh produces a new ``rules_cache_snapshot`` + diff report. Open
engagements remain pinned to their own snapshot; a UI prompt asks whether
to re-run scenarios against the new snapshot.

Phase 0: skeleton only. Source polling lands in Phase 7.
"""

from __future__ import annotations


async def refresh_forever() -> None:
    """Phase 0 stub — full scheduler lands in Phase 7."""
    raise NotImplementedError("Phase 0 stub — scheduler lands in Phase 7.")


def run_once() -> int:
    """Synchronous one-shot refresh for manual / test invocation. Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — manual refresh lands in Phase 7.")
