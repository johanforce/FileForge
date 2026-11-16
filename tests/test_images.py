import tempfile
import unittest
from pathlib import Path

from PIL import Image

from fileforge.images import convert_images
from fileforge.task_control import TaskCancelledError


class ImageConversionTests(unittest.TestCase):
    def test_converts_png_to_jpeg_and_flattens_transparency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "transparent.png"
            Image.new("RGBA", (8, 8), (255, 0, 0, 0)).save(source)

            outputs, errors = convert_images([source], root / "converted", "JPG", 95)

            self.assertEqual(errors, [])
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0].suffix, ".jpg")
            with Image.open(outputs[0]) as result:
                self.assertEqual(result.mode, "RGB")
                self.assertEqual(result.size, (8, 8))
                red, green, blue = result.getpixel((4, 4))
                self.assertGreater(red, 240)
                self.assertGreater(green, 240)
                self.assertGreater(blue, 240)

    def test_converts_to_webp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "sample.bmp"
            Image.new("RGB", (12, 9), (20, 40, 60)).save(source)

            outputs, errors = convert_images([source], root / "out", "WEBP", 85)

            self.assertEqual(errors, [])
            self.assertEqual(len(outputs), 1)
            with Image.open(outputs[0]) as result:
                self.assertEqual(result.format, "WEBP")
                self.assertEqual(result.size, (12, 9))

    def test_cancellation_does_not_publish_partial_image_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "photo.png"
            Image.new("RGB", (32, 32), (20, 40, 60)).save(source)
            output_dir = root / "out"
            calls = 0

            def cancel_before_publish():
                nonlocal calls
                calls += 1
                return calls >= 4

            with self.assertRaises(TaskCancelledError):
                convert_images(
                    [source], output_dir, "JPG", 90,
                    is_cancelled=cancel_before_publish,
                )

            self.assertEqual(list(output_dir.glob("*.jpg")), [])
            self.assertEqual(list(output_dir.glob(".fileforge-image-*")), [])

    def test_continues_after_corrupt_image_and_avoids_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "photo.png"
            bad = root / "broken.png"
            Image.new("RGB", (4, 4), (1, 2, 3)).save(good)
            bad.write_text("not an image", encoding="utf-8")
            output_dir = root / "out"
            output_dir.mkdir()
            (output_dir / "photo.jpg").write_bytes(b"keep existing")

            outputs, errors = convert_images(
                [good, bad], output_dir, "JPG", 90
            )

            self.assertEqual(len(outputs), 1)
            self.assertEqual(len(errors), 1)
            self.assertEqual(outputs[0].name, "photo_2.jpg")
            self.assertEqual((output_dir / "photo.jpg").read_bytes(), b"keep existing")


if __name__ == "__main__":
    unittest.main()
