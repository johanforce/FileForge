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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fileforge.archive import create_zip


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
    min-width: 150px;
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
"""


COMPRESSION_OPTIONS = {
    "Nhanh nhất": "Fast",
    "Cân bằng": "Balanced",
    "Nén tối đa": "Best",
}


class ArchiveWorker(QThread):
    progress = Signal(int, int, str)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, paths: list[str], destination: str, compression: str):
        super().__init__()
        self.paths = paths
        self.destination = destination
        self.compression = compression

    def run(self):
        try:
            result = create_zip(
                self.paths,
                self.destination,
                self.compression,
                lambda done, total, name: self.progress.emit(done, total, name),
            )
            self.succeeded.emit(str(result))
        except Exception as exc:
            self.failed.emit(str(exc))


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("DropArea")
        self.setMinimumHeight(102)
        self.setProperty("dragActive", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Kéo thả tệp hoặc thư mục vào đây")
        title.setObjectName("DropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("Thư mục sẽ được thêm cùng toàn bộ tệp bên trong")
        hint.setObjectName("Muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(hint)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileForge")
        self.resize(1040, 720)
        self.setMinimumSize(860, 600)

        self.paths: list[str] = []
        self.worker: ArchiveWorker | None = None
        self.busy = False
        self.icon_provider = QFileIconProvider()

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 22, 26, 22)
        outer.setSpacing(16)

        # Header: brand and the two primary ways to add files.
        header = QHBoxLayout()
        header.setSpacing(9)

        brand = QLabel("✦  FileForge")
        brand.setObjectName("Brand")
        header.addWidget(brand)
        header.addStretch()

        self.add_files_btn = QPushButton("＋  Thêm tệp")
        self.add_files_btn.setToolTip("Chọn một hoặc nhiều tệp để nén")
        self.add_files_btn.clicked.connect(self.choose_files)

        self.add_folder_btn = QPushButton("＋  Thêm thư mục")
        self.add_folder_btn.setToolTip("Thêm toàn bộ tệp trong một thư mục")
        self.add_folder_btn.clicked.connect(self.choose_folder)

        header.addWidget(self.add_files_btn)
        header.addWidget(self.add_folder_btn)
        outer.addLayout(header)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_paths)
        outer.addWidget(self.drop_area)

        # File queue: keep the visible information to filename and size.
        queue_panel = QFrame()
        queue_panel.setObjectName("Panel")
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(16, 14, 16, 14)
        queue_layout.setSpacing(11)

        queue_header = QHBoxLayout()
        queue_header.setSpacing(10)

        section = QLabel("Tệp đã chọn")
        section.setObjectName("Section")
        queue_header.addWidget(section)

        self.queue_summary = QLabel("0 tệp  ·  0 B")
        self.queue_summary.setObjectName("Muted")
        queue_header.addWidget(self.queue_summary)
        queue_header.addStretch()

        self.remove_btn = QPushButton("Xóa mục chọn")
        self.remove_btn.setToolTip("Xóa các tệp đang chọn khỏi danh sách")
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
        empty_label = QLabel("Danh sách đang trống")
        empty_label.setObjectName("Muted")
        empty_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.queue_stack.addWidget(empty_state)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["TÊN TỆP", "DUNG LƯỢNG"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
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

        # Primary action strip.
        action_panel = QFrame()
        action_panel.setObjectName("Panel")
        action_layout = QVBoxLayout(action_panel)
        action_layout.setContentsMargins(16, 13, 16, 13)
        action_layout.setSpacing(10)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        compression_label = QLabel("Mức nén")
        compression_label.setObjectName("Muted")
        controls.addWidget(compression_label)

        self.compression = QComboBox()
        self.compression.addItems(list(COMPRESSION_OPTIONS.keys()))
        self.compression.setCurrentText("Cân bằng")
        self.compression.setToolTip(
            "Nhanh nhất: ưu tiên tốc độ · Nén tối đa: ưu tiên dung lượng nhỏ"
        )
        controls.addWidget(self.compression)
        controls.addStretch()

        self.zip_button = QPushButton("Tạo tệp ZIP  →")
        self.zip_button.setObjectName("Primary")
        self.zip_button.setMinimumWidth(180)
        self.zip_button.clicked.connect(self.create_archive)
        controls.addWidget(self.zip_button)

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

        self.refresh_queue()

    @staticmethod
    def format_size(size: int) -> str:
        amount = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if amount < 1024 or unit == "TB":
                if unit == "B":
                    return f"{amount:.0f} {unit}"
                return f"{amount:.1f} {unit}"
            amount /= 1024
        return f"{amount:.1f} TB"

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
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn tệp", str(Path.home()), "Tất cả tệp (*)"
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
        self.table.setRowCount(0)
        total_size = 0
        valid_paths: list[str] = []

        for raw in self.paths:
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
            name_item.setFlags(
                name_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )

            size_item = QTableWidgetItem(self.format_size(size))
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            size_item.setFlags(
                size_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, size_item)

            valid_paths.append(str(path))
            total_size += size

        self.paths = valid_paths
        count = len(valid_paths)
        self.queue_summary.setText(
            f"{count} tệp  ·  {self.format_size(total_size)}"
        )
        self.queue_stack.setCurrentIndex(1 if count else 0)
        self.update_controls()

    def update_controls(self):
        has_files = bool(self.paths)
        has_selection = bool(self.table.selectionModel().selectedRows())

        self.remove_btn.setEnabled(has_selection and not self.busy)
        self.clear_btn.setEnabled(has_files and not self.busy)
        self.zip_button.setEnabled(has_files and not self.busy)

    def set_busy(self, busy: bool):
        self.busy = busy
        self.add_files_btn.setEnabled(not busy)
        self.add_folder_btn.setEnabled(not busy)
        self.compression.setEnabled(not busy)
        self.table.setEnabled(not busy)
        self.update_controls()

    def remove_selected(self):
        selected_paths = set()
        for index in self.table.selectionModel().selectedRows():
            item = self.table.item(index.row(), 0)
            if item:
                selected_paths.add(item.data(Qt.ItemDataRole.UserRole))

        self.paths = [
            path for path in self.paths if path not in selected_paths
        ]
        self.refresh_queue()

    def clear_queue(self):
        if self.busy:
            return
        self.paths.clear()
        self.refresh_queue()
        self.progress_area.hide()
        self.progress.setValue(0)

    def create_archive(self):
        if self.busy:
            return

        if not self.paths:
            return

        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu tệp ZIP",
            str(Path.home() / "FileForge.zip"),
            "Tệp ZIP (*.zip)",
        )
        if not destination:
            return

        if not destination.lower().endswith(".zip"):
            destination += ".zip"

        compression_label = self.compression.currentText()
        compression = COMPRESSION_OPTIONS[compression_label]

        self.set_busy(True)
        self.progress_area.show()
        self.progress.setValue(0)
        self.progress_text.setText("Đang chuẩn bị nén…")

        self.worker = ArchiveWorker(
            self.paths.copy(), destination, compression
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.succeeded.connect(self.on_success)
        self.worker.failed.connect(self.on_failure)
        self.worker.finished.connect(lambda: self.set_busy(False))
        self.worker.start()

    def on_progress(self, done: int, total: int, name: str):
        percent = int(done * 100 / total) if total else 100
        self.progress.setValue(percent)
        self.progress_text.setText(f"Đang nén: {name}")

    def on_success(self, path: str):
        self.progress.setValue(100)
        self.progress_text.setText("Đã tạo tệp ZIP thành công")

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Hoàn tất")
        dialog.setText("Tệp ZIP đã được tạo.")
        dialog.setInformativeText(Path(path).name)
        open_folder_btn = dialog.addButton(
            "Mở thư mục", QMessageBox.ButtonRole.ActionRole
        )
        dialog.addButton("Đóng", QMessageBox.ButtonRole.AcceptRole)
        dialog.exec()

        if dialog.clickedButton() == open_folder_btn:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(Path(path).parent))
            )

    def on_failure(self, message: str):
        self.progress_text.setText("Không thể tạo tệp ZIP")
        QMessageBox.critical(
            self, "Lỗi nén tệp", f"Không thể tạo tệp ZIP.\n\n{message}"
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
