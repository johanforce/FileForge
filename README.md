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

### macOS

Use Python 3.10 or newer (Python 3.12 is recommended). Avoid the Python 3.9 interpreter bundled with older Apple Command Line Tools.

With Homebrew:

```bash
brew install python@3.12

git clone https://github.com/johanforce/FileForge.git
cd FileForge

# Recreate the virtual environment if it was made with an older Python:
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
# --no-compile avoids pip trying to byte-compile Qt's Jinja .tmpl.py files.
python -m pip install --no-compile -r requirements.txt
python main.py
```

If your shell cannot find `python3.12` after installing Homebrew Python, run:
```bash
$(brew --prefix python@3.12)/bin/python3.12 -m venv .venv
```

### Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
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
