from __future__ import annotations

import difflib
import html
import re
import sys
from pathlib import Path

from PySide6.QtCore import QFileInfo, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QFont, QColor, QPainter, QPen, QSyntaxHighlighter, QTextCharFormat, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QCheckBox,
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
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QPlainTextEdit,
    QLineEdit,
    QListView,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from fileforge.archive import create_zip
from fileforge.extraction import extract_archives
from fileforge.images import SUPPORTED_IMAGE_EXTENSIONS, convert_images
from fileforge.text_utils import process_text
from fileforge.compare import compare_text, compare_json, format_text_diff_report
from fileforge.curl_utils import parse_http_request


STYLE = """
QMainWindow, QWidget { background: #f6f8fc; color: #202124; font-family: "Google Sans", "Segoe UI", sans-serif; font-size: 14px; }
QFrame#Panel { background: #ffffff; border: 1px solid #e3e7ef; border-radius: 16px; }
QFrame#DropArea { background: #f8faff; border: 1px dashed #9aaecb; border-radius: 15px; }
QFrame#DropArea[dragActive="true"] { background: #e8f0fe; border: 2px dashed #1a73e8; }
QLabel#Brand { font-size: 24px; font-weight: 750; color: #202124; }
QLabel#Muted { color: #5f6368; }
QLabel#Section { font-size: 15px; font-weight: 700; color: #202124; }
QLabel#DropTitle { font-size: 16px; font-weight: 650; color: #202124; }
QPushButton { background: #f1f3f4; border: 1px solid #dadce0; border-radius: 10px; padding: 9px 15px; color: #202124; font-weight: 600; }
QPushButton:hover { background: #e8eaed; border-color: #bdc1c6; }
QPushButton#Primary { background: #1a73e8; border: 0; color: #ffffff; font-size: 14px; font-weight: 700; padding: 11px 22px; }
QPushButton#Primary:hover { background: #1765cc; }
QPushButton:disabled { color: #9aa0a6; background: #f8f9fa; border-color: #e8eaed; }
QLineEdit { background: #ffffff; border: 1px solid #dadce0; border-radius: 10px; padding: 9px 12px; min-width: 110px; color: #202124; selection-background-color: #d2e3fc; selection-color: #174ea6; }
QComboBox {
    background: #ffffff;
    color: #202124;
    border: 1px solid #d7deea;
    border-radius: 12px;
    min-height: 40px;
    min-width: 112px;
    padding: 0 44px 0 14px;
    font-weight: 600;
    selection-background-color: #d2e3fc;
    selection-color: #174ea6;
}
QComboBox:hover { border-color: #8ab4f8; background: #fbfdff; }
QComboBox:focus, QComboBox:on { border: 1px solid #1a73e8; background: #ffffff; }
QComboBox:disabled { color: #9aa0a6; background: #f8f9fa; border-color: #e8eaed; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 38px;
    border: 0;
    border-left: 1px solid #edf0f5;
    border-top-right-radius: 11px;
    border-bottom-right-radius: 11px;
    background: transparent;
}
QComboBox::drop-down:hover { background: #f1f6ff; }
/* The arrow is painted by StyledComboBox so it renders consistently on Windows. */
QComboBox::down-arrow { image: none; width: 0px; height: 0px; }
QFrame#ComboPopupContainer {
    background: #ffffff;
    border: 1px solid #dce3ed;
    border-radius: 12px;
}
QListView#ComboPopupView {
    background: transparent;
    color: #202124;
    border: none;
    padding: 6px;
    outline: 0;
    selection-background-color: #e8f0fe;
    selection-color: #174ea6;
}
QListView#ComboPopupView::item {
    min-height: 22px;
    padding: 7px 12px;
    margin: 2px;
    border-radius: 7px;
}
QListView#ComboPopupView::item:hover { background: #f4f7fc; color: #174ea6; }
QListView#ComboPopupView::item:selected { background: #e8f0fe; color: #174ea6; font-weight: 700; }
QListView#ComboPopupView QScrollBar:vertical { width: 8px; background: transparent; margin: 4px 2px; }
QListView#ComboPopupView QScrollBar::handle:vertical { background: #c7d2e2; border-radius: 4px; min-height: 24px; }
QLineEdit:hover { border-color: #8ab4f8; }
QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #1a73e8; }
QTabWidget::pane { border: 0; border-bottom: 1px solid #e8eaed; }
QTabBar::tab { background: transparent; color: #5f6368; padding: 10px 18px; margin-right: 5px; border-bottom: 2px solid transparent; font-weight: 650; }
QTabBar::tab:selected { color: #1a73e8; border-bottom: 2px solid #1a73e8; }
QTabBar::tab:hover { color: #174ea6; }
QTableWidget { background: #ffffff; alternate-background-color: #f8fafd; border: 0; border-radius: 10px; gridline-color: transparent; selection-background-color: #e8f0fe; selection-color: #174ea6; outline: 0; }
QHeaderView::section { background: #f8f9fa; color: #5f6368; padding: 10px 12px; border: 0; font-size: 11px; font-weight: 700; }
QTableWidget::item { padding: 7px 10px; border: 0; }
QPlainTextEdit#CodeEditor { background: #1e1f22; border: 1px solid #34363b; border-radius: 10px; padding: 12px; color: #dfe1e5; selection-background-color: #214283; selection-color: #ffffff; font-family: "JetBrains Mono", "SFMono-Regular", "Menlo", "Consolas", monospace; font-size: 14px; }
QTextEdit#DiffOutput { background: #fbfcff; border: 1px solid #e1e5ec; border-radius: 10px; padding: 10px; color: #202124; selection-background-color: #d2e3fc; font-family: "SFMono-Regular", "Menlo", "Consolas", monospace; font-size: 12px; }
QTableWidget#DiffTable { background: #ffffff; alternate-background-color: #f8fafd; border: 1px solid #e1e5ec; border-radius: 10px; color: #202124; selection-background-color: #e8f0fe; selection-color: #174ea6; }
QCheckBox { spacing: 7px; color: #3c4043; }
QCheckBox::indicator { width: 17px; height: 17px; }
QCheckBox::indicator:checked { background: #1a73e8; border: 1px solid #1a73e8; border-radius: 4px; }
QCheckBox::indicator:unchecked { background: #ffffff; border: 1px solid #9aa0a6; border-radius: 4px; }
QTreeWidget { background: #fbfcff; alternate-background-color: #f3f6fb; border: 1px solid #e1e5ec; border-radius: 10px; padding: 8px; color: #202124; selection-background-color: #d2e3fc; selection-color: #174ea6; font-family: "Google Sans", "Segoe UI", sans-serif; font-size: 13px; }
QTreeWidget::item { padding: 6px 5px; }
QProgressBar { background: #e8eaed; border: 0; border-radius: 5px; height: 9px; color: transparent; }
QProgressBar::chunk { background: #1a73e8; border-radius: 5px; }
QSlider::groove:horizontal { background: #e8eaed; height: 5px; border-radius: 2px; }
QSlider::handle:horizontal { background: #1a73e8; width: 14px; margin: -5px 0; border-radius: 7px; }
"""


