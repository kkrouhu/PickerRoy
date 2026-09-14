from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from framepick.gui import APP_STYLE, MainWindow
from framepick.logging_setup import configure_logging
from framepick.pipeline import load_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis")
    parser.add_argument("output")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    data_dir = output.parent / "gui-data"
    app = QApplication([])
    app.setApplicationName("PickerRoy")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow(data_dir, configure_logging(data_dir))
    window.results = [load_analysis(args.analysis)]
    window.pages.setCurrentIndex(1)
    window.refresh_results()
    window.show()

    def capture() -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        if not window.grab().save(str(output)):
            raise RuntimeError(f"Could not save GUI smoke image: {output}")
        window.close()
        app.quit()

    QTimer.singleShot(800, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
