from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .gui import APP_STYLE, MainWindow, data_directory
from .logging_setup import configure_logging
from .resources import resource_path


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PickerRoy")
    app.setOrganizationName("PickerRoy")
    icon_path = resource_path("assets/PickerRoy-logo.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    data_dir = data_directory()
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = configure_logging(data_dir)
    window = MainWindow(data_dir, log_path)
    window.show()
    return app.exec()
