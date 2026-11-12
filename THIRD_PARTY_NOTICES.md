# Third-party notices

Better SMTC Bridge combines original SMTC Bridge material by nutty with new
contributions by Sveenet. The [license scope](LICENSE) distinguishes original
upstream material from Sveenet's reusable [MIT-licensed additions](LICENSE-MIT).
Dependencies retain their own copyrights and
license terms; the additions' license does not replace them.
Keep this document and the complete `licenses/` directory with redistributed
release packages.

This inventory was collected from the Windows build environment for version
1.0.0 on 2026-11-10. Exact license and notice texts are included under
[`licenses/`](licenses/); [`licenses/manifest.json`](licenses/manifest.json)
records each copied file, its provenance, and SHA-256 digest. Wheel-provided
texts are copied without modification. Extra upstream texts fill omissions in
the PyWinRT and PyAudioWPatch wheels. This is a distribution inventory, not a
legal opinion or warranty.

## Application runtime dependencies

| Component | Version | License / notice location |
| --- | --- | --- |
| [aiohttp](https://github.com/aio-libs/aiohttp) | 3.14.5 | Apache-2.0 and MIT; `licenses/aiohttp-3.14.5/` includes the bundled llhttp MIT license |
| [aiohappyeyeballs](https://github.com/aio-libs/aiohappyeyeballs) | 2.7.1 | PSF-2.0; `licenses/aiohappyeyeballs-2.7.1/` |
| [aiosignal](https://github.com/aio-libs/aiosignal) | 1.4.0 | Apache-2.0; `licenses/aiosignal-1.4.0/` |
| [attrs](https://github.com/python-attrs/attrs) | 26.1.0 | MIT; `licenses/attrs-26.1.0/` |
| [frozenlist](https://github.com/aio-libs/frozenlist) | 1.8.0 | Apache-2.0; `licenses/frozenlist-1.8.0/` |
| [idna](https://github.com/kjd/idna) | 3.20 | BSD-3-Clause; `licenses/idna-3.20/` |
| [multidict](https://github.com/aio-libs/multidict) | 7.2.1 | Apache-2.0; `licenses/multidict-7.2.1/` |
| [propcache](https://github.com/aio-libs/propcache) | 0.5.4 | Apache-2.0 and its NOTICE; `licenses/propcache-0.5.4/` |
| [yarl](https://github.com/aio-libs/yarl) | 1.25.1 | Apache-2.0 and its NOTICE; `licenses/yarl-1.25.1/` |
| [typing_extensions](https://github.com/python/typing_extensions) | 4.16.0 | PSF-2.0; `licenses/typing-extensions-4.16.0/` |
| [NumPy](https://github.com/numpy/numpy) | 2.5.4 | BSD-3-Clause and embedded component terms below; `licenses/numpy-2.5.4/` |
| [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch/tree/v0.2.12.9) | 0.2.12.9 | S0D3S's Apache-2.0 notice, inherited PyAudio MIT terms, and PortAudio terms below |
| [PyWinRT](https://github.com/pywinrt/pywinrt/tree/v3.2.1) | 3.2.1 | Microsoft Corporation and David Lechner, MIT; `licenses/pywinrt-3.2.1/LICENSE` |

The preserved upstream tray and configuration workflow also uses these
packages and their transitive dependencies:

| Component | Version | Terms / included texts |
| --- | --- | --- |
| Flask | 3.1.3 | BSD-3-Clause; `licenses/flask-3.1.3/` |
| Flask-CORS | 6.0.5 | MIT; `licenses/flask-cors-6.0.5/LICENSE` recovered from its checksum-verified source distribution |
| Werkzeug | 3.1.9 | BSD-3-Clause and separately included debugger-icon notice; `licenses/werkzeug-3.1.9/` |
| Jinja2 | 3.1.6 | BSD-3-Clause; `licenses/jinja2-3.1.6/` |
| MarkupSafe | 3.0.4 | BSD-3-Clause; `licenses/markupsafe-3.0.4/` |
| itsdangerous | 2.2.0 | BSD-3-Clause; `licenses/itsdangerous-2.2.0/` |
| click | 8.5.1 | BSD-3-Clause; `licenses/click-8.5.1/` |
| blinker | 1.9.0 | MIT; `licenses/blinker-1.9.0/` |
| psutil | 7.2.2 | BSD-3-Clause; `licenses/psutil-7.2.2/` |
| pystray | 0.19.5 | LGPLv3; complete GPL and LGPL texts plus matching source archive in `licenses/pystray-0.19.5/` |
| Pillow | 13.0.0 | MIT-CMU and complete embedded-library terms in `licenses/pillow-13.0.0/` |
| plyer | 2.1.0 | MIT; `licenses/plyer-2.1.0/` |
| six | 1.17.0 | MIT; `licenses/six-1.17.0/` |

**This application uses pystray, and that library and its use are covered by
the GNU Lesser General Public License version 3.** The complete matching
source archive is supplied with the release. Instructions for replacing the
library and rebuilding the executable are in
[`docs/rebuilding-pystray.md`](docs/rebuilding-pystray.md). The added project
terms do not restrict modification of the library portions or reverse
engineering for debugging those modifications.

The PyWinRT entry covers all six installed distributions: `winrt-runtime`,
`winrt-Windows.Foundation`, `winrt-Windows.Foundation.Collections`,
`winrt-Windows.Media`, `winrt-Windows.Media.Control`, and
`winrt-Windows.Storage.Streams`, all at 3.2.1. Their wheels declare MIT but omit
a license file; the included text comes from the exact upstream version tag.

### Embedded libraries and runtimes

- **CPython 3.14.3 and the Python standard library:** the complete Windows
  distribution license is in `licenses/python-3.14.3/LICENSE.txt`. It contains
  the PSF agreement, historical Python terms, incorporated bzip2/libffi/Zstandard
  notices, Apache text, Tcl/Tk terms, and additional conditions for Microsoft
  Distributable Code in this Windows build. Those Microsoft conditions apply
  to the Microsoft components, not to the original application code. Preserve
  the notices and comply with those redistribution restrictions.
- **Additional CPython incorporated software:** the complete official Python
  3.14.3 documentation license page is preserved at
  `licenses/python-3.14.3/additional-runtime-notices.html`. It includes notices
  for Mersenne Twister, SipHash, dtoa, and other incorporated software. Exact
  Expat 2.7.3 MIT terms, mpdecimal 4.0.0 BSD terms, and the HACL* MIT notice
  are also provided separately in that directory. These cover components
  identified in the final executable and Python built-ins.
- **Tcl/Tk 8.6.15:** `licenses/tcl-8.6.15/license.terms` and
  `licenses/tk-8.6.15/license.terms` retain the original copyright notices and
  permissive license for the desktop interface.
- **OpenSSL 3.0.18:** Apache-2.0 text at
  `licenses/openssl-3.0.18/LICENSE.txt`; used by the bundled Python SSL module.
- **zlib-ng 2.2.4:** the zlib license is in
  `licenses/zlib-ng-2.2.4/LICENSE.md`. The bundled Python runtime reports
  zlib compatibility version `1.3.1.zlib-ng`.
- **XZ Utils/liblzma 5.2.5:** `licenses/xz-5.2.5/COPYING` documents the public
  domain liblzma code. The XZ command-line programs and their separate licenses
  are not part of this application.
- **NumPy's bundled OpenBLAS, LAPACK, and GCC runtime:** the complete wheel
  license at `licenses/numpy-2.5.4/numpy-2.5.4.dist-info/licenses/LICENSE.txt`
  includes OpenBLAS BSD-3-Clause, LAPACK's BSD terms, and the GCC runtime
  GPL-3.0-or-later text with GCC Runtime Library Exception 3.1. That exception
  is part of the supplied runtime's terms; these libraries are not relicensed
  under the application's MIT license.
- **Other NumPy components:** the complete wheel notice tree is retained,
  including libdivide, pythoncapi-compat, Highway, Dragon4, x86-simd-sort, SVML,
  pocketfft, lapack_lite, masked arrays, and the random-number algorithms.
  Their individual BSD, MIT, 0BSD, Zlib, CC0 and other applicable notices are
  authoritative in that tree.
- **PyAudio:** Hubert Pham's original MIT license comment is copied from the
  PyAudioWPatch 0.2.12.9 source to
  `licenses/pyaudio-in-pyaudiowpatch-0.2.12.9/LICENSE-header.txt`.
- **PyAudioWPatch:** S0D3S's notice is in `licenses/pyaudiowpatch-0.2.12.9/`;
  the full Apache-2.0 license is additionally provided at
  `licenses/common/Apache-2.0.txt`.
- **PortAudio:** the exact bundled vendor license is in
  `licenses/portaudio-pyaudiowpatch-0.2.12.9/LICENSE.txt`. The upstream wheel
  build enables WASAPI, WMME and DirectSound. No ASIO SDK is included by this
  project.

Pillow's single complete wheel license additionally contains its vendored
Brotli 1.2.0, FreeType 2.14.3, HarfBuzz 14.5.0, LittleCMS 2.19.1, libavif 1.4.2,
libjpeg-turbo 3.2.0, libpng 1.6.58, libwebp 1.6.0, OpenJPEG 2.5.4, TIFF 4.7.2,
XZ 5.8.4 and zlib-ng 2.3.3 notices. These texts are retained even for optional
features unused by the tray. This product includes software developed by the
FreeType Project (https://www.freetype.org/), and software based in part on the
work of the Independent JPEG Group, as credited by the included notices.

The Windows system libraries and Windows Runtime services are supplied by
Windows; the application does not redistribute Windows itself. Any SQLite
library collected incidentally from Python remains under SQLite's
[public-domain dedication](https://www.sqlite.org/copyright.html).

## Packaging and development tools

These tools are recorded for reproducibility. Their presence in this inventory
does not mean their entire development distributions are bundled in the app.
PyInstaller's bootloader and runtime hooks are part of the packaged executable.

| Component | Version | Terms / included texts |
| --- | --- | --- |
| [PyInstaller](https://pyinstaller.org/en/stable/license.html) | 6.17.0 | GPL-2.0-or-later with the bootloader exception, plus Apache-2.0/MIT portions; complete `licenses/pyinstaller-6.17.0/` |
| pyinstaller-hooks-contrib | 2026.10 | Build hooks GPL-2.0-or-later, runtime hooks Apache-2.0; `licenses/pyinstaller-hooks-contrib-2026.10/` |
| altgraph | 0.17.5 | MIT; `licenses/altgraph-0.17.5/` |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause; both texts in `licenses/packaging-26.3/` |
| pefile | 2024.8.26 | MIT; `licenses/pefile-2024.8.26/` |
| pywin32-ctypes | 0.2.3 | BSD-3-Clause; `licenses/pywin32-ctypes-0.2.3/` |
| setuptools | 84.2.1 | MIT and vendored terms; `licenses/setuptools-84.2.1/` |
| pip | 25.3 | MIT and vendored terms; `licenses/pip-25.3/` |

PyInstaller's unmodified bootloader exception permits applications to be
distributed under their own terms, subject to dependency licenses. The full
exception text is included; this project does not claim ownership of or apply
MIT to the bootloader. Vendored pip/setuptools notices are included for build
environment completeness, including their separate dependency license texts.

## Upstream SMTC Bridge attribution

This project adapts [nutty's SMTC Bridge](https://github.com/nuttylmao/smtc-bridge)
and preserves credit for the original code and assets. The reviewed upstream
repository did not provide a public license. This project does not relicense
that original material or include it in the MIT grant for Sveenet's additions.
See [provenance](docs/provenance.md) for the upstream revision, inherited files,
original additions and licensing boundaries.
