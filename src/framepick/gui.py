from __future__ import annotations

import itertools
import logging
import os
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QThread, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .config import AnalysisConfig, VIDEO_EXTENSIONS
from .control import AnalysisCancelled, AnalysisControl
from .database import FeedbackStore
from .exporter import export_candidates
from .models import AnalysisResult, Candidate
from .pipeline import VideoAnalyzer, discover_videos
from .runtime import runtime_checks, runtime_ready
from .resources import resource_path
from .usage_notice import NOTICE_PARAGRAPHS, NOTICE_TITLE, UsageNoticeStore
from . import __version__

LOGGER = logging.getLogger(__name__)

CATEGORY_ZH = {
    "Person": "人物",
    "Action": "动作",
    "Landscape": "风景",
    "Animal": "动物",
    "Plant": "植物",
    "Product": "产品/装备",
    "Detail": "细节/特写",
    "Other": "其他",
}


APP_STYLE = """
QWidget { background: #F4F4F1; color: #20211F; font-family: 'PingFang SC', 'Helvetica Neue', sans-serif; font-size: 14px; }
QMainWindow { background: #F4F4F1; }
#sidebar { background: #171916; border: none; }
#brand { color: #F7F8F4; background: transparent; font-size: 21px; font-weight: 700; padding: 0; }
#brandRow { background: transparent; }
#sideButton { color: #C9CBC5; background: transparent; text-align: left; padding: 13px 15px; border-radius: 9px; font-weight: 600; }
#sideButton:checked, #sideButton:hover { color: white; background: #30332D; }
#title { font-size: 28px; font-weight: 720; color: #171916; }
#subtitle { color: #696D66; font-size: 14px; }
#panel { background: white; border: 1px solid #E3E4DF; border-radius: 14px; }
#panel QLabel { background: transparent; }
#dropArea { background: #FBFBF9; border: 2px dashed #B9BDB4; border-radius: 14px; }
#dropArea[active="true"] { border-color: #5B7E62; background: #EFF6EF; }
QPushButton { background: #E8E9E4; border: none; border-radius: 8px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background: #DDDFD8; }
QPushButton#primary { color: white; background: #42634A; padding: 11px 18px; }
QPushButton#primary:hover { background: #34523C; }
QPushButton#danger { color: #9A3E38; background: #F4E5E3; }
QPushButton#favorite { color: #815A10; background: #F9EFCF; }
QPushButton:disabled { color: #999C96; background: #E6E7E3; }
QComboBox { background: white; border: 1px solid #D9DBD5; border-radius: 8px; padding: 8px 12px; min-width: 130px; }
QListWidget { background: white; border: 1px solid #E3E4DF; border-radius: 10px; padding: 6px; }
QProgressBar { background: #E1E3DD; border: none; border-radius: 5px; height: 10px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #5B7E62; border-radius: 5px; }
#card { background: white; border: 1px solid #E2E4DE; border-radius: 12px; }
#meta { color: #777B73; font-size: 12px; }
#pill { color: #385440; background: #E7F0E7; border-radius: 7px; padding: 4px 7px; font-size: 11px; }
QScrollArea { border: none; background: transparent; }
"""


class DropArea(QFrame):
    paths_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.video_count = 0
        self.setObjectName("dropArea")
        self.setProperty("active", False)
        self.setAcceptDrops(True)
        self.setMinimumHeight(170)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel("＋")
        icon.setStyleSheet("font-size: 34px; color: #55725C; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel("把视频或文件夹拖到这里")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 650; background: transparent;")
        self.note_label = QLabel("支持单个视频、多个视频和包含视频的文件夹")
        self.note_label.setObjectName("subtitle")
        self.note_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.note_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_summary(self, count: int) -> None:
        self.video_count = count
        if count:
            self.title_label.setText(f"✓ 已成功导入 {count} 条视频")
            self.note_label.setText("可以继续添加视频，或选择画面比例后开始分析")
            self.setProperty("active", True)
        else:
            self.title_label.setText("把视频或文件夹拖到这里")
            self.note_label.setText("支持单个视频、多个视频和包含视频的文件夹")
            self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("active", bool(self.video_count))
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if paths:
            self.paths_dropped.emit(paths)
        event.acceptProposedAction()


