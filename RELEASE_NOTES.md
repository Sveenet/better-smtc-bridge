Better SMTC Bridge 1.0.0 combines Windows song information and real audio analysis in one local app.

This project was created solely to add functionality to [nutty's original SMTC Bridge](https://github.com/nuttylmao/smtc-bridge) for seamless use in the [Universal Music widget](https://widgets.sveenet.com/universal-music/settings). It adds live audio analysis and saved output controls while retaining the original SMTC metadata interface and port **5000**.

I appreciate nutty's work and the effort behind the original SMTC Bridge. This project is a good-faith extension made to add useful functionality for music widgets, with no intention of harming nutty or the original project.

Download the **Windows x64 ZIP**, extract the entire folder, close the original SMTC Bridge, and open **Better SMTC Bridge.exe**. Select your music output once and click **Start visualizing**. Later launches reconnect automatically and stay in the tray without reopening the selection page. No separate Python installation is needed for the packaged release.

- Existing song metadata remains on port **5000**.
- Audio waveforms and spectrum use **ws://127.0.0.1:5000/audio**.
- Your output selection is remembered by name. Missing outputs are retried automatically; Stop audio also remains stopped across restarts.
- Compatible with CreatorSuite Universal Music's six-color creative themes.
- Audio remains in memory on your PC; no microphone capture, recordings, or cloud uploads.
- Includes README, license, dependency notices, and SHA-256 checksums.

Version 1.0.0 analyzes the selected output device, including all applications playing through that output. It does not isolate an individual application. The Windows application is unsigned.

Built on [nutty's original SMTC Bridge code](https://github.com/nuttylmao/smtc-bridge), with audio analysis and local controls added by Sveenet. Original credits and rights are retained. This is an independently maintained modification, not an official nutty release. Sveenet's original additions are reusable under the included MIT License. The original SMTC Bridge material and dependencies retain their separate rights; see LICENSE, LICENSE-MIT and THIRD_PARTY_NOTICES.md.
