"""govinfo.gov — authoritative GPO source for USCODE (Title 26), CFR
Title 26 monthly snapshots, daily Federal Register.

Per §12A.14 this is the **statutory verification authority of record**. Any
IRC text Convergent relies on is re-parsed from the govinfo USCODE bulk
feed monthly and diffed against the cache. Cornell LII is convenience
secondary; govinfo USCODE is primary.

Phase 0 stub.
"""

from __future__ import annotations

SOURCE_NAME = "govinfo.gov"
USCODE_CADENCE = "monthly"
CFR_CADENCE = "weekly"
FEDERAL_REGISTER_CADENCE = "daily"

USCODE_BULK_URL = "https://www.govinfo.gov/bulkdata/USCODE"
CFR_TITLE_26_URL = "https://www.govinfo.gov/bulkdata/CFR/title-26"
FEDERAL_REGISTER_URL = "https://www.govinfo.gov/bulkdata/FR"
