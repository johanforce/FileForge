from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView,
)

from fileforge.archive import create_zip


STYLE = """
QMainWindow, QWidget { background: #10131a; color: #e8ecf4; font-family: 'Segoe UI', sans-serif; }
QFrame#Sidebar { background: #151a24; border: 1px solid #252d3b; border-radius: 16px; }
QFrame#Panel { background: #171d28; border: 1px solid #293244; border-radius: 16px; }
QLabel#Muted { color: #8e9aaf; }
QLabel#Hero { font-size: 27px; font-weight: 700; }
QLabel#Section { font-size: 15px; font-weight: 650; }
QPushButton { background: #252e3e; border: 1px solid #344158; border-radius: 9px; padding: 9px 14px; color: #edf2fa; }
QPushButton:hover { background: #303d52; }
QPushButton#Primary { background: #6d63e8; border: 0; font-weight: 650; }
QPushButton#Primary:hover { background: #8178f2; }
QPushButton:disabled { color: #6f7888; background: #202633; }
QComboBox { background: #202838; border: 1px solid #344158; border-radius: 8px; padding: 8px; min-width: 120px; }
QTableWidget { background: #141a24; border: 0; gridline-color: #273143; border-radius: 10px; }
QHeaderView::section { background: #202838; color: #aab5c8; padding: 9px; border: 0; }
QProgressBar { background: #242d3c; border: 0; border-radius: 6px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #6d63e8; border-radius: 6px; }
"""


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
                self.paths, self.destination, self.compression,
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
        self.setObjectName("Panel")
        self.setMinimumHeight(132)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Drop files or folders here")
        title.setStyleSheet("font-size: 17px; font-weight: 650;")
        subtitle = QLabel("Files stay on your device. Folders are added recursively.")
        subtitle.setObjectName("Muted")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileForge")
        self.resize(1120, 760)
        self.paths: list[str] = []
        self.worker: ArchiveWorker | None = None

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        brand = QLabel("✦  FileForge")
        brand.setStyleSheet("font-size: 21px; font-weight: 750; padding: 10px 4px 22px;")
        side.addWidget(brand)
        for label in ("▦   Workspace", "▣   Archive", "⇄   Converter  ·  Soon"):
            item = QLabel(label)
            item.setStyleSheet("padding: 12px 9px; color: #c5cddd;")
            side.addWidget(item)
        side.addStretch()
        version = QLabel("VERSION 0.1.0")
        version.setObjectName("Muted")
        side.addWidget(version)
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setSpacing(15)
        outer.addLayout(main, 1)

        top = QHBoxLayout()
        heading = QVBoxLayout()
        hero = QLabel("Your files, in good order.")
        hero.setObjectName("Hero")
        subtitle = QLabel("Collect files and create a ZIP archive in a few clicks.")
        subtitle.setObjectName("Muted")
        heading.addWidget(hero)
        heading.addWidget(subtitle)
        top.addLayout(heading)
        top.addStretch()
        add_files = QPushButton("+ Add files")
        add_files.clicked.connect(self.choose_files)
        add_folder = QPushButton("Add folder")
        add_folder.clicked.connect(self.choose_folder)
        top.addWidget(add_files)
        top.addWidget(add_folder)
        main.addLayout(top)

        stats = QHBoxLayout()
        self.file_stat = self.stat_card("FILES IN QUEUE", "0")
        self.size_stat = self.stat_card("TOTAL SIZE", "0 B")
        self.type_stat = self.stat_card("FILE TYPES", "0")
        stats.addWidget(self.file_stat)
        stats.addWidget(self.size_stat)
        stats.addWidget(self.type_stat)
        main.addLayout(stats)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_paths)
        main.addWidget(self.drop_area)

        queue_panel = QFrame()
        queue_panel.setObjectName("Panel")
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(15, 14, 15, 15)
        queue_header = QHBoxLayout()
        section = QLabel("File queue")
        section.setObjectName("Section")
        self.queue_count = QLabel("0 items")
        self.queue_count.setObjectName("Muted")
        queue_header.addWidget(section)
        queue_header.addStretch()
        queue_header.addWidget(self.queue_count)
        clear_btn = QPushButton("Clear queue")
        clear_btn.clicked.connect(self.clear_queue)
        queue_header.addWidget(clear_btn)
        remove_btn = QPushButton("Remove selected")
        remove_btn.clicked.connect(self.remove_selected)
        queue_header.addWidget(remove_btn)
        queue_layout.addLayout(queue_header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["NAME", "LOCATION", "SIZE"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(230)
        queue_layout.addWidget(self.table)
        main.addWidget(queue_panel, 1)

        bottom = QFrame()
        bottom.setObjectName("Panel")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(15, 12, 15, 12)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Compression"))
        self.compression = QComboBox()
        self.compression.addItems(["Fast", "Balanced", "Best"])
        self.compression.setCurrentText("Balanced")
        controls.addWidget(self.compression)
        controls.addSpacing(12)
        self.output_label = QLabel("Output: choose when creating")
        self.output_label.setObjectName("Muted")
        controls.addWidget(self.output_label, 1)
        self.zip_button = QPushButton("Create ZIP  →")
        self.zip_button.setObjectName("Primary")
        self.zip_button.clicked.connect(self.create_archive)
        controls.addWidget(self.zip_button)
        bottom_layout.addLayout(controls)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Ready")
        bottom_layout.addWidget(self.progress)
        main.addWidget(bottom)

    def stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Panel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        caption = QLabel(title)
        caption.setObjectName("Muted")
        number = QLabel(value)
        number.setStyleSheet("font-size: 23px; font-weight: 700;")
        layout.addWidget(caption)
        layout.addWidget(number)
        card.value_label = number
        return card

    @staticmethod
    def format_size(size: int) -> str:
        amount = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if amount < 1024 or unit == "TB":
                return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
            amount /= 1024
        return f"{amount:.1f} TB"

    def add_paths(self, paths: list[str]):
        added = 0
        for raw in paths:
            path = Path(raw).expanduser()
            if not path.exists():
                continue
            if path.is_file():
                candidates = [path]
            elif path.is_dir():
                candidates = [p for p in path.rglob("*") if p.is_file()]
            else:
                continue
            for candidate in candidates:
                value = str(candidate.resolve())
                if value not in self.paths:
                    self.paths.append(value)
                    added += 1
        self.refresh_queue()
        if added == 0 and paths:
            self.progress.setFormat("No new files added")

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add files")
        if files:
            self.add_paths(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add folder")
        if folder:
            self.add_paths([folder])

    def refresh_queue(self):
        self.table.setRowCount(0)
        total = 0
        extensions = set()
        valid = []
        for raw in self.paths:
            path = Path(raw)
            if not path.is_file():
                continue
            size = path.stat().st_size
            total += size
            extensions.add(path.suffix.lower() or "no extension")
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, value in enumerate((path.name, str(path.parent), self.format_size(size))):
                self.table.setItem(row, col, QTableWidgetItem(value))
            valid.append(raw)
        self.paths = valid
        self.file_stat.value_label.setText(str(len(valid)))
        self.size_stat.value_label.setText(self.format_size(total))
        self.type_stat.value_label.setText(str(len(extensions)))
        self.queue_count.setText(f"{len(valid)} items")

    def remove_selected(self):
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        for row in rows:
            item = self.table.item(row, 1)
            name = self.table.item(row, 0)
            if item and name:
                target = str(Path(item.text()) / name.text())
                if target in self.paths:
                    self.paths.remove(target)
        self.refresh_queue()

    def clear_queue(self):
        self.paths.clear()
        self.refresh_queue()
        self.progress.setValue(0)
        self.progress.setFormat("Ready")

    def create_archive(self):
        if self.worker and self.worker.isRunning():
            return
        if not self.paths:
            QMessageBox.information(self, "Nothing to archive", "Add at least one file first.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self, "Save ZIP archive", str(Path.home() / "FileForge-archive.zip"),
            "ZIP archive (*.zip)"
        )
        if not destination:
            return
        if not destination.lower().endswith(".zip"):
            destination += ".zip"
        self.output_label.setText(f"Output: {destination}")
        self.zip_button.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setFormat("Preparing archive…")
        self.worker = ArchiveWorker(self.paths.copy(), destination, self.compression.currentText())
        self.worker.progress.connect(self.on_progress)
        self.worker.succeeded.connect(self.on_success)
        self.worker.failed.connect(self.on_failure)
        self.worker.finished.connect(lambda: self.zip_button.setEnabled(True))
        self.worker.start()

    def on_progress(self, done: int, total: int, name: str):
        percent = int(done * 100 / total) if total else 100
        self.progress.setValue(percent)
        self.progress.setFormat(f"{percent}%  ·  {name}")

    def on_success(self, path: str):
        self.progress.setValue(100)
        self.progress.setFormat("Archive created successfully")
        QMessageBox.information(self, "ZIP created", f"Your archive is ready:\n{path}")

    def on_failure(self, message: str):
        self.progress.setFormat("Archive failed")
        QMessageBox.critical(self, "Could not create ZIP", message)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
