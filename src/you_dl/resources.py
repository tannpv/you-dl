"""Package resources resolve identically in source and frozen applications."""

from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets"
ICON_SOURCE = ASSET_DIR / "icon.svg"
