# Changelog

## 1.0.1 — 2026-11-13

- Keeps audio frames flowing when an overlay disconnects or a browser connection stalls.
- Bounds failed-client cleanup and isolates transient capture errors from the shared stream.
- Adds regression coverage for sustained audio, client failures, and recovery.
- Preserves the saved output, quiet startup, and port 5000.
- Supports read-only metadata and audio access from widgets.sveenet.com.
- Restores the original v1.0.0 release separately; later fixes are released as v1.0.1.

## 1.0.0 — 2026-11-10

Initial release of Better SMTC Bridge.

- Retains nutty's original SMTC media-reading implementation, metadata shape, tray behavior, and attribution, with compatibility updates for the packaged runtime.
- Real WASAPI output analysis: 256 waveform samples, 96 logarithmic spectrum bands, and an RMS level, up to 30 updates per second.
- One loopback-only service on port 5000 for metadata, audio streaming, health, and local controls.
- Local browser output selection, start/stop controls, audio level display, original tray menu, and optional headless operation.
- Remembered output selection, automatic reconnect on later launches, and no repeated selection page after initial setup.
- Explicit capture start, no microphone capture, no audio recordings, and no cloud uploads.
- Preserved upstream rights and credits, separately licensed additions, and bundled dependency notices and required corresponding sources.
