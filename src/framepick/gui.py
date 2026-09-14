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
    QComboBox,
    QDialog,
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
from .database import FeedbackStore
from .exporter import export_candidates
from .models import AnalysisResult, Candidate
from .pipeline import VideoAnalyzer, discover_videos

LOGGER = logging.getLogger(__name__)

CATEGORY_ZH = {
    "Person": "人物",
    "Action": "动作",
    "Landscape": "风景",
    "Animal": "动物",
    "Product": "产品/装备",
    "Detail": "细节/特写",
    "Other": "其他",
}


APP_STYLE = """
QWidget { background: #F4F4F1; color: #20211F; font-family: 'PingFang SC', 'Helvetica Neue', sans-serif; font-size: 14px; }
QMainWindow { background: #F4F4F1; }
#sidebar { background: #171916; border: none; }
#brand { color: #F7F8F4; background: transparent; font-size: 22px; font-weight: 700; padding: 10px 12px 20px 12px; }
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

    def __init__(self, paths: list[Path], data_dir: Path, store: FeedbackStore, config: AnalysisConfig):
        super().__init__()
        self.paths = paths
        self.data_dir = data_dir
        self.store = store
        self.config = config

    def run(self) -> None:
        try:
            analyzer = VideoAnalyzer(self.data_dir, self.config, self.store)
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
        meta = QLabel(f"推荐 #{candidate.rank or '–'}  ·  {candidate.timestamp:.2f} 秒  ·  评分 {candidate.final_score:.2f}")
        meta.setObjectName("meta")
        layout.addWidget(meta)
        controls = QHBoxLayout()
        self.keep = QPushButton("保留")
        self.reject = QPushButton("淘汰")
        self.reject.setObjectName("danger")
        self.favorite = QPushButton("★")
        self.favorite.setObjectName("favorite")
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
        self.pending_paths: list[Path] = []
        self.results: list[AnalysisResult] = []
        self.feedback = self.store.latest_feedback()
        self.worker: AnalysisWorker | None = None
        self.current_pair: tuple[Candidate, Candidate] | None = None
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
        brand = QLabel("PickerRoy")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        nav_items = [("导入", 0), ("筛选结果", 1), ("偏好训练", 2), ("设置", 3)]
        for label, index in nav_items:
            button = QPushButton(label)
            button.setObjectName("sideButton")
            button.setCheckable(True)
            button.setProperty("page", index)
            button.clicked.connect(lambda _checked=False, page=index: self.pages.setCurrentIndex(page))
            self.nav_group.addButton(button)
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
        outer.addWidget(sidebar)
        outer.addWidget(self.pages, 1)

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
        page, layout = self._page_shell("导入视频", "PickerRoy 会先识别镜头，再让同一镜头里的多个画面竞争，找出最值得保存的瞬间。")
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
        panel_layout.addWidget(self.progress_label)
        panel_layout.addWidget(self.progress_detail)
        panel_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_panel)
        layout.addStretch()
        return page

    def _results_page(self) -> QWidget:
        page, layout = self._page_shell("推荐静帧", "系统已经过滤技术废片和近重复画面，并保留不同内容类型。点击图片可以放大预览。")
        toolbar = QHBoxLayout()
        self.category_filter = QComboBox()
        for text, value in [
            ("全部", "All"), ("人物", "Person"), ("动作", "Action"), ("风景", "Landscape"),
            ("动物", "Animal"), ("产品/装备", "Product"), ("细节/特写", "Detail"),
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
        page, layout = self._page_shell("哪一帧更好？", "每组画面来自同一个镜头和相近时间。你的每次选择都只保存在本机。")
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
        return page

    def _settings_page(self) -> QWidget:
        page, layout = self._page_shell("设置", "模式只会改变选帧侧重点，不会修改原视频。")
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
        layout.addStretch()
        return page

    def choose_videos(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择视频", "", "视频文件 (*.mp4 *.mov *.m4v *.mkv *.avi *.webm *.mts *.m2ts *.mxf)")
        self.add_inputs(paths)

    def choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择包含视频的文件夹")
        if path:
            self.add_inputs([path])

    def add_inputs(self, raw_paths: list[str]) -> None:
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
        self.start_button.setEnabled(bool(self.pending_paths) and not (self.worker and self.worker.isRunning()))

    def remove_selected_inputs(self) -> None:
        selected = {Path(item.data(Qt.ItemDataRole.UserRole)) for item in self.input_list.selectedItems()}
        self.pending_paths = [path for path in self.pending_paths if path not in selected]
        for item in self.input_list.selectedItems():
            self.input_list.takeItem(self.input_list.row(item))
        total = len(self.pending_paths)
        self.drop_area.set_summary(total)
        self.import_status.setText(f"当前已有 {total} 条视频等待分析" if total else "尚未导入视频")
        self.import_status.setStyleSheet(
            "background: #E8E9E4; color: #5F635C; border-radius: 8px; padding: 10px 13px; font-weight: 600;"
        )
        self.start_button.setEnabled(bool(self.pending_paths))

    def start_analysis(self) -> None:
        if not self.pending_paths:
            return
        self.start_button.setEnabled(False)
        self.progress_label.setText("正在准备分析……")
        config = AnalysisConfig.for_mode(
            str(self.mode_combo.currentData()),
            aspect_ratio=str(self.aspect_combo.currentData()),
        )
        self.worker = AnalysisWorker(list(self.pending_paths), self.data_dir, self.store, config)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.video_completed.connect(self.analysis_completed)
        self.worker.failed.connect(self.analysis_failed)
        self.worker.finished.connect(lambda: self.start_button.setEnabled(bool(self.pending_paths)))
        self.worker.start()

    def update_progress(self, payload: dict) -> None:
        stage_names = {
            "scene_detection": "正在识别镜头",
            "sampling": "正在分析候选画面",
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
        self.refresh_results()
        self.next_pair()
        self.pages.setCurrentIndex(1)
        for button in self.nav_group.buttons():
            button.setChecked(button.property("page") == 1)

    def analysis_failed(self, message: str) -> None:
        self.progress_label.setText("分析已停止")
        self.progress_detail.setText(message)
        QMessageBox.critical(self, "PickerRoy 无法完成分析", f"{message}\n\n详细信息已保存到：\n{self.log_path}")

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

    def export_selected(self) -> None:
        selected = [item for item in self._visible_candidates() if self.feedback.get(item.id) in {"KEEP", "FAVORITE"}]
        if not selected:
            QMessageBox.information(self, "尚未选择画面", "请先把需要导出的画面标记为“保留”或“收藏”。")
            return
        destination = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not destination:
            return
        format_box = QMessageBox(self)
        format_box.setWindowTitle("选择导出格式")
        format_box.setText("请选择原始分辨率的图片格式。")
        png_button = format_box.addButton("PNG", QMessageBox.ButtonRole.AcceptRole)
        jpg_button = format_box.addButton("JPEG", QMessageBox.ButtonRole.AcceptRole)
        format_box.addButton(QMessageBox.StandardButton.Cancel)
        format_box.exec()
        clicked = format_box.clickedButton()
        if clicked not in {png_button, jpg_button}:
            return
        image_format = "PNG" if clicked is png_button else "JPEG"
        by_video: dict[str, list[Candidate]] = defaultdict(list)
        for item in selected:
            by_video[item.video_id].append(item)
        outputs = []
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for result in self.results:
                if result.video.id in by_video:
                    outputs.extend(export_candidates(result.video, by_video[result.video.id], destination, image_format))
        except Exception as exc:
            LOGGER.exception("导出失败")
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        finally:
            QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "导出完成", f"已导出 {len(outputs)} 张原始分辨率画面。")

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
        self.preference_status.setText(f"同一镜头 · {a.timestamp:.2f} 秒 对比 {b.timestamp:.2f} 秒")

    def choose_preference(self, side: str) -> None:
        if not self.current_pair:
            return
        a, b = self.current_pair
        self.store.record_preference(a, b, a if side == "A" else b)
        self.next_pair()


def data_directory() -> Path:
    override = os.environ.get("PICKERROY_DATA_DIR") or os.environ.get("FRAMEPICK_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    from PySide6.QtCore import QStandardPaths

    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
