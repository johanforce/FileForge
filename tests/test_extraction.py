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
                return calls >= 6

            with self.assertRaises(TaskCancelledError):
                extract_archives(
                    [archive_path], destination, is_cancelled=cancel_during_copy
                )

            self.assertEqual(list(destination.iterdir()), [])

    def test_cancellation_reports_archives_already_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first.zip"
            second = root / "second.zip"
            with zipfile.ZipFile(first, "w") as archive:
                archive.writestr("first.txt", "first")
            with zipfile.ZipFile(second, "w") as archive:
                archive.writestr("second.txt", "second")
            destination = root / "out"
            calls = 0

            def cancel_before_second_archive():
                nonlocal calls
                calls += 1
                return calls >= 8

            with self.assertRaises(TaskCancelledError) as raised:
                extract_archives(
                    [first, second], destination,
                    is_cancelled=cancel_before_second_archive,
                )

            self.assertEqual(len(raised.exception.completed_outputs), 1)
            completed_folder = Path(raised.exception.completed_outputs[0])
            self.assertTrue((completed_folder / "first.txt").is_file())
            self.assertEqual([p.name for p in destination.iterdir()], ["first"])

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
