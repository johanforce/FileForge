import tempfile
import unittest
import zipfile
from pathlib import Path

from fileforge.archive import create_zip
from fileforge.task_control import TaskCancelledError


class ArchiveTests(unittest.TestCase):
    def test_create_zip_with_file_and_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            single = root / "hello.txt"
            single.write_text("hello", encoding="utf-8")
            folder = root / "docs"
            folder.mkdir()
            (folder / "guide.txt").write_text("guide", encoding="utf-8")
            output = root / "out.zip"

            create_zip([single, folder], output)

            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.read("hello.txt"), b"hello")
                self.assertEqual(archive.read("docs/guide.txt"), b"guide")
                self.assertIsNone(archive.testzip())

    def test_empty_folder_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "empty"
            folder.mkdir()
            with self.assertRaises(ValueError):
                create_zip([folder], Path(tmp) / "empty.zip")

    def test_invalid_compression_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "a.txt"
            source.write_text("a", encoding="utf-8")
            with self.assertRaises(ValueError):
                create_zip([source], Path(tmp) / "x.zip", "Unknown")

    def test_cancellation_preserves_existing_archive_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "large.bin"
            source.write_bytes(b"x" * (3 * 1024 * 1024))
            target = root / "out.zip"
            target.write_bytes(b"previous archive")
            calls = 0

            def cancel_after_first_chunk():
                nonlocal calls
                calls += 1
                return calls >= 4

            with self.assertRaises(TaskCancelledError):
                create_zip(
                    [source], target, is_cancelled=cancel_after_first_chunk
                )

            self.assertEqual(target.read_bytes(), b"previous archive")
            self.assertEqual(list(root.glob(".out.zip.*.tmp")), [])

    def test_cancellation_during_validation_keeps_previous_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "large.bin"
            source.write_bytes(b"y" * (3 * 1024 * 1024))
            target = root / "out.zip"
            target.write_bytes(b"existing")
            calls = 0

            def cancel_during_validation():
                nonlocal calls
                calls += 1
                return calls >= 10

            with self.assertRaises(TaskCancelledError):
                create_zip(
                    [source], target, is_cancelled=cancel_during_validation
                )

            self.assertEqual(target.read_bytes(), b"existing")
            self.assertEqual(list(root.glob(".out.zip.*.tmp")), [])
    def test_existing_destination_is_preserved_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "a.txt"
            source.write_text("a", encoding="utf-8")
            target = root / "out.zip"
            target.write_bytes(b"previous")
            missing = root / "missing.txt"
            with self.assertRaises(FileNotFoundError):
                create_zip([missing], target, "Balanced")
            self.assertEqual(target.read_bytes(), b"previous")


if __name__ == "__main__":
    unittest.main()
