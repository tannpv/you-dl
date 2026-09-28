import pytest

from you_dl.config import COPY, Event
from you_dl.core import Request
from you_dl.worker import run_download


class Pipe:
    def __init__(self):
        self.events = []
        self.closed = False

    def send(self, event):
        self.events.append(event)

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    "files, code, message",
    [
        ([], 0, "empty"),
        (["existing.mp3"], 0, "done"),
        (["saved.mp3"], 1, "partial"),
    ],
)
def test_worker_results(monkeypatch, tmp_path, files, code, message):
    # TC: YDL-005, YDL-017. Exit code alone cannot prove a playlist produced files.
    class Downloader:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def download(self, urls):
            if code:
                self.options["logger"].error("Unavailable playlist entry")
            for file in files:
                for hook in self.options["post_hooks"]:
                    hook(file)
            return code

    monkeypatch.setattr("yt_dlp.YoutubeDL", Downloader)
    pipe = Pipe()
    request = Request("fixture", "mp3-192", str(tmp_path), True)
    run_download(request, {"ffmpeg": "/tools/ffmpeg", "node": "/tools/node"}, pipe)
    result = pipe.events[-1]
    assert result["kind"] == Event.RESULT
    assert result["success"] is (message == "done")
    assert result["completed"] == len(files)
    assert result["text"] == COPY[message]
    assert pipe.closed
