import tempfile
import unittest
import zipfile
from pathlib import Path

from fileforge.extraction import extract_archives
from fileforge.task_control import TaskCancelledError


class ExtractionTests(unittest.TestCase):
    def test_extracts_files_into_archive_named_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "documents.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("notes/readme.txt", "hello")
                archive.writestr("todo.txt", "next")

            destination = root / "out"
            outputs, errors = extract_archives([archive_path], destination)

            self.assertEqual(errors, [])
            self.assertEqual(len(outputs), 1)
            self.assertEqual(
                (outputs[0] / "notes" / "readme.txt").read_text(encoding="utf-8"),
                "hello",
            )
            self.assertEqual(
                (outputs[0] / "todo.txt").read_text(encoding="utf-8"),
                "next",
            )

    def test_cancellation_removes_temporary_extraction_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "large.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("large.bin", b"x" * (3 * 1024 * 1024))
            destination = root / "out"
            calls = 0

            def cancel_during_copy():
                nonlocal calls
                calls += 1
                return calls >= 5

            with self.assertRaises(TaskCancelledError):
                extract_archives(
                    [archive_path], destination, is_cancelled=cancel_during_copy
                )

            self.assertEqual(list(destination.iterdir()), [])

    def test_rejects_parent_directory_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "malicious.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../outside.txt", "not allowed")

            destination = root / "out"
            outputs, errors = extract_archives([archive_path], destination)

            self.assertEqual(outputs, [])
            self.assertEqual(len(errors), 1)
            self.assertFalse((root / "outside.txt").exists())
            self.assertEqual(list(destination.iterdir()), [])

    def test_rejects_non_zip_input_and_continues_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid = root / "bad.zip"
            invalid.write_text("not a zip", encoding="utf-8")
            good = root / "good.zip"
            with zipfile.ZipFile(good, "w") as archive:
                archive.writestr("ok.txt", "ok")

            outputs, errors = extract_archives([invalid, good], root / "out")

            self.assertEqual(len(outputs), 1)
            self.assertEqual(len(errors), 1)
            self.assertEqual((outputs[0] / "ok.txt").read_text(), "ok")


if __name__ == "__main__":
    unittest.main()
