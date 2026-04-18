; Convergent Inno Setup installer — Phase 0 skeleton
; Target: Windows 11 22H2+, x64, per-user install (no admin required)

#define AppName "Convergent"
#define AppVersion "0.1.0-phase0"
#define AppPublisher "Convergent"
#define AppExeName "Convergent.exe"

[Setup]
AppId={{C0A36E24-8F72-4F4B-9E62-BE9FCED90C01}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=Convergent-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.22000  ; Windows 11 22H2 minimum
UninstallDisplayIcon={app}\{#AppExeName}
; Code signing: set by build_installer.ps1 if a cert is configured.
; SignTool=sign /d $q{#AppName}$q /a /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; PyInstaller one-folder output
Source: "..\dist\Convergent\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Vendor binaries (Phase 0: stubbed; populated by scripts/fetch_vendor_binaries.ps1 in Phase 10)
Source: "vendor\tesseract\*"; DestDir: "{app}\vendor\tesseract"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist
Source: "vendor\ghostscript\*"; DestDir: "{app}\vendor\ghostscript"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Ensure Edge WebView2 runtime is installed (required by NiceGUI native mode per §3.1)
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; \
    Parameters: "/silent /install"; \
    StatusMsg: "Installing Microsoft Edge WebView2 runtime..."; \
    Check: NeedsWebView2Runtime; \
    Flags: waituntilterminated skipifdoesntexist

Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
// Minimal WebView2 detection. Phase 10 adds registry-based robust detection
// and embeds MicrosoftEdgeWebview2Setup.exe in [Files] as a temp file.
function NeedsWebView2Runtime(): Boolean;
var
    RegValue: String;
begin
    // Runtime registry key (per-machine). Production check covers per-user too.
    if RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', RegValue) then
        Result := False
    else if RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', RegValue) then
        Result := False
    else
        Result := True;
end;

[UninstallDelete]
; Preserve %APPDATA%\Convergent by default. Uninstaller prompts the user
; separately if they want to remove engagement data. Logic added in
; Phase 10.
Type: filesandordirs; Name: "{userappdata}\Convergent\logs"
