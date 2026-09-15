import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from framepick.gui import MainWindow


def test_main_window_can_be_created(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(tmp_path / "data", tmp_path / "framepick.log")
    assert window.windowTitle() == "PickerRoy"
    assert window.pages.count() == 4
    assert window.aspect_combo.count() == 8
    assert any(label.text() == "从视频中精选好照片" for label in window.findChildren(QLabel))
    assert any(label.pixmap() and not label.pixmap().isNull() for label in window.findChildren(QLabel))
    assert window.runtime_summary.text() in {"✓ 可以开始使用", "需要处理后才能分析视频"}
    window.close()
    app.processEvents()


def test_sidebar_checked_state_and_page_stay_in_sync(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(tmp_path / "data", tmp_path / "framepick.log")
    try:
        # Native accessibility can toggle a checkable button without clicked().
        preference = next(b for b in window.nav_group.buttons() if b.property("page") == 2)
        preference.setChecked(True)
        assert window.pages.currentIndex() == 2
        assert window.nav_group.checkedButton() is preference

        # Programmatic navigation must also update the visible selection.
        window.pages.setCurrentIndex(3)
        assert window.nav_group.checkedButton().property("page") == 3

        # Ordinary activation still works and changes the page only once.
        changes = []
        window.pages.currentChanged.connect(changes.append)
        import_button = next(b for b in window.nav_group.buttons() if b.property("page") == 0)
        import_button.click()
        assert window.pages.currentIndex() == 0
        assert changes == [0]
    finally:
        window.close()
        app.processEvents()
