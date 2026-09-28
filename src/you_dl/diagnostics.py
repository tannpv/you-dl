"""Offline frozen-package acceptance check; explicit CLI use only."""

import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
from multiprocessing.connection import Connection
from pathlib import Path

from .core import resolve_tools

SELF_TEST_FLAG = "--self-test"
SELF_TEST_TIMEOUT = 120


def probe_tools(pipe: Connection) -> None:
    """Run in a spawned child to also verify frozen multiprocessing dispatch."""
    try:
        tools = resolve_tools()
        if getattr(sys, "frozen", False):
            bundle_root = Path(getattr(sys, "_MEIPASS", "")).resolve()
            for path in tools.values():
                if not Path(path).resolve().is_relative_to(bundle_root):
                    raise RuntimeError("Tool resolved outside the app bundle")

        def run(args: list[str]) -> str:
            return subprocess.check_output(
                args, stderr=subprocess.STDOUT, timeout=SELF_TEST_TIMEOUT
            ).decode()

        versions = {
            name: run([path, "-version" if name.startswith("ff") else "--version"]).splitlines()[0]
            for name, path in tools.items()
        }
        assert run([tools["node"], "-e", "process.stdout.write(String(6 * 7))"]) == "42"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fixture.mp3"
            run(
                [
                    tools["ffmpeg"],
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=duration=1",
                    "-codec:a",
                    "libmp3lame",
                    str(output),
                ]
            )
            media = json.loads(
                run([tools["ffprobe"], "-v", "quiet", "-show_streams", "-of", "json", str(output)])
            )
            assert media["streams"][0]["codec_name"] == "mp3"
        pipe.send({"ok": True, "tools": versions, "conversion": "mp3", "spawn": "passed"})
    except Exception as error:
        pipe.send({"ok": False, "error": str(error)})
    finally:
        pipe.close()


def self_test(report_path: Path) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from .app import Window

    app = QApplication.instance() or QApplication([])
    window = Window()
    app.processEvents()
    assert not window.windowIcon().isNull(), "App icon is missing"
    window.close()
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=probe_tools, args=(sender,))
    process.start()
    sender.close()
    try:
        result = (
            receiver.recv()
            if receiver.poll(SELF_TEST_TIMEOUT)
            else {"ok": False, "error": "Self-test timed out"}
        )
    finally:
        process.join(timeout=5)
        if process.is_alive():
            from .controller import terminate_tree

            assert process.pid is not None
            terminate_tree(process.pid)
            process.join(timeout=5)
        process.close()
        receiver.close()
    result["qt"] = "passed"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1
