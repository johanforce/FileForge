"""User preferences dialog for FileForge.

The application stores preferences with QSettings so paths and UI/session state
are persisted in the platform-appropriate user configuration directory.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from fileforge.i18n import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, translate_object_tree, translate_text


class PreferencesDialog(QDialog):
    """Small preferences window for persistent desktop-app behavior."""

    def __init__(
        self,
        settings: QSettings,
        parent: QWidget | None = None,
        tray_available: bool = True,
    ):
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

        language_row = QHBoxLayout()
        language_label = QLabel("Ngôn ngữ")
        language_label.setObjectName("Section")
        language_row.addWidget(language_label)
        self.language_combo = QComboBox()
        for language_code in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(LANGUAGE_NAMES[language_code], language_code)
        saved_language = str(settings.value("preferences/language", "vi") or "vi")
        language_index = self.language_combo.findData(saved_language)
        self.language_combo.setCurrentIndex(max(0, language_index))
        language_row.addWidget(self.language_combo, 1)
        root.addLayout(language_row)

        language_hint = QLabel(
            "Thay đổi ngôn ngữ có hiệu lực ngay lập tức và được lưu cho lần mở tiếp theo."
        )
        language_hint.setWordWrap(True)
        language_hint.setObjectName("Muted")
        root.addWidget(language_hint)

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

        self.minimize_to_tray = QCheckBox(
            "Thu nhỏ FileForge xuống khay hệ thống khi nhấn nút đóng"
        )
        self.minimize_to_tray.setChecked(
            settings.value("preferences/minimize_to_tray", False, type=bool)
        )
        self.minimize_to_tray.setEnabled(tray_available)
        if not tray_available:
            self.minimize_to_tray.setToolTip(
                "Khay hệ thống hiện không khả dụng trên môi trường này."
            )
        root.addWidget(self.minimize_to_tray)

        self.show_notifications = QCheckBox(
            "Hiển thị thông báo khi tác vụ hoàn tất trong lúc ứng dụng đang ẩn"
        )
        self.show_notifications.setChecked(
            settings.value("preferences/show_notifications", True, type=bool)
        )
        self.show_notifications.setEnabled(tray_available)
        root.addWidget(self.show_notifications)

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
        translate_object_tree(self)

    def choose_output_directory(self):
        current = self.output_directory.text().strip()
        start = current if current and Path(current).is_dir() else str(Path.home())
        selected = QFileDialog.getExistingDirectory(
            self, translate_text("Chọn thư mục đầu ra ưu tiên"), start
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
                translate_text("Thư mục không hợp lệ"),
                translate_text("Thư mục đầu ra đã chọn không tồn tại hoặc không thể truy cập."),
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
            "preferences/minimize_to_tray",
            self.minimize_to_tray.isChecked(),
        )
        self.settings.setValue(
            "preferences/show_notifications",
            self.show_notifications.isChecked(),
        )
        self.settings.setValue(
            "preferences/language",
            str(self.language_combo.currentData() or "vi"),
        )
        self.settings.setValue(
            "paths/default_output_directory",
            str(Path(output_directory).expanduser()) if output_directory else "",
        )
        self.settings.sync()
