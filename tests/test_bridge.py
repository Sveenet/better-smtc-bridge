"""Offline fixtures: never access a microphone, play audio, or record sound."""
import asyncio
import json
from pathlib import Path
import sys
import time
import tempfile
import unittest
from unittest.mock import patch

import aiohttp
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio import Analyzer, OutputCapture
from artwork import ArtworkCache
from prefs import Preferences
from server import Bridge, origin_allowed


class DSPTests(unittest.TestCase):
    def test_silence_has_no_invented_motion(self):
        frame = Analyzer().frame(np.zeros(4096))
        self.assertEqual(len(frame["waveform"]), 256)
        self.assertEqual(len(frame["spectrum"]), 96)
        self.assertEqual(frame["level"], 0)
        self.assertTrue(all(x == 0 for x in frame["waveform"] + frame["spectrum"]))

    def test_known_tone_and_antiphase_stereo(self):
        analyzer = Analyzer()
        tone = .5 * np.sin(2 * np.pi * 1000 * np.arange(4096) / 48000)
        mono = analyzer.frame(tone)
        stereo = analyzer.frame(np.column_stack((tone, -tone)))
        strongest = int(np.argmax(stereo["spectrum"]))
        self.assertTrue(850 < analyzer.centers[strongest] < 1150)
        self.assertAlmostEqual(stereo["level"], .5 / np.sqrt(2), delta=.01)
        self.assertEqual(mono["spectrum"], stereo["spectrum"])
        self.assertGreater(max(stereo["waveform"]), .4)

    def test_malformed_pcm_cannot_emit_nonfinite_values(self):
        frame = Analyzer().frame([np.nan, np.inf, -np.inf, 5, -5])
        json.dumps(frame, allow_nan=False)
        self.assertTrue(all(-1 <= x <= 1 for x in frame["waveform"]))
        self.assertTrue(all(0 <= x <= 1 for x in frame["spectrum"]))


class FakeStream:
    def __init__(self):
        self.active = True
    def is_active(self):
        return self.active
    def stop_stream(self):
        self.active = False
    def close(self):
        self.active = False


class FakeAudio:
    def get_device_info_by_index(self, index):
        return {"index": index, "name": "Fixture output", "isLoopbackDevice": index in (1, 2),
                "maxInputChannels": 2, "defaultSampleRate": 48000}
    def open(self, **kwargs):
        self.callback = kwargs["stream_callback"]
        return FakeStream()
    def terminate(self):
        pass


class CaptureTests(unittest.TestCase):
    def test_explicit_loopback_only_and_clear_on_switch(self):
        with patch("audio.pa.PyAudio", FakeAudio):
            capture = OutputCapture()
            self.assertEqual(capture.frame()["connected"], False)
            with self.assertRaises(ValueError):
                capture.start(0)  # A microphone-like device must never be opened.
            capture.start(1)
            pcm = np.ones((1024, 2), dtype=np.float32) * .4
            capture.interface.callback(pcm.tobytes(), 1024, None, 0)
            self.assertGreater(capture.frame()["level"], .3)
            capture.start(2)
            self.assertEqual(capture.frame()["level"], 0)
            capture.interface.callback(pcm.tobytes(), 1024, None, 0)
            capture._last_data = time.monotonic() - 1
            self.assertEqual(capture.frame()["level"], 0)
            capture.stop()
            self.assertFalse(capture.frame()["connected"])
            capture.close()


class CacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_bounded_artwork_cache_retries_missing_and_expires(self):
        reader = ArtworkCache()
        calls = []
        async def thumbnail(value):
            calls.append(value)
            return value
        reader.thumbnail = thumbnail
        class Session:
            source_app_user_model_id = "fixture"
        class Media:
            title = "fixture"
            artist = "fixture"
            album_title = "fixture"
            thumbnail = None
        media = Media()
        self.assertIsNone(await reader.get(Session.source_app_user_model_id, media))
        media.thumbnail = "data:image/png;base64,fixture"
        self.assertEqual(await reader.get(Session.source_app_user_model_id, media), media.thumbnail)
        await reader.get(Session.source_app_user_model_id, media)
        self.assertEqual(len(calls), 2)
        key = next(iter(reader.artwork))
        reader.artwork[key] = (time.monotonic() - 20, "expired")
        await reader.get(Session.source_app_user_model_id, media)
        self.assertEqual(len(calls), 3)
        for i in range(40):
            media.title = str(i)
            await reader.get(Session.source_app_user_model_id, media)
        self.assertEqual(len(reader.artwork), 32)


