# Provenance for Better SMTC Bridge 1.0.0

Review date: 2026-11-10.

## Upstream source and permission

This project is an adaptation of
[nuttylmao/smtc-bridge](https://github.com/nuttylmao/smtc-bridge), preserving
credit for its code and assets. The source revision is
[`442cdc81290a3127dea3200bcdc5883c820a328e`](https://github.com/nuttylmao/smtc-bridge/tree/442cdc81290a3127dea3200bcdc5883c820a328e).
The reviewed tree contains no LICENSE/COPYING file. The project owner has
confirmed private permission to modify and redistribute the upstream material.
That private correspondence is not reproduced, and this repository does not
grant a general sublicense or assign an invented public license to that work.
Permission for other reuse must come from the original rights holder.

The root [LICENSE](../LICENSE) scopes MIT to Sveenet's original additions.
It does not apply MIT to pre-existing upstream source, icons, images or other
assets. Existing authorship and copyright notices are preserved. Dependency
licenses remain separate.

## Implementation boundaries

The following files contain upstream material and are **not** wholly covered
by the MIT terms for new contributions:

| Files | Treatment |
| --- | --- |
| `smtc-bridge.pyw` | Adapted from the original main program. Preserves its metadata/session workflow, Flask routes, tray menu and startup behavior; adds the shared local audio service, PyWinRT compatibility, bounded in-memory artwork cache and integration fixes. The Customize Overlay and Try Widgets tray actions open CreatorSuite destinations. Quit closes the native tray, gives the service a bounded cleanup interval and preserves the original process-exit behavior. Credit to nutty remains preserved in the source and project documentation. |
| `build.bat`, `launch.bat` | Adapted upstream launch/build entry points. |
| `smtc-bridge.ico`, `icon.png`, `icon.af` | Unmodified original upstream assets. |
| `settings.ini`, `smtc-bridge.spec` | Unmodified upstream configuration/build files retained for provenance and compatibility. |

[`upstream-files.json`](upstream-files.json) records each source path, original
revision and SHA-256 hashes for the upstream and adapted copies. It identifies
modified files; it does not license the original content. The MIT grant covers
only Sveenet's original contributions within adapted files, subject to the
upstream permission for using the surrounding original work.

The following are newly implemented additions by Sveenet and are covered by
the MIT terms in the root LICENSE: `bridge.py`, `audio.py`, `server.py`,
`metadata.py`, `artwork.py`, `control.html`, `make_icon.py`, generated
`assets/icon.png` and `assets/icon.ico`, `tests/`, `build.ps1`,
`package_release.py`, `install_deps.py`, `Start Better SMTC Bridge.bat`,
`requirements.txt`, `requirements-build.txt`, `requirements-lock.txt`,
`windows-version-info.txt`, and
new project documentation. The generated icon under `assets/` is distinct
from the preserved upstream icon in the repository root. Third-party license
texts and the pystray source archive under `licenses/` retain their original
terms, not the new-contribution MIT terms.

No source or assets from the OBS waveform plugin, OBS Browser, or OBS
WebSocket are incorporated. The visualizer widgets are a separate project;
this bridge distributes the local metadata/audio service. Music and album art
received from Windows are runtime data, not bundled project assets. The
default local port remains 5000.

## Dependency evidence

The license inventory was collected from the actual `.venv` used for the
Windows build: CPython 3.14.3 and the pinned packages in `requirements.txt`
and `requirements-build.txt`. It includes every license, notice, copyright
and authors file advertised by the installed distributions, including nested
vendored components of build tools. Full wheel copies remain unmodified.

Additional evidence used where the wheels omitted or abbreviated terms:

| Material | Source |
| --- | --- |
| PyWinRT MIT license for all six 3.2.1 distributions | [v3.2.1 LICENSE](https://github.com/pywinrt/pywinrt/blob/v3.2.1/LICENSE), tag tree `21cbd0fd7ff91422ed76b4e3611d3fb52716e017` |
| PyAudio inherited MIT notice | [PyAudioWPatch v0.2.12.9 source header](https://github.com/s0d3s/PyAudioWPatch/blob/v0.2.12.9/src/_portaudiomodule.c); only the opening license comment was copied |
| PortAudio vendor terms | [PyAudioWPatch v0.2.12.9 vendor LICENSE](https://github.com/s0d3s/PyAudioWPatch/blob/v0.2.12.9/portaudio_v19/LICENSE.txt), commit `8b68e78c31dd1e12e9c603901b8cd0d9d6510b2a` |
| CPython full Windows license, additional incorporated-software notices, and Tk terms | Exact files in the installed CPython 3.14.3 Windows distribution, including `Doc/html/license.html` |
| Expat, HACL* and mpdecimal | Versioned CPython 3.14.3 source notices and its `mpdecimal-4.0.0` source dependency; locations and hashes are in the manifest |
| Tcl 8.6.15 terms | [core-8-6-15 license.terms](https://github.com/tcltk/tcl/blob/core-8-6-15/license.terms) |
| Python embedded-library version identification | [CPython v3.14.3 PCbuild/get_externals.bat](https://github.com/python/cpython/blob/v3.14.3/PCbuild/get_externals.bat), plus runtime OpenSSL/zlib version reports |
| OpenSSL 3.0.18 | [Exact tag LICENSE](https://github.com/openssl/openssl/blob/openssl-3.0.18/LICENSE.txt) |
| zlib-ng 2.2.4 | [Exact tag LICENSE](https://github.com/zlib-ng/zlib-ng/blob/2.2.4/LICENSE.md) |
| liblzma 5.2.5 | [XZ v5.2.5 COPYING](https://github.com/tukaani-project/xz/blob/v5.2.5/COPYING) |
| pystray 0.19.5 source | [Exact upstream tag archive](https://github.com/moses-palmer/pystray/tree/v0.19.5); all 13 installed package source files matched the archive after line-ending normalization |
| Flask-CORS 6.0.5 missing license | Original source distribution from PyPI, verified against published SHA-256 `30c5031552cd59f620ac0c8211dac45b345d3b2df310e7721879e4f46ef9c601` |
| Full Apache-2.0 text | Unmodified `LICENSE.APACHE` from the installed packaging 26.3 wheel |

NumPy's complete installed wheel license tree supplies its embedded
OpenBLAS/LAPACK/GCC runtime and CPU implementation notices. PyInstaller's
complete `COPYING.txt` supplies the bootloader exception and other component
terms. See [third-party notices](../THIRD_PARTY_NOTICES.md) for the component
inventory and [`licenses/manifest.json`](../licenses/manifest.json) for file
digests and source paths.

No third-party Python dependency source was modified for this release; the
upstream SMTC Bridge adaptation is separately identified above. Future dependency or
packaging changes must refresh this inventory and preserve the applicable
notices. This review records concrete provenance and included license texts;
it does not provide a legal guarantee about every possible use or redistribution.
