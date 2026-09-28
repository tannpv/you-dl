from pathlib import Path

from PIL import Image

from scripts.installer import installer_script
from scripts.package_assets import generate_icons
from scripts.package_config import INSTALLER_ID, VERSION
from you_dl.config import APP_NAME


def test_single_icon_source(tmp_path):
    # TC: YDL-018
    icons = generate_icons(tmp_path)
    for path in icons.values():
        with Image.open(path) as image:
            assert image.width >= 256
            assert image.height == image.width


def test_installer_metadata(monkeypatch):
    # TC: YDL-019, YDL-021, YDL-023
    monkeypatch.setattr("scripts.package_config.platform.system", lambda: "Windows")
    monkeypatch.setattr("scripts.package_config.platform.machine", lambda: "AMD64")
    script = installer_script(Path("app.ico"))
    for directive in (
        f"AppId={INSTALLER_ID}",
        f"AppVersion={VERSION}",
        "PrivilegesRequired=lowest",
        "ArchitecturesAllowed=x64compatible",
        "CloseApplications=yes",
        f"UninstallDisplayIcon={{app}}\\{APP_NAME}.exe",
    ):
        assert directive in script
    assert "-Windows-x64-Setup" in script
