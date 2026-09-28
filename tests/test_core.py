from pathlib import Path

import pytest

from you_dl.config import PROFILES
from you_dl.core import Request, download_options, normalize_url, resolve_tools


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com/watch?v=BaW_jenozKc&t=2",
        "https://youtu.be/BaW_jenozKc",
        "https://www.youtube.com/shorts/BaW_jenozKc",
        "https://m.youtube.com/live/BaW_jenozKc",
    ],
)
def test_video_links(url):
    # TC: YDL-001
    assert normalize_url(url, False) == "https://www.youtube.com/watch?v=BaW_jenozKc"


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com.evil.test/watch?v=BaW_jenozKc",
        "file:///tmp/file",
        "https://user:pass@youtube.com/watch?v=BaW_jenozKc",
        "https://youtube.com:443/watch?v=BaW_jenozKc",
        "--exec rm -rf /",
        "https://youtube.com/watch?v=$(touch-file)",
        "https://youtube.com/watch?v=bad",
        "https://youtube.com/@channel",
        "https://[bad",
        "",
    ],
)
def test_invalid_links(url):
    # TC: YDL-002
    with pytest.raises(ValueError):
        normalize_url(url, False)


def test_playlist_is_explicit():
    # TC: YDL-001, YDL-005
    playlist = "https://www.youtube.com/playlist?list=PLabcdefghijk"
    assert normalize_url(playlist, True) == playlist
    with pytest.raises(ValueError, match="Enable"):
        normalize_url(playlist, False)
    assert "playlist?" in normalize_url(
        "https://youtube.com/watch?v=BaW_jenozKc&list=PLabcdefghijk", True
    )
    assert "watch?" in normalize_url(
        "https://youtube.com/watch?v=BaW_jenozKc&list=PLabcdefghijk", False
    )


@pytest.mark.parametrize("key", PROFILES)
def test_profiles(tmp_path, key):
    # TC: YDL-003, YDL-004, YDL-007
    request = Request.create("https://youtu.be/BaW_jenozKc", key, str(tmp_path), False)
    options = download_options(request, {"ffmpeg": "/tools/ffmpeg", "node": "/tools/node"})
    profile = PROFILES[key]
    if profile.bitrate:
        assert options["postprocessors"][0]["preferredquality"] == str(profile.bitrate)
    else:
        assert "avc1" in options["format"] and "mp4a" in options["format"]
        assert options["merge_output_format"] == "mp4"
    assert options["continuedl"] and not options["overwrites"]


def test_unwritable_destination(tmp_path):
    # TC: YDL-008
    file = tmp_path / "file"
    file.write_text("occupied")
    with pytest.raises(ValueError, match="Cannot write"):
        Request.create("https://youtu.be/BaW_jenozKc", "mp3-192", str(file), False)
    with pytest.raises(ValueError, match="Cannot write"):
        Request.create("https://youtu.be/BaW_jenozKc", "mp3-192", "", False)


def test_missing_tools(monkeypatch):
    # TC: YDL-008
    monkeypatch.setattr("you_dl.core.shutil.which", lambda _: None)
    monkeypatch.setattr(Path, "is_file", lambda _: False)
    with pytest.raises(ValueError, match="Missing tools"):
        resolve_tools()
