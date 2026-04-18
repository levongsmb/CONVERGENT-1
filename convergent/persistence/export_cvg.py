"""Portable .cvg export/import per §16.4.

The resident engagement DB is DPAPI-sealed to a specific user account on a
specific machine. The .cvg format is the portable, machine-and-account
independent alternative: the SQLite bytes are decrypted, then re-encrypted
with a passphrase-derived key (Argon2id + AES-256-GCM), then wrapped in a
tar archive with an unencrypted manifest.

Phase 0: API surface + manifest schema. Implementation lands alongside the
engagement DB in Phase 2 and the full UI wiring in Phase 10.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# Argon2id parameters per §16.4: memory cost 256 MiB, time cost 4, parallelism 2.
ARGON2_MEMORY_KIB = 256 * 1024
ARGON2_TIME_COST = 4
ARGON2_PARALLELISM = 2
KEY_BYTES = 32


@dataclass(frozen=True)
class CvgManifest:
    engagement_id: str
    export_timestamp: datetime
    exporting_user: str
    source_machine_fingerprint: str
    convergent_version: str
    rules_cache_snapshot_id: str
    file_size_bytes: int
    ciphertext_sha256: str
    argon2_salt_b64: str
    argon2_memory_kib: int
    argon2_time_cost: int
    argon2_parallelism: int


def export_engagement(
    engagement_db_path: Path,
    destination_cvg: Path,
    passphrase: str,
    *,
    exporting_user: str,
    rules_cache_snapshot_id: str,
) -> CvgManifest:
    """Serialize an engagement to a .cvg file. Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — .cvg export lands in Phase 2.")


def import_engagement(
    source_cvg: Path,
    passphrase: str,
    *,
    importing_user: str,
    destination_engagements_dir: Path,
) -> Path:
    """Import a .cvg file, re-seal the DB under the local DPAPI key, return the new path."""
    raise NotImplementedError("Phase 0 stub — .cvg import lands in Phase 2.")


def inspect_manifest(source_cvg: Path) -> CvgManifest:
    """Read the unencrypted manifest from a .cvg file. Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — .cvg import lands in Phase 2.")


WEAK_PASSPHRASE_FLOOR_LEN = 12


def is_passphrase_acceptable(passphrase: str) -> tuple[bool, str | None]:
    """Minimum-length and weak-list check per §16.4. Placeholder until Phase 2."""
    if len(passphrase) < WEAK_PASSPHRASE_FLOOR_LEN:
        return False, f"Export passphrase must be at least {WEAK_PASSPHRASE_FLOOR_LEN} characters."
    return True, None
