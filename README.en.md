# FileForge

**Version 1.0.0** · Desktop file and developer utility for Windows, macOS, and Linux.

[Tiếng Việt](README.md) · **English**

FileForge brings common file-processing and developer utilities into one desktop application built with Python and PySide6. Files are processed locally on your computer.

## Features

### ZIP archive creation
- Add multiple files or an entire folder; drag and drop is supported.
- Choose Fastest, Balanced, or Maximum compression.
- Preserve relative folder structure inside the archive.
- Show progress while work runs in a background thread.
- Stream large files in chunks and validate the archive before publishing the final output.

### ZIP extraction
- Extract one or multiple ZIP files in a single batch.
- Extract each archive into its own folder to avoid name collisions.
- Reject path traversal entries and symbolic links.
- Continue processing valid archives when another archive in the batch fails.
- Cooperatively cancel an active extraction and clean up its temporary folder.

### Image conversion
- Input: PNG, JPG/JPEG, WEBP, BMP, and TIFF.
- Output: JPG, PNG, and WEBP.
- Adjust JPG/WEBP quality from 50% to 100%.
- Flatten transparency onto a white background when exporting JPG.
- Preserve EXIF orientation and ICC profiles when possible.
- Keep completed images if a batch is cancelled; publish each image only after its temporary output has been written.

### JSON, XML, HTML, and model generation
- Format or minify JSON and XML.
- Convert JSON to an escaped string and decode it back.
- Convert JSON and XML in both directions, including XML attributes and repeated elements.
- Convert strings and HTML in both directions.
- Generate Python dataclasses, Pydantic v2 models, TypeScript interfaces, Java classes, Kotlin data classes, and C structs from JSON.
- Inspect JSON in a lazy-loaded tree view, or work directly in the text editor.
- Search, copy, fold HTML output, and adjust indentation.

### Compare
- Compare text by line, word, or character.
- Optionally ignore case, whitespace, or blank lines.
- Compare JSON structurally; object-key order and formatting do not create false differences.
- Compare arrays by index or ignore array order while retaining duplicate counts.
- Filter differences and copy a report.

### Additional developer tools
- Convert a copied HTTP request into a cURL command.
- Encode and decode URLs and URI components using UTF-8.
- AES-128/192/256 with CBC, GCM, CTR, and ECB modes.
- Key and IV/nonce input formats include UTF-8, HEX, and Base64.

**AES security note:** GCM is recommended when authenticated encryption is required. Never reuse a nonce with the same key in GCM, or reuse an IV/counter with the same key in CTR. CBC, CTR, and ECB do not authenticate ciphertext; ECB is not suitable for sensitive data. UTF-8 key input is used directly as bytes and is not processed through a password KDF.

### Desktop preferences and task history
- Remember the window size, selected tool, recent input/output folders, preferred output folder, and ZIP/image settings.
- Search and inspect up to 500 recent tasks in the local SQLite history.
- Open output folders from the history window or clear the history.
- Rotating diagnostic logs and an optional system-tray workflow are available where supported.
- History stores task metadata only: it does not store file/editor contents, AES keys, plaintext, or ciphertext.

### Safe task cancellation
- ZIP creation, extraction, and image batches support cooperative cancellation.
- The application does not force-terminate a running QThread.
- ZIP output is replaced only after the archive is written and validated.
- Temporary extraction/image output is cleaned up when cancellation is observed.
- Completed outputs from earlier items in the batch are retained and recorded in task history.
- A Pillow decode/encode operation already in progress cannot be interrupted mid-codec; cancellation is observed at the next safe checkpoint.

## Languages

The interface currently supports:
- Vietnamese
- English

Open **FileForge → Preferences → Language** to change the interface language. The selection is applied immediately after saving and is remembered for the next launch. Vietnamese is the default for new installations.

## Requirements

- Python 3.10 or later (Python 3.12 is recommended).
- PySide6.
- Pillow.
- cryptography.

The Pydantic v2 package is only required in the target project when generating Pydantic models; FileForge itself does not need Pydantic to run.

## Install and run

### macOS

```bash
brew install python@3.12

git clone https://github.com/johanforce/FileForge.git
cd FileForge

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --no-compile -r requirements.txt
python main.py
```

The `--no-compile` option avoids a PySide6 template-compilation issue on some macOS environments.

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

```bash
python -m unittest discover -s tests -v
```

## Project layout

- `main.py` — PySide6 desktop interface and application orchestration.
- `fileforge/archive.py` — ZIP creation and validation.
- `fileforge/extraction.py` — safe ZIP extraction.
- `fileforge/images.py` — image conversion.
- `fileforge/text_utils.py` — JSON/XML/text conversions.
- `fileforge/i18n.py` — Vietnamese and English UI translations.
- `fileforge/preferences.py` — persistent preferences.
- `fileforge/app_services.py` — application paths, logging, and task history.
- `tests/` — automated tests.

## Privacy

FileForge processes files locally and does not upload user files to a server. Diagnostic logs and task history are stored locally in the application data directory.

## License and acknowledgments

The FileForge source code is distributed under the [MIT License](LICENSE).

Third-party libraries retain their own licenses and notices. Review [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) before redistributing a packaged build. In particular, check the applicable Qt for Python licensing obligations for the way you distribute the application.

## Windows executable

The repository includes a GitHub Actions workflow for building a standalone Windows executable. The build workflow is configured to run after a pull request targeting `main` is merged. See the **Build Windows EXE** workflow under the repository's Actions tab for artifacts and build logs.
