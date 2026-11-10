"""One shared, memory-only WASAPI output analyzer. No microphone or file capture."""
from collections import deque
import threading
import time

import numpy as np
import pyaudiowpatch as pa


class Analyzer:
    SIZE = 4096

    def __init__(self, rate=48000):
        self.rate = rate
        self.window = np.hanning(self.SIZE)
        self.frequencies = np.fft.rfftfreq(self.SIZE, 1 / rate)
        self.edges = np.geomspace(20, min(20000, rate / 2), 97)
        self.centers = np.sqrt(self.edges[:-1] * self.edges[1:])
        self.bins = [(self.frequencies >= a) & (self.frequencies < b)
                     for a, b in zip(self.edges[:-1], self.edges[1:])]

    def frame(self, samples):
        signal = np.nan_to_num(np.asarray(samples, dtype=np.float32), nan=0, posinf=0, neginf=0)
        if signal.ndim == 1:
            signal = signal[:, None]
        signal = np.clip(signal[-self.SIZE:], -1, 1)
        if len(signal) < self.SIZE:
            signal = np.pad(signal, ((self.SIZE - len(signal), 0), (0, 0)))
        recent = signal[-1024:]
        # Energy is combined after FFT, so opposite-phase stereo cannot cancel out.
        strongest = recent[:, np.argmax(np.mean(recent ** 2, axis=0))]
        waveform = np.interp(np.linspace(0, len(strongest) - 1, 256), np.arange(len(strongest)), strongest)
        magnitude = np.abs(np.fft.rfft(signal * self.window[:, None], axis=0)).mean(axis=1) * (2 / self.window.sum())
        # Interpolation fills bands below the FFT's bin resolution without fake energy.
        bands = np.array([magnitude[mask].max() if mask.any()
                          else np.interp(center, self.frequencies, magnitude)
                          for mask, center in zip(self.bins, self.centers)])
        spectrum = np.clip((20 * np.log10(np.maximum(bands, 1e-12)) + 72) / 72, 0, 1)
        return {"type": "audio-frame", "version": 1, "connected": True,
                "timestamp": int(time.time() * 1000),
                "waveform": np.round(waveform, 5).tolist(),
                "spectrum": np.round(spectrum, 5).tolist(),
                "level": round(float(np.clip(np.sqrt(np.mean(recent ** 2)), 0, 1)), 5)}


class OutputCapture:
    def __init__(self):
        self.interface = pa.PyAudio()
        self.stream = None
        self.device = None
        self.analyzer = Analyzer()
        self._chunks = deque(maxlen=12)
        self._lock = threading.Lock()
        self._last_data = 0.0
        self.error = "Choose an output and start visualizing."

    def devices(self):
        # PortAudio snapshots endpoints at initialization. Refresh safely while stopped.
        if not self.active:
            self.stop()
            self.interface.terminate()
            self.interface = pa.PyAudio()
        try:
            default = self.interface.get_default_wasapi_loopback()["index"]
        except (OSError, ValueError):
            default = -1
        return [{"id": int(d["index"]), "name": d["name"],
                 "sample_rate": int(d["defaultSampleRate"]),
                 "default": int(d["index"]) == default}
                for d in self.interface.get_loopback_device_info_generator()
                if d.get("isLoopbackDevice") and d["maxInputChannels"] > 0]

    def start(self, index):
        # The selected input MUST be a duplicated output endpoint, never a microphone.
        device = self.interface.get_device_info_by_index(index)
        if not device.get("isLoopbackDevice") or device["maxInputChannels"] < 1:
            raise ValueError("Choose a Windows audio output from the list.")
        self.stop()
        channels = int(device["maxInputChannels"])
        rate = int(device["defaultSampleRate"])
        self.analyzer = Analyzer(rate)

        def on_audio(data, count, timing, status):
            samples = np.frombuffer(data, dtype=np.float32)
            if samples.size and samples.size % channels == 0:
                with self._lock:
                    self._chunks.append(samples.reshape(-1, channels).copy())
                    self._last_data = time.monotonic()
            return (None, pa.paContinue)

        try:
            self.stream = self.interface.open(format=pa.paFloat32, channels=channels, rate=rate,
                                              input=True, input_device_index=index,
                                              frames_per_buffer=1024, stream_callback=on_audio)
            self.device = {"id": int(device["index"]), "name": device["name"]}
            self.error = None
        except Exception:
            self.stop()
            self.error = "The output could not be opened. Refresh devices and try again."
            raise RuntimeError(self.error) from None

    @property
    def active(self):
        try:
            stream = self.stream
            return stream is not None and stream.is_active()
        except OSError:
            return False

    def frame(self):
        if not self.active:
            return {"type": "status", "version": 1, "connected": False,
                    "timestamp": int(time.time() * 1000)}
        with self._lock:
            # WASAPI can stop callbacks during genuine digital silence.
            samples = np.concatenate(tuple(self._chunks)) if self._chunks and time.monotonic() - self._last_data < .20 else np.zeros(4096)
        return self.analyzer.frame(samples)

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop_stream()
            except OSError:
                pass
            finally:
                try:
                    self.stream.close()
                except OSError:
                    pass
                finally:
                    self.stream = None
        self.device = None
        with self._lock:
            self._chunks.clear()
            self._last_data = 0

    def close(self):
        self.stop()
        self.interface.terminate()
