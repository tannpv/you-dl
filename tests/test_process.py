import multiprocessing as mp
import subprocess
import sys
import time

import psutil

from you_dl.config import Event, State
from you_dl.controller import Controller, terminate_tree
from you_dl.core import Request


def child_with_descendant(pipe):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pipe.send(child.pid)
    time.sleep(60)


def test_cancel_kills_descendants():
    # TC: YDL-006
    ctx = mp.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    process = ctx.Process(target=child_with_descendant, args=(sender,))
    process.start()
    sender.close()
    try:
        assert receiver.poll(10)
        child_pid = receiver.recv()
        terminate_tree(process.pid)
        process.join(5)
        assert not process.is_alive()
        try:
            child = psutil.Process(child_pid)
            child.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
    finally:
        if process.is_alive():
            terminate_tree(process.pid)
            process.join(5)
        receiver.close()
        process.close()


def simulated_download(request, tools, pipe):
    pipe.send({"kind": Event.PROGRESS, "percent": 50, "title": "Fixture"})
    pipe.send({"kind": Event.RESULT, "success": True, "text": "Saved"})
    pipe.close()


def stalled_download(request, tools, pipe):
    time.sleep(60)


def test_controller_reaps_and_retries(qtbot, monkeypatch, tmp_path):
    # TC: YDL-007, YDL-010
    monkeypatch.setattr("you_dl.controller.resolve_tools", lambda: {})
    monkeypatch.setattr("you_dl.controller.run_download", simulated_download)
    controller = Controller()
    request = Request("fixture", "mp3-192", str(tmp_path), False)
    for _ in range(2):
        with qtbot.waitSignal(controller.finished, timeout=10000) as signal:
            controller.start(request)
        assert signal.args == [State.COMPLETE, "Saved"]
        assert not controller.busy


def test_controller_cancel(qtbot, monkeypatch, tmp_path):
    # TC: YDL-006
    monkeypatch.setattr("you_dl.controller.resolve_tools", lambda: {})
    monkeypatch.setattr("you_dl.controller.run_download", stalled_download)
    controller = Controller()
    controller.start(Request("fixture", "mp3-192", str(tmp_path), False))
    with qtbot.waitSignal(controller.finished, timeout=5000) as signal:
        controller.cancel()
    assert signal.args[0] == State.CANCELLED
    assert not controller.busy
