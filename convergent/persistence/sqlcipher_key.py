"""SQLCipher key derivation, DPAPI-sealed per §16.2.

Every engagement SQLite file is encrypted with a per-engagement 256-bit
random key. That key is sealed via Windows DPAPI with
`CRYPTPROTECT_LOCAL_MACHINE=off` so the seal is bound to the user account
(not the machine globally), then stored alongside the DB as a
`.key` sidecar.

Phase 0 ships the API surface; the DPAPI ``pywin32`` wiring is implemented
in Phase 2 alongside the engagement DB session manager. On non-Windows
dev machines the stub raises ``NotImplementedError`` loudly so no test
silently uses cleartext storage.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def generate_engagement_key() -> bytes:
    """Return a fresh 32-byte random key suitable for SQLCipher."""
    return os.urandom(32)


def seal_key(plaintext_key: bytes, description: str) -> bytes:
    """Seal an engagement key via DPAPI (user-scope). Stubbed in Phase 0."""
    if sys.platform != "win32":
        raise NotImplementedError(
            "DPAPI seal requires Windows. Encryption key management is Windows-only."
        )
    raise NotImplementedError("Phase 0 stub — DPAPI wiring lands in Phase 2.")


def unseal_key(sealed_blob: bytes) -> bytes:
    """Unseal a DPAPI-sealed engagement key. Stubbed in Phase 0."""
    if sys.platform != "win32":
        raise NotImplementedError(
            "DPAPI unseal requires Windows. Encryption key management is Windows-only."
        )
    raise NotImplementedError("Phase 0 stub — DPAPI wiring lands in Phase 2.")


def key_sidecar_path(engagement_db_path: Path) -> Path:
    return engagement_db_path.with_suffix(engagement_db_path.suffix + ".key")
