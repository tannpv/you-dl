"""Validation and downloader configuration, independent of the desktop UI."""

import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

from .config import (
    CANONICAL_ROOT,
    COPY,
    MAX_PLAYLIST_ITEMS,
    OUTPUT_TEMPLATE,
    PLAYLIST_TEMPLATE,
    PROFILES,
    RETRIES,
    SHORT_HOST,
    SOCKET_TIMEOUT,
    TOOL_NAMES,
    YOUTUBE_HOSTS,
    ExportKind,
)

VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
PLAYLIST_ID = re.compile(r"[A-Za-z0-9_-]{10,100}\Z")


def normalize_url(raw: str, playlist: bool) -> str:
    try:
        url = urlsplit(raw.strip())
        if (
            url.scheme not in {"https", "http"}
            or url.username
            or url.password
            or url.port
            or url.hostname not in YOUTUBE_HOSTS | {SHORT_HOST}
        ):
            raise ValueError(COPY["invalid"])
        query = parse_qs(url.query)
        video = query.get("v", [""])[0] if url.path == "/watch" else ""
        parts = url.path.strip("/").split("/")
        if url.hostname == SHORT_HOST and len(parts) == 1:
            video = parts[0]
        elif len(parts) == 2 and parts[0] in {"shorts", "live", "embed"}:
            video = parts[1]
        list_id = query.get("list", [""])[0]
        if playlist and PLAYLIST_ID.fullmatch(list_id):
            return CANONICAL_ROOT + "playlist?" + urlencode({"list": list_id})
        if VIDEO_ID.fullmatch(video):
            return CANONICAL_ROOT + "watch?" + urlencode({"v": video})
        if not playlist and url.path == "/playlist" and PLAYLIST_ID.fullmatch(list_id):
            raise ValueError(COPY["playlist_required"])
    except (ValueError, TypeError) as error:
        if str(error) in (COPY["invalid"], COPY["playlist_required"]):
            raise
        raise ValueError(COPY["invalid"]) from error
    raise ValueError(COPY["invalid"])


def resolve_tools() -> dict[str, str]:
    bundled = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "tools"
    suffix = ".exe" if sys.platform == "win32" else ""
    result = {}
    for name in TOOL_NAMES:
        candidate = bundled / (name + suffix)
        found = str(candidate) if candidate.is_file() else shutil.which(name)
        if found:
            result[name] = found
    missing = set(TOOL_NAMES) - result.keys()
    if missing:
        raise ValueError(COPY["missing"].format(tools=", ".join(sorted(missing))))
    return result


@dataclass(frozen=True)
class Request:
    url: str
    profile: str
    destination: str
    playlist: bool

    @classmethod
    def create(cls, url: str, profile: str, destination: str, playlist: bool) -> "Request":
        canonical = normalize_url(url, playlist)
        if profile not in PROFILES:
            raise ValueError("Unknown output format.")
        if not destination.strip():
            raise ValueError(COPY["folder_error"])
        path = Path(destination).expanduser().resolve()
        try:
            path.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=path):
                pass
        except OSError as error:
            raise ValueError(COPY["folder_error"]) from error
        return cls(canonical, profile, str(path), playlist)


def download_options(request: Request, tools: dict[str, str]) -> dict[str, Any]:
    profile = PROFILES[request.profile]
    options: dict[str, Any] = {
        "format": profile.selector,
        "paths": {"home": request.destination},
        "outtmpl": PLAYLIST_TEMPLATE if request.playlist else OUTPUT_TEMPLATE,
        "noplaylist": not request.playlist,
        "playlistend": MAX_PLAYLIST_ITEMS,
        "windowsfilenames": True,
        "continuedl": True,
        "overwrites": False,
        "ignoreerrors": True,
        "socket_timeout": SOCKET_TIMEOUT,
        "retries": RETRIES,
        "fragment_retries": RETRIES,
        "ffmpeg_location": str(Path(tools["ffmpeg"]).parent),
        "js_runtimes": {"node": {"path": tools["node"]}},
        "quiet": True,
        "noprogress": True,
        "postprocessors": [{"key": "FFmpegMetadata"}],
    }
    if profile.kind == ExportKind.AUDIO:
        processor = {"key": "FFmpegExtractAudio", "preferredcodec": profile.extension}
        if profile.bitrate is not None:
            processor["preferredquality"] = str(profile.bitrate)
        options["postprocessors"].insert(0, processor)
    else:
        options["merge_output_format"] = profile.extension
    return options
