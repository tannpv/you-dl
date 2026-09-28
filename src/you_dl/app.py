"""Native desktop interface."""

import multiprocessing
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import (
    APP_ID,
    APP_NAME,
    COPY,
    DEFAULT_PROFILE,
    DOWNLOAD_FOLDER,
    MAX_LOG_LINES,
    MAX_PLAYLIST_ITEMS,
    PROFILES,
    Event,
    Preference,
    State,
)
from .controller import Controller
from .core import Request
from .resources import ICON_SOURCE

STYLE = """
QWidget { background: #f6f5f1; color: #20332e; font-size: 14px; }
QLabel#brand { color: #397263; font-size: 15px; font-weight: 700; }
QLabel#headline { font-size: 32px; font-weight: 700; }
QLabel#muted { color: #68766f; }
QLineEdit, QComboBox, QPlainTextEdit {
  background: white; border: 1px solid #cfd7d1; border-radius: 8px; padding: 11px;
}
QPushButton { padding: 11px 20px; border: 1px solid #cfd7d1; border-radius: 8px; }
QPushButton:hover { background: #e3ebe5; }
QPushButton#primary { background: #25634e; color: white; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #194934; }
QPushButton:disabled { background: #e0e4df; color: #8b958e; }
QProgressBar { border: none; border-radius: 5px; background: #dfe5df; height: 10px; }
QProgressBar::chunk { background: #388a69; border-radius: 5px; }
QCheckBox { spacing: 8px; }
"""


class Window(QMainWindow):
    def __init__(self, settings: QSettings | None = None) -> None:
        super().__init__()
        self.settings = settings if settings is not None else QSettings(APP_ID, APP_NAME)
        self.controller = Controller(self)
        self.controller.update.connect(self.on_event)
        self.controller.finished.connect(self.on_finished)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(ICON_SOURCE)))
        self.resize(780, 770)
        self.setMinimumSize(640, 700)
        self.setStyleSheet(STYLE)
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(14)
        self.add_label(layout, "↓  " + APP_NAME.upper(), "brand")
        self.add_label(layout, COPY["headline"], "headline")
        self.add_label(layout, COPY["subtitle"], "muted")
        layout.addSpacing(10)
        self.add_label(layout, COPY["link_label"])
        self.url = QLineEdit()
        self.url.setAccessibleName(COPY["link_label"])
        self.url.setPlaceholderText(COPY["placeholder"])
        self.url.returnPressed.connect(self.start)
        layout.addWidget(self.url)
        self.playlist = QCheckBox(COPY["playlist"])
        self.playlist.setToolTip(f"Up to {MAX_PLAYLIST_ITEMS} entries per playlist.")
        layout.addWidget(self.playlist)
        self.add_label(layout, COPY["format"])
        self.profile = QComboBox()
        self.profile.setAccessibleName(COPY["format"])
        for key, profile in PROFILES.items():
            self.profile.addItem(profile.label, key)
        saved_profile = self.settings.value(Preference.PROFILE, DEFAULT_PROFILE)
        self.profile.setCurrentIndex(max(0, self.profile.findData(saved_profile)))
        layout.addWidget(self.profile)
        self.add_label(layout, COPY["quality"], "muted")
        self.add_label(layout, COPY["folder"])
        folder_row = QHBoxLayout()
        default_folder = (
            Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation))
            / DOWNLOAD_FOLDER
        )
        self.folder = QLineEdit(
            str(self.settings.value(Preference.DESTINATION, str(default_folder)))
        )
        self.folder.setAccessibleName(COPY["folder"])
        self.browse = QPushButton(COPY["browse"])
        self.browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(self.browse)
        layout.addLayout(folder_row)
        buttons = QHBoxLayout()
        self.download = QPushButton(COPY["start"])
        self.download.setObjectName("primary")
        self.download.clicked.connect(self.start)
        self.cancel = QPushButton(COPY["cancel"])
        self.cancel.clicked.connect(self.controller.cancel)
        self.cancel.setEnabled(False)
        self.open_folder = QPushButton(COPY["open"])
        self.open_folder.clicked.connect(self.show_folder)
        buttons.addWidget(self.download)
        buttons.addWidget(self.cancel)
        buttons.addStretch()
        buttons.addWidget(self.open_folder)
        layout.addLayout(buttons)
        self.status = self.add_label(layout, COPY["ready"])
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(MAX_LOG_LINES)
        self.log.setAccessibleName("Download details")
        layout.addWidget(self.log, 1)
        self.add_label(layout, COPY["rights"], "muted")

    @staticmethod
    def add_label(layout: QVBoxLayout, text: str, style: str = "") -> QLabel:
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setObjectName(style)
        layout.addWidget(label)
        return label

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, COPY["browse"], self.folder.text())
        if folder:
            self.folder.setText(folder)

    def show_folder(self) -> None:
        path = Path(self.folder.text()).expanduser()
        if path.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def set_busy(self, busy: bool) -> None:
        for widget in (
            self.url,
            self.playlist,
            self.profile,
            self.folder,
            self.browse,
            self.download,
        ):
            widget.setEnabled(not busy)
        self.cancel.setEnabled(busy)

    def start(self) -> None:
        if self.controller.busy:
            return
        try:
            request = Request.create(
                self.url.text(),
                self.profile.currentData(),
                self.folder.text(),
                self.playlist.isChecked(),
            )
            self.controller.start(request)
        except (ValueError, OSError, RuntimeError) as error:
            self.status.setText(str(error))
            return
        self.settings.setValue(Preference.PROFILE, request.profile)
        self.settings.setValue(Preference.DESTINATION, request.destination)
        self.folder.setText(request.destination)
        self.log.clear()
        self.progress.setRange(0, 0)
        self.status.setText(COPY["working"])
        self.set_busy(True)

    def on_event(self, event: dict) -> None:
        if event["kind"] == Event.PROGRESS:
            percent = event["percent"]
            self.progress.setRange(0, 100 if percent >= 0 else 0)
            self.progress.setValue(max(0, percent))
            self.status.setText(event["title"])
        elif event["kind"] == Event.STATUS:
            self.log.appendPlainText(event["text"])
            self.status.setText(event["text"])

    def on_finished(self, state: str, text: str) -> None:
        self.set_busy(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if state == State.COMPLETE else 0)
        self.status.setText(text)
        self.log.appendPlainText(f"{state}: {text}")
        self.download.setText(COPY["start"] if state == State.COMPLETE else COPY["retry"])

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.controller.busy:
            QMessageBox.information(self, APP_NAME, COPY["busy_close"])
            event.ignore()
        else:
            event.accept()


def main() -> None:
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = Window()
    window.show()
    sys.exit(app.exec())
