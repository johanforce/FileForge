# Acknowledgments

FileForge is built with the help of the open-source projects below. We are grateful to their maintainers and contributors.

## Runtime dependencies

| Project | Purpose in FileForge | License / notice |
|---|---|---|
| [Python](https://www.python.org/) | Application runtime | Python Software Foundation License |
| [Qt for Python (PySide6)](https://doc.qt.io/qtforpython/) | Desktop UI and platform integration | Qt for Python is offered under LGPLv3/GPLv3 and commercial terms. The exact obligations depend on the Qt version, distribution method, and selected license. |
| [Pillow](https://python-pillow.org/) | Image loading, conversion, and encoding | Pillow's license depends on the release: current PyPI metadata reports MIT-CMU, while older release lines may carry HPND. Check the license file and metadata for the exact installed release before redistributing it. |
| [cryptography](https://cryptography.io/) | AES encryption and decryption primitives | Apache-2.0 OR BSD-3-Clause, according to the project metadata. |

## Build and packaging tools

| Project | Purpose | License / notice |
|---|---|---|
| [PyInstaller](https://pyinstaller.org/) | Builds the standalone Windows executable in CI | GPLv2 with the PyInstaller bootloader exception; some bundled components use Apache-2.0. See the upstream license and exception text. |

## Project license versus dependency licenses

The FileForge application source code is distributed under the **MIT License** in the repository's LICENSE file.

That license does not replace or re-license third-party dependencies. When redistributing a packaged executable, retain the applicable third-party notices and comply with the license terms for the exact dependency versions included in that build. In particular, review the Qt for Python licensing options and obligations for the distribution model you choose.

This file is an informational inventory, not legal advice. Dependency versions and license metadata can change; consult the license files shipped with the actual artifacts you distribute.

## Upstream license references

- [Qt for Python licensing](https://doc.qt.io/qtforpython-6/licenses.html)
- [PySide6 on PyPI](https://pypi.org/project/PySide6/)
- [Pillow license](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
- [Pillow on PyPI](https://pypi.org/project/pillow/)
- [cryptography on PyPI](https://pypi.org/project/cryptography/)
- [PyInstaller licensing and exception](https://pyinstaller.org/en/stable/license.html)
