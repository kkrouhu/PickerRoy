import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from framepick.gui import MainWindow


def test_main_window_can_be_created(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(tmp_path / "data", tmp_path / "framepick.log")
    assert window.windowTitle() == "FramePick Local"
    assert window.pages.count() == 4
    window.close()
    app.processEvents()

