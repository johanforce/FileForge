"""Searchable task history dialog."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fileforge.app_services import TaskHistoryStore


class TaskHistoryDialog(QDialog):
    """Show recent file-processing tasks and allow opening their output folders."""

    HEADERS = ["Thời gian", "Tác vụ", "Trạng thái", "Số mục", "Thời lượng", "Kết quả"]

    def __init__(self, history: TaskHistoryStore, parent: QWidget | None = None):
        super().__init__(parent)
        self.history = history
        self.records: list[dict] = []
        self.setWindowTitle("Lịch sử tác vụ – FileForge")
        self.resize(900, 520)
        self.setMinimumSize(700, 380)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Lịch sử tác vụ")
        title.setObjectName("Section")
        header.addWidget(title)
        header.addStretch()
        self.count_label = QLabel()
        self.count_label.setObjectName("Muted")
        header.addWidget(self.count_label)
        root.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Tìm theo tác vụ, tên tệp hoặc trạng thái…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.apply_filter)
        root.addWidget(self.search)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(False)
        self.table.itemDoubleClicked.connect(lambda _item: self.show_selected_details())
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.open_button = QPushButton("Mở thư mục kết quả")
        self.open_button.clicked.connect(self.open_selected_folder)
        self.open_button.setEnabled(False)
        self.table.itemSelectionChanged.connect(self._update_actions)
        footer.addWidget(self.open_button)

        self.details_button = QPushButton("Chi tiết")
        self.details_button.clicked.connect(self.show_selected_details)
        self.details_button.setEnabled(False)
        footer.addWidget(self.details_button)

        self.clear_button = QPushButton("Xóa lịch sử")
        self.clear_button.clicked.connect(self.clear_history)
        footer.addWidget(self.clear_button)
        footer.addStretch()

        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        root.addLayout(footer)

        self.reload()

    def reload(self):
        self.records = self.history.recent()
        self.table.setRowCount(0)
        for record in self.records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            status_text = {
                "success": "Thành công",
                "partial": "Một phần",
                "failed": "Thất bại",
            }.get(record["status"], record["status"])
            duration = record["duration_ms"]
            duration_text = f"{duration / 1000:.1f} giây" if duration >= 1000 else f"{duration} ms"
            summary = record["summary"] or record["error_message"] or "—"
            values = [
                record["created_at"].replace("T", " "),
                record["operation"],
                status_text,
                str(record["input_count"]),
                duration_text,
                summary,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, record["id"])
                item.setToolTip(value)
                self.table.setItem(row, column, item)

        self.count_label.setText(f"{len(self.records)} tác vụ gần đây")
        self.apply_filter(self.search.text())

    def apply_filter(self, query: str):
        needle = query.strip().casefold()
        visible = 0
        for row, record in enumerate(self.records):
            searchable = " ".join(
                [
                    record["operation"],
                    record["status"],
                    {
                        "success": "Thành công",
                        "partial": "Một phần",
                        "failed": "Thất bại",
                    }.get(record["status"], record["status"]),
                    record["summary"],
                    record["error_message"],
                    *record["input_names"],
                ]
            ).casefold()
            matches = not needle or needle in searchable
            self.table.setRowHidden(row, not matches)
            visible += int(matches)
        self.count_label.setText(
            f"{visible}/{len(self.records)} tác vụ" if needle else f"{len(self.records)} tác vụ gần đây"
        )

    def _selected_record(self) -> dict | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        record_id = self.table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return next((item for item in self.records if item["id"] == record_id), None)

    def _update_actions(self):
        record = self._selected_record()
        folder = self._folder_for_record(record) if record else None
        self.open_button.setEnabled(bool(folder and folder.is_dir()))
        self.details_button.setEnabled(record is not None)

    def show_selected_details(self):
        record = self._selected_record()
        if not record:
            return
        status_text = {
            "success": "Thành công",
            "partial": "Một phần",
            "failed": "Thất bại",
        }.get(record["status"], record["status"])
        lines = [
            f"Tác vụ: {record['operation']}",
            f"Trạng thái: {status_text}",
            f"Thời gian: {record['created_at'].replace('T', ' ')}",
            f"Số tệp đầu vào: {record['input_count']}",
            f"Thời lượng: {record['duration_ms']} ms",
            "",
            "Tệp đầu vào:",
            *(record["input_names"] or ["Không có"]),
            "",
            f"Thư mục đầu ra: {record['output_folder'] or 'Không có'}",
        ]
        if record["output_paths"]:
            lines.extend(["", "Kết quả:", *record["output_paths"]])
        if record["summary"]:
            lines.extend(["", "Tóm tắt:", record["summary"]])
        if record["error_message"]:
            lines.extend(["", "Chi tiết lỗi:", record["error_message"]])
        QMessageBox.information(
            self, "Chi tiết tác vụ", "\n".join(lines)
        )

    @staticmethod
    def _folder_for_record(record: dict | None) -> Path | None:
        if not record:
            return None
        candidates = [record.get("output_folder", "")]
        for output in record.get("output_paths", []):
            path = Path(output).expanduser()
            candidates.append(str(path if path.is_dir() else path.parent))
        for candidate in candidates:
            if candidate:
                path = Path(candidate).expanduser()
                if path.is_dir():
                    return path
        return None

    def open_selected_folder(self):
        folder = self._folder_for_record(self._selected_record())
        if folder and folder.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def clear_history(self):
        if not self.records:
            return
        answer = QMessageBox.question(
            self,
            "Xóa lịch sử",
            "Xóa toàn bộ lịch sử tác vụ trên máy này? Thao tác này không xóa các tệp kết quả.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.reload()
