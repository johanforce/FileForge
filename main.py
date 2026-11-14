from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QFileInfo, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFileIconProvider,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QPlainTextEdit,
    QLineEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fileforge.archive import create_zip
from fileforge.extraction import extract_archives
from fileforge.images import SUPPORTED_IMAGE_EXTENSIONS, convert_images
from fileforge.text_utils import process_text


STYLE = """
QMainWindow, QWidget {
    background: #10131a;
    color: #edf0f7;
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
}
QFrame#Panel {
    background: #171d28;
    border: 1px solid #293244;
    border-radius: 16px;
}
QFrame#DropArea {
    background: #151b27;
    border: 1px dashed #53617a;
    border-radius: 15px;
}
QFrame#DropArea[dragActive="true"] {
    background: #20253c;
    border: 2px dashed #8c83ff;
}
QLabel#Brand {
    font-size: 23px;
    font-weight: 750;
    color: #ffffff;
}
QLabel#Muted {
    color: #929db0;
}
QLabel#Section {
    font-size: 15px;
    font-weight: 700;
}
QLabel#DropTitle {
    font-size: 16px;
    font-weight: 650;
}
QPushButton {
    background: #252e3e;
    border: 1px solid #354158;
    border-radius: 9px;
    padding: 9px 15px;
    color: #edf2fa;
    font-weight: 600;
}
QPushButton:hover {
    background: #303d52;
    border-color: #53627d;
}
QPushButton#Primary {
    background: #7066ed;
    border: 0;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    padding: 11px 22px;
}
QPushButton#Primary:hover {
    background: #8178f5;
}
QPushButton:disabled {
    color: #687386;
    background: #202633;
    border-color: #2b3444;
}
QComboBox {
    background: #202838;
    border: 1px solid #354158;
    border-radius: 9px;
    padding: 9px 12px;
    min-width: 125px;
    color: #edf2fa;
}
QComboBox:hover {
    border-color: #65738e;
}
QComboBox QAbstractItemView {
    background: #202838;
    color: #edf2fa;
    selection-background-color: #5149a8;
}
QTabWidget::pane {
    border: 0;
    border-bottom: 1px solid #293244;
}
QTabBar::tab {
    background: transparent;
    color: #929db0;
    padding: 10px 18px;
    margin-right: 5px;
    border-bottom: 2px solid transparent;
    font-weight: 650;
}
QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid #8178f5;
}
QTabBar::tab:hover {
    color: #ffffff;
}
QTableWidget {
    background: #141a24;
    alternate-background-color: #181f2b;
    border: 0;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #34345a;
    selection-color: #ffffff;
    outline: 0;
}
QHeaderView::section {
    background: #202838;
    color: #929db0;
    padding: 10px 12px;
    border: 0;
    font-size: 10px;
    font-weight: 700;
}
QTableWidget::item {
    padding: 7px 10px;
    border: 0;
}
QPlainTextEdit, QTreeWidget {
    background: #141a24;
    border: 1px solid #293244;
    border-radius: 10px;
    padding: 8px;
    selection-background-color: #34345a;
    selection-color: #ffffff;
    font-family: 'SF Mono', 'Menlo', monospace;
    font-size: 12px;
}
QTreeWidget::item {
    padding: 5px 4px;
}
QProgressBar {
    background: #252e3e;
    border: 0;
    border-radius: 5px;
    height: 9px;
    color: transparent;
}
QProgressBar::chunk {
    background: #8178f5;
    border-radius: 5px;
}
QSlider::groove:horizontal {
    background: #252e3e;
    height: 5px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #8178f5;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
"""


COMPRESSION_OPTIONS = {
    "Nhanh nhất": "Fast",
    "Cân bằng": "Balanced",
    "Nén tối đa": "Best",
}
IMAGE_FILTER = "Ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)"
ZIP_FILTER = "Tệp ZIP (*.zip)"


