# Better SMTC Bridge

**Song details, album artwork, and real audio analysis for Windows stream overlays.**

Better SMTC Bridge 1.0.1 extends [nutty's original SMTC Bridge](https://github.com/nuttylmao/smtc-bridge) with a live waveform and frequency spectrum. It runs on your own computer and serves both through **port 5000**. This repository and its release are private.

[Download the Windows release](https://github.com/Sveenet/better-smtc-bridge/releases/latest) · [Report a problem](https://github.com/Sveenet/better-smtc-bridge/issues)

## Get started

1. Download the Windows x64 ZIP from Releases and extract the whole folder.
2. Close the original SMTC Bridge if it is running, including its system-tray instance. Both applications use port 5000 and cannot run there simultaneously.
3. Open **Better SMTC Bridge.exe**. The packaged release includes Python and its required libraries; you do not need to install Python separately.
4. On the first launch, select the headphones, speakers, or virtual output carrying your music in the local controls, then click **Start visualizing**. Your choice is saved automatically.
5. On later launches, the app stays in the Windows system tray and reconnects to that output without reopening the selection page. Right-click the tray icon to open **Audio Controls** when you want to change it, or choose **Quit** to stop the bridge and release port 5000.

The output is remembered by name so Windows can renumber devices without losing your selection. If it is temporarily unavailable, the app waits and retries instead of switching to another output. **Stop audio** saves the stopped state; use **Start visualizing** to enable it again.

Your existing metadata address stays `http://127.0.0.1:5000/now-playing`. The additional audio connection is `ws://127.0.0.1:5000/audio`.

The program leaves the original SMTC installation, audio routing, OBS configuration, and existing widget settings intact. **Start with Windows** is optional and off until you choose it in the tray menu; it uses its own Better SMTC Bridge shortcut. If your original bridge starts with Windows, turn off its startup option before enabling this bridge's startup option.

## Use with CreatorSuite Universal Music

Open [Universal Music settings](https://creator-suite-amv.pages.dev/universal-music/settings/) and choose a creative theme:

- **Wave Line** — a live waveform, with adjustable thickness and amplitude.
- **Mirrored Bars** — a mirrored frequency spectrum, with adjustable bar count, spacing, and corners.
- **Stepped Bars** — a segmented frequency display, with adjustable columns and steps.
- **Radial Halo** — a circular spectrum, with adjustable radius, thickness, and spokes.
- **Ribbon Wave** — layered waveform ribbons, with adjustable layers, thickness, and spread.
- **Particle Bloom** — particles responding to measured audio energy, with adjustable count, size, and spread.
- **Aurora Flow** and **Smoke Wisps** — ambient artwork-colored effects with their own motion controls; these also work without audio capture.

Choose **Artwork color** in the widget settings: Dominant, Vibrant, Muted, Dark Vibrant, Dark Muted, Light Vibrant, or Light Muted. New widget URLs show one visualization, with no cropping needed. Existing six-color URLs retain their layout until replaced. The settings show the suggested OBS source dimensions.

The bridge supplies audio measurements; the widget renders the visuals and extracts artwork colors. These are separate projects. Sample preview animation is explicitly labeled as a demo; live reactive themes use actual measurements and settle when audio stops.

## What gets analyzed

- Audio capture uses **WASAPI output loopback**. The device list contains output loopback devices, not microphone inputs.
- A shared output includes **all applications playing through that output**. Choosing a song application in your widget filters song metadata; it does not isolate that application's audio.
- For music-only reaction, route music to a separate output or virtual device and choose that output in the bridge.
- Audio samples stay in memory. The app does not record audio files, upload audio, or call a cloud service.
- Audio capture is enabled when you choose **Start visualizing**, or explicitly request a device in headless mode. Once enabled, it resumes from your saved output on later launches. Metadata remains available when audio capture is stopped.
- The selected output and enabled/stopped preference are saved locally in `%LOCALAPPDATA%\BetterSMTCBridge\settings.json`. No recordings or private credentials are stored there.
- One capture and analysis pipeline serves all connected overlays, at up to 30 updates per second.

## Local API

The service binds to `127.0.0.1` only. It is not exposed to other computers on your network.

| Address | Purpose |
| --- | --- |
| `http://127.0.0.1:5000/` | Local controls and output selection |
| `http://127.0.0.1:5000/health` | Version, capture state, and connected overlay count |
| `http://127.0.0.1:5000/now-playing` | Windows SMTC sessions, playback state, timeline, and artwork |
| `http://127.0.0.1:5000/sessions` | Available media-session data |
| `http://127.0.0.1:5000/devices` | Available output loopback devices |
| `ws://127.0.0.1:5000/audio` | Read-only waveform and spectrum stream |

An audio message has `type: "audio-frame"`, `version: 1`, a millisecond `timestamp`, 256 signed `waveform` samples, 96 logarithmically spaced `spectrum` values, and an RMS `level`. Waveform values are in `[-1, 1]`; spectrum and level values are in `[0, 1]`. Spectrum magnitudes use a -72 dB to 0 dB display range. A stopped capture sends a status message with `connected: false`. Digital silence is reported as zero signal, not simulated movement.

WebSocket clients cannot start recording or change devices. Local capture controls require a per-run token obtained from the local control page. Hosted widget access is restricted to the built-in allowed origins. Developers can add an exact origin explicitly in headless mode.

## Requirements and limitations

- Windows 10 or 11, x64, with a working audio output.
- The music player must publish Windows SMTC information for song titles and artwork to appear. Unsupported players may still supply output audio, but no song metadata.
- Output loopback is device-based. Version 1.0.1 does not provide per-application audio capture.
- Only one service can use port 5000 at a time. A port-conflict message tells you to close the other bridge; the app does not silently change ports or terminate another program.
- If the saved output is disconnected, the bridge waits for it and retries automatically. Use **Audio Controls** and **Refresh outputs** if you want to choose a different output.
- The release is not digitally signed. Verify that you downloaded it from this repository and compare the included SHA-256 checksums if needed.

## Run from source

Use Python 3.14 on Windows x64. From this folder:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe bridge.py
```

The included `Start Better SMTC Bridge.bat` can set up a local virtual environment on its first run. A source setup needs Internet access to download dependencies; the packaged application runs offline.

For browser controls without a desktop window:

```powershell
.venv\Scripts\python.exe bridge.py --headless
```

Then open `http://127.0.0.1:5000/`. `--device <id>` explicitly starts one of the output loopback devices listed by `/devices`. `--allow-origin https://your-widget.example` adds an exact permitted widget origin for that process. These options are for headless mode; they do not change your saved widget settings.

## License and credits

This is an adaptation of nutty's code, used under the repository owner's confirmed private permission. The upstream code and assets retain their author's rights. CreatorSuite additions have a separate, explicitly scoped license; see [LICENSE](LICENSE). This repository does not grant a new open-source license over nutty's work. Private permission correspondence is not included.

[nutty](https://nutty.gg/) created the original [SMTC Bridge](https://github.com/nuttylmao/smtc-bridge) and [Universal Now Playing](https://widgets.nutty.gg/now-playing/settings/). Better SMTC Bridge retains the original media-reading implementation, metadata interface, tray behavior, and upstream assets, with additional output-audio analysis and local controls. The Git history preserves the original authorship. This is a modified version maintained by Sveenet, not an official nutty release, and does not imply endorsement. See [the provenance record](docs/provenance.md) for the exact upstream revision and changes.

Bundled libraries retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the `licenses` folder, which are also distributed with the Windows release. Corresponding source and replacement instructions are included for LGPL components.

Microsoft provides the Windows SMTC and WASAPI interfaces. Thanks to the maintainers of PyWinRT, PyAudioWPatch, PortAudio, NumPy, aiohttp, Python, Tcl/Tk, and PyInstaller. The exact component notices and provenance are included with this project.
