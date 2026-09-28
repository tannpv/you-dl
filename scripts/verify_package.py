"""Exercise actual installers, then run installed apps without developer PATH."""

import hashlib
import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

from scripts.package_config import (
    DIST,
    PACKAGE_TIMEOUT,
    artifact_stem,
    executable_path,
)
from you_dl.config import APP_NAME
from you_dl.diagnostics import SELF_TEST_FLAG


def run_app(executable: Path, report: Path) -> None:
    environment = os.environ.copy()
    environment["PATH"] = (
        str(Path(os.environ["SystemRoot"]) / "System32")
        if platform.system() == "Windows"
        else "/usr/bin:/bin"
    )
    environment["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(
        [str(executable), SELF_TEST_FLAG, str(report)],
        env=environment,
        check=True,
        timeout=PACKAGE_TIMEOUT,
    )
    result = json.loads(report.read_text())
    if not result.get("ok"):
        raise RuntimeError(f"Frozen self-test failed: {result}")


def verify() -> None:
    system = platform.system()
    suffix = ".dmg" if system == "Darwin" else "-Setup.exe"
    artifact = DIST / f"{artifact_stem()}{suffix}"
    metadata = json.loads(artifact.with_suffix(artifact.suffix + ".json").read_text())
    with artifact.open("rb") as file:
        assert hashlib.file_digest(file, "sha256").hexdigest() == metadata["sha256"]
    report = DIST / f"{artifact_stem()}-self-test.json"
    with tempfile.TemporaryDirectory(prefix="you-dl-install-") as directory:
        root = Path(directory)
        install = root / "installed"
        if system == "Darwin":
            subprocess.run(["hdiutil", "verify", str(artifact)], check=True)
            mount = root / "image"
            mount.mkdir()
            subprocess.run(
                [
                    "hdiutil",
                    "attach",
                    str(artifact),
                    "-readonly",
                    "-nobrowse",
                    "-mountpoint",
                    str(mount),
                ],
                check=True,
            )
            try:
                install.mkdir()
                subprocess.run(
                    ["ditto", str(mount / f"{APP_NAME}.app"), str(install / f"{APP_NAME}.app")],
                    check=True,
                )
                run_app(executable_path(install), report)
            finally:
                subprocess.run(["hdiutil", "detach", str(mount)], check=True)
        elif system == "Windows":
            arguments = [
                str(artifact),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                f"/DIR={install}",
            ]
            for _ in range(2):
                subprocess.run(arguments, check=True, timeout=PACKAGE_TIMEOUT)
                run_app(executable_path(install), report)
            uninstaller = install / "unins000.exe"
            assert uninstaller.is_file(), "Uninstaller is missing"
            shortcut = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"
            assert (shortcut / f"{APP_NAME}.lnk").is_file(), "Start Menu shortcut is missing"
            subprocess.run(
                [str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                check=True,
                timeout=PACKAGE_TIMEOUT,
            )
            deadline = time.monotonic() + 15
            while executable_path(install).exists() and time.monotonic() < deadline:
                time.sleep(0.1)
            assert not executable_path(install).exists(), "Uninstall left the executable behind"
        else:
            raise ValueError(f"Unsupported platform: {system}")
    print(f"Installer verification passed: {artifact.name}")


if __name__ == "__main__":
    verify()
