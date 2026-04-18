"""Source-specific polling modules.

Each source implements::

    async def poll(since: datetime) -> SourceDelta:
        ...

and returns a structured delta the scheduler folds into a new snapshot. All
source modules are Phase 0 stubs; real implementations land in Phase 7.
"""
