from PySide6.QtCore import QSettings

from you_dl.app import Window
from you_dl.config import COPY, Event, State


def test_form_lifecycle(qtbot, tmp_path, monkeypatch):
    # TC: YDL-010, YDL-014, YDL-007
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = Window(settings)
    qtbot.addWidget(window)
    calls = []
    monkeypatch.setattr(window.controller, "start", calls.append)
    window.url.setText("https://youtu.be/BaW_jenozKc")
    window.folder.setText(str(tmp_path))
    window.start()
    assert len(calls) == 1 and not window.download.isEnabled()
    window.on_event({"kind": Event.PROGRESS, "percent": 42, "title": "Sample"})
    assert window.progress.value() == 42
    window.on_finished(State.CANCELLED, COPY["cancelled"])
    assert window.download.text() == COPY["retry"]
    window.start()
    assert calls[0] == calls[1]
    window.on_finished(State.COMPLETE, COPY["done"])
    restored = Window(settings)
    qtbot.addWidget(restored)
    assert restored.folder.text() == str(tmp_path)
    assert restored.profile.currentData() == calls[0].profile


def test_invalid_form_never_starts(qtbot, tmp_path, monkeypatch):
    # TC: YDL-002, YDL-010
    window = Window(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    calls = []
    monkeypatch.setattr(window.controller, "start", calls.append)
    window.url.setText("https://evil.test/")
    window.start()
    assert not calls
    assert window.status.text() == COPY["invalid"]
