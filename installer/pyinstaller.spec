# PyInstaller spec — Convergent
# Phase 0: one-folder build, Windows target. Runs end-to-end even though
# the app is a stub; produces `dist\Convergent\Convergent.exe` for Inno
# Setup to package.

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
ROOT = Path(".").resolve()

hidden_imports = [
    "sqlalchemy.dialects.sqlite",
    "anthropic",
    "anthropic._client",
    "plotly.graph_objects",
    "nicegui",
    "pytesseract",
    "pdfplumber",
    "camelot",
    "cryptography",
    "argon2",
    "keyring",
    "keyring.backends.Windows",
    "win32crypt",
    "win32api",
]

datas = [
    # Strategy Library — ships with install
    (str(ROOT / "strategy_library"), "strategy_library"),
    # Authority Layer assets (pitfalls, prompts, seed)
    (str(ROOT / "authority_layer"), "authority_layer"),
    (str(ROOT / "convergent" / "authority_layer" / "prompts"), "convergent/authority_layer/prompts"),
    # Rules cache bootstrap (seed only)
    (str(ROOT / "rules_cache_bootstrap"), "rules_cache_bootstrap"),
]

binaries = [
    # Phase 0: empty. Phase 10 build script populates installer/vendor/
    # and the Inno Setup [Files] section — these binaries are packaged by
    # Inno Setup rather than by PyInstaller to keep the PyInstaller bundle
    # fast to rebuild.
]

a = Analysis(
    ["../convergent/__main__.py"],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=["installer/runtime_hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "test",
        "pydoc_data",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Convergent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX reduces size but triggers more AV false positives
    console=False,  # native windowed app
    icon="installer/convergent.ico" if (ROOT / "installer" / "convergent.ico").exists() else None,
    version="installer/version_info.txt" if (ROOT / "installer" / "version_info.txt").exists() else None,
    target_arch="x86_64",
    codesign_identity=None,  # code signing done by build_installer.ps1 after ISCC
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Convergent",
)
