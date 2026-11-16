"""User preferences dialog for FileForge.

The application stores preferences with QSettings so paths and UI/session state
are persisted in the platform-appropriate user configuration directory.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PreferencesDialog(QDialog):
    """Small preferences window for persistent desktop-app behavior."""

    def __init__(self, settings: QSettings, parent: QWidget | None = None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Tùy chọn FileForge")
        self.setMinimumWidth(540)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(16)

        intro = QLabel("Thiết lập cách FileForge ghi nhớ phiên làm việc và thư mục.")
        intro.setWordWrap(True)
        intro.setObjectName("Muted")
        root.addWidget(intro)

        self.restore_session = QCheckBox(
            "Khôi phục kích thước cửa sổ và công cụ đã mở lần trước"
        )
        self.restore_session.setChecked(
            settings.value("preferences/restore_session", True, type=bool)
        )
        root.addWidget(self.restore_session)

        self.remember_last_directory = QCheckBox(
            "Ghi nhớ thư mục gần nhất khi mở và lưu tệp"
        )
        self.remember_last_directory.setChecked(
            settings.value("preferences/remember_last_directory", True, type=bool)
        )
        root.addWidget(self.remember_last_directory)

        self.remember_operation_options = QCheckBox(
            "Ghi nhớ tùy chọn xử lý gần nhất (mức nén, định dạng và chất lượng ảnh)"
        )
        self.remember_operation_options.setChecked(
            settings.value("preferences/remember_operation_options", True, type=bool)
        )
        self.remember_operation_options.setWordWrap(True)
        root.addWidget(self.remember_operation_options)

        root.addSpacing(2)
        output_label = QLabel("Thư mục đầu ra ưu tiên")
        output_label.setObjectName("Section")
        root.addWidget(output_label)

        output_hint = QLabel(
            "Thư mục này được dùng làm vị trí gợi ý khi lưu ZIP hoặc giải nén/chuyển ảnh. "
            "Để trống để dùng thư mục gần nhất hoặc thư mục cá nhân."
        )
        output_hint.setWordWrap(True)
        output_hint.setObjectName("Muted")
        root.addWidget(output_hint)

        output_row = QHBoxLayout()
        self.output_directory = QLineEdit(
            str(settings.value("paths/default_output_directory", "") or "")
        )
        self.output_directory.setPlaceholderText("Mặc định: thư mục gần nhất")
        self.output_directory.setClearButtonEnabled(True)
        output_row.addWidget(self.output_directory, 1)

        browse_button = QPushButton("Duyệt…")
        browse_button.clicked.connect(self.choose_output_directory)
        output_row.addWidget(browse_button)
        root.addLayout(output_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def choose_output_directory(self):
        current = self.output_directory.text().strip()
        start = current if current and Path(current).is_dir() else str(Path.home())
        selected = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục đầu ra ưu tiên", start
        )
        if selected:
            self.output_directory.setText(selected)

    def is_output_directory_valid(self) -> bool:
        output_directory = self.output_directory.text().strip()
        return not output_directory or Path(output_directory).expanduser().is_dir()

    def accept(self):
        if not self.is_output_directory_valid():
            QMessageBox.warning(
                self,
                "Thư mục không hợp lệ",
                "Thư mục đầu ra đã chọn không tồn tại hoặc không thể truy cập.",
            )
            self.output_directory.setFocus()
            return
        super().accept()

    def save_to_settings(self) -> None:
        """Persist the values after the dialog has passed validation."""
        output_directory = self.output_directory.text().strip()
        self.settings.setValue(
            "preferences/restore_session", self.restore_session.isChecked()
        )
        self.settings.setValue(
            "preferences/remember_last_directory",
            self.remember_last_directory.isChecked(),
        )
        self.settings.setValue(
            "preferences/remember_operation_options",
            self.remember_operation_options.isChecked(),
        )
        self.settings.setValue(
            "paths/default_output_directory",
            str(Path(output_directory).expanduser()) if output_directory else "",
        )
        self.settings.sync()
