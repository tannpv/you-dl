"""Windows installer metadata generated from shared application identity."""

from pathlib import Path

from scripts.package_config import DIST, INSTALLER_ID, VERSION, artifact_stem
from you_dl.config import APP_NAME


def installer_script(icon: Path) -> str:
    # Inno Setup directives: https://jrsoftware.org/ishelp/topic_setupsection.htm
    launch_flags = "nowait postinstall skipifsilent"
    return f'''[Setup]
AppId={INSTALLER_ID}
AppName={APP_NAME}
AppVersion={VERSION}
AppVerName={APP_NAME} {VERSION}
VersionInfoVersion={VERSION}.0
DefaultDirName={{localappdata}}\\Programs\\{APP_NAME}
DefaultGroupName={APP_NAME}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={DIST}
OutputBaseFilename={artifact_stem()}-Setup
SetupIconFile={icon}
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "{DIST / APP_NAME}\\*"; DestDir: "{{app}}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{{autoprograms}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon
[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "Launch {APP_NAME}"; Flags: {launch_flags}
'''
