"""ZIP archive creation helpers (standard library only)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
import os
import tempfile
import zipfile

from fileforge.task_control import raise_if_cancelled


@dataclass(frozen=True)
class ArchiveItem:
    path: Path
    archive_name: str
    size: int = 0
    is_dir: bool = False


# Every preset uses DEFLATE so the archive opens in Windows Explorer, macOS
# Archive Utility and every other tool (LZMA/BZIP2 ZIPs often do not).
# "Fast" still compresses (level 1) instead of just storing the files.
PRESETS: dict[str, tuple[int, int]] = {
    "Fast": (zipfile.ZIP_DEFLATED, 1),
    "Balanced": (zipfile.ZIP_DEFLATED, 6),
    "Best": (zipfile.ZIP_DEFLATED, 9),
}
# Kept for backwards compatibility with code importing COMPRESSION.
COMPRESSION = {name: method for name, (method, _level) in PRESETS.items()}

# Already-compressed formats: recompressing wastes CPU for ~0% gain.
STORE_ONLY_EXTENSIONS = {
    ".zip", ".7z", ".rar", ".gz", ".bz2", ".xz", ".zst", ".tgz",
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".avif",
    ".mp3", ".aac", ".m4a", ".ogg", ".flac",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
    ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".epub", ".jar", ".apk",
}


def _unique_name(name: str, used: set[str]) -> str:
    """Return a name not yet used in the archive (report.txt -> report_2.txt).

    Comparison is case-insensitive because Windows/macOS extract
    case-insensitively and would otherwise overwrite one file with the other.
    """
    def key(value: str) -> str:
        return value.replace("\\", "/").lower()

    candidate = name
    if key(candidate) in used:
        base = Path(name)
        counter = 2
        while True:
            candidate = str(base.with_name(f"{base.stem}_{counter}{base.suffix}"))
            if key(candidate) not in used:
                break
            counter += 1
    used.add(key(candidate))
    return candidate


def collect_items(paths: Iterable[str | Path]) -> list[ArchiveItem]:
    """Expand folders recursively, keep folder-relative paths and empty folders."""
    items: list[ArchiveItem] = []
    seen: set[tuple[str, str]] = set()
    used_names: set[str] = set()

    def add_file(path: Path, name: str):
        if (str(path), name) in seen:
            return
        seen.add((str(path), name))
        items.append(
            ArchiveItem(path, _unique_name(name, used_names), path.stat().st_size)
        )

    def add_dir(path: Path, name: str):
        key = name.replace("\\", "/").lower().rstrip("/") + "/"
        if key in used_names:
            return
        used_names.add(key)
        items.append(ArchiveItem(path, name, 0, True))

    for raw in paths:
        source = Path(raw).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        if source.is_file():
            add_file(source, source.name)
        elif source.is_dir():
            root = Path(source.name)
            if not any(source.iterdir()):
                add_dir(source, str(root))
            for path in sorted(source.rglob("*")):
                name = str(root / path.relative_to(source))
                if path.is_file():
                    add_file(path, name)
                elif path.is_dir() and not any(path.iterdir()):
                    add_dir(path, name)
    return items


def create_zip(
    paths: Iterable[str | Path],
    destination: str | Path,
    compression: str = "Balanced",
    progress: Callable[[int, int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> Path:
    """Create an archive atomically; cancellation preserves any previous output."""
    raise_if_cancelled(is_cancelled)
    if compression not in PRESETS:
        raise ValueError(f"Unknown compression preset: {compression}")
    method, level = PRESETS[compression]
    items = collect_items(paths)
    if not items:
        raise ValueError("There are no files to archive.")

    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    source_paths = {item.path for item in items}
    if target in source_paths:
        raise ValueError("The output archive cannot be one of its own input files.")

    total = sum(item.size for item in items)
    completed = 0
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(
            temp_path,
            "w",
            compression=method,
            compresslevel=level,
            allowZip64=True,
            strict_timestamps=False,  # files dated before 1980 no longer abort the job
        ) as archive:
            for item in items:
                raise_if_cancelled(is_cancelled)
                if item.is_dir:
                    archive.write(item.path, arcname=item.archive_name)
                else:
                    store_only = item.path.suffix.lower() in STORE_ONLY_EXTENSIONS
                    info = zipfile.ZipInfo.from_file(item.path, arcname=item.archive_name)
                    info.compress_type = (
                        zipfile.ZIP_STORED if store_only else method
                    )
                    with item.path.open("rb") as source, archive.open(
                        info,
                        "w",
                        force_zip64=item.size > zipfile.ZIP64_LIMIT,
                    ) as destination_stream:
                        while True:
                            raise_if_cancelled(is_cancelled)
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            destination_stream.write(chunk)
                            completed += len(chunk)
                            if progress:
                                progress(completed, total, item.archive_name)
                if item.is_dir:
                    completed += item.size
                    if progress:
                        progress(completed, total, item.archive_name)
        # Validate before replacing a possibly existing output.
        raise_if_cancelled(is_cancelled)
        with zipfile.ZipFile(temp_path, "r") as archive:
            for member in archive.infolist():
                raise_if_cancelled(is_cancelled)
                if member.is_dir():
                    continue
                with archive.open(member, "r") as member_stream:
                    while True:
                        raise_if_cancelled(is_cancelled)
                        chunk = member_stream.read(1024 * 1024)
                        if not chunk:
                            break
        raise_if_cancelled(is_cancelled)
        try:
            os.chmod(temp_path, 0o644)  # mkstemp creates 0600
        except OSError:
            pass
        os.replace(temp_path, target)
        if progress:
            progress(total, total, "Done")
        return target
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass