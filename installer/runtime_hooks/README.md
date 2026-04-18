# PyInstaller runtime hooks

Hooks that run at app startup before `convergent.__main__` executes.
Placeholder for Phase 2+ hooks:

- Setting `pytesseract.pytesseract.tesseract_cmd` to the bundled binary path
- Setting the Ghostscript executable path for camelot
- Configuring `keyring` to prefer the Windows Credential Manager backend
- Establishing the Decimal context (`convergent.util.decimal_tax.setup_decimal_context`)

Phase 0 is empty.
