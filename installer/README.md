# Installer Build

Phase 0 skeleton for the Windows installer. The Phase 0 acceptance test
requires PyInstaller + Inno Setup to compile end-to-end against the
current Python package, producing a runnable `Convergent-Setup-{version}.exe`
even while the app itself is a stub.

## Build prerequisites (developer machine only)

- Windows 11 22H2 or later
- Python 3.12 from python.org
- Visual Studio Build Tools 2022 — Desktop development with C++
- Inno Setup 6 — https://jrsoftware.org/isdl.php
- PowerShell 7+

## Vendor directory

The installer bundles third-party binaries under `installer/vendor/`:

- `tesseract/tesseract.exe` — Tesseract 5.x Windows 64-bit
- `tesseract/tessdata/` — tax-form fine-tuned traineddata
- `ghostscript/gswin64c.exe` — Ghostscript 10.x Windows 64-bit

These files are **not committed to the repo** (binary blobs, licensed). A
developer running the build locally must download them first using
`scripts/fetch_vendor_binaries.ps1` (lands in Phase 10). Phase 0 ships
the directory structure and the Inno Setup `[Files]` section stubbed to
reference them — a clean Phase 0 build with empty vendor dirs succeeds
with warnings.

## Build invocation (one command)

```powershell
pwsh scripts/build_installer.ps1
```

The script:

1. Verifies Python version and PowerShell environment
2. Creates a clean .venv and installs the repo `[dev]` extras
3. Runs `pytest` (unit + integration, excluding UI smoke + Windows-only)
4. Runs `pyinstaller installer/pyinstaller.spec`
5. Invokes `ISCC.exe installer/convergent.iss`
6. Outputs `dist/Convergent-Setup-{version}.exe`

If a code-signing certificate is configured, the script signs the output
with `signtool`. Open Question Q0.4: Phase 0 default is unsigned, with
the SmartScreen warning documented in README.

## File layout at install time

Following §3.3:

- Program files: `%LOCALAPPDATA%\Programs\Convergent\`
  - `Convergent.exe` (PyInstaller onefolder launcher)
  - `vendor\` (tesseract, ghostscript)
  - `strategy_library\` (ships with the install)
  - `authority_layer\` (prompts + seed authority cache)
  - `rules_cache_bootstrap\` (seed rule parameters — user reviews in-place during Phase 0 acceptance for development builds; production installs treat this as read-only seed)
- User data: `%APPDATA%\Convergent\`
  - `engagements\`
  - `backups\`
  - `authority_cache\`
  - `rules_cache\`
  - `convergent.log`
- Shortcuts: Start menu and optional desktop
- Uninstaller: registered; retains user data by default (prompt offers removal)
