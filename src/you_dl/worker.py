"""Child process boundary. Only structured events cross into the UI."""

from multiprocessing.connection import Connection
from typing import Any

from .config import COPY, Event
from .core import Request, download_options


def run_download(request: Request, tools: dict[str, str], pipe: Connection) -> None:
    from yt_dlp import YoutubeDL

    completed: list[str] = []

    def emit(kind: Event, **data: Any) -> None:
        pipe.send({"kind": kind, **data})

    class Logger:
        def debug(self, message: str) -> None:
            pass

        def warning(self, message: str) -> None:
            emit(Event.STATUS, text=message)

        def error(self, message: str) -> None:
            emit(Event.STATUS, text=message)

    def progress(data: dict[str, Any]) -> None:
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        percent = min(100, int(data.get("downloaded_bytes", 0) * 100 / total)) if total else -1
        info = data.get("info_dict", {})
        emit(Event.PROGRESS, percent=percent, title=info.get("title", ""))

    try:
        options = download_options(request, tools)
        options.update(
            {
                "logger": Logger(),
                "progress_hooks": [progress],
                "post_hooks": [completed.append],
                "postprocessor_hooks": [lambda _: emit(Event.STATUS, text=COPY["processing"])],
            }
        )
        with YoutubeDL(options) as downloader:
            result = downloader.download([request.url])
        success = result == 0 and bool(completed)
        message = COPY["done"] if success else COPY["partial"] if result else COPY["empty"]
        emit(Event.RESULT, success=success, text=message, completed=len(completed))
    except Exception as error:
        emit(Event.RESULT, success=False, text=str(error))
    finally:
        pipe.close()
