import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fileforge.app_services import TaskHistoryStore
from fileforge.history_dialog import TaskHistoryDialog


class TaskHistoryDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_history_dialog_lists_and_filters_tasks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "output"
            output.mkdir()
            store = TaskHistoryStore(root / "history.sqlite3")
            store.record(
                "Nén ZIP",
                "success",
                inputs=[root / "report.txt"],
                outputs=[output / "report.zip"],
                output_folder=output,
                summary="Đã tạo report.zip",
            )
            store.record(
                "Chuyển ảnh sang WEBP",
                "partial",
                inputs=[root / "portrait.png"],
                outputs=[],
                output_folder=output,
                summary="Hoàn tất 0/1 mục",
                error_message="Không đọc được ảnh",
            )

            store.record(
                "Nén ZIP",
                "cancelled",
                inputs=[root / "archive-source.bin"],
                output_folder=output,
                summary="Đã hủy theo yêu cầu người dùng",
            )

            dialog = TaskHistoryDialog(store)
            self.assertEqual(dialog.table.rowCount(), 3)
            self.assertEqual(dialog.table.item(0, 2).text(), "Đã hủy")

            dialog.search.setText("portrait")
            self.app.processEvents()
            self.assertFalse(dialog.table.isRowHidden(0))
            self.assertTrue(dialog.table.isRowHidden(1))
            self.assertIn("1/3", dialog.count_label.text())

            dialog.search.clear()
            self.app.processEvents()
            self.assertFalse(dialog.table.isRowHidden(0))
            self.assertFalse(dialog.table.isRowHidden(1))
            self.assertFalse(dialog.table.isRowHidden(2))
            dialog.close()


if __name__ == "__main__":
    unittest.main()
