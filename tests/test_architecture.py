"""Rule #1 guards: boundaries and configuration-driven extension."""

import ast
from pathlib import Path

from you_dl.config import PROFILES, ExportKind, Profile
from you_dl.core import Request, download_options


def test_external_effects_stay_at_boundaries():
    source = Path(__file__).resolve().parents[1] / "src" / "you_dl"
    owners = {"yt_dlp": "worker.py", "psutil": "controller.py", "subprocess": "diagnostics.py"}
    forbidden = {"requests", "httpx", "socket"}
    for path in source.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            imports = []
            if isinstance(node, ast.Import):
                imports = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports = [node.module.split(".")[0]]
            for module in imports:
                assert module not in forbidden, f"Unowned external-effect boundary: {path}:{module}"
                if module in owners:
                    assert path.name == owners[module]


def test_new_audio_format_needs_only_profile_data(monkeypatch, tmp_path):
    monkeypatch.setitem(PROFILES, "flac", Profile("FLAC", "flac", "bestaudio", ExportKind.AUDIO))
    request = Request.create("https://youtu.be/BaW_jenozKc", "flac", str(tmp_path), False)
    options = download_options(request, {"ffmpeg": "/tools/ffmpeg", "node": "/tools/node"})
    assert options["postprocessors"][0] == {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "flac",
    }
    assert "merge_output_format" not in options
