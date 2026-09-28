"""Qt process lifecycle boundary, including descendants such as FFmpeg."""

import multiprocessing as mp
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

from .config import COPY, MAX_EVENTS_PER_TICK, POLL_MS, Event, State
from .core import Request, resolve_tools
from .worker import run_download


def terminate_tree(pid: int) -> None:
    try:
        parent = psutil.Process(pid)
        # Freeze the worker before enumerating descendants so it cannot spawn more.
        parent.suspend()
        children = parent.children(recursive=True)
        for process in reversed(children):
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        parent.kill()
    except psutil.NoSuchProcess:
        pass


class Controller(QObject):
    update = Signal(dict)
    finished = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.process: BaseProcess | None = None
        self.pipe: Connection | None = None
        self.result: dict[str, Any] | None = None
        self.cancelled = False
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)

    @property
    def busy(self) -> bool:
        return self.process is not None

    def start(self, request: Request) -> None:
        if self.busy:
            raise ValueError("A download is already running.")
        tools = resolve_tools()
        context = mp.get_context("spawn")
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=run_download, args=(request, tools, sender))
        try:
            process.start()
        except Exception:
            receiver.close()
            sender.close()
            raise
        sender.close()
        self.pipe, self.process, self.result = receiver, process, None
        self.cancelled = False
        self.timer.start()

    def poll(self) -> None:
        if self.pipe is None or self.process is None:
            return
        drained = False
        for _ in range(MAX_EVENTS_PER_TICK):
            if not self.pipe.poll():
                drained = True
                break
            try:
                event = self.pipe.recv()
            except EOFError:
                drained = True
                break
            if event["kind"] == Event.RESULT:
                self.result = event
            self.update.emit(event)
        if not self.process.is_alive() and drained:
            if self.cancelled:
                self._finish(State.CANCELLED, COPY["cancelled"])
                return
            result = self.result or {"success": False, "text": COPY["crashed"]}
            self._finish(State.COMPLETE if result["success"] else State.FAILED, result["text"])

    def cancel(self) -> None:
        if self.process is not None and self.process.pid is not None:
            self.cancelled = True
            terminate_tree(self.process.pid)

    def _finish(self, state: State, message: str) -> None:
        self.timer.stop()
        if self.process is not None:
            self.process.join(timeout=0)
            self.process.close()
        if self.pipe is not None:
            self.pipe.close()
        self.process, self.pipe = None, None
        self.finished.emit(state, message)
