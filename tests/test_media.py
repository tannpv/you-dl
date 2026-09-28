import functools
import json
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from yt_dlp import YoutubeDL

from you_dl.core import Request, download_options, resolve_tools


def test_real_media_outputs(tmp_path):
    # TC: YDL-009. Synthetic media only; no third-party content.
    tools = resolve_tools()
    source = tmp_path / "fixture.mp4"
    subprocess.run(
        [
            tools["ffmpeg"],
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x90:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            str(source),
        ],
        check=True,
    )
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for profile, expected in (("mp3-192", {"mp3"}), ("mp4-1080", {"h264", "aac"})):
            output = tmp_path / profile
            request = Request(
                f"http://127.0.0.1:{server.server_port}/fixture.mp4", profile, str(output), False
            )
            options = download_options(request, tools)
            # Generic HTTP fixture has no codec metadata; use actual file format.
            options["format"] = "best"
            with YoutubeDL(options) as downloader:
                assert downloader.download([request.url]) == 0
            file = next(output.glob("*.mp3" if profile.startswith("mp3") else "*.mp4"))
            probe = subprocess.run(
                [tools["ffprobe"], "-v", "quiet", "-show_streams", "-of", "json", str(file)],
                check=True,
                capture_output=True,
            )
            codecs = {s["codec_name"] for s in json.loads(probe.stdout)["streams"]}
            assert codecs == expected
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
