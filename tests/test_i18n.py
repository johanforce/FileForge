import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from fileforge import __version__
from fileforge.i18n import (
    get_language,
    set_language,
    translate_object_tree,
    translate_text,
)


class I18nTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.previous_language = get_language()

    def tearDown(self):
        set_language(self.previous_language)

    def test_application_version_is_1_0_0(self):
        self.assertEqual(__version__, "1.0.0")

    def test_static_and_dynamic_translation_round_trip(self):
        set_language("en")
        self.assertEqual(translate_text("Sẵn sàng"), "Ready")
        self.assertEqual(translate_text("Đang nén: archive.zip"), "Creating ZIP: archive.zip")
        self.assertEqual(translate_text("Xử lý dữ liệu: JSON → String"), "Process data: JSON → String")

        set_language("vi")
        self.assertEqual(translate_text("Ready"), "Sẵn sàng")
        self.assertEqual(translate_text("Creating ZIP: archive.zip"), "Đang nén: archive.zip")
        self.assertEqual(translate_text("Process data: JSON → String"), "Xử lý dữ liệu: JSON → String")

    def test_dynamic_counts_and_durations_translate_both_ways(self):
        set_language("en")
        self.assertEqual(translate_text("3 tệp  ·  1.5 MB"), "3 files  ·  1.5 MB")
        self.assertEqual(translate_text("2.5 giây"), "2.5 seconds")
        self.assertEqual(translate_text("4 tác vụ gần đây"), "4 recent task(s)")
        self.assertEqual(translate_text("Hoàn tất 2/3 mục"), "Completed 2/3 item(s)")
        self.assertEqual(translate_text("Đã giữ lại 2 kết quả hoàn tất"), "Kept 2 completed result(s)")

        set_language("vi")
        self.assertEqual(translate_text("3 files  ·  1.5 MB"), "3 tệp  ·  1.5 MB")
        self.assertEqual(translate_text("2.5 seconds"), "2.5 giây")
        self.assertEqual(translate_text("4 recent task(s)"), "4 tác vụ gần đây")
        self.assertEqual(translate_text("Completed 2/3 item(s)"), "Hoàn tất 2/3 mục")
        self.assertEqual(translate_text("Kept 2 completed result(s)"), "Đã giữ lại 2 kết quả hoàn tất")

    def test_unsupported_language_falls_back_to_vietnamese(self):
        set_language("fr")
        self.assertEqual(get_language(), "vi")

    def test_widget_tree_translates_labels_placeholders_tabs_and_headers(self):
        root = QWidget()
        layout = QVBoxLayout(root)

        label = QLabel("Sẵn sàng")
        button = QPushButton("Xóa tất cả")
        editor = QLineEdit()
        editor.setPlaceholderText("Tìm trong kết quả…")
        combo = QComboBox()
        combo.addItem("Cân bằng", "Balanced")
        tabs = QTabWidget()
        tabs.addTab(QWidget(), "Chuyển ảnh")
        table = QTableWidget(0, 1)
        table.setHorizontalHeaderLabels(["TÊN TỆP"])

        for widget in (label, button, editor, combo, tabs, table):
            layout.addWidget(widget)

        set_language("en")
        translate_object_tree(root)
        self.assertEqual(label.text(), "Ready")
        self.assertEqual(button.text(), "Clear all")
        self.assertEqual(editor.placeholderText(), "Find in results…")
        self.assertEqual(combo.currentText(), "Balanced")
        self.assertEqual(combo.currentData(), "Balanced")
        self.assertEqual(tabs.tabText(0), "Image conversion")
        self.assertEqual(table.horizontalHeaderItem(0).text(), "FILE NAME")

        set_language("vi")
        translate_object_tree(root)
        self.assertEqual(label.text(), "Sẵn sàng")
        self.assertEqual(button.text(), "Xóa tất cả")
        self.assertEqual(editor.placeholderText(), "Tìm trong kết quả…")
        self.assertEqual(combo.currentText(), "Cân bằng")
        self.assertEqual(combo.currentData(), "Balanced")
        self.assertEqual(tabs.tabText(0), "Chuyển ảnh")
        self.assertEqual(table.horizontalHeaderItem(0).text(), "TÊN TỆP")
        root.close()


if __name__ == "__main__":
    unittest.main()