class StyledComboBox(QComboBox):
    """Combo box with a deterministic chevron and a rounded popup frame."""

    def __init__(self, parent=None):
        super().__init__(parent)
        popup = QListView()
        popup.setObjectName("ComboPopupView")
        popup.setFrameShape(QFrame.Shape.NoFrame)
        popup.setLineWidth(0)
        popup.setUniformItemSizes(True)
        popup.setMouseTracking(True)
        popup.setSpacing(1)
        popup.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        popup.setAutoFillBackground(False)
        popup.viewport().setAutoFillBackground(False)
        self.setView(popup)
        self.setMaxVisibleItems(10)
        self.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.setMinimumContentsLength(10)

        # QComboBox owns a separate QFrame for its popup. Style that frame,
        # rather than trying to round the scroll area's viewport itself.
        self._popup_container = popup.parentWidget()
        if self._popup_container is not None:
            self._popup_container.setObjectName("ComboPopupContainer")
            self._popup_container.setAttribute(
                Qt.WidgetAttribute.WA_StyledBackground, True
            )
            if isinstance(self._popup_container, QFrame):
                self._popup_container.setFrameShape(QFrame.Shape.NoFrame)

    def paintEvent(self, event):
        super().paintEvent(event)

        # Qt styles on Windows may ignore CSS border-based arrow shapes.
        # Draw a compact chevron ourselves after the native combo painting.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = "#1a73e8" if self.hasFocus() else "#5f6368"
        if not self.isEnabled():
            color = "#9aa0a6"
        painter.setPen(
            QPen(
                QColor(color),
                1.8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        center_x = self.width() - 19
        center_y = self.height() // 2
        if self.view().isVisible():
            painter.drawLine(center_x - 4, center_y + 2, center_x, center_y - 2)
            painter.drawLine(center_x, center_y - 2, center_x + 4, center_y + 2)
        else:
            painter.drawLine(center_x - 4, center_y - 2, center_x, center_y + 2)
            painter.drawLine(center_x, center_y + 2, center_x + 4, center_y - 2)
        painter.end()

    def showPopup(self):
        super().showPopup()
        self.update()

    def hidePopup(self):
        super().hidePopup()
        self.update()


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
        indent_size: int = 2,
    ):
        super().__init__()
        self.operation = operation
        self.text = text
        self.class_name = class_name
        self.model_target = model_target
        self.indent_size = indent_size

    def run(self):
        try:
            result = process_text(
                self.operation,
                self.text,
                self.class_name,
                self.model_target,
                self.indent_size,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class FoldablePlainTextEdit(QPlainTextEdit):
    foldRequested = Signal(int)

    def mousePressEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        block = cursor.block()
        line = block.text()
        marker = min((pos for pos in (line.find("▼ "), line.find("▶ ")) if pos >= 0), default=-1)
        if marker >= 0 and cursor.positionInBlock() <= marker + 1:
            self.foldRequested.emit(block.blockNumber())
            return
        super().mousePressEvent(event)


class JSONTreeWidget(QTreeWidget):
    """Lazy, paginated JSON tree that does not omit large object members."""

    MAX_CHILDREN_PER_PAGE = 300
    LAZY_ROLE = Qt.ItemDataRole.UserRole + 1
    MORE_ROLE = Qt.ItemDataRole.UserRole + 2
    PAGE_ROLE = Qt.ItemDataRole.UserRole + 3

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHeaderLabels(["TRƯỜNG", "GIÁ TRỊ"])
        self.setColumnWidth(0, 180)
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.itemExpanded.connect(self._populate_item)
        self.itemDoubleClicked.connect(self._load_more)

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
        item.addChild(QTreeWidgetItem(["", ""]))

    @staticmethod
    def _children(value):
        if isinstance(value, dict):
            return list(value.items())
        if isinstance(value, list):
            return [(f"[{index}]", child) for index, child in enumerate(value)]
        return []

    def set_json(self, value):
        self.clear()
        root = QTreeWidgetItem(["$", self._preview(value)])
        root.setData(0, Qt.ItemDataRole.UserRole, value)
        self.addTopLevelItem(root)
        if self._is_container(value) and value:
            self._add_lazy_marker(root)
            self._populate_item(root)
            root.setExpanded(True)
        self.expandToDepth(0)

    def _append_page(self, parent: QTreeWidgetItem, start: int):
        value = parent.data(0, Qt.ItemDataRole.UserRole)
        values = self._children(value)
        end = min(start + self.MAX_CHILDREN_PER_PAGE, len(values))

        for key, child_value in values[start:end]:
            child = QTreeWidgetItem([str(key), self._preview(child_value)])
            child.setData(0, Qt.ItemDataRole.UserRole, child_value)
            child.setForeground(0, QColor("#5f6368"))
            if isinstance(child_value, str):
                value_color = "#137333"
            elif isinstance(child_value, bool):
                value_color = "#9334e6"
            elif child_value is None:
                value_color = "#80868b"
            elif isinstance(child_value, (int, float)):
                value_color = "#1a73e8"
            else:
                value_color = "#b06000"
            child.setForeground(1, QColor(value_color))
            if self._is_container(child_value) and child_value:
                self._add_lazy_marker(child)
            parent.addChild(child)

        parent.setData(0, self.PAGE_ROLE, end)
        remaining = len(values) - end
        if remaining:
            next_count = min(self.MAX_CHILDREN_PER_PAGE, remaining)
            more = QTreeWidgetItem([
                f"Nạp thêm {next_count} mục",
                f"Còn {remaining} mục",
            ])
            more.setData(0, self.MORE_ROLE, True)
            more.setToolTip(0, "Nhấp đúp để nạp trang tiếp theo")
            more.setToolTip(1, "Các mục còn lại không bị loại khỏi dữ liệu")
            parent.addChild(more)

    def _populate_item(self, item: QTreeWidgetItem):
        if not item.data(0, self.LAZY_ROLE):
            return

        item.setData(0, self.LAZY_ROLE, False)
        while item.childCount():
            item.takeChild(0)
        self._append_page(item, 0)

    def _load_more(self, item: QTreeWidgetItem, _column: int = 0):
        if not item.data(0, self.MORE_ROLE):
            return

        parent = item.parent()
        if parent is None:
            return

        index = parent.indexOfChild(item)
        if index >= 0:
            parent.takeChild(index)

        start = parent.data(0, self.PAGE_ROLE) or 0
        self._append_page(parent, start)


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


class HTMLSyntaxHighlighter(QSyntaxHighlighter):
    """Lightweight HTML syntax highlighting for the result editor."""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        for pattern, color, bold in [
            (r"<!--.*?-->", "#80868b", False),
            (r"<!DOCTYPE[^>]*>", "#9334e6", True),
            (r"</?|/?>", "#5f6368", True),
            (r"\b[\w:-]+(?=\s*=)", "#137333", True),
            (r'"[^"]*"|\'[^\']*\'', "#b06000", False),
            (r"</?[\w:-]+", "#1a73e8", True),
        ]:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            self.rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class CodeSyntaxHighlighter(QSyntaxHighlighter):
    """Android Studio-inspired syntax colors for JSON and generated source."""

    def __init__(self, document, language: str):
        super().__init__(document)
        palette = {
            "keyword": "#CF8E6D", "type": "#56A8F5", "string": "#6AAB73",
            "number": "#2AACB8", "comment": "#7A7E85", "literal": "#C77DBB",
            "annotation": "#BBB529",
        }
        if language == "json":
            rules = [
                (r'"(?:[^"\\]|\\.)*"(?=\s*:)', "type", True),
                (r'"(?:[^"\\]|\\.)*"', "string", False),
                (r'\b(?:true|false|null)\b', "literal", True),
                (r'-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', "number", False),
            ]
        else:
            rules = [
                (r'//.*$|/\*.*?\*/', "comment", False),
                (r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', "string", False),
                (r'@[A-Za-z_][\w.]*', "annotation", False),
                (r'\b(?:class|public|private|protected|static|final|void|new|return|if|else|for|while|import|package|extends|implements|interface|data|val|var|fun|object|when|is|in|const|struct|typedef|include|true|false|null|NULL|sizeof)\b', "keyword", True),
                (r'\b(?:String|Integer|Long|Double|Boolean|List|Object|Int|Float|Any|Unit|char|int|int64_t|bool|size_t)\b', "type", False),
                (r'\b\d+(?:\.\d+)?\b', "number", False),
            ]
        self.rules = []
        for pattern, color, bold in rules:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(palette[color]))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            self.rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


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
        self.text_html_highlighter = None
        self.text_input_highlighter = None
        self.text_output_code_highlighter = None
        self.text_html_mode = False
        self.text_wrap_enabled = False
        self.text_folded_blocks = []
        self._html_folded_blocks: set[int] = set()

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
        self.tabs.addTab(QWidget(), "So sánh")
        self.tabs.addTab(QWidget(), "String → cURL")
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

        self.compression = StyledComboBox()
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

        self.compare_panel = self.build_compare_panel()
        outer.addWidget(self.compare_panel, 1)
        self.compare_panel.hide()

        self.curl_panel = self.build_curl_panel()
        outer.addWidget(self.curl_panel, 1)
        self.curl_panel.hide()

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
        editor = FoldablePlainTextEdit()
        editor.setObjectName("CodeEditor")
        editor.setPlaceholderText(placeholder)
        editor.setReadOnly(read_only)
        # Avoid expensive line wrapping for long compact JSON/string payloads.
        # QPlainTextEdit has no fixed input-size cap here.
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor.setMaximumBlockCount(0)
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
            ("JSON Format", "format_json"),
            ("JSON Minify", "minify_json"),
            ("JSON → String", "json_to_string"),
            ("String → JSON", "string_to_json"),
            ("JSON → XML", "act_json_to_xml"),
            ("XML → JSON", "act_xml_to_json"),
            ("XML Format", "format_xml"),
            ("XML Minify", "minify_xml"),
            ("XML → String", "xml_to_string"),
            ("String → XML", "string_to_xml"),
            ("String → HTML", "string_to_html"),
            ("HTML → String", "html_to_string"),
            ("JSON → Model", "json_to_model"),
        ]
        for label, operation in operations:
            self.text_operation.addItem(label, operation)
        self.text_operation.setObjectName("OperationCombo")
        self.text_operation.setMinimumWidth(210)
        self.text_operation.setMaxVisibleItems(14)
        self.text_operation.currentIndexChanged.connect(
            self.on_text_operation_changed
        )
        toolbar.addWidget(self.text_operation, 2)

        self.text_pair_tabs = QTabWidget()
        self.text_pair_definitions = [
            ("JSON Format ⇄ Minify", "format_json", "minify_json"),
            ("JSON ⇄ String", "json_to_string", "string_to_json"),
            ("JSON ⇄ XML", "act_json_to_xml", "act_xml_to_json"),
            ("XML Format ⇄ Minify", "format_xml", "minify_xml"),
            ("String ⇄ HTML", "string_to_html", "html_to_string"),
        ]
        self.text_pair_flip = [False] * len(self.text_pair_definitions)
        for title, _forward, _reverse in self.text_pair_definitions:
            self.text_pair_tabs.addTab(QWidget(), title)
        self.text_pair_tabs.currentChanged.connect(self.select_text_pair)
        # Keep pair state internally; the dropdown is the only visible toolbar.
        self.text_pair_tabs.hide()

        self.text_swap_btn = QPushButton("⇄")
        self.text_swap_btn.setToolTip("Đảo chiều chuyển đổi và đưa kết quả hiện tại về ô đầu vào")
        self.text_swap_btn.clicked.connect(self.swap_text_direction)
        toolbar.addWidget(self.text_swap_btn)

        self.text_indent_label = QLabel("Indent")
        self.text_indent_label.setObjectName("Muted")
        toolbar.addWidget(self.text_indent_label)
        self.text_indent = QComboBox()
        self.text_indent.addItem("2 spaces", 2)
        self.text_indent.addItem("4 spaces", 4)
        self.text_indent.setCurrentIndex(0)
        self.text_indent.setMinimumWidth(104)
        self.text_indent.setMaximumWidth(116)
        toolbar.addWidget(self.text_indent)

        self.text_wrap_btn = QPushButton("Wrap: Tắt")
        self.text_wrap_btn.clicked.connect(self.toggle_text_wrap)
        toolbar.addWidget(self.text_wrap_btn)
        self.text_layout_btn = QPushButton("Xếp dọc")
        self.text_layout_btn.clicked.connect(self.toggle_text_layout)
        toolbar.addWidget(self.text_layout_btn)

        self.text_model_label = QLabel("Model")
        self.text_model_label.setObjectName("Muted")
        toolbar.addWidget(self.text_model_label)

        self.text_model_target = QComboBox()
        self.text_model_target.addItem("Python dataclass", "dataclass")
        self.text_model_target.addItem("Pydantic v2", "pydantic")
        self.text_model_target.addItem("TypeScript", "typescript")
        self.text_model_target.addItem("Java", "java")
        self.text_model_target.addItem("Kotlin", "kotlin")
        self.text_model_target.addItem("C", "c")
        self.text_model_target.setObjectName("ModelCombo")
        self.text_model_target.setMinimumWidth(158)
        self.text_model_target.setMaxVisibleItems(8)
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

        self.text_clear_btn = QPushButton("Clear")
        self.text_clear_btn.clicked.connect(self.clear_text_all)
        toolbar.addWidget(self.text_clear_btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.text_splitter = splitter

        self.input_pane = self._build_text_pane(
            "ĐẦU VÀO",
            'Dán JSON hoặc XML vào đây…\n\nVí dụ JSON:\n{\n  "name": "FileForge",\n  "active": true\n}',
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
        self.output_editor.foldRequested.connect(self.toggle_html_block)
        self.output_tree = self.output_pane["tree"]
        self.output_tree_button = self.output_pane["tree_button"]

        footer = QHBoxLayout()
        self.text_status = QLabel("Sẵn sàng")
        self.text_status.setObjectName("Muted")
        footer.addWidget(self.text_status)
        footer.addStretch()

        self.text_search = QLineEdit()
        self.text_search.setPlaceholderText("Tìm trong kết quả…")
        self.text_search.setMaximumWidth(180)
        self.text_search.returnPressed.connect(self.find_next_text)
        footer.addWidget(self.text_search)
        self.text_find_prev = QPushButton("↑")
        self.text_find_prev.setToolTip("Tìm kết quả trước")
        self.text_find_prev.clicked.connect(lambda: self.find_text_match(backward=True))
        footer.addWidget(self.text_find_prev)
        self.text_find_next = QPushButton("↓")
        self.text_find_next.setToolTip("Tìm kết quả tiếp theo")
        self.text_find_next.clicked.connect(self.find_next_text)
        footer.addWidget(self.text_find_next)
        self.text_fold_btn = QPushButton("Thu gọn HTML")
        self.text_fold_btn.clicked.connect(self.fold_html_output)
        footer.addWidget(self.text_fold_btn)
        self.text_unfold_btn = QPushButton("Mở rộng HTML")
        self.text_unfold_btn.clicked.connect(self.unfold_html_output)
        footer.addWidget(self.text_unfold_btn)

        self.text_copy_input_btn = QPushButton("Copy đầu vào")
        self.text_copy_input_btn.clicked.connect(self.copy_text_input)
        footer.addWidget(self.text_copy_input_btn)

        self.text_copy_btn = QPushButton("Copy kết quả")
        self.text_copy_btn.setEnabled(False)
        self.text_copy_btn.clicked.connect(self.copy_text_result)
        footer.addWidget(self.text_copy_btn)

        self.text_reset_btn = QPushButton("Reset 50/50")
        self.text_reset_btn.clicked.connect(self.reset_text_splitter)
        footer.addWidget(self.text_reset_btn)

        self.text_progress = QProgressBar()
        self.text_progress.setRange(0, 0)
        self.text_progress.setFixedWidth(120)
        self.text_progress.hide()
        footer.addWidget(self.text_progress)

        layout.addLayout(footer)
        self.text_fold_btn.hide()
        self.text_unfold_btn.hide()
        self.text_search.hide()
        self.text_find_prev.hide()
        self.text_find_next.hide()
        self.text_input_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.input_editor)
        self.text_input_search_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.text_input_search_shortcut.activated.connect(
            lambda: self.toggle_text_search("input")
        )
        self.text_output_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self.output_editor)
        self.text_output_search_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.text_output_search_shortcut.activated.connect(
            lambda: self.toggle_text_search("output")
        )
        self.text_convert_shortcut = QShortcut(QKeySequence("Ctrl+Return"), panel)
        self.text_convert_shortcut.activated.connect(self.run_text_action)
        self.text_escape_shortcut = QShortcut(QKeySequence("Escape"), panel)
        self.text_escape_shortcut.activated.connect(self.close_text_search)
        self.update_text_model_controls()
        return panel

    def on_text_operation_changed(self):
        """Keep the action dropdown and paired tabs synchronized."""
        self.update_text_model_controls()
        operation = self.text_operation.currentData()
        for index, (_title, forward, reverse) in enumerate(self.text_pair_definitions):
            if operation == forward or operation == reverse:
                self.text_pair_flip[index] = operation == reverse
                if self.text_pair_tabs.currentIndex() != index:
                    self.text_pair_tabs.setCurrentIndex(index)
                break

    def update_text_model_controls(self):
        is_model = self.text_operation.currentData() == "json_to_model"
        self.text_model_label.setVisible(is_model)
        self.text_model_target.setVisible(is_model)
        self.text_class_label.setVisible(is_model)
        self.text_class_name.setVisible(is_model)
        if is_model:
            if self.text_input_highlighter is None:
                self.text_input_highlighter = CodeSyntaxHighlighter(
                    self.input_editor.document(), "json"
                )
        elif self.text_input_highlighter is not None:
            self.text_input_highlighter.setDocument(None)
            self.text_input_highlighter = None

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
        indent_size = int(self.text_indent.currentData())

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
            indent_size,
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

        self._text_output_plain = result["output"]
        self.output_editor.setPlainText(result["output"])
        self.text_html_mode = self.text_operation.currentData() == "string_to_html"
        self._html_folded_blocks.clear()
        if self.text_output_code_highlighter is not None:
            self.text_output_code_highlighter.setDocument(None)
            self.text_output_code_highlighter = None
        if self.text_html_highlighter is not None:
            self.text_html_highlighter.setDocument(None)
            self.text_html_highlighter = None
        if self.text_html_mode:
            self.output_editor.setPlainText(self.decorate_html_output(result["output"]))
            self.text_html_highlighter = HTMLSyntaxHighlighter(self.output_editor.document())
        elif self.text_operation.currentData() == "json_to_model":
            self.text_output_code_highlighter = CodeSyntaxHighlighter(
                self.output_editor.document(), self.text_model_target.currentData()
            )
        self.text_fold_btn.setVisible(self.text_html_mode)
        self.text_unfold_btn.setVisible(self.text_html_mode)

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
            "Không thể xử lý nội dung. Kiểm tra cú pháp JSON/XML/HTML rồi thử lại.\n\n"
            + message,
        )


    def swap_text_direction(self):
        index = self.text_pair_tabs.currentIndex()
        if index < 0:
            return
        self.text_pair_flip[index] = not self.text_pair_flip[index]
        forward, reverse = self.text_pair_definitions[index][1:]
        operation = reverse if self.text_pair_flip[index] else forward
        previous_output = self._plain_text_result()
        self.text_operation.setCurrentIndex(self.text_operation.findData(operation))
        if previous_output.strip():
            self.input_editor.setPlainText(previous_output)
            self.run_text_action()

    def select_text_pair(self, index):
        if index < 0:
            return
        forward, reverse = self.text_pair_definitions[index][1:]
        operation = reverse if self.text_pair_flip[index] else forward
        self.text_operation.setCurrentIndex(self.text_operation.findData(operation))

    def toggle_text_wrap(self):
        self.text_wrap_enabled = not self.text_wrap_enabled
        mode = (
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if self.text_wrap_enabled
            else QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.input_editor.setLineWrapMode(mode)
        self.output_editor.setLineWrapMode(mode)
        self.text_wrap_btn.setText(
            "Wrap: Bật" if self.text_wrap_enabled else "Wrap: Tắt"
        )

    def toggle_text_layout(self):
        vertical = self.text_splitter.orientation() == Qt.Orientation.Horizontal
        self.text_splitter.setOrientation(
            Qt.Orientation.Vertical if vertical else Qt.Orientation.Horizontal
        )
        self.text_layout_btn.setText("Xếp ngang" if vertical else "Xếp dọc")

    def copy_text_input(self):
        value = self.input_editor.toPlainText()
        if value:
            QApplication.clipboard().setText(value)
            self.text_status.setText("Đã sao chép nội dung đầu vào")

    def clear_text_all(self):
        if self.text_busy:
            return
        self.input_editor.clear()
        self.output_editor.clear()
        self._text_output_plain = ""
        self.input_tree.clear()
        self.output_tree.clear()
        self.input_tree_button.setEnabled(False)
        self.output_tree_button.setEnabled(False)
        self.text_copy_btn.setEnabled(False)
        self.text_html_mode = False
        self._html_folded_blocks.clear()
        self.text_fold_btn.hide()
        self.text_unfold_btn.hide()
        self.text_status.setText("Đã xóa nội dung")

    def reset_text_splitter(self):
        self.text_splitter.setSizes([1, 1])
        self.text_status.setText("Đã đưa hai khung về tỷ lệ 50/50")

    def toggle_text_search(self, target="output"):
        visible = not self.text_search.isVisible() or self._text_search_target != target
        self._text_search_target = target
        self.text_search.setVisible(visible)
        self.text_find_prev.setVisible(visible)
        self.text_find_next.setVisible(visible)
        if visible:
            self.text_search.setFocus()
            self.text_search.selectAll()

    def close_text_search(self):
        self.text_search.hide()
        self.text_find_prev.hide()
        self.text_find_next.hide()
        if getattr(self, "_text_search_target", "output") == "input":
            self.input_editor.setFocus()
        else:
            self.output_editor.setFocus()

    def find_text_match(self, backward=False):
        query = self.text_search.text()
        if not query:
            return
        flags = QPlainTextEdit.FindFlag()
        if backward:
            flags |= QPlainTextEdit.FindFlag.FindBackward
        editor = self.input_editor if getattr(self, "_text_search_target", "output") == "input" else self.output_editor
        if not editor.find(query, flags):
            cursor = editor.textCursor()
            cursor.movePosition(
                cursor.MoveOperation.End if backward else cursor.MoveOperation.Start
            )
            editor.setTextCursor(cursor)
            editor.find(query, flags)

    def find_next_text(self):
        self.find_text_match(False)

    @staticmethod
    def decorate_html_output(value):
        void_tags = {"area", "base", "br", "col", "embed", "hr", "img",
                     "input", "link", "meta", "param", "source", "track", "wbr"}
        decorated = []
        for line in value.splitlines():
            stripped = line.lstrip()
            match = re.match(r"<\s*([\w:-]+)\b", stripped)
            if match and not stripped.startswith(("</", "<!", "<?")) and not stripped.rstrip().endswith("/>"):
                prefix = line[:len(line) - len(stripped)]
                if match.group(1).lower() not in void_tags:
                    line = prefix + "▼ " + stripped
            decorated.append(line)
        return "\n".join(decorated)

    def _html_matching_close(self, blocks, open_index, tag):
        depth = 1
        for index in range(open_index + 1, len(blocks)):
            line = blocks[index].text()
            if re.search(r"</\s*" + re.escape(tag) + r"\s*>", line, re.I):
                depth -= 1
                if depth == 0:
                    return index
            opened = re.search(r"<\s*" + re.escape(tag) + r"\b", line, re.I)
            if opened and not line.strip().endswith("/>"):
                depth += 1
        return None

    def _html_document_blocks(self):
        blocks = []
        block = self.output_editor.document().firstBlock()
        while block.isValid():
            blocks.append(block)
            block = block.next()
        return blocks

    def _html_matching_close(self, blocks, open_index, tag):
        depth = 1
        escaped_tag = re.escape(tag)
        close_re = re.compile(r"</\s*" + escaped_tag + r"\s*>", re.I)
        open_re = re.compile(r"<\s*" + escaped_tag + r"\b", re.I)
        for index in range(open_index + 1, len(blocks)):
            line = blocks[index].text()
            if close_re.search(line):
                depth -= 1
                if depth == 0:
                    return index
            elif open_re.search(line) and not line.strip().endswith("/>"):
                depth += 1
        return None

    def _set_html_block_marker(self, block, marker):
        line = block.text()
        stripped = line.lstrip()
        if not stripped.startswith(("▼ ", "▶ ")):
            return
        updated = line[:len(line) - len(stripped)] + marker + stripped[2:]
        cursor = self.output_editor.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(cursor.MoveOperation.EndOfBlock, cursor.MoveMode.KeepAnchor)
        cursor.insertText(updated)

    def _apply_html_fold_state(self, blocks=None):
        if blocks is None:
            blocks = self._html_document_blocks()
        hidden = set()
        for open_index in tuple(self._html_folded_blocks):
            if open_index < 0 or open_index >= len(blocks):
                continue
            match = re.search(r"<\s*([\w:-]+)\b", blocks[open_index].text())
            if not match:
                continue
            end_index = self._html_matching_close(blocks, open_index, match.group(1))
            if end_index is not None:
                hidden.update(range(open_index + 1, end_index + 1))

        doc = self.output_editor.document()
        for index, block in enumerate(blocks):
            is_hidden = index in hidden
            block.setVisible(not is_hidden)
            block.setLineCount(0 if is_hidden else max(1, block.layout().lineCount()))
        doc.markContentsDirty(0, doc.characterCount())
        self.output_editor.viewport().update()

    def toggle_html_block(self, block_number):
        if not self.text_html_mode:
            return
        blocks = self._html_document_blocks()
        if block_number < 0 or block_number >= len(blocks):
            return
        line = blocks[block_number].text().lstrip()
        if line.startswith("▼ "):
            self._html_folded_blocks.add(block_number)
            self._set_html_block_marker(blocks[block_number], "▶ ")
        elif line.startswith("▶ "):
            self._html_folded_blocks.discard(block_number)
            self._set_html_block_marker(blocks[block_number], "▼ ")
        else:
            return
        self._apply_html_fold_state()

    def fold_html_output(self):
        if not self.text_html_mode:
            return
        blocks = self._html_document_blocks()
        self._html_folded_blocks = {
            index for index, block in enumerate(blocks)
            if block.text().lstrip().startswith("▼ ")
        }
        for index, block in enumerate(blocks):
            if index in self._html_folded_blocks:
                self._set_html_block_marker(block, "▶ ")
        self._apply_html_fold_state(blocks)
        self.text_status.setText("Đã thu gọn các thẻ HTML")

    def unfold_html_output(self):
        if not self.text_html_mode:
            return
        blocks = self._html_document_blocks()
        self._html_folded_blocks.clear()
        for block in blocks:
            if block.text().lstrip().startswith("▶ "):
                self._set_html_block_marker(block, "▼ ")
        self._apply_html_fold_state()
        self.text_status.setText("Đã mở rộng tất cả thẻ HTML")

    def _plain_text_result(self):
        """Return conversion output, never the UI-only HTML fold decorations."""
        if self.text_html_mode:
            # Keep the formatter's actual HTML separately from the decorated
            # QPlainTextEdit view. This is the same separation used by the
            # original Tkinter formatter's _html_plain_text.
            return getattr(self, "_text_output_plain", self.output_editor.toPlainText())
        return self.output_editor.toPlainText()

    def copy_text_result(self):
        value = self._plain_text_result()
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

    def _build_compare_text_pane(self, title: str, placeholder: str):
        pane = QFrame()
        pane.setObjectName("Panel")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(7)
        header = QHBoxLayout()
        label = QLabel(title)
        label.setObjectName("Section")
        header.addWidget(label)
        header.addStretch()
        count = QLabel("0 ký tự")
        count.setObjectName("Muted")
        header.addWidget(count)
        layout.addLayout(header)
        editor = QPlainTextEdit()
        editor.setObjectName("CodeEditor")
        editor.setPlaceholderText(placeholder)
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor.setTabStopDistance(28)
        editor.textChanged.connect(
            lambda ed=editor, lbl=count: lbl.setText(f"{len(ed.toPlainText()):,} ký tự")
        )
        layout.addWidget(editor, 1)
        return {"widget": pane, "editor": editor, "count": count}

    def _build_json_compare_pane(self, title: str, placeholder: str, side: str):
        pane = QFrame()
        pane.setObjectName("Panel")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(7)
        header = QHBoxLayout()
        label = QLabel(title)
        label.setObjectName("Section")
        header.addWidget(label)
        header.addStretch()
        source = QComboBox()
        source.addItem("Dán JSON", "paste")
        source.addItem("Mở tệp .json…", "file")
        source.setToolTip("Chọn dán JSON hoặc nạp nội dung từ tệp JSON trên máy")
        source.currentIndexChanged.connect(
            lambda index, key=side, combo=source: self.load_json_compare_file(key, index, combo)
        )
        header.addWidget(source)
        layout.addLayout(header)
        editor = QPlainTextEdit()
        editor.setObjectName("CodeEditor")
        editor.setPlaceholderText(placeholder)
        editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor.setTabStopDistance(28)
        layout.addWidget(editor, 1)
        return {"widget": pane, "editor": editor, "source": source}


    def build_curl_panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        intro = QLabel("Dán HTTP request đã copy từ DevTools hoặc tài liệu. FileForge sẽ tách METHOD, URL và HEADERS thành lệnh cURL.")
        intro.setObjectName("Muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        editors = QSplitter(Qt.Orientation.Horizontal)
        self.curl_input = QPlainTextEdit()
        self.curl_input.setObjectName("CodeEditor")
        self.curl_input.setPlaceholderText("Dán request dạng Markdown hoặc HTTP raw vào đây…")
        self.curl_output = QPlainTextEdit()
        self.curl_output.setObjectName("CodeEditor")
        self.curl_output.setReadOnly(True)
        self.curl_output.setPlaceholderText("Lệnh cURL sẽ xuất hiện ở đây…")
        editors.addWidget(self.curl_input)
        editors.addWidget(self.curl_output)
        editors.setStretchFactor(0, 1)
        editors.setStretchFactor(1, 1)
        layout.addWidget(editors, 1)

        actions = QHBoxLayout()
        self.curl_status = QLabel("Sẵn sàng")
        self.curl_status.setObjectName("Muted")
        actions.addWidget(self.curl_status)
        actions.addStretch()
        convert = QPushButton("Chuyển thành cURL  →")
        convert.setObjectName("Primary")
        convert.clicked.connect(self.convert_to_curl)
        actions.addWidget(convert)
        copy = QPushButton("Copy cURL")
        copy.clicked.connect(self.copy_curl_result)
        actions.addWidget(copy)
        clear = QPushButton("Xóa")
        clear.clicked.connect(lambda: (self.curl_input.clear(), self.curl_output.clear(), self.curl_status.setText("Đã xóa")))
        actions.addWidget(clear)
        layout.addLayout(actions)
        return panel

    def convert_to_curl(self):
        try:
            parsed = parse_http_request(self.curl_input.toPlainText())
        except ValueError as exc:
            self.curl_status.setText("Không thể phân tích request")
            QMessageBox.warning(self, "Request chưa hợp lệ", str(exc))
            return
        self.curl_output.setPlainText(parsed["curl"])
        self.curl_status.setText(
            f"Đã nhận diện {parsed['method']} · {len(parsed['headers'])} headers"
        )

    def copy_curl_result(self):
        value = self.curl_output.toPlainText()
        if value:
            QApplication.clipboard().setText(value)
            self.curl_status.setText("Đã sao chép lệnh cURL")

    def build_compare_panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        root = QVBoxLayout(panel)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        heading = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel("Compare workspace")
        title.setObjectName("Brand")
        subtitle = QLabel("So sánh văn bản và JSON cục bộ — dữ liệu không rời khỏi máy")
        subtitle.setObjectName("Muted")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        heading.addLayout(title_col)
        heading.addStretch()
        root.addLayout(heading)

        self.compare_tabs = QTabWidget()
        self.compare_tabs.addTab(self._build_string_compare_tab(), "Compare String")
        self.compare_tabs.addTab(self._build_json_diff_tab(), "JSON Diff")
        root.addWidget(self.compare_tabs, 1)
        return panel

    def _build_string_compare_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 10, 4, 4)
        layout.setSpacing(9)

        options = QHBoxLayout()
        mode_label = QLabel("Độ chi tiết")
        mode_label.setObjectName("Muted")
        options.addWidget(mode_label)
        self.string_diff_mode = QComboBox()
        self.string_diff_mode.addItem("Theo dòng", "line")
        self.string_diff_mode.addItem("Theo từ", "word")
        self.string_diff_mode.addItem("Theo ký tự", "character")
        self.string_diff_mode.setMinimumWidth(125)
        options.addWidget(self.string_diff_mode)
        self.string_ignore_case = QCheckBox("Bỏ qua hoa/thường")
        self.string_ignore_whitespace = QCheckBox("Bỏ qua khoảng trắng")
        self.string_ignore_blank = QCheckBox("Bỏ qua dòng trống")
        options.addWidget(self.string_ignore_case)
        options.addWidget(self.string_ignore_whitespace)
        options.addWidget(self.string_ignore_blank)
        options.addStretch()
        self.string_compare_btn = QPushButton("So sánh")
        self.string_compare_btn.setObjectName("Primary")
        self.string_compare_btn.clicked.connect(self.run_string_compare)
        options.addWidget(self.string_compare_btn)
        self.string_swap_btn = QPushButton("⇄ Đổi bên")
        self.string_swap_btn.clicked.connect(self.swap_string_compare)
        options.addWidget(self.string_swap_btn)
        self.string_clear_btn = QPushButton("Xóa")
        self.string_clear_btn.clicked.connect(self.clear_string_compare)
        options.addWidget(self.string_clear_btn)
        layout.addLayout(options)

        inputs = QSplitter(Qt.Orientation.Horizontal)
        self.string_before = self._build_compare_text_pane(
            "BẢN GỐC", "Dán văn bản phiên bản ban đầu…"
        )
        self.string_after = self._build_compare_text_pane(
            "BẢN MỚI", "Dán văn bản phiên bản đã chỉnh sửa…"
        )
        inputs.addWidget(self.string_before["widget"])
        inputs.addWidget(self.string_after["widget"])
        inputs.setStretchFactor(0, 1)
        inputs.setStretchFactor(1, 1)
        inputs.setSizes([500, 500])
        inputs.setMinimumHeight(160)
        layout.addWidget(inputs, 2)

        result_header = QHBoxLayout()
        result_title = QLabel("KẾT QUẢ SO SÁNH")
        result_title.setObjectName("Section")
        result_header.addWidget(result_title)
        result_header.addStretch()
        self.string_diff_summary = QLabel("Nhập hai bản văn bản rồi chọn So sánh")
        self.string_diff_summary.setObjectName("Muted")
        result_header.addWidget(self.string_diff_summary)
        layout.addLayout(result_header)

        results = QSplitter(Qt.Orientation.Horizontal)
        self.string_before_result = QTextEdit()
        self.string_before_result.setObjectName("DiffOutput")
        self.string_before_result.setReadOnly(True)
        self.string_before_result.setPlaceholderText("Các phần đã xóa sẽ được đánh dấu ở đây")
        self.string_after_result = QTextEdit()
        self.string_after_result.setObjectName("DiffOutput")
        self.string_after_result.setReadOnly(True)
        self.string_after_result.setPlaceholderText("Các phần được thêm sẽ được đánh dấu ở đây")
        results.addWidget(self.string_before_result)
        results.addWidget(self.string_after_result)
        results.setStretchFactor(0, 1)
        results.setStretchFactor(1, 1)
        layout.addWidget(results, 3)
        return page

    def _build_json_diff_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 10, 4, 4)
        layout.setSpacing(9)

        controls = QHBoxLayout()
        array_label = QLabel("So sánh mảng")
        array_label.setObjectName("Muted")
        controls.addWidget(array_label)
        self.json_array_mode = QComboBox()
        self.json_array_mode.addItem("Theo vị trí", False)
        self.json_array_mode.addItem("Bỏ qua thứ tự", True)
        self.json_array_mode.setToolTip(
            "Theo vị trí: phần tử [0] so với [0]. Bỏ qua thứ tự: xem mảng như tập hợp có giữ số lần lặp."
        )
        controls.addWidget(self.json_array_mode)
        controls.addStretch()
        self.json_compare_btn = QPushButton("So sánh JSON")
        self.json_compare_btn.setObjectName("Primary")
        self.json_compare_btn.clicked.connect(self.run_json_diff)
        controls.addWidget(self.json_compare_btn)
        self.json_swap_btn = QPushButton("⇄ Đổi bên")
        self.json_swap_btn.clicked.connect(self.swap_json_inputs)
        controls.addWidget(self.json_swap_btn)
        self.json_sample_btn = QPushButton("Ví dụ")
        self.json_sample_btn.clicked.connect(self.load_json_diff_sample)
        controls.addWidget(self.json_sample_btn)
        self.json_clear_btn = QPushButton("Xóa")
        self.json_clear_btn.clicked.connect(self.clear_json_diff)
        controls.addWidget(self.json_clear_btn)
        layout.addLayout(controls)

        inputs = QSplitter(Qt.Orientation.Horizontal)
        self.json_before = self._build_json_compare_pane(
            "JSON GỐC (A)", "Dán JSON ban đầu vào đây…", "before"
        )
        self.json_after = self._build_json_compare_pane(
            "JSON MỚI (B)", "Dán JSON đã thay đổi vào đây…", "after"
        )
        inputs.addWidget(self.json_before["widget"])
        inputs.addWidget(self.json_after["widget"])
        inputs.setStretchFactor(0, 1)
        inputs.setStretchFactor(1, 1)
        inputs.setSizes([500, 500])
        inputs.setMinimumHeight(180)
        layout.addWidget(inputs, 2)

        result_header = QHBoxLayout()
        result_title = QLabel("KHÁC BIỆT THEO CẤU TRÚC")
        result_title.setObjectName("Section")
        result_header.addWidget(result_title)
        result_header.addStretch()
        self.json_diff_summary = QLabel("Object key được so sánh không phụ thuộc thứ tự")
        self.json_diff_summary.setObjectName("Muted")
        result_header.addWidget(self.json_diff_summary)
        self.json_diff_filter = QComboBox()
        self.json_diff_filter.addItem("Tất cả", "all")
        self.json_diff_filter.addItem("Được thêm", "added")
        self.json_diff_filter.addItem("Đã xóa", "removed")
        self.json_diff_filter.addItem("Đã sửa", "changed")
        self.json_diff_filter.currentIndexChanged.connect(self.filter_json_diff_rows)
        result_header.addWidget(self.json_diff_filter)
        layout.addLayout(result_header)

        self.json_diff_table = QTableWidget(0, 4)
        self.json_diff_table.setObjectName("DiffTable")
        self.json_diff_table.setHorizontalHeaderLabels(
            ["LOẠI", "ĐƯỜNG DẪN", "GIÁ TRỊ GỐC", "GIÁ TRỊ MỚI"]
        )
        self.json_diff_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.json_diff_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.json_diff_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.json_diff_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.json_diff_table.verticalHeader().setVisible(False)
        self.json_diff_table.setWordWrap(True)
        self.json_diff_table.setAlternatingRowColors(True)
        self.json_diff_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.json_diff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.json_diff_table, 3)

        footer = QHBoxLayout()
        self.json_copy_report_btn = QPushButton("Copy báo cáo")
        self.json_copy_report_btn.clicked.connect(self.copy_json_diff_report)
        self.json_copy_report_btn.setEnabled(False)
        footer.addWidget(self.json_copy_report_btn)
        footer.addStretch()
        self.json_diff_status = QLabel("Sẵn sàng")
        self.json_diff_status.setObjectName("Muted")
        footer.addWidget(self.json_diff_status)
        layout.addLayout(footer)
        self._json_diff_result = None
        return page

    def load_json_compare_file(self, side: str, index: int, combo: QComboBox):
        if index != 1:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn tệp JSON", str(Path.home()), "JSON (*.json);;Tất cả tệp (*)"
        )
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8-sig")
                target = self.json_before if side == "before" else self.json_after
                target["editor"].setPlainText(content)
                self.json_diff_status.setText(f"Đã nạp {Path(path).name}")
            except (OSError, UnicodeError) as exc:
                QMessageBox.warning(self, "Không thể mở JSON", str(exc))
        combo.blockSignals(True)
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def run_string_compare(self):
        before = self.string_before["editor"].toPlainText()
        after = self.string_after["editor"].toPlainText()
        if not before and not after:
            self.string_diff_summary.setText("Hãy nhập nội dung ở cả hai bên")
            return
        try:
            result = compare_text(
                before,
                after,
                self.string_diff_mode.currentData(),
                ignore_case=self.string_ignore_case.isChecked(),
                ignore_whitespace=self.string_ignore_whitespace.isChecked(),
                ignore_blank_lines=self.string_ignore_blank.isChecked(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Không thể so sánh", str(exc))
            return

        style = """
        <style>
          body { color:#202124; font-family:Consolas,monospace; font-size:12px; }
          pre { white-space:pre-wrap; overflow-wrap:anywhere; margin:0; }
          .diff-removed { background:#fce8e6; color:#b3261e; }
          .diff-added { background:#e6f4ea; color:#137333; }
        </style>
        """
        self.string_before_result.setHtml(
            style + "<pre>" + result["before_html"] + "</pre>"
        )
        self.string_after_result.setHtml(
            style + "<pre>" + result["after_html"] + "</pre>"
        )
        self.string_diff_summary.setText(
            f"Thêm {result['added']} · Xóa {result['removed']} · Sửa {result['changed']}"
        )

    def swap_string_compare(self):
        before = self.string_before["editor"].toPlainText()
        after = self.string_after["editor"].toPlainText()
        self.string_before["editor"].setPlainText(after)
        self.string_after["editor"].setPlainText(before)

    def clear_string_compare(self):
        self.string_before["editor"].clear()
        self.string_after["editor"].clear()
        self.string_before_result.clear()
        self.string_after_result.clear()
        self.string_diff_summary.setText("Đã xóa nội dung")

    def run_json_diff(self):
        before = self.json_before["editor"].toPlainText()
        after = self.json_after["editor"].toPlainText()
        if not before.strip() or not after.strip():
            self.json_diff_status.setText("Hãy nhập JSON ở cả hai bên")
            return
        try:
            result = compare_json(
                before,
                after,
                ignore_array_order=bool(self.json_array_mode.currentData()),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "JSON không hợp lệ", str(exc))
            self.json_diff_status.setText("Kiểm tra JSON đầu vào")
            return

        self._json_diff_result = result
        self.json_diff_summary.setText(
            f"{result['total']} khác biệt  ·  +{result['added']} thêm  ·  "
            f"−{result['removed']} xóa  ·  ~{result['changed']} sửa"
        )
        self.json_diff_table.setRowCount(0)
        for diff in result["differences"]:
            row = self.json_diff_table.rowCount()
            self.json_diff_table.insertRow(row)
            kind_labels = {"added": "THÊM", "removed": "XÓA", "changed": "SỬA"}
            kind_item = QTableWidgetItem(kind_labels[diff["kind"]])
            color = {
                "added": QColor("#137333"),
                "removed": QColor("#c5221f"),
                "changed": QColor("#b06000"),
            }[diff["kind"]]
            kind_item.setForeground(color)
            path_item = QTableWidgetItem(diff["path"])
            before_item = QTableWidgetItem(diff["before"])
            after_item = QTableWidgetItem(diff["after"])
            for item, full in (
                (before_item, diff["before"]),
                (after_item, diff["after"]),
            ):
                item.setToolTip(full)
            for col, item in enumerate((kind_item, path_item, before_item, after_item)):
                self.json_diff_table.setItem(row, col, item)
            self.json_diff_table.setRowHeight(row, 58)
        self.filter_json_diff_rows()
        self.json_copy_report_btn.setEnabled(bool(result["differences"]))
        self.json_diff_status.setText(
            "Hai tài liệu giống nhau" if not result["differences"] else "So sánh hoàn tất"
        )

    def filter_json_diff_rows(self):
        if not hasattr(self, "json_diff_table"):
            return
        selected = self.json_diff_filter.currentData()
        for row in range(self.json_diff_table.rowCount()):
            kind = self.json_diff_table.item(row, 0)
            data_kind = {
                "THÊM": "added", "XÓA": "removed", "SỬA": "changed"
            }.get(kind.text() if kind else "", "")
            self.json_diff_table.setRowHidden(
                row, selected != "all" and data_kind != selected
            )

    def swap_json_inputs(self):
        before = self.json_before["editor"].toPlainText()
        after = self.json_after["editor"].toPlainText()
        self.json_before["editor"].setPlainText(after)
        self.json_after["editor"].setPlainText(before)

    def load_json_diff_sample(self):
        before = """{
  "name": "FileForge",
  "version": "1.0",
  "features": ["zip", "image"],
  "active": true
}"""
        after = """{
  "name": "FileForge",
  "version": "1.1",
  "features": ["zip", "image", "diff"],
  "license": "MIT",
  "active": true
}"""
        self.json_before["editor"].setPlainText(before)
        self.json_after["editor"].setPlainText(after)

    def clear_json_diff(self):
        self.json_before["editor"].clear()
        self.json_after["editor"].clear()
        self.json_diff_table.setRowCount(0)
        self._json_diff_result = None
        self.json_diff_summary.setText("Object key được so sánh không phụ thuộc thứ tự")
        self.json_diff_status.setText("Đã xóa nội dung")
        self.json_copy_report_btn.setEnabled(False)

    def copy_json_diff_report(self):
        if not self._json_diff_result:
            return
        text = format_text_diff_report(self._json_diff_result)
        if text:
            QApplication.clipboard().setText(text)
            self.json_diff_status.setText("Đã sao chép báo cáo")

    def on_mode_changed(self, index: int):
        if index == 3:
            self.mode = "text"
            self.curl_panel.hide()
            self.add_files_btn.hide()
            self.add_folder_btn.hide()
            self.drop_area.hide()
            self.queue_panel.hide()
            self.action_panel.hide()
            self.compare_panel.hide()
            self.text_panel.show()
            return

        if index == 4:
            self.mode = "compare"
            self.curl_panel.hide()
            self.add_files_btn.hide()
            self.add_folder_btn.hide()
            self.drop_area.hide()
            self.queue_panel.hide()
            self.action_panel.hide()
            self.text_panel.hide()
            self.compare_panel.show()
            return

        if index == 5:
            self.mode = "curl"
            self.add_files_btn.hide()
            self.add_folder_btn.hide()
            self.drop_area.hide()
            self.queue_panel.hide()
            self.action_panel.hide()
            self.text_panel.hide()
            self.compare_panel.hide()
            self.curl_panel.show()
            return

        self.curl_panel.hide()
        self.compare_panel.hide()
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
