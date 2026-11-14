# FileForge

A desktop utility for collecting files and creating ZIP archives. Built with Python and PySide6.

## Current features

- Add individual files or recursively add a folder.
- Drag and drop files and folders into the drop area.
- Review queued files, sizes, file types, and source locations.
- Remove selected files or clear the queue.
- Create ZIP archives with Fast, Balanced, or Best compression.
- Archive creation runs in a background thread so the interface remains responsive.
- Preserve useful relative folder paths inside the archive.
- Show byte-based progress while the archive is being written.

## Not implemented yet

File conversion is planned, but is not implemented in this version. The Converter item is intentionally marked as coming soon. No conversion is claimed or performed.

## Requirements

- Python 3.10+
- PySide6

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Run tests

The archive engine uses only the Python standard library, so its tests do not require PySide6.

```bash
python -m unittest discover -s tests -v
```

## Project layout

- `main.py` — PySide6 desktop application.
- `fileforge/archive.py` — ZIP creation engine.
- `tests/` — standard-library unit tests.

## Notes

FileForge creates archives locally on the user's machine. The application does not upload selected files to a server.
