"""ZIP archive creation helpers (standard library only)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
import os
import tempfile
import zipfile


@dataclass(frozen=True)
class ArchiveItem:
    path: Path
    archive_name: str


COMPRESSION = {
    "Fast": zipfile.ZIP_STORED,
    "Balanced": zipfile.ZIP_DEFLATED,
    "Best": zipfile.ZIP_LZMA,
}


def collect_items(paths: Iterable[str | Path]) -> list[ArchiveItem]:
    """Expand folders recursively while keeping folder-relative paths."""
    items: list[ArchiveItem] = []
    seen: set[tuple[str, str]] = set()
    for raw in paths:
        source = Path(raw).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        if source.is_file():
            candidates = [(source, source.name)]
        elif source.is_dir():
            candidates = [
                (p, str(Path(source.name) / p.relative_to(source)))
                for p in sorted(source.rglob("*")) if p.is_file()
            ]
        else:
            continue
        for path, name in candidates:
            key = (str(path), name)
            if key not in seen:
                seen.add(key)
                items.append(ArchiveItem(path, name))
    return items


def create_zip(
    paths: Iterable[str | Path],
    destination: str | Path,
    compression: str = "Balanced",
    progress: Callable[[int, int, str], None] | None = None,
) -> Path:
    """Create an archive atomically; an existing destination survives failures."""
    if compression not in COMPRESSION:
        raise ValueError(f"Unknown compression preset: {compression}")
    items = collect_items(paths)
    if not items:
        raise ValueError("There are no files to archive.")

    target = Path(destination).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    source_paths = {item.path for item in items}
    if target in source_paths:
        raise ValueError("The output archive cannot be one of its own input files.")

    total = sum(item.path.stat().st_size for item in items)
    completed = 0
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(
            temp_path, "w", compression=COMPRESSION[compression], allowZip64=True
        ) as archive:
            for item in items:
                archive.write(item.path, arcname=item.archive_name)
                completed += item.path.stat().st_size
                if progress:
                    progress(completed, total, item.archive_name)
        # Validate before replacing a possibly existing output.
        with zipfile.ZipFile(temp_path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise zipfile.BadZipFile(f"Archive validation failed: {bad_member}")
        os.replace(temp_path, target)
        if progress:
            progress(total, total, "Done")
        return target
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