class AnalysisWorker(QThread):
    progress_changed = Signal(dict)
    video_completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, paths: list[Path], data_dir: Path, store: FeedbackStore, config: AnalysisConfig):
        super().__init__()
        self.paths = paths
        self.data_dir = data_dir
        self.store = store
        self.config = config
        self.control = AnalysisControl()

    def pause(self) -> None:
        self.control.pause()

    def resume(self) -> None:
        self.control.resume()

    def cancel(self) -> None:
        self.control.cancel()

    def run(self) -> None:
        try:
            analyzer = VideoAnalyzer(self.data_dir, self.config, self.store, control=self.control)
            total = len(self.paths)
            for index, path in enumerate(self.paths):
                def relay(payload: dict, item=index) -> None:
                    local = float(payload.get("progress", 0))
                    payload["overall"] = (item + local) / max(total, 1)
                    payload["file_index"] = item + 1
                    payload["file_total"] = total
                    self.progress_changed.emit(payload)

                result = analyzer.analyze(path, relay)
                self.video_completed.emit(result)
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:
            LOGGER.exception("Analysis worker failed")
            self.failed.emit(str(exc))


class ImagePreviewDialog(QDialog):
    def __init__(self, candidate: Candidate, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"画面预览 · {candidate.timestamp:.3f} 秒")
        self.resize(1100, 760)
        layout = QVBoxLayout(self)
        label = QLabel()
        pixmap = QPixmap(candidate.preview_path)
        label.setPixmap(pixmap.scaled(1060, 680, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("background: #111; border-radius: 8px;")
        layout.addWidget(label)
        categories = "、".join(CATEGORY_ZH.get(label, label) for label in candidate.labels)
        layout.addWidget(QLabel(f"{candidate.timestamp:.3f} 秒  ·  {categories}  ·  评分 {candidate.final_score:.2f}"))


class UsageNoticeDialog(QDialog):
    def __init__(self, parent=None, require_acknowledgement: bool = True):
        super().__init__(parent)
        self.setWindowTitle(NOTICE_TITLE)
        self.setMinimumWidth(460)
        self.setMaximumWidth(540)
        layout = QVBoxLayout(self)
        heading = QLabel(NOTICE_TITLE)
        heading.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(heading)
        for paragraph in NOTICE_PARAGRAPHS:
            label = QLabel(paragraph)
            label.setWordWrap(True)
            layout.addWidget(label)
        if require_acknowledgement:
            self.confirmation = QCheckBox("我已阅读并理解素材与使用须知")
            self.confirmation.setChecked(False)
            layout.addWidget(self.confirmation)
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            self.continue_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
            self.continue_button.setText("继续导入")
            self.continue_button.setEnabled(False)
            buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("暂不导入")
            self.confirmation.toggled.connect(self.continue_button.setEnabled)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
        else:
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.button(QDialogButtonBox.StandardButton.Close).setText("关闭")
            buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class ExportOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出画面")
        self.setMinimumWidth(510)
        layout = QVBoxLayout(self)
        title = QLabel("选择导出方式")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)
        self.mode = QComboBox()
        self.mode.addItem("直接导出（忠实保留原画）", False)
        self.mode.addItem("增强画质", True)
        layout.addWidget(self.mode)
        layout.addWidget(QLabel("图片格式"))
        self.format = QComboBox()
        self.format.addItem("PNG（无损、文件较大）", "PNG")
        self.format.addItem("JPEG（高质量、文件较小）", "JPEG")
        layout.addWidget(self.format)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("开始导出")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CandidateCard(QFrame):
    feedback_requested = Signal(object, str)
    preview_requested = Signal(object)

    def __init__(self, candidate: Candidate, current_feedback: str = ""):
        super().__init__()
        self.candidate = candidate
        self.setObjectName("card")
        self.setMinimumWidth(250)
        self.setMaximumWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 10)
        image = QLabel()
        image.setFixedHeight(170)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setStyleSheet("background: #ECEDE8; border-radius: 8px;")
        pixmap = QPixmap(candidate.preview_path)
        image.setPixmap(pixmap.scaled(340, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        image.setCursor(Qt.CursorShape.PointingHandCursor)
        image.mousePressEvent = lambda _event: self.preview_requested.emit(candidate)
        layout.addWidget(image)
        pills = QHBoxLayout()
        for text in candidate.labels[:3]:
            label = QLabel(CATEGORY_ZH.get(text, text))
            label.setObjectName("pill")
            pills.addWidget(label)
        pills.addStretch()
        layout.addLayout(pills)
        popularity = candidate.scores.get("social_popularity")
        hot_text = f"  ·  热门视觉 {popularity:.0%}" if popularity is not None else ""
        meta = QLabel(f"推荐 #{candidate.rank or '–'}  ·  {candidate.timestamp:.2f} 秒  ·  评分 {candidate.final_score:.2f}{hot_text}")
        meta.setObjectName("meta")
        layout.addWidget(meta)
        controls = QHBoxLayout()
        self.keep = QPushButton("保留")
        self.reject = QPushButton("淘汰")
        self.reject.setObjectName("danger")
        self.favorite = QPushButton("★")
        self.favorite.setObjectName("favorite")
        self.favorite.setToolTip("收藏：特别喜欢，也会加入导出选择。标记后仍需导出才能保存图片。")
        self.keep.clicked.connect(lambda: self._send("KEEP"))
        self.reject.clicked.connect(lambda: self._send("REJECT"))
        self.favorite.clicked.connect(lambda: self._send("FAVORITE"))
        controls.addWidget(self.keep)
        controls.addWidget(self.reject)
        controls.addWidget(self.favorite)
        layout.addLayout(controls)
        self.set_feedback(current_feedback)

    def _send(self, decision: str) -> None:
        self.feedback_requested.emit(self.candidate, decision)
        self.set_feedback(decision)

    def set_feedback(self, decision: str) -> None:
        active = "border: 2px solid #42634A;" if decision else ""
        self.setStyleSheet(active)
        self.keep.setText("✓ 已保留" if decision == "KEEP" else "保留")
        self.reject.setText("✓ 已淘汰" if decision == "REJECT" else "淘汰")
        self.favorite.setText("★ 已收藏" if decision == "FAVORITE" else "★")


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path, log_path: Path):
        super().__init__()
        self.data_dir = data_dir
        self.log_path = log_path
        self.store = FeedbackStore(data_dir / "pickerroy.sqlite3")
        self.usage_notice = UsageNoticeStore(data_dir)
        self.pending_paths: list[Path] = []
        self.active_paths: set[Path] = set()
        self.results: list[AnalysisResult] = []
        self.feedback = self.store.latest_feedback()
        self.worker: AnalysisWorker | None = None
        self.current_pair: tuple[Candidate, Candidate] | None = None
        self.environment_ready = False
        self.batch_cancelled = False
        self.batch_failed = False
        self.setWindowTitle("PickerRoy")
        self.resize(1320, 860)
        self.setMinimumSize(1000, 680)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 22, 14, 18)
        brand_row = QFrame()
        brand_row.setObjectName("brandRow")
        brand_layout = QHBoxLayout(brand_row)
        brand_layout.setContentsMargins(0, 4, 0, 20)
        brand_layout.setSpacing(10)
        mark = QLabel()
        mark.setFixedSize(42, 42)
        mark.setStyleSheet("background: transparent;")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark_image = QPixmap(str(resource_path("assets/PickerRoy-logo.png"))).scaled(
            84, 84, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        mark_image.setDevicePixelRatio(2)
        mark.setPixmap(mark_image)
        brand_layout.addWidget(mark)
        brand = QLabel("PickerRoy")
        brand.setObjectName("brand")
        brand_layout.addWidget(brand)
        brand_layout.addStretch()
        side_layout.addWidget(brand_row)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        nav_items = [("导入", 0), ("筛选结果", 1), ("偏好训练", 2), ("设置", 3)]
        for label, index in nav_items:
            button = QPushButton(label)
            button.setObjectName("sideButton")
            button.setCheckable(True)
            button.setProperty("page", index)
            self.nav_group.addButton(button, index)
            side_layout.addWidget(button)
            if index == 0:
                button.setChecked(True)
        side_layout.addStretch()
        log_button = QPushButton("打开运行日志")
        log_button.setObjectName("sideButton")
        log_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_path))))
        side_layout.addWidget(log_button)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._import_page())
        self.pages.addWidget(self._results_page())
        self.pages.addWidget(self._preference_page())
        self.pages.addWidget(self._settings_page())
        # Accessibility activation can change checked state without clicked().
        # Connect after page construction, since the first button starts checked.
        self.nav_group.idToggled.connect(self._navigate_checked_page)
        self.pages.currentChanged.connect(self._sync_navigation)
        outer.addWidget(sidebar)
        outer.addWidget(self.pages, 1)

    def _navigate_checked_page(self, page: int, checked: bool) -> None:
        if checked:
            self.pages.setCurrentIndex(page)

    def _sync_navigation(self, page: int) -> None:
        button = self.nav_group.button(page)
        if button is not None and not button.isChecked():
            button.setChecked(True)

    def _page_shell(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 30, 34, 28)
        heading = QLabel(title)
        heading.setObjectName("title")
        layout.addWidget(heading)
        description = QLabel(subtitle)
        description.setObjectName("subtitle")
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addSpacing(14)
        return page, layout

    def _import_page(self) -> QWidget:
        page, layout = self._page_shell("从视频中精选好照片", "快速筛选清晰、自然、适合使用的画面，保存到本地。视频与偏好数据在本机处理，无需上传。")
        self.drop_area = DropArea()
        self.drop_area.paths_dropped.connect(self.add_inputs)
        layout.addWidget(self.drop_area)
        buttons = QHBoxLayout()
        add_videos = QPushButton("添加视频")
        add_folder = QPushButton("添加文件夹")
        add_videos.clicked.connect(self.choose_videos)
        add_folder.clicked.connect(self.choose_folder)
        buttons.addWidget(add_videos)
        buttons.addWidget(add_folder)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.import_status = QLabel("尚未导入视频")
        self.import_status.setStyleSheet(
            "background: #E8E9E4; color: #5F635C; border-radius: 8px; padding: 10px 13px; font-weight: 600;"
        )
        layout.addWidget(self.import_status)
        self.input_list = QListWidget()
        self.input_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.input_list.setMinimumHeight(110)
        layout.addWidget(self.input_list)
        ratio_panel = QFrame()
        ratio_panel.setObjectName("panel")
        ratio_layout = QHBoxLayout(ratio_panel)
        ratio_text = QVBoxLayout()
        ratio_title = QLabel("生成画面比例")
        ratio_title.setStyleSheet("font-weight: 650;")
        ratio_note = QLabel("分析、预览和导出都会按所选比例智能裁切，原视频不会改变。")
        ratio_note.setObjectName("subtitle")
        ratio_text.addWidget(ratio_title)
        ratio_text.addWidget(ratio_note)
        self.aspect_combo = QComboBox()
        for text, value in [
            ("原视频比例", "original"),
            ("1:1 方形", "1:1"),
            ("3:2 横版", "3:2"),
            ("2:3 竖版", "2:3"),
            ("4:3 横版", "4:3"),
            ("3:4 竖版", "3:4"),
            ("16:9 横版", "16:9"),
            ("9:16 竖版", "9:16"),
        ]:
            self.aspect_combo.addItem(text, value)
        ratio_layout.addLayout(ratio_text, 1)
        ratio_layout.addWidget(self.aspect_combo)
        layout.addWidget(ratio_panel)
        actions = QHBoxLayout()
        remove = QPushButton("移除选中项目")
        remove.clicked.connect(self.remove_selected_inputs)
        self.start_button = QPushButton("开始分析")
        self.start_button.setObjectName("primary")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_analysis)
        actions.addWidget(remove)
        actions.addStretch()
        actions.addWidget(self.start_button)
        layout.addLayout(actions)
        self.progress_panel = QFrame()
        self.progress_panel.setObjectName("panel")
        panel_layout = QVBoxLayout(self.progress_panel)
        self.progress_label = QLabel("准备就绪")
        self.progress_detail = QLabel("当前没有正在处理的视频")
        self.progress_detail.setObjectName("subtitle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)
        progress_controls = QHBoxLayout()
        progress_controls.addStretch()
        self.pause_button = QPushButton("暂停分析")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.cancel_button = QPushButton("取消分析")
        self.cancel_button.setObjectName("danger")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        progress_controls.addWidget(self.pause_button)
        progress_controls.addWidget(self.cancel_button)
        panel_layout.addWidget(self.progress_label)
        panel_layout.addWidget(self.progress_detail)
        panel_layout.addWidget(self.progress_bar)
        panel_layout.addLayout(progress_controls)
        layout.addWidget(self.progress_panel)
        layout.addStretch()
        return page

    def _results_page(self) -> QWidget:
        page, layout = self._page_shell("推荐静帧", "系统已经过滤技术废片和近重复画面，并保留不同内容类型。点击图片可以放大预览。")
        toolbar = QHBoxLayout()
        self.category_filter = QComboBox()
        for text, value in [
            ("全部", "All"), ("人物", "Person"), ("动作", "Action"), ("风景", "Landscape"),
            ("动物", "Animal"), ("植物", "Plant"), ("产品/装备", "Product"), ("细节/特写", "Detail"),
        ]:
            self.category_filter.addItem(text, value)
        self.category_filter.currentTextChanged.connect(self.refresh_results)
        self.results_count = QLabel("暂无结果")
        self.results_count.setObjectName("subtitle")
        export = QPushButton("导出已选画面")
        export.setObjectName("primary")
        export.clicked.connect(self.export_selected)
        toolbar.addWidget(self.category_filter)
        toolbar.addWidget(self.results_count)
        toolbar.addStretch()
        toolbar.addWidget(export)
        layout.addLayout(toolbar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.results_grid = QGridLayout(self.grid_host)
        self.results_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.results_grid.setSpacing(14)
        scroll.setWidget(self.grid_host)
        layout.addWidget(scroll, 1)
        return page

    def _preference_page(self) -> QWidget:
        page, layout = self._page_shell("哪一帧更好？", "每组画面来自同一个镜头和相近时间。你的选择只保存在本机，并从下一次分析开始参与排序。")
        learning_panel = QFrame()
        learning_panel.setObjectName("panel")
        learning_layout = QVBoxLayout(learning_panel)
        self.personalization_title = QLabel("你的专属 PickerRoy 正在起步")
        self.personalization_title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.personalization_detail = QLabel()
        self.personalization_detail.setObjectName("subtitle")
        self.personalization_detail.setWordWrap(True)
        self.personalization_progress = QProgressBar()
        self.personalization_progress.setRange(0, 100)
        self.personalization_progress.setFormat("学习样本积累 %p%（不是准确率）")
        learning_layout.addWidget(self.personalization_title)
        learning_layout.addWidget(self.personalization_detail)
        learning_layout.addWidget(self.personalization_progress)
        layout.addWidget(learning_panel)
        self.preference_status = QLabel("分析视频后，这里会生成偏好对比。")
        self.preference_status.setObjectName("subtitle")
        layout.addWidget(self.preference_status)
        pair = QHBoxLayout()
        self.pair_images: list[QLabel] = []
        for side in ("A", "B"):
            column = QVBoxLayout()
            image = QLabel(side)
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setMinimumSize(340, 330)
            image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            image.setStyleSheet("background: #20211F; color: white; border-radius: 12px; font-size: 28px;")
            choose = QPushButton(f"选择 {side}")
            choose.setObjectName("primary")
            choose.clicked.connect(lambda _checked=False, value=side: self.choose_preference(value))
            column.addWidget(image, 1)
            column.addWidget(choose)
            pair.addLayout(column, 1)
            self.pair_images.append(image)
        layout.addLayout(pair, 1)
        skip = QPushButton("跳过这一组")
        skip.clicked.connect(self.next_pair)
        layout.addWidget(skip, alignment=Qt.AlignmentFlag.AlignCenter)
        self.refresh_personalization_status()
        return page

    def _settings_page(self) -> QWidget:
        page, layout = self._page_shell("设置", f"PickerRoy {__version__} · 先确认运行环境，再按内容选择选帧侧重点；所有处理都在本机完成。")
        health_panel = QFrame()
        health_panel.setObjectName("panel")
        health_layout = QVBoxLayout(health_panel)
        health_header = QHBoxLayout()
        health_header.addWidget(QLabel("运行环境自检"))
        health_header.addStretch()
        refresh_health = QPushButton("重新检查")
        refresh_health.clicked.connect(self.refresh_runtime_status)
        health_header.addWidget(refresh_health)
        health_layout.addLayout(health_header)
        self.runtime_summary = QLabel()
        self.runtime_summary.setWordWrap(True)
        health_layout.addWidget(self.runtime_summary)
        self.runtime_details = QLabel()
        self.runtime_details.setObjectName("subtitle")
        self.runtime_details.setWordWrap(True)
        health_layout.addWidget(self.runtime_details)
        layout.addWidget(health_panel)
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.addWidget(QLabel("选帧模式"))
        self.mode_combo = QComboBox()
        for text, value in [
            ("综合", "Balanced"), ("人像", "Portrait"), ("动作", "Action"),
            ("风景", "Landscape"), ("产品", "Product"),
        ]:
            self.mode_combo.addItem(text, value)
        panel_layout.addWidget(self.mode_combo)
        panel_layout.addSpacing(10)
        data_note = QLabel(f"本地数据位置：{self.data_dir}\n视频、缓存、导出图片和偏好数据都不会上传。")
        data_note.setObjectName("subtitle")
        data_note.setWordWrap(True)
        panel_layout.addWidget(data_note)
        layout.addWidget(panel)
        usage_button = QPushButton("素材与使用须知")
        usage_button.clicked.connect(lambda: UsageNoticeDialog(self, require_acknowledgement=False).exec())
        layout.addWidget(usage_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        self.refresh_runtime_status()
        return page

    def refresh_runtime_status(self) -> None:
        checks = runtime_checks()
        self.environment_ready = runtime_ready(checks)
        self.runtime_summary.setText("✓ 可以开始使用" if self.environment_ready else "需要处理后才能分析视频")
        self.runtime_summary.setStyleSheet(
            "color: #315C3A; font-weight: 700;" if self.environment_ready else "color: #91453E; font-weight: 700;"
        )
        self.runtime_details.setText("\n".join(f"{'✓' if row.ready else '✕'} {row.label}：{row.detail}" for row in checks))
        if hasattr(self, "start_button"):
            self.start_button.setEnabled(bool(self.pending_paths) and self.environment_ready and not (self.worker and self.worker.isRunning()))

    def choose_videos(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择视频", "", "视频文件 (*.mp4 *.mov *.m4v *.mkv *.avi *.webm *.mts *.m2ts *.mxf)")
        self.add_inputs(paths)

    def choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")
        if path:
            self.add_inputs([path])

    def add_inputs(self, raw_paths: list[str]) -> None:
        if not raw_paths or not self.confirm_usage_notice():
            return
        videos = discover_videos(raw_paths)
        existing = set(self.pending_paths)
        added = 0
        for path in videos:
            if path not in existing:
                self.pending_paths.append(path)
                existing.add(path)
                added += 1
                item = QListWidgetItem(f"✓  {path.name}")
                item.setToolTip(str(path))
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                self.input_list.addItem(item)
        total = len(self.pending_paths)
        self.drop_area.set_summary(total)
        if added:
            if self.worker and self.worker.isRunning():
                self.import_status.setText(f"✓ 已加入下一轮：新增 {added} 条；当前分析结束后可继续开始")
            else:
                self.import_status.setText(f"✓ 导入成功：本次新增 {added} 条，共 {total} 条视频等待分析")
            self.import_status.setStyleSheet(
                "background: #E4F1E6; color: #315C3A; border-radius: 8px; padding: 10px 13px; font-weight: 650;"
            )
        elif videos and total:
            self.import_status.setText(f"这些视频已经在列表中，目前共 {total} 条")
        else:
            self.import_status.setText("没有找到支持的视频，请选择 MP4、MOV、MKV、AVI 等视频文件")
            self.import_status.setStyleSheet(
                "background: #F8E8E5; color: #91453E; border-radius: 8px; padding: 10px 13px; font-weight: 650;"
            )
        self.start_button.setEnabled(bool(self.pending_paths) and self.environment_ready and not (self.worker and self.worker.isRunning()))

    def remove_selected_inputs(self) -> None:
        selected = {
            Path(item.data(Qt.ItemDataRole.UserRole)) for item in self.input_list.selectedItems()
            if Path(item.data(Qt.ItemDataRole.UserRole)) not in self.active_paths
        }
        self.pending_paths = [path for path in self.pending_paths if path not in selected]
        self._refresh_input_items()
        total = len(self.pending_paths)
        self.drop_area.set_summary(total)
        self.import_status.setText(f"当前已有 {total} 条视频等待分析" if total else "尚未导入视频")
        self.import_status.setStyleSheet(
            "background: #E8E9E4; color: #5F635C; border-radius: 8px; padding: 10px 13px; font-weight: 600;"
        )
        self.start_button.setEnabled(
            bool(self.pending_paths) and self.environment_ready and not (self.worker and self.worker.isRunning())
        )

    def start_analysis(self) -> None:
        if not self.pending_paths:
            return
        if not self.confirm_usage_notice():
            return
        if not self.environment_ready:
            QMessageBox.warning(self, "运行环境未就绪", "请先打开“设置”查看运行环境自检结果。")
            return
        self.start_button.setEnabled(False)
        self.batch_cancelled = False
        self.batch_failed = False
        self.active_paths = set(self.pending_paths)
        self._refresh_input_items()
        self.progress_label.setText("正在准备分析……")
        config = AnalysisConfig.for_mode(
            str(self.mode_combo.currentData()),
            aspect_ratio=str(self.aspect_combo.currentData()),
        )
        self.worker = AnalysisWorker(list(self.pending_paths), self.data_dir, self.store, config)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.video_completed.connect(self.analysis_completed)
        self.worker.failed.connect(self.analysis_failed)
        self.worker.cancelled.connect(self.analysis_cancelled)
        self.worker.finished.connect(self.analysis_finished)
        self.pause_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.pause_button.setText("暂停分析")
        self.worker.start()

    def confirm_usage_notice(self) -> bool:
        if self.usage_notice.acknowledged():
            return True
        if UsageNoticeDialog(self).exec() != QDialog.DialogCode.Accepted:
            self.import_status.setText("尚未确认素材与使用须知，未导入或分析视频")
            return False
        try:
            self.usage_notice.acknowledge()
        except OSError:
            QMessageBox.warning(self, "无法保存确认记录", "请检查本地数据目录是否可写，再重新确认。")
            return False
        return True

    def toggle_pause(self) -> None:
        if not self.worker or not self.worker.isRunning():
            return
        if self.worker.control.is_paused:
            self.worker.resume()
            self.pause_button.setText("暂停分析")
            self.progress_label.setText("正在恢复分析……")
        else:
            self.worker.pause()
            self.pause_button.setText("继续分析")
            self.progress_label.setText("⏸ 分析已暂停")
            self.progress_detail.setText("可以继续导入新视频；它们会进入下一轮。")

    def cancel_analysis(self) -> None:
        if not self.worker or not self.worker.isRunning():
            return
        self.worker.cancel()
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.progress_label.setText("正在取消分析……")
        self.progress_detail.setText("正在安全停止当前解码任务，已完成的视频结果会保留。")

    def update_progress(self, payload: dict) -> None:
        stage_names = {
            "scene_detection": "正在识别镜头",
            "sampling": "正在分析候选画面",
            "popularity": "正在评估热门视觉",
            "ranking": "正在去重并排序",
            "done": "分析完成",
        }
        stage = stage_names.get(payload.get("stage"), "正在处理")
        self.progress_label.setText(f"{stage}: {payload.get('video', '')}")
        self.progress_detail.setText(
            f"视频 {payload.get('file_index', 1)}/{payload.get('file_total', 1)}  ·  "
            f"镜头 {payload.get('shot', 0)}/{payload.get('shots', '–')}  ·  "
            f"候选画面 {payload.get('candidates', 0)}"
        )
        self.progress_bar.setValue(round(float(payload.get("overall", 0)) * 1000))

    def analysis_completed(self, result: AnalysisResult) -> None:
        self.results = [row for row in self.results if row.video.id != result.video.id] + [result]
        completed_path = Path(result.video.path).resolve()
        self.pending_paths = [path for path in self.pending_paths if path.resolve() != completed_path]
        self.active_paths.discard(completed_path)
        self._refresh_input_items()
        recommended = len([item for item in result.candidates if item.rank is not None and not item.rejected and not item.duplicate_of])
        self.progress_label.setText(f"✓ 分析完成：{Path(result.video.path).name}")
        self.progress_detail.setText(f"已生成 {recommended} 张推荐画面，可在“筛选结果”中保留、收藏或导出。")
        self.progress_bar.setValue(1000)
        self.refresh_results()
        self.next_pair()
        self.refresh_personalization_status()

    def analysis_failed(self, message: str) -> None:
        self.batch_failed = True
        self.progress_label.setText("分析已停止")
        self.progress_detail.setText(message)
        QMessageBox.critical(self, "PickerRoy 无法完成分析", f"{message}\n\n详细信息已保存到：\n{self.log_path}")

    def analysis_cancelled(self) -> None:
        self.batch_cancelled = True
        self.progress_label.setText("已取消分析")
        self.progress_detail.setText("已安全停止；已完成的视频结果仍可在“筛选结果”中查看，未完成视频保留在列表。")

    def analysis_finished(self) -> None:
        self.active_paths.clear()
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.pause_button.setText("暂停分析")
        self.worker = None
        self._refresh_input_items()
        self.start_button.setEnabled(bool(self.pending_paths) and self.environment_ready)
        if self.results and not self.batch_cancelled and not self.batch_failed:
            self.pages.setCurrentIndex(1)
            for button in self.nav_group.buttons():
                button.setChecked(button.property("page") == 1)

    def _refresh_input_items(self) -> None:
        self.input_list.clear()
        for path in self.pending_paths:
            prefix = "▶" if path in self.active_paths else "✓"
            suffix = "（正在分析）" if path in self.active_paths else ""
            item = QListWidgetItem(f"{prefix}  {path.name}{suffix}")
            item.setToolTip(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.input_list.addItem(item)
        self.drop_area.set_summary(len(self.pending_paths))

    def _visible_candidates(self) -> list[Candidate]:
        candidates = list(itertools.chain.from_iterable(result.candidates for result in self.results))
        candidates = [item for item in candidates if item.rank is not None and not item.rejected and not item.duplicate_of]
        candidates.sort(key=lambda item: (item.video_id, item.rank or 9999))
        category = str(self.category_filter.currentData())
        if category != "All":
            candidates = [item for item in candidates if category in item.labels]
        return candidates

    def refresh_results(self) -> None:
        while self.results_grid.count():
            item = self.results_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        candidates = self._visible_candidates()
        self.results_count.setText(f"共 {len(candidates)} 张推荐画面")
        columns = 3 if self.width() < 1450 else 4
        for index, candidate in enumerate(candidates):
            card = CandidateCard(candidate, self.feedback.get(candidate.id, ""))
            card.feedback_requested.connect(self.record_feedback)
            card.preview_requested.connect(self.show_preview)
            self.results_grid.addWidget(card, index // columns, index % columns)

    def show_preview(self, candidate: Candidate) -> None:
        ImagePreviewDialog(candidate, self).exec()

    def record_feedback(self, candidate: Candidate, decision: str) -> None:
        self.store.record_feedback(candidate, decision)
        self.feedback[candidate.id] = decision
        self.refresh_personalization_status()

    def export_selected(self) -> None:
        selected = [item for item in self._visible_candidates() if self.feedback.get(item.id) in {"KEEP", "FAVORITE"}]
        if not selected:
            QMessageBox.information(self, "尚未选择画面", "请先把需要导出的画面标记为“保留”或“收藏”。")
            return
        destination = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not destination:
            return
        options = ExportOptionsDialog(self)
        if options.exec() != QDialog.DialogCode.Accepted:
            return
        image_format = str(options.format.currentData())
        optimized = bool(options.mode.currentData())
        by_video: dict[str, list[Candidate]] = defaultdict(list)
        for item in selected:
            by_video[item.video_id].append(item)
        outputs = []
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for result in self.results:
                if result.video.id in by_video:
                    outputs.extend(export_candidates(
                        result.video, by_video[result.video.id], destination, image_format, optimized=optimized
                    ))
        except Exception as exc:
            LOGGER.exception("导出失败")
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        finally:
            QApplication.restoreOverrideCursor()
        mode_text = "增强画质并" if optimized else "直接"
        QMessageBox.information(self, "导出完成", f"已{mode_text}导出 {len(outputs)} 张画面。")

    def _pair_pool(self) -> list[tuple[Candidate, Candidate]]:
        pairs = []
        for result in self.results:
            grouped: dict[str, list[Candidate]] = defaultdict(list)
            for item in result.candidates:
                if not item.rejected and not item.duplicate_of:
                    grouped[item.shot_id].append(item)
            for items in grouped.values():
                items.sort(key=lambda candidate: candidate.timestamp)
                for left, right in zip(items, items[1:]):
                    if right.timestamp - left.timestamp <= 2.5:
                        pairs.append((left, right))
        return pairs

    def next_pair(self) -> None:
        pairs = self._pair_pool()
        if not pairs:
            self.current_pair = None
            self.preference_status.setText("目前没有可供比较的相邻候选画面。")
            return
        current_id = self.current_pair[0].id if self.current_pair else ""
        index = next((i + 1 for i, pair in enumerate(pairs) if pair[0].id == current_id), 0) % len(pairs)
        self.current_pair = pairs[index]
        for label, candidate in zip(self.pair_images, self.current_pair):
            pixmap = QPixmap(candidate.preview_path)
            label.setPixmap(pixmap.scaled(520, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        a, b = self.current_pair
        learned = self.store.counts()["preferences"]
        learned_text = f"  ·  已学习 {learned} 次选择" if learned else ""
        self.preference_status.setText(f"同一镜头 · {a.timestamp:.2f} 秒 对比 {b.timestamp:.2f} 秒{learned_text}")

    def choose_preference(self, side: str) -> None:
        if not self.current_pair:
            return
        a, b = self.current_pair
        self.store.record_preference(a, b, a if side == "A" else b)
        self.refresh_personalization_status()
        self.next_pair()

    def refresh_personalization_status(self) -> None:
        if not hasattr(self, "personalization_title"):
            return
        stats = self.store.personalization_stats()
        pairs = int(stats["training_pairs"])
        videos = int(stats["videos"])
        progress = min(100, round(100 * pairs / 50))
        self.personalization_progress.setValue(progress)
        if pairs:
            title = "越选，越懂你的眼光"
        else:
            title = "你的专属 PickerRoy 正在起步"
        decisions = stats["decisions"]
        top = "、".join(CATEGORY_ZH.get(name, name) for name, _count in stats["top_categories"]) or "尚未形成"
        applied = max((int(candidate.scores.get("personal_preference_samples", 0))
                       for result in self.results for candidate in result.candidates), default=0)
        applied_text = (f"当前载入结果最多参考了 {applied} 组本机比较。" if applied else
                        "当前载入结果尚未使用本机比较。")
        self.personalization_title.setText(title)
        self.personalization_detail.setText(
            f"已分析 {videos} 条视频，形成 {pairs} 组有效学习对；"
            f"收藏 {decisions['FAVORITE']}、保留 {decisions['KEEP']}、淘汰 {decisions['REJECT']}。"
            f"常保留的主题：{top}。{applied_text}"
            "新的有效选择会在下一次分析时参与排序；仅增加导入次数不会自动提升准确率。"
        )

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            if not self.worker.wait(5000):
                event.ignore()
                return
        event.accept()


def data_directory() -> Path:
    override = os.environ.get("PICKERROY_DATA_DIR") or os.environ.get("FRAMEPICK_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    from PySide6.QtCore import QStandardPaths

    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
