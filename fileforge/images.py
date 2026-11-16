"""Image conversion helpers powered by Pillow."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image, ImageOps

from fileforge.task_control import TaskCancelledError, raise_if_cancelled


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"
}
OUTPUT_FORMATS = {"JPG": "JPEG", "PNG": "PNG", "WEBP": "WEBP"}


def _unique_output(folder: Path, stem: str, extension: str) -> Path:
    candidate = folder / f"{stem}.{extension}"
    suffix = 2
    while candidate.exists():
        candidate = folder / f"{stem}_{suffix}.{extension}"
        suffix += 1
    return candidate


def _prepare_image(image: Image.Image, output_format: str) -> Image.Image:
    has_alpha = "A" in image.getbands() or "transparency" in image.info

    if output_format == "JPEG":
        if has_alpha:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.getchannel("A"))
            return background
        return image.convert("RGB")

    if output_format == "WEBP":
        return image.convert("RGBA" if has_alpha else "RGB")

    # PNG can retain palette transparency; normalize uncommon modes.
    if image.mode in ("1", "L", "LA", "P", "RGB", "RGBA", "I", "I;16"):
        if image.mode == "P" and has_alpha:
            return image.convert("RGBA")
        return image.copy()
    return image.convert("RGBA" if has_alpha else "RGB")


def convert_images(
    image_paths: Iterable[str | Path],
    destination: str | Path,
    output_format: str,
    quality: int = 90,
    progress: Callable[[int, int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> tuple[list[Path], list[tuple[str, str]]]:
    """Convert a batch of images, continuing past individual file failures."""
    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Định dạng đầu ra không hỗ trợ: {output_format}")
    if not 1 <= quality <= 100:
        raise ValueError("Chất lượng ảnh phải nằm trong khoảng 1 đến 100.")

    paths = [Path(raw).expanduser().resolve() for raw in image_paths]
    target = Path(destination).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    pillow_format = OUTPUT_FORMATS[output_format]
    extension = output_format.lower()
    outputs: list[Path] = []
    errors: list[tuple[str, str]] = []

    for index, source in enumerate(paths, start=1):
        try:
            raise_if_cancelled(is_cancelled)
            if source.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                raise ValueError("Định dạng ảnh đầu vào chưa được hỗ trợ.")

            with Image.open(source) as original:
                original.load()
                raise_if_cancelled(is_cancelled)
                image = ImageOps.exif_transpose(original)
                icc_profile = image.info.get("icc_profile")
                exif = image.info.get("exif")
                converted = _prepare_image(image, pillow_format)

                output_path = _unique_output(target, source.stem, extension)
                fd, temporary_name = tempfile.mkstemp(
                    prefix=".fileforge-image-",
                    suffix=f".{extension}",
                    dir=str(target),
                )
                os.close(fd)
                temporary_path = Path(temporary_name)
                try:
                    raise_if_cancelled(is_cancelled)
                    options: dict[str, object] = {}
                    if pillow_format in ("JPEG", "WEBP"):
                        options["quality"] = quality
                    if pillow_format == "JPEG":
                        options.update(optimize=True, progressive=True)
                    elif pillow_format == "WEBP":
                        options.update(method=6)
                    elif pillow_format == "PNG":
                        options.update(optimize=True)

                    if icc_profile:
                        options["icc_profile"] = icc_profile
                    if exif and pillow_format in ("JPEG", "WEBP", "PNG"):
                        options["exif"] = exif

                    converted.save(
                        temporary_path,
                        format=pillow_format,
                        **options,
                    )
                    raise_if_cancelled(is_cancelled)
                    os.replace(temporary_path, output_path)
                    outputs.append(output_path)
                finally:
                    temporary_path.unlink(missing_ok=True)
                    if converted is not image:
                        converted.close()
        except TaskCancelledError as exc:
            exc.completed_outputs = [str(output) for output in outputs]
            raise
        except Exception as exc:
            errors.append((str(source), str(exc)))
        finally:
            if progress:
                progress(index, len(paths), source.name)

    return outputs, errors
