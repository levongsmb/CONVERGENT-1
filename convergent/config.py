"""Path and environment configuration.

All on-disk paths flow through this module. Windows is the only supported
platform (§3.1); on non-Windows dev machines we fall back to XDG-style paths
for test runs so CI and headless scaffolding work, but production deployment
is Windows-only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Final

APP_NAME: Final[str] = "Convergent"


def _appdata_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if not base:
            raise RuntimeError("APPDATA is not set; Convergent requires Windows 11.")
        return Path(base) / APP_NAME
    # Dev/test fallback only — not a supported deployment path.
    return Path(os.environ.get("CONVERGENT_HOME", Path.home() / ".convergent"))


def _localappdata_programs() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise RuntimeError("LOCALAPPDATA is not set; Convergent requires Windows 11.")
        return Path(base) / "Programs" / APP_NAME
    return Path(os.environ.get("CONVERGENT_INSTALL", Path.home() / ".convergent-install"))


def appdata_dir() -> Path:
    """`%APPDATA%\\Convergent` — per-user data root."""
    p = _appdata_root()
    p.mkdir(parents=True, exist_ok=True)
    return p


def engagements_dir() -> Path:
    p = appdata_dir() / "engagements"
    p.mkdir(parents=True, exist_ok=True)
    return p


def backups_dir() -> Path:
    p = appdata_dir() / "backups"
    p.mkdir(parents=True, exist_ok=True)
    return p


def authority_cache_dir() -> Path:
    p = appdata_dir() / "authority_cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def rules_cache_dir() -> Path:
    p = appdata_dir() / "rules_cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def install_dir() -> Path:
    """`%LOCALAPPDATA%\\Programs\\Convergent` — read-only program files."""
    return _localappdata_programs()


def vendor_dir() -> Path:
    """Bundled tesseract / ghostscript / tessdata."""
    return install_dir() / "vendor"


def tesseract_binary() -> Path:
    return vendor_dir() / "tesseract" / "tesseract.exe"


def tesseract_tessdata() -> Path:
    return vendor_dir() / "tesseract" / "tessdata"


def ghostscript_binary() -> Path:
    return vendor_dir() / "ghostscript" / "gswin64c.exe"


def strategy_library_dir() -> Path:
    """Shipped with the install (not user data)."""
    return install_dir() / "strategy_library"


def authority_layer_assets_dir() -> Path:
    return install_dir() / "authority_layer"


def rules_cache_seed_dir() -> Path:
    return install_dir() / "rules_cache_bootstrap"
