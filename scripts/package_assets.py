"""Generate all platform icon variants from the shared SVG."""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from scripts.package_config import ICO_SIZES, ICON_SIZE
from you_dl.resources import ICON_SOURCE


def generate_icons(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    image = QImage(ICON_SIZE, ICON_SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer = QSvgRenderer(str(ICON_SOURCE))
    if not renderer.isValid():
        raise ValueError("Invalid app icon SVG")
    renderer.render(painter)
    painter.end()
    png = directory / "icon.png"
    if not image.save(str(png)):
        raise OSError("Unable to save app icon")
    paths = {extension: directory / f"icon.{extension}" for extension in ("ico", "icns")}
    with Image.open(png) as source:
        source.save(paths["ico"], sizes=[(size, size) for size in ICO_SIZES])
        source.save(paths["icns"])
    return paths
