"""Safe ZIP extraction helpers."""
from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

from fileforge.task_control import TaskCancelledError, raise_if_cancelled


def _member_destination(root: Path, info: zipfile.ZipInfo) -> Path:
    """Resolve one ZIP member and reject traversal, absolute paths and symlinks."""
    raw_name = info.filename.replace("\\", "/")
    relative = PurePosixPath(raw_name)

    if relative.is_absolute() or re.match(r"^[A-Za-z]:", raw_name):
        raise ValueError(f"Đường dẫn không an toàn trong ZIP: {info.filename}")
    if any(part == ".." for part in relative.parts):
        raise ValueError(f"Đường dẫn không an toàn trong ZIP: {info.filename}")

    mode = (info.external_attr >> 16) & 0o170000
    if stat.S_ISLNK(mode):
        raise ValueError(f"Không hỗ trợ liên kết tượng trưng trong ZIP: {info.filename}")

    destination = root.joinpath(*relative.parts).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError(f"Đường dẫn vượt khỏi thư mục giải nén: {info.filename}")
    return destination


def _unique_folder(parent: Path, name: str) -> Path:
    safe_name = "".join(
        character for character in name
        if character.isalnum() or character in (" ", ".", "_", "-")
    ).strip(" .")
    safe_name = safe_name or "FileForge"
    candidate = parent / safe_name
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{safe_name} ({suffix})"
        suffix += 1
    return candidate


def _extract_one(
    archive_path: Path,
    destination: Path,
    progress: Callable[[int, int, str], None] | None,
    completed_before: int,
    total_all: int,
    is_cancelled: Callable[[], bool] | None = None,
) -> tuple[Path, int]:
    if not zipfile.is_zipfile(archive_path):
        raise zipfile.BadZipFile("Tệp không phải ZIP hợp lệ.")

    final_folder = _unique_folder(destination, archive_path.stem)
    temporary_folder = Path(
        tempfile.mkdtemp(prefix=".fileforge-extract-", dir=str(destination))
    )
    completed = 0
    seen_files: set[Path] = set()

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            # Validate the complete member list before writing any content.
            destinations = []
            for info in infos:
                raise_if_cancelled(is_cancelled)
                destinations.append((info, _member_destination(temporary_folder, info)))
            for info, target in destinations:
                raise_if_cancelled(is_cancelled)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if target in seen_files:
                    raise ValueError(f"Tệp bị lặp trong ZIP: {info.filename}")
                seen_files.add(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("xb") as output:
                    while True:
                        raise_if_cancelled(is_cancelled)
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        completed += len(chunk)
                        if progress:
                            progress(
                                completed_before + completed,
                                total_all,
                                info.filename,
                            )

        raise_if_cancelled(is_cancelled)
        os.replace(temporary_folder, final_folder)
        return final_folder, completed
    except Exception:
        shutil.rmtree(temporary_folder, ignore_errors=True)
        raise


def extract_archives(
    archive_paths: Iterable[str | Path],
    destination: str | Path,
    progress: Callable[[int, int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> tuple[list[Path], list[tuple[str, str]]]:
    """Extract each archive into its own folder; report per-archive failures."""
    target = Path(destination).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    valid_archives: list[tuple[Path, int]] = []
    errors: list[tuple[str, str]] = []
    total_size = 0

    for raw in archive_paths:
        raise_if_cancelled(is_cancelled)
        path = Path(raw).expanduser().resolve()
        try:
            if not path.is_file() or not zipfile.is_zipfile(path):
                raise zipfile.BadZipFile("Tệp không phải ZIP hợp lệ.")
            with zipfile.ZipFile(path, "r") as archive:
                size = sum(info.file_size for info in archive.infolist() if not info.is_dir())
            valid_archives.append((path, size))
            total_size += size
        except TaskCancelledError:
            raise
        except Exception as exc:
            errors.append((str(path), str(exc)))

    outputs: list[Path] = []
    completed_before = 0
    for path, archive_size in valid_archives:
        raise_if_cancelled(is_cancelled)
        try:
            extracted, actual_size = _extract_one(
                path, target, progress, completed_before, total_size, is_cancelled
            )
            outputs.append(extracted)
            completed_before += archive_size
            if progress:
                progress(
                    min(completed_before, total_size),
                    total_size,
                    path.name,
                )
        except TaskCancelledError as exc:
            exc.completed_outputs = [str(output) for output in outputs]
            raise
        except Exception as exc:
            errors.append((str(path), str(exc)))
            completed_before += archive_size

    if progress:
        progress(total_size, total_size, "Hoàn tất")
    return outputs, errors
