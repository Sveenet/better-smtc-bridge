Better SMTC Bridge 1.0.1 fixes audio visualizations freezing after browser sources reconnect or a connection stalls. Healthy overlays keep receiving frames, and transient capture failures recover automatically.

Download the **Windows x64 ZIP**, extract the entire folder, close the original SMTC Bridge, and open **Better SMTC Bridge.exe**. Select your music output once and click **Start visualizing**. Later launches reconnect automatically and stay in the tray without reopening the selection page. No separate Python installation is needed for the packaged release.

- Existing song metadata remains on port **5000**.
- Supports the current widgets.sveenet.com site for read-only metadata and audio access.
- Restores normal versioning: the original v1.0.0 package remains available separately.
- Audio waveforms and spectrum use **ws://127.0.0.1:5000/audio**.
- Your output selection is remembered by name. Missing outputs are retried automatically; Stop audio also remains stopped across restarts.
- Compatible with CreatorSuite Universal Music's selectable artwork colors, Dominant color, and existing six-color URLs.
- Audio remains in memory on your PC; no microphone capture, recordings, or cloud uploads.
- Includes README, license, dependency notices, and SHA-256 checksums.

Version 1.0.1 analyzes the selected output device, including all applications playing through that output. It does not isolate an individual application. The Windows application is unsigned.

Built on [nutty's original SMTC Bridge code](https://github.com/nuttylmao/smtc-bridge), with audio analysis and local controls added by Sveenet. Original credits and rights are retained. This is a private, modified release made under the repository owner's confirmed permission; it is not an official nutty release. See the included license and third-party notices for the separate rights applicable to each component.
