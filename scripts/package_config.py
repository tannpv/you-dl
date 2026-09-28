"""One source for package identity, paths and release policy."""

import importlib.metadata
import platform
from pathlib import Path

from you_dl.config import APP_BUNDLE_ID, APP_NAME

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
VERSION = importlib.metadata.version("you-dl")
INSTALLER_ID = APP_BUNDLE_ID
SIGN_IDENTITY_ENV = "MACOS_SIGN_IDENTITY"
NOTARY_PROFILE_ENV = "MACOS_NOTARY_PROFILE"
PACKAGE_TIMEOUT = 180
ICON_SIZE = 1024
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
ARCHITECTURES = {"AMD64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}
PLATFORMS = {"Darwin": "macOS", "Windows": "Windows"}


def artifact_stem() -> str:
    return (
        f"{APP_NAME}-{VERSION}-{PLATFORMS[platform.system()]}-{ARCHITECTURES[platform.machine()]}"
    )


def executable_path(root: Path) -> Path:
    if platform.system() == "Darwin":
        return root / f"{APP_NAME}.app" / "Contents" / "MacOS" / APP_NAME
    return root / f"{APP_NAME}.exe"
