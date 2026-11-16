import json
import tempfile
import unittest
from pathlib import Path

from fileforge.app_services import TaskHistoryStore


class TaskHistoryStoreTests(unittest.TestCase):
    def test_records_metadata_without_storing_input_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "app" / "history.sqlite3"
            source = root / "private" / "customer-list.csv"
            source.parent.mkdir()
            source.write_text("not stored in history", encoding="utf-8")
            output = root / "output"
            output.mkdir()

            store = TaskHistoryStore(database)
            record_id = store.record(
                operation="Nén ZIP",
                status="success",
                inputs=[source],
                outputs=[output / "bundle.zip"],
                output_folder=output,
                duration_ms=1234,
                summary="Đã tạo bundle.zip",
            )

            self.assertGreater(record_id, 0)
            record = store.recent()[0]
            self.assertEqual(record["input_names"], ["customer-list.csv"])
            self.assertNotIn(str(source), json.dumps(record, ensure_ascii=False))
            self.assertEqual(record["output_folder"], str(output))
            self.assertEqual(record["duration_ms"], 1234)
            self.assertEqual(record["status"], "success")

    def test_history_is_bounded_and_newest_records_are_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskHistoryStore(Path(temp_dir) / "history.sqlite3", max_entries=2)
            store.record("Nén ZIP", "success", summary="one")
            store.record("Giải nén ZIP", "partial", summary="two")
            store.record("Chuyển ảnh", "failed", summary="three")

            records = store.recent()
            self.assertEqual(len(records), 2)
            self.assertEqual([item["summary"] for item in records], ["three", "two"])

    def test_cancelled_status_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskHistoryStore(Path(temp_dir) / "history.sqlite3")
            store.record(
                "Chuyển ảnh", "cancelled", summary="Đã hủy · giữ lại 1 kết quả",
            )
            record = store.recent()[0]
            self.assertEqual(record["status"], "cancelled")

    def test_clear_removes_all_task_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TaskHistoryStore(Path(temp_dir) / "history.sqlite3")
            store.record("Nén ZIP", "success")
            store.clear()
            self.assertEqual(store.recent(), [])


if __name__ == "__main__":
    unittest.main()