class StubCapture:
    def __init__(self):
        self.active = False
        self.device = None
    def devices(self):
        return [{"id": 1, "name": "Fixture output", "default": True}]
    def start(self, index):
        if index != 1:
            raise ValueError("Invalid output")
        self.active, self.device = True, {"id": 1, "name": "Fixture output"}
    def stop(self):
        self.active, self.device = False, None
    def frame(self):
        return Analyzer().frame(np.zeros(4096)) if self.active else {"type": "status", "connected": False}
    def close(self):
        self.stop()


class BroadcastTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.bridge = Bridge(preferences=Preferences(Path(self.folder.name) / "settings.json"))
        self.bridge.capture = StubCapture()
        self.bridge.capture.start(1)
        self.bridge.started = True

    async def asyncTearDown(self):
        if self.bridge.pump:
            self.bridge.pump.cancel()
            await asyncio.gather(self.bridge.pump, return_exceptions=True)
        self.folder.cleanup()

    class Listener:
        def __init__(self):
            self.frames = []
            self.repeated = asyncio.Event()
        async def send_str(self, value):
            self.frames.append(json.loads(value))
            if len(self.frames) >= 3:
                self.repeated.set()

    async def test_stalled_client_close_cannot_freeze_other_overlays(self):
        class Stalled:
            async def send_str(self, value):
                raise asyncio.TimeoutError()
            async def close(self):
                await asyncio.Event().wait()
        healthy, stalled = self.Listener(), Stalled()
        self.bridge.clients.update((healthy, stalled))
        self.bridge.pump = asyncio.create_task(self.bridge.broadcast())
        await asyncio.wait_for(healthy.repeated.wait(), 1)
        self.assertNotIn(stalled, self.bridge.clients)
        self.assertFalse(self.bridge.pump.done())
        self.assertTrue(self.bridge.health()["audio_connected"])

    async def test_close_error_cannot_kill_shared_broadcast(self):
        class Broken:
            async def send_str(self, value):
                raise ConnectionResetError("browser navigated away")
            async def close(self):
                raise RuntimeError("transport already gone")
        healthy, broken = self.Listener(), Broken()
        self.bridge.clients.update((healthy, broken))
        self.bridge.pump = asyncio.create_task(self.bridge.broadcast())
        await asyncio.wait_for(healthy.repeated.wait(), 1)
        self.assertNotIn(broken, self.bridge.clients)
        self.assertFalse(self.bridge.pump.done())

    async def test_failed_pump_is_reported_and_restarted(self):
        def fail_once():
            self.bridge.capture.frame = lambda: Analyzer().frame(np.zeros(4096))
            raise RuntimeError("transient capture failure")
        self.bridge.capture.frame = fail_once
        self.bridge.pump = asyncio.create_task(self.bridge.broadcast())
        with self.assertRaisesRegex(RuntimeError, "transient capture"):
            await self.bridge.pump
        health = self.bridge.health()
        self.assertFalse(health["audio_connected"])
        self.assertFalse(health["broadcast_running"])
        self.assertIsNone(health["last_broadcast_age_ms"])
        self.assertIn("recover", health["audio_message"])
        healthy = self.Listener()
        self.bridge.clients.add(healthy)
        await self.bridge.ensure_broadcast()
        await asyncio.wait_for(healthy.repeated.wait(), 1)
        self.assertTrue(self.bridge.health()["audio_connected"])
        self.assertIsNone(self.bridge.health()["audio_message"])
        self.assertEqual(self.bridge.health()["last_broadcast_error"], "RuntimeError")

    async def test_stale_pump_is_cancelled_before_replacement(self):
        healthy = self.Listener()
        self.bridge.clients.add(healthy)
        self.bridge.last_broadcast_at = time.monotonic() - 3
        self.bridge.pump = asyncio.create_task(asyncio.Event().wait())
        old_pump = self.bridge.pump
        await self.bridge.ensure_broadcast()
        self.assertTrue(old_pump.cancelled())
        self.assertIsNot(self.bridge.pump, old_pump)
        await asyncio.wait_for(healthy.repeated.wait(), 1)
        self.assertEqual(self.bridge.health()["last_broadcast_error"], "BroadcastStalled")

    async def test_health_detects_stale_pump_and_shutdown_does_not_restart(self):
        healthy = self.Listener()
        self.bridge.clients.add(healthy)
        self.bridge.pump = asyncio.create_task(self.bridge.broadcast())
        await asyncio.wait_for(healthy.repeated.wait(), 1)
        health = self.bridge.health()
        self.assertTrue(health["broadcast_running"])
        self.assertLess(health["last_broadcast_age_ms"], 500)
        self.bridge.last_broadcast_at = time.monotonic() - 2
        self.assertFalse(self.bridge.health()["audio_connected"])
        self.bridge.pump.cancel()
        await asyncio.gather(self.bridge.pump, return_exceptions=True)
        old_pump = self.bridge.pump
        self.bridge.closing = True
        await self.bridge.ensure_broadcast()
        self.assertIs(self.bridge.pump, old_pump)


class APITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.preferences_dir = tempfile.TemporaryDirectory()
        self.patcher = patch("server.OutputCapture", StubCapture)
        self.patcher.start()
        self.bridge = Bridge(port=0, preferences=Preferences(Path(self.preferences_dir.name) / "settings.json"))
        self.task = asyncio.create_task(self.bridge.run())
        for _ in range(100):
            if self.bridge.started or self.task.done():
                break
            await asyncio.sleep(.02)
        if self.task.done():
            await self.task
        self.url = f"http://127.0.0.1:{self.bridge.port}"
        self.client = aiohttp.ClientSession()

    async def asyncTearDown(self):
        self.bridge.stopped.set()
        await self.task
        await self.client.close()
        self.patcher.stop()
        self.preferences_dir.cleanup()

    async def test_health_origin_and_control_protection(self):
        async with self.client.get(self.url + "/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual((await response.json())["application"], "Better SMTC Bridge")
        for origin in ("https://untrusted.example", "null", "https://localhost.evil.example"):
            async with self.client.get(self.url + "/health", headers={"Origin": origin}) as response:
                self.assertEqual(response.status, 403)
        async with self.client.get(self.url + "/health", headers={"Origin": "https://creator-suite-amv.pages.dev"}) as response:
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://creator-suite-amv.pages.dev")
        async with self.client.get(self.url + "/", headers={"Origin": "https://creator-suite-amv.pages.dev"}) as response:
            self.assertEqual(response.status, 403)
        async with self.client.post(self.url + "/api/start", json={"device": 1}) as response:
            self.assertEqual(response.status, 403)
        headers = {"X-Bridge-Token": self.bridge.token}
        for malformed in (None, [], {"device": True}, {"device": -1}):
            async with self.client.post(self.url + "/api/start", data=json.dumps(malformed), headers={**headers, "Content-Type": "application/json"}) as response:
                self.assertEqual(response.status, 400)

    async def test_websocket_schema_and_stop(self):
        async with self.client.ws_connect(self.url + "/audio", origin="https://widgets.nutty.gg") as socket:
            self.assertFalse((await socket.receive_json())["connected"])
            async with self.client.post(self.url + "/api/start", json={"device": 1}, headers={"X-Bridge-Token": self.bridge.token}) as response:
                self.assertEqual(response.status, 200)
            frame = await socket.receive_json(timeout=2)
            self.assertEqual(frame["type"], "audio-frame")
            self.assertEqual(frame["version"], 1)
            self.assertEqual(len(frame["waveform"]), 256)
            self.assertEqual(len(frame["spectrum"]), 96)
            self.assertEqual(frame["level"], 0)
            await self.bridge.stop_audio()
            for _ in range(35):
                frame = await socket.receive_json(timeout=2)
                if frame["type"] == "status":
                    break
            self.assertFalse(frame["connected"])


if __name__ == "__main__":
    unittest.main()
