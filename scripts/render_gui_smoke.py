from __future__ import annotations

import argparse
import os
from tempfile import TemporaryDirectory
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel

from framepick.gui import APP_STYLE, ExportOptionsDialog, MainWindow, UsageNoticeDialog
from framepick.logging_setup import configure_logging
from framepick.pipeline import load_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", nargs="?")
    parser.add_argument("output")
    parser.add_argument("--import-video", help="渲染已导入视频的中文导入页面")
    parser.add_argument("--page", choices=("import", "results", "preference", "settings", "notice", "export"), default="results")
    parser.add_argument("--aspect", default="original")
    parser.add_argument("--public-example", action="store_true", help="在公开说明书示例中隐藏本机测试数据目录")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    fixture = TemporaryDirectory(prefix="pickerroy-gui-render-")
    data_dir = Path(fixture.name)
    app = QApplication([])
    app.setApplicationName("PickerRoy")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow(data_dir, configure_logging(data_dir))
    if args.public_example:
        for label in window.findChildren(QLabel):
            if str(data_dir) in label.text():
                label.setText(label.text().replace(str(data_dir), "[本机应用数据目录 · 界面示例]"))
    if args.import_video:
        # Rendering uses a separate fixture directory, never the user's actual
        # acknowledgement. This prevents the first-use modal blocking a render.
        window.usage_notice.acknowledge()
        window.add_inputs([args.import_video])
        aspect_index = window.aspect_combo.findData(args.aspect)
        if aspect_index >= 0:
            window.aspect_combo.setCurrentIndex(aspect_index)
    if args.analysis:
        window.results = [load_analysis(args.analysis)]
        window.refresh_results()
        window.next_pair()
    page_index = {"import": 0, "results": 1, "preference": 2, "settings": 3}.get(args.page, 0)
    window.pages.setCurrentIndex(page_index)
    target = window
    if args.page == "notice":
        target = UsageNoticeDialog()
    elif args.page == "export":
        target = ExportOptionsDialog()
        target.mode.setCurrentIndex(1)
    target.show()

    def capture() -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        if not target.grab().save(str(output)):
            raise RuntimeError(f"Could not save GUI smoke image: {output}")
        target.close()
        window.close()
        app.quit()

    QTimer.singleShot(800, capture)
    status = app.exec()
    fixture.cleanup()
    return status


if __name__ == "__main__":
    raise SystemExit(main())
