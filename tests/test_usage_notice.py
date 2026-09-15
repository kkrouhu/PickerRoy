import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QLabel
from framepick.gui import ExportOptionsDialog, MainWindow, UsageNoticeDialog
from framepick.usage_notice import NOTICE_VERSION, UsageNoticeStore
from framepick import __version__


def test_notice_is_explicit_versioned_and_local(tmp_path):
    store = UsageNoticeStore(tmp_path)
    assert not store.acknowledged()
    store.acknowledge()
    assert UsageNoticeStore(tmp_path).acknowledged()
    value = json.loads(store.path.read_text())
    assert set(value) == {"version", "acknowledged", "acknowledged_at"}
    assert value["version"] == NOTICE_VERSION
    value["version"] = "older-notice"
    store.path.write_text(json.dumps(value))
    assert not store.acknowledged()
    store.path.write_text("bad json")
    assert not store.acknowledged()


def test_notice_starts_unchecked_and_export_label_is_only_four_characters(tmp_path):
    app = QApplication.instance() or QApplication([])
    notice = UsageNoticeDialog()
    assert not notice.confirmation.isChecked()
    assert not notice.continue_button.isEnabled()
    notice.confirmation.setChecked(True)
    assert notice.continue_button.isEnabled()
    export = ExportOptionsDialog()
    assert export.mode.itemText(0) == "直接导出（忠实保留原画）"
    assert export.mode.itemText(1) == "增强画质"
    assert not any("锐" in label.text() or "像素" in label.text() for label in export.findChildren(QLabel))
    notice.close()
    export.close()
    app.processEvents()


def test_declining_notice_prevents_import_and_does_not_record_acknowledgement(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(tmp_path / "app", tmp_path / "test.log")
    assert any(f"PickerRoy {__version__}" in label.text() for label in window.findChildren(QLabel))
    monkeypatch.setattr(UsageNoticeDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    window.add_inputs([str(tmp_path / "unused.mp4")])
    assert window.pending_paths == []
    assert not window.usage_notice.path.exists()
    assert "未导入" in window.import_status.text()
    window.close()
    app.processEvents()