class TaskWorker(QThread):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        mode: str,
        paths: list[str],
        destination: str,
        compression: str = "Balanced",
        output_format: str = "JPG",
        quality: int = 90,
    ):
        super().__init__()
        self.mode = mode
        self.paths = paths
        self.destination = destination
        self.compression = compression
        self.output_format = output_format
        self.quality = quality

    def run(self):
        try:
            if self.mode == "zip":
                result = create_zip(
                    self.paths,
                    self.destination,
                    self.compression,
                    lambda done, total, name: self.progress.emit(done, total, name),
                )
                self.completed.emit({"mode": "zip", "path": str(result)})
            elif self.mode == "extract":
                outputs, errors = extract_archives(
                    self.paths,
                    self.destination,
                    lambda done, total, name: self.progress.emit(done, total, name),
                )
                self.completed.emit({
                    "mode": "extract",
                    "outputs": [str(path) for path in outputs],
                    "errors": errors,
                })
            elif self.mode == "image":
                outputs, errors = convert_images(
                    self.paths,
                    self.destination,
                    self.output_format,
                    self.quality,
                    lambda done, total, name: self.progress.emit(done, total, name),
                )
                self.completed.emit({
                    "mode": "image",
                    "outputs": [str(path) for path in outputs],
                    "errors": errors,
                })
            else:
                raise ValueError("Tác vụ không hợp lệ.")
        except Exception as exc:
            self.failed.emit(str(exc))


class TextTaskWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        operation: str,
        text: str,
        class_name: str,
        model_target: str,
    ):
        super().__init__()
        self.operation = operation
        self.text = text
        self.class_name = class_name
        self.model_target = model_target

    def run(self):
        try:
            result = process_text(
                self.operation,
                self.text,
                self.class_name,
                self.model_target,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class JSONTreeWidget(QTreeWidget):
    """Lazy JSON tree: nested objects are expanded only when the user opens them."""

    MAX_CHILDREN_PER_NODE = 300
    LAZY_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(["TRƯỜNG", "GIÁ TRỊ"])
        self.setColumnWidth(0, 180)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.itemExpanded.connect(self._populate_item)

    @staticmethod
    def _is_container(value) -> bool:
        return isinstance(value, (dict, list))

    @staticmethod
    def _preview(value) -> str:
        if isinstance(value, dict):
            return f"{{ {len(value)} mục }}"
        if isinstance(value, list):
            return f"[ {len(value)} mục ]"
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        text = str(value)
        if isinstance(value, str):
            text = '"' + text + '"'
        if len(text) > 100:
            text = text[:97] + "…"
        return text

    def _add_lazy_marker(self, item: QTreeWidgetItem):
        item.setData(0, self.LAZY_ROLE, True)
        marker = QTreeWidgetItem(["", ""])
        item.addChild(marker)

    def set_json(self, value):
        self.clear()
        root = QTreeWidgetItem(["$", self._preview(value)])
        root.setData(0, Qt.ItemDataRole.UserRole, value)
        self.addTopLevelItem(root)
        if self._is_container(value) and value:
            self._add_lazy_marker(root)
            root.setExpanded(True)
        self.expandToDepth(0)

    def _populate_item(self, item: QTreeWidgetItem):
        if not item.data(0, self.LAZY_ROLE):
            return

        value = item.data(0, Qt.ItemDataRole.UserRole)
        item.setData(0, self.LAZY_ROLE, False)
        while item.childCount():
            item.takeChild(0)

        if isinstance(value, dict):
            values = list(value.items())
        elif isinstance(value, list):
            values = [(f"[{index}]", child) for index, child in enumerate(value)]
        else:
            return

        shown = values[: self.MAX_CHILDREN_PER_NODE]
        for key, child_value in shown:
            child = QTreeWidgetItem([str(key), self._preview(child_value)])
            child.setData(0, Qt.ItemDataRole.UserRole, child_value)
            if self._is_container(child_value) and child_value:
                self._add_lazy_marker(child)
            item.addChild(child)

        remaining = len(values) - len(shown)
        if remaining:
            more = QTreeWidgetItem(["…", f"Còn {remaining} mục"])
            more.setDisabled(True)
            item.addChild(more)


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("DropArea")
        self.setMinimumHeight(96)
        self.setProperty("dragActive", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel()
        self.title.setObjectName("DropTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel()
        self.hint.setObjectName("Muted")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        self.set_instruction(
            "Kéo thả tệp hoặc thư mục vào đây",
            "Có thể chọn nhiều tệp cùng lúc",
        )

    def set_instruction(self, title: str, hint: str):
        self.title.setText(title)
        self.hint.setText(hint)

    def _set_drag_active(self, active: bool):
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        self._set_drag_active(False)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileForge")
        self.resize(1040, 740)
        self.setMinimumSize(860, 620)

        self.paths: list[str] = []
        self.worker: TaskWorker | None = None
        self.busy = False
        self.icon_provider = QFileIconProvider()
        self.mode = "zip"
        self.text_worker: TextTaskWorker | None = None
        self.text_busy = False

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(14)

        header = QHBoxLayout()
        brand = QLabel("✦  FileForge")
        brand.setObjectName("Brand")
        header.addWidget(brand)
        header.addStretch()

        self.add_files_btn = QPushButton("＋  Thêm tệp")
        self.add_files_btn.clicked.connect(self.choose_files)
        self.add_folder_btn = QPushButton("＋  Thêm thư mục")
        self.add_folder_btn.clicked.connect(self.choose_folder)
        header.addWidget(self.add_files_btn)
        header.addWidget(self.add_folder_btn)
        outer.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(QWidget(), "Nén ZIP")
        self.tabs.addTab(QWidget(), "Giải nén")
        self.tabs.addTab(QWidget(), "Chuyển ảnh")
        self.tabs.addTab(QWidget(), "JSON / XML")
        self.tabs.currentChanged.connect(self.on_mode_changed)
        outer.addWidget(self.tabs)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_paths)
        outer.addWidget(self.drop_area)

        queue_panel = QFrame()
        queue_panel.setObjectName("Panel")
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(16, 14, 16, 14)
        queue_layout.setSpacing(11)

        queue_header = QHBoxLayout()
        section = QLabel("Tệp đã chọn")
        section.setObjectName("Section")
        queue_header.addWidget(section)

        self.queue_summary = QLabel("0 tệp  ·  0 B")
        self.queue_summary.setObjectName("Muted")
        queue_header.addWidget(self.queue_summary)
        queue_header.addStretch()

        self.remove_btn = QPushButton("Xóa mục chọn")
        self.remove_btn.clicked.connect(self.remove_selected)
        queue_header.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("Xóa tất cả")
        self.clear_btn.clicked.connect(self.clear_queue)
        queue_header.addWidget(self.clear_btn)
        queue_layout.addLayout(queue_header)

        self.queue_stack = QStackedWidget()
        empty_state = QWidget()
        empty_layout = QVBoxLayout(empty_state)
        empty_layout.setContentsMargins(8, 24, 8, 24)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label = QLabel("Danh sách đang trống")
        self.empty_label.setObjectName("Muted")
        empty_layout.addWidget(self.empty_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.queue_stack.addWidget(empty_state)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["TÊN TỆP", "DUNG LƯỢNG"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(190)
        self.table.itemSelectionChanged.connect(self.update_controls)
        self.queue_stack.addWidget(self.table)
        queue_layout.addWidget(self.queue_stack, 1)
        outer.addWidget(queue_panel, 1)
        self.queue_panel = queue_panel

        action_panel = QFrame()
        action_panel.setObjectName("Panel")
        action_layout = QVBoxLayout(action_panel)
        action_layout.setContentsMargins(16, 13, 16, 13)
        action_layout.setSpacing(10)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.compression_label = QLabel("Mức nén")
        self.compression_label.setObjectName("Muted")
        controls.addWidget(self.compression_label)

        self.compression = QComboBox()
        self.compression.addItems(list(COMPRESSION_OPTIONS.keys()))
        self.compression.setCurrentText("Cân bằng")
        controls.addWidget(self.compression)

        self.extract_hint = QLabel("Mỗi tệp ZIP sẽ được giải nén vào một thư mục riêng")
        self.extract_hint.setObjectName("Muted")
        controls.addWidget(self.extract_hint)

        self.format_label = QLabel("Định dạng")
        self.format_label.setObjectName("Muted")
        controls.addWidget(self.format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPG", "PNG", "WEBP"])
        self.format_combo.setCurrentText("JPG")
        self.format_combo.currentTextChanged.connect(self.update_quality_state)
        controls.addWidget(self.format_combo)

        self.quality_label = QLabel("Chất lượng")
        self.quality_label.setObjectName("Muted")
        controls.addWidget(self.quality_label)

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(50, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setFixedWidth(105)
        self.quality_slider.valueChanged.connect(
            lambda value: self.quality_value.setText(f"{value}%")
        )
        controls.addWidget(self.quality_slider)

        self.quality_value = QLabel("90%")
        self.quality_value.setMinimumWidth(34)
        self.quality_value.setObjectName("Muted")
        controls.addWidget(self.quality_value)

        controls.addStretch()

        self.action_button = QPushButton("Tạo tệp ZIP  →")
        self.action_button.setObjectName("Primary")
        self.action_button.setMinimumWidth(185)
        self.action_button.clicked.connect(self.run_action)
        controls.addWidget(self.action_button)
        action_layout.addLayout(controls)

        self.progress_area = QWidget()
        progress_layout = QVBoxLayout(self.progress_area)
        progress_layout.setContentsMargins(0, 2, 0, 0)
        progress_layout.setSpacing(5)
        self.progress_text = QLabel("Đang chuẩn bị…")
        self.progress_text.setObjectName("Muted")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        progress_layout.addWidget(self.progress_text)
        progress_layout.addWidget(self.progress)
        action_layout.addWidget(self.progress_area)
        self.progress_area.hide()

        outer.addWidget(action_panel)
        self.action_panel = action_panel

        self.text_panel = self.build_text_panel()
        outer.addWidget(self.text_panel, 1)
        self.text_panel.hide()

        self.on_mode_changed(0)
        self.refresh_queue()

    def _build_text_pane(self, title: str, placeholder: str, read_only: bool):
        pane = QFrame()
        pane.setObjectName("Panel")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(12, 11, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("Section")
        header.addWidget(title_label)
        header.addStretch()

        text_button = QPushButton("Văn bản")
        tree_button = QPushButton("Cấu trúc")
        tree_button.setEnabled(False)
        header.addWidget(text_button)
        header.addWidget(tree_button)
        layout.addLayout(header)

        stack = QStackedWidget()
        editor = QPlainTextEdit()
        editor.setPlaceholderText(placeholder)
        editor.setReadOnly(read_only)
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        editor.setTabStopDistance(28)
        tree = JSONTreeWidget()
        stack.addWidget(editor)
        stack.addWidget(tree)
        layout.addWidget(stack, 1)

        text_button.clicked.connect(lambda: stack.setCurrentIndex(0))
        tree_button.clicked.connect(lambda: stack.setCurrentIndex(1))

        return {
            "widget": pane,
            "stack": stack,
            "editor": editor,
            "tree": tree,
            "text_button": text_button,
            "tree_button": tree_button,
        }

    def build_text_panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        operation_label = QLabel("Chức năng")
        operation_label.setObjectName("Muted")
        toolbar.addWidget(operation_label)

        self.text_operation = QComboBox()
        operations = [
            ("JSON → Chuỗi", "json_to_string"),
            ("Chuỗi → JSON", "string_to_json"),
            ("Định dạng JSON", "format_json"),
            ("XML → Chuỗi", "xml_to_string"),
            ("Chuỗi → XML", "string_to_xml"),
            ("JSON → Model", "json_to_model"),
        ]
        for label, operation in operations:
            self.text_operation.addItem(label, operation)
        self.text_operation.currentIndexChanged.connect(
            self.update_text_model_controls
        )
        toolbar.addWidget(self.text_operation, 2)

        self.text_model_label = QLabel("Model")
        self.text_model_label.setObjectName("Muted")
        toolbar.addWidget(self.text_model_label)

        self.text_model_target = QComboBox()
        self.text_model_target.addItem("Python dataclass", "dataclass")
        self.text_model_target.addItem("Pydantic v2", "pydantic")
        self.text_model_target.addItem("TypeScript", "typescript")
        toolbar.addWidget(self.text_model_target, 1)

        self.text_class_label = QLabel("Tên lớp")
        self.text_class_label.setObjectName("Muted")
        toolbar.addWidget(self.text_class_label)

        self.text_class_name = QLineEdit("RootModel")
        self.text_class_name.setPlaceholderText("RootModel")
        self.text_class_name.setMaximumWidth(145)
        toolbar.addWidget(self.text_class_name)

        self.text_execute_btn = QPushButton("Thực hiện  →")
        self.text_execute_btn.setObjectName("Primary")
        self.text_execute_btn.clicked.connect(self.run_text_action)
        toolbar.addWidget(self.text_execute_btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.input_pane = self._build_text_pane(
            "ĐẦU VÀO",
            'Dán JSON hoặc XML vào đây…\\n\\nVí dụ JSON:\\n{\\n  "name": "FileForge",\\n  "active": true\\n}',
            False,
        )
        self.output_pane = self._build_text_pane(
            "KẾT QUẢ",
            "Kết quả sẽ hiển thị ở đây…",
            True,
        )

        splitter.addWidget(self.input_pane["widget"])
        splitter.addWidget(self.output_pane["widget"])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, 1)

        self.input_editor = self.input_pane["editor"]
        self.input_tree = self.input_pane["tree"]
        self.input_tree_button = self.input_pane["tree_button"]
        self.input_editor.textChanged.connect(self.invalidate_input_tree)

        self.output_editor = self.output_pane["editor"]
        self.output_tree = self.output_pane["tree"]
        self.output_tree_button = self.output_pane["tree_button"]

        footer = QHBoxLayout()
        self.text_status = QLabel("Sẵn sàng")
        self.text_status.setObjectName("Muted")
        footer.addWidget(self.text_status)
        footer.addStretch()

        self.text_copy_btn = QPushButton("Sao chép kết quả")
        self.text_copy_btn.setEnabled(False)
        self.text_copy_btn.clicked.connect(self.copy_text_result)
        footer.addWidget(self.text_copy_btn)

        self.text_progress = QProgressBar()
        self.text_progress.setRange(0, 0)
        self.text_progress.setFixedWidth(120)
        self.text_progress.hide()
        footer.addWidget(self.text_progress)

        layout.addLayout(footer)
        self.update_text_model_controls()
        return panel

    def update_text_model_controls(self):
        is_model = self.text_operation.currentData() == "json_to_model"
        self.text_model_label.setVisible(is_model)
        self.text_model_target.setVisible(is_model)
        self.text_class_label.setVisible(is_model)
        self.text_class_name.setVisible(is_model)

    def invalidate_input_tree(self):
        self.input_tree_button.setEnabled(False)
        self.input_tree.clear()
        if self.input_pane["stack"].currentIndex() == 1:
            self.input_pane["stack"].setCurrentIndex(0)
        self.text_status.setText("Nội dung đã thay đổi · hãy thực hiện lại để xem cấu trúc")

    def run_text_action(self):
        if self.text_busy:
            return

        source = self.input_editor.toPlainText()
        if not source.strip():
            QMessageBox.information(
                self, "Chưa có dữ liệu", "Dán JSON hoặc XML vào ô đầu vào trước."
            )
            return

        operation = self.text_operation.currentData()
        class_name = self.text_class_name.text().strip() or "RootModel"
        model_target = self.text_model_target.currentData()

        self.text_busy = True
        self.tabs.setEnabled(False)
        self.text_execute_btn.setEnabled(False)
        self.text_copy_btn.setEnabled(False)
        self.input_editor.setReadOnly(True)
        self.text_progress.show()
        self.text_status.setText("Đang xử lý trong luồng nền…")

        self.text_worker = TextTaskWorker(
            operation,
            source,
            class_name,
            model_target,
        )
        self.text_worker.completed.connect(self.on_text_completed)
        self.text_worker.failed.connect(self.on_text_failed)
        self.text_worker.start()

    def on_text_completed(self, result: dict):
        self.text_busy = False
        self.tabs.setEnabled(True)
        self.text_execute_btn.setEnabled(True)
        self.input_editor.setReadOnly(False)
        self.text_progress.hide()

        self.output_editor.setPlainText(result["output"])

        input_valid = result.get("input_json_valid", False)
        output_valid = result.get("output_json_valid", False)

        if input_valid:
            self.input_tree.set_json(result["input_json"])
            self.input_tree_button.setEnabled(True)
        else:
            self.input_tree.clear()
            self.input_tree_button.setEnabled(False)
            self.input_pane["stack"].setCurrentIndex(0)

        if output_valid:
            self.output_tree.set_json(result["output_json"])
            self.output_tree_button.setEnabled(True)
        else:
            self.output_tree.clear()
            self.output_tree_button.setEnabled(False)
            self.output_pane["stack"].setCurrentIndex(0)

        if result.get("output_kind") == "json":
            self.output_pane["stack"].setCurrentIndex(1)
        else:
            self.output_pane["stack"].setCurrentIndex(0)

        size = len(self.input_editor.toPlainText())
        self.text_status.setText(f"Hoàn tất · {size:,} ký tự đầu vào")
        self.text_execute_btn.setEnabled(True)
        self.text_copy_btn.setEnabled(bool(result["output"]))

    def on_text_failed(self, message: str):
        self.text_busy = False
        self.tabs.setEnabled(True)
        self.text_execute_btn.setEnabled(True)
        self.input_editor.setReadOnly(False)
        self.text_progress.hide()
        self.text_status.setText("Không thể xử lý · kiểm tra dữ liệu đầu vào")
        QMessageBox.warning(
            self,
            "Dữ liệu chưa hợp lệ",
            "Không thể xử lý nội dung. Kiểm tra cú pháp JSON/XML rồi thử lại.\\n\\n"
            + message,
        )

    def copy_text_result(self):
        value = self.output_editor.toPlainText()
        if not value:
            return
        QApplication.clipboard().setText(value)
        self.text_status.setText("Đã sao chép kết quả")

    @staticmethod
    def format_size(size: int) -> str:
        amount = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if amount < 1024 or unit == "TB":
                return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
            amount /= 1024
        return f"{amount:.1f} TB"

    def current_paths(self) -> list[str]:
        if self.mode == "extract":
            return [path for path in self.paths if Path(path).suffix.lower() == ".zip"]
        if self.mode == "image":
            return [
                path for path in self.paths
                if Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ]
        return list(self.paths)

    def on_mode_changed(self, index: int):
        if index == 3:
            self.mode = "text"
            self.add_files_btn.hide()
            self.add_folder_btn.hide()
            self.drop_area.hide()
            self.queue_panel.hide()
            self.action_panel.hide()
            self.text_panel.show()
            return

        self.text_panel.hide()
        self.add_files_btn.show()
        self.add_folder_btn.show()
        self.drop_area.show()
        self.queue_panel.show()
        self.action_panel.show()
        self.mode = ("zip", "extract", "image")[index]

        if self.mode == "zip":
            self.add_files_btn.setText("＋  Thêm tệp")
            self.drop_area.set_instruction(
                "Kéo thả tệp hoặc thư mục vào đây",
                "Thêm nhiều tệp để gom vào một tệp ZIP",
            )
            self.compression_label.show()
            self.compression.show()
            self.extract_hint.hide()
            self.format_label.hide()
            self.format_combo.hide()
            self.quality_label.hide()
            self.quality_slider.hide()
            self.quality_value.hide()
            self.action_button.setText("Tạo tệp ZIP  →")
            self.empty_label.setText("Thêm tệp để bắt đầu nén")
        elif self.mode == "extract":
            self.add_files_btn.setText("＋  Chọn ZIP")
            self.drop_area.set_instruction(
                "Kéo thả tệp ZIP vào đây",
                "Có thể giải nén nhiều tệp ZIP cùng lúc",
            )
            self.compression_label.hide()
            self.compression.hide()
            self.extract_hint.show()
            self.format_label.hide()
            self.format_combo.hide()
            self.quality_label.hide()
            self.quality_slider.hide()
            self.quality_value.hide()
            self.action_button.setText("Giải nén ZIP  →")
            self.empty_label.setText("Chọn một hoặc nhiều tệp ZIP")
        else:
            self.add_files_btn.setText("＋  Chọn ảnh")
            self.drop_area.set_instruction(
                "Kéo thả ảnh vào đây",
                "Hỗ trợ PNG, JPG, WEBP, BMP và TIFF",
            )
            self.compression_label.hide()
            self.compression.hide()
            self.extract_hint.hide()
            self.format_label.show()
            self.format_combo.show()
            self.quality_label.show()
            self.quality_slider.show()
            self.quality_value.show()
            self.action_button.setText("Chuyển đổi ảnh  →")
            self.empty_label.setText("Chọn ảnh cần chuyển đổi")

        self.update_quality_state()
        self.progress_area.hide()
        self.refresh_queue()

    def update_quality_state(self):
        enabled = self.mode == "image" and self.format_combo.currentText() != "PNG"
        self.quality_label.setEnabled(enabled)
        self.quality_slider.setEnabled(enabled)
        self.quality_value.setEnabled(enabled)

    def add_paths(self, paths: list[str]):
        for raw in paths:
            path = Path(raw).expanduser()
            if not path.exists():
                continue

            if path.is_file():
                candidates = [path]
            elif path.is_dir():
                candidates = [item for item in path.rglob("*") if item.is_file()]
            else:
                continue

            for candidate in candidates:
                value = str(candidate.resolve())
                if value not in self.paths:
                    self.paths.append(value)

        self.refresh_queue()

    def choose_files(self):
        if self.mode == "extract":
            file_filter = ZIP_FILTER
            title = "Chọn tệp ZIP"
        elif self.mode == "image":
            file_filter = IMAGE_FILTER
            title = "Chọn ảnh"
        else:
            file_filter = "Tất cả tệp (*)"
            title = "Chọn tệp"

        files, _ = QFileDialog.getOpenFileNames(
            self, title, str(Path.home()), file_filter
        )
        if files:
            self.add_paths(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục", str(Path.home())
        )
        if folder:
            self.add_paths([folder])

    def refresh_queue(self):
        visible_paths = self.current_paths()
        self.table.setRowCount(0)
        total_size = 0
        valid_paths: list[str] = []

        for raw in visible_paths:
            path = Path(raw)
            try:
                if not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(path.name)
            name_item.setIcon(self.icon_provider.icon(QFileInfo(str(path))))
            name_item.setToolTip(str(path))
            name_item.setData(Qt.ItemDataRole.UserRole, str(path))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            size_item = QTableWidgetItem(self.format_size(size))
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, size_item)
            valid_paths.append(str(path))
            total_size += size

        self.queue_summary.setText(
            f"{len(valid_paths)} tệp  ·  {self.format_size(total_size)}"
        )
        self.queue_stack.setCurrentIndex(1 if valid_paths else 0)
        self.update_controls()

    def update_controls(self):
        has_files = bool(self.current_paths())
        has_selection = bool(self.table.selectionModel().selectedRows())
        self.remove_btn.setEnabled(has_selection and not self.busy)
        self.clear_btn.setEnabled(bool(self.paths) and not self.busy)
        self.action_button.setEnabled(has_files and not self.busy)

    def set_busy(self, busy: bool):
        self.busy = busy
        self.tabs.setEnabled(not busy)
        self.add_files_btn.setEnabled(not busy)
        self.add_folder_btn.setEnabled(not busy)
        self.compression.setEnabled(not busy and self.mode == "zip")
        self.format_combo.setEnabled(not busy and self.mode == "image")
        self.quality_slider.setEnabled(
            not busy and self.mode == "image" and self.format_combo.currentText() != "PNG"
        )
        self.table.setEnabled(not busy)
        self.update_controls()

    def remove_selected(self):
        selected_paths = set()
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 0)
            if item:
                selected_paths.add(item.data(Qt.ItemDataRole.UserRole))
        self.paths = [path for path in self.paths if path not in selected_paths]
        self.refresh_queue()

    def clear_queue(self):
        if self.busy:
            return
        self.paths.clear()
        self.refresh_queue()
        self.progress_area.hide()
        self.progress.setValue(0)

    def run_action(self):
        if self.busy:
            return
        paths = self.current_paths()
        if not paths:
            QMessageBox.information(self, "Chưa có tệp", "Hãy thêm tệp trước khi tiếp tục.")
            return

        compression = "Balanced"
        output_format = "JPG"
        quality = self.quality_slider.value()

        if self.mode == "zip":
            destination, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu tệp ZIP",
                str(Path.home() / "FileForge.zip"),
                ZIP_FILTER,
            )
            if not destination:
                return
            if not destination.lower().endswith(".zip"):
                destination += ".zip"
            compression = COMPRESSION_OPTIONS[self.compression.currentText()]
        elif self.mode == "extract":
            destination = QFileDialog.getExistingDirectory(
                self, "Chọn nơi giải nén", str(Path.home())
            )
            if not destination:
                return
        else:
            destination = QFileDialog.getExistingDirectory(
                self, "Chọn thư mục lưu ảnh", str(Path.home())
            )
            if not destination:
                return
            output_format = self.format_combo.currentText()

        self.set_busy(True)
        self.progress_area.show()
        self.progress.setValue(0)
        self.progress_text.setText("Đang chuẩn bị…")

        self.worker = TaskWorker(
            self.mode,
            paths,
            destination,
            compression,
            output_format,
            quality,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.completed.connect(self.on_completed)
        self.worker.failed.connect(self.on_failure)
        self.worker.finished.connect(lambda: self.set_busy(False))
        self.worker.start()

    def on_progress(self, done: int, total: int, name: str):
        percent = int(done * 100 / total) if total else 100
        self.progress.setValue(percent)
        if self.mode == "zip":
            prefix = "Đang nén"
        elif self.mode == "extract":
            prefix = "Đang giải nén"
        else:
            prefix = "Đang chuyển đổi"
        self.progress_text.setText(f"{prefix}: {name}")

    def show_result(self, title: str, message: str, folder: str, details: str = ""):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if details:
            dialog.setDetailedText(details)
        open_folder_btn = dialog.addButton(
            "Mở thư mục", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton("Đóng", QMessageBox.ButtonRole.AcceptRole)
        dialog.exec()
        if dialog.clickedButton() == open_folder_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def on_completed(self, result: dict):
        self.progress.setValue(100)
        mode = result["mode"]

        if mode == "zip":
            path = Path(result["path"])
            self.progress_text.setText("Đã tạo tệp ZIP")
            self.show_result(
                "Hoàn tất",
                "Tệp ZIP đã được tạo thành công.",
                str(path.parent),
                path.name,
            )
            return

        outputs = result["outputs"]
        errors = result["errors"]
        output_count = len(outputs)
        error_count = len(errors)

        if mode == "extract":
            self.progress_text.setText("Đã hoàn tất giải nén")
            title = "Hoàn tất giải nén"
            message = f"Đã giải nén thành công {output_count} tệp ZIP."
            folder = str(Path(outputs[0]).parent) if outputs else str(Path.home())
        else:
            self.progress_text.setText("Đã hoàn tất chuyển đổi")
            title = "Hoàn tất chuyển đổi"
            message = f"Đã chuyển đổi thành công {output_count} ảnh."
            folder = str(Path(outputs[0]).parent) if outputs else str(Path.home())

        details = ""
        if error_count:
            details = "\n".join(
                f"{Path(path).name}: {message}"
                for path, message in errors[:10]
            )
            if error_count > 10:
                details += f"\n… và {error_count - 10} lỗi khác."
        if not output_count:
            QMessageBox.warning(
                self,
                "Không có tệp được xử lý",
                "Không có tệp nào được xử lý thành công.",
            )
            if details:
                QMessageBox.information(self, "Chi tiết lỗi", details)
            return
        if error_count:
            message += f"\nBỏ qua {error_count} tệp bị lỗi."
        self.show_result(title, message, folder, details)

    def on_failure(self, message: str):
        self.progress_text.setText("Tác vụ không thành công")
        QMessageBox.critical(
            self, "Có lỗi xảy ra", f"Không thể hoàn thành tác vụ.\n\n{message}"
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("SF Pro Display", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
