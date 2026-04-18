# Vendor binaries

Third-party binaries bundled with the installer. **These files are not
committed to the repo.** A developer machine running a full build must
populate this directory first via `scripts/fetch_vendor_binaries.ps1`
(Phase 10 deliverable).

Expected layout at build time:

```
installer/vendor/
  tesseract/
    tesseract.exe        Tesseract 5.x Windows 64-bit
    tessdata/            Language + tax-form traineddata files
  ghostscript/
    gswin64c.exe         Ghostscript 10.x Windows 64-bit
  webview2/              (optional bootstrapped WebView2 installer)
    MicrosoftEdgeWebview2Setup.exe
```

Phase 0 installer builds run successfully with this directory empty — the
Inno Setup `[Files]` section uses `skipifsourcedoesntexist` so missing
vendor files produce warnings, not errors. End-user installers built
without vendor binaries will lack OCR and PDF table extraction until the
next build cycle populates this directory. That gap is acceptable for
Phase 0 (ingestion work begins in Phase 3).
