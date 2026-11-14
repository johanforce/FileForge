import tempfile
import unittest
import zipfile
from pathlib import Path

from fileforge.archive import create_zip


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
