#Requires -Version 7.0
<#
.SYNOPSIS
    Convergent Windows installer build driver.

.DESCRIPTION
    Phase 0 skeleton. Runs the full build end-to-end on a developer
    Windows 11 machine per installer/README.md. This script is the single
    entry point for producing dist\Convergent-Setup-<version>.exe.

    Phases 1+ will extend:
    - Golden-scenario regression before packaging
    - Code signing with signtool when a certificate is configured
    - Installer smoke test on a clean Windows 11 VM via Hyper-V checkpoint

.NOTES
    Must be run on Windows 11 with Python 3.12 from python.org, Inno
    Setup 6 on PATH as ISCC.exe, and PowerShell 7+.
#>
[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipSign,
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues["*:Encoding"] = "utf8"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Convergent installer build ==="
Write-Host "Root: $Root"
Write-Host "Configuration: $Configuration"

# ---- 1. Verify prerequisites -----------------------------------------------

$python = (Get-Command py.exe -ErrorAction SilentlyContinue).Source
if (-not $python) { throw "py.exe not found; install Python 3.12 from python.org" }

$pyVersion = & py -3.12 --version
Write-Host "Python: $pyVersion"

$iscc = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
if (-not $iscc) { throw "ISCC.exe not found; install Inno Setup 6 and add to PATH" }
Write-Host "Inno Setup: $iscc"

# ---- 2. Clean and prepare venv ---------------------------------------------

$venv = Join-Path $Root ".venv"
if (Test-Path $venv) { Remove-Item -Recurse -Force $venv }
& py -3.12 -m venv $venv
$pip = Join-Path $venv "Scripts\pip.exe"
$py  = Join-Path $venv "Scripts\python.exe"

& $pip install --upgrade pip
& $pip install -e ".[dev]"

# ---- 3. Run tests (unless --SkipTests) -------------------------------------

if (-not $SkipTests) {
    Write-Host "--- Running pytest ---"
    & $py -m pytest -m "not ui and not windows" --tb=short
    if ($LASTEXITCODE -ne 0) { throw "Tests failed." }
}

# ---- 4. Run PyInstaller ----------------------------------------------------

if (Test-Path (Join-Path $Root "dist")) {
    Remove-Item -Recurse -Force (Join-Path $Root "dist")
}
if (Test-Path (Join-Path $Root "build")) {
    Remove-Item -Recurse -Force (Join-Path $Root "build")
}

Write-Host "--- Running PyInstaller ---"
& $py -m PyInstaller installer\pyinstaller.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

# ---- 5. Run Inno Setup -----------------------------------------------------

Write-Host "--- Running Inno Setup ---"
& $iscc installer\convergent.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed." }

# ---- 6. Optional code signing ----------------------------------------------

if (-not $SkipSign) {
    $cert = $env:CONVERGENT_SIGNING_CERT
    if ($cert -and (Test-Path $cert)) {
        $signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
        if (-not $signtool) { Write-Warning "signtool.exe not found; skipping signing." }
        else {
            $installerExe = Get-ChildItem "$Root\dist\Convergent-Setup-*.exe" | Select-Object -First 1
            Write-Host "--- Signing $installerExe ---"
            & $signtool sign /f $cert /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $installerExe
            if ($LASTEXITCODE -ne 0) { throw "signtool failed." }
        }
    } else {
        Write-Host "No signing certificate configured; shipping unsigned installer (per Q0.4 default)."
    }
}

Write-Host "=== Build complete ==="
Get-ChildItem "$Root\dist\Convergent-Setup-*.exe" | ForEach-Object {
    Write-Host "Output: $($_.FullName) ($([math]::Round($_.Length / 1MB, 1)) MiB)"
}
