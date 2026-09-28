"""Shared product settings and format registry."""

from dataclasses import dataclass
from enum import StrEnum

APP_NAME = "You-DL"
APP_ID = "you-dl"
APP_BUNDLE_ID = "app.youdl.desktop"
DOWNLOAD_FOLDER = APP_NAME
POLL_MS = 100
MAX_EVENTS_PER_TICK = 100
MAX_LOG_LINES = 300
SOCKET_TIMEOUT = 20
RETRIES = 3
MAX_PLAYLIST_ITEMS = 500
OUTPUT_TEMPLATE = "%(title).150B [%(id)s].%(ext)s"
PLAYLIST_TEMPLATE = "%(playlist_title).100B/%(playlist_index)03d - " + OUTPUT_TEMPLATE
YOUTUBE_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"})
SHORT_HOST = "youtu.be"
CANONICAL_ROOT = "https://www.youtube.com/"
TOOL_NAMES = ("ffmpeg", "ffprobe", "node")


class State(StrEnum):
    COMPLETE = "Complete"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class Event(StrEnum):
    PROGRESS = "progress"
    STATUS = "status"
    RESULT = "result"


class ExportKind(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"


class Preference(StrEnum):
    PROFILE = "profile"
    DESTINATION = "destination"


@dataclass(frozen=True)
class Profile:
    label: str
    extension: str
    selector: str
    kind: ExportKind
    bitrate: int | None = None


def compatible_video(height: int) -> str:
    # yt-dlp format filter syntax: https://github.com/yt-dlp/yt-dlp#format-selection
    video = f"[height<={height}][vcodec^=avc1]"
    return f"bv{video}+ba[acodec^=mp4a]/b{video}[acodec^=mp4a]"


PROFILES = {
    f"mp3-{bitrate}": Profile(
        f"MP3 · Audio · {bitrate} kbps", "mp3", "bestaudio/best", ExportKind.AUDIO, bitrate
    )
    for bitrate in (192, 320)
} | {
    f"mp4-{height}": Profile(
        f"MP4 · Video · Up to {height}p", "mp4", compatible_video(height), ExportKind.VIDEO
    )
    for height in (1080, 720)
}
DEFAULT_PROFILE = next(iter(PROFILES))

COPY = {
    "headline": "Keep something good.",
    "subtitle": "Your favorite videos and playlists, ready when you are offline.",
    "link_label": "YouTube link",
    "placeholder": "Paste a video or playlist link…",
    "playlist": f"Download playlist (up to {MAX_PLAYLIST_ITEMS} entries)",
    "format": "Save as",
    "folder": "Save to",
    "browse": "Choose folder…",
    "start": "Download",
    "cancel": "Cancel",
    "retry": "Retry download",
    "open": "Open folder",
    "ready": "Paste a link to get started.",
    "rights": "Download only content you own or have permission to save.",
    "quality": "Audio quality depends on the original. MP4 uses H.264 video and AAC audio.",
    "missing": "Missing tools: {tools}. Reinstall the app or see README setup instructions.",
    "invalid": "Enter a valid YouTube video or playlist link.",
    "playlist_required": "This is a playlist link. Enable the playlist option.",
    "busy_close": "Cancel the active download before closing this window.",
    "cancelled": "Cancelled. Retry to resume supported partial downloads.",
    "working": "Connecting to YouTube…",
    "processing": "Converting / finalizing…",
    "done": "Finished. Files are ready in your save folder.",
    "empty": "No downloadable items found. Check the link or choose another playlist.",
    "partial": "Some items failed. See details below; retry to resume unfinished downloads.",
    "crashed": "Download process stopped unexpectedly. Retry the download.",
    "folder_error": "Cannot write to this folder. Choose another destination.",
}
