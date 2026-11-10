import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from metadata import load_original
from prefs import Preferences
from server import Bridge


class PreferenceTests(unittest.TestCase):
    def test_atomic_saved_name_and_disabled_state(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            prefs = Preferences(path)
            self.assertFalse(prefs.configured)
            prefs.save("Music output", True)
            restored = Preferences(path)
            self.assertTrue(restored.enabled)
            self.assertEqual(restored.output_name, "Music output")
            restored.save("Music output", False)
            self.assertFalse(Preferences(path).enabled)
            self.assertTrue(Preferences(path).configured)
            self.assertEqual(set(json.loads(path.read_text())), {"schema", "output_name", "enabled"})
            self.assertFalse(list(path.parent.glob("*.tmp")))

    def test_invalid_file_returns_to_setup_without_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            for contents in ("broken JSON", "[]", '{"schema":1,"output_name":"Music","enabled":"yes"}'):
                path.write_text(contents)
                prefs = Preferences(path)
                self.assertFalse(prefs.enabled)
                self.assertFalse(prefs.configured)

    def test_failed_atomic_replace_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            prefs = Preferences(path)
            prefs.save("Music", True)
            with patch("prefs.os.replace", side_effect=OSError("fixture")):
                with self.assertRaises(RuntimeError):
                    prefs.save("Other output", True)
            self.assertEqual(Preferences(path).output_name, "Music")
            self.assertFalse(list(path.parent.glob("*.tmp")))

    def test_setup_browser_only_opens_before_output_is_configured(self):
        original = load_original()
        for configured in (False, True):
            bridge = SimpleNamespace(started=True, preferences=SimpleNamespace(configured=configured))
            with patch.multiple(original, service_bridge=bridge, service_error=None,
                                service_ready=Mock(), service_loop=Mock(is_running=lambda: False)), \
                 patch.object(original.threading, "Thread"), patch.object(original, "setup_tray"), \
                 patch.object(original.os, "_exit"), patch.object(original.webbrowser, "open") as browser:
                original.main()
                self.assertEqual(browser.call_count, 0 if configured else 1)


class DeviceCapture:
    def __init__(self):
        self.active = False
        self.device = None
        self.outputs = [{"id": 87, "name": "Music", "default": False}]
        self.starts = []
        self.enumerations = 0
    def devices(self):
        self.enumerations += 1
        return self.outputs
    def start(self, index):
        self.starts.append(index)
        self.device = next(device for device in self.outputs if device["id"] == index)
        self.active = True
    def stop(self):
        self.active = False
        self.device = None


class RestoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.preferences = Preferences(Path(self.folder.name) / "settings.json")
        self.preferences.save("Music", True)
        self.bridge = Bridge(preferences=self.preferences)
        self.bridge.capture = DeviceCapture()
    async def asyncTearDown(self):
        self.folder.cleanup()

    async def test_restore_matches_name_after_device_index_changes(self):
        await self.bridge.resume_saved_output()
        self.assertEqual(self.bridge.capture.starts, [87])
        await self.bridge.resume_saved_output()
        self.assertEqual(self.bridge.capture.enumerations, 1)

    async def test_missing_output_waits_and_later_reconnects(self):
        self.bridge.capture.outputs = [{"id": 3, "name": "Unrelated default", "default": True}]
        await self.bridge.resume_saved_output()
        self.assertFalse(self.bridge.capture.active)
        self.assertEqual(self.bridge.capture.starts, [])
        self.bridge.capture.outputs.append({"id": 92, "name": "Music"})
        await self.bridge.resume_saved_output()
        self.assertEqual(self.bridge.capture.starts, [92])

    async def test_stop_stays_disabled_across_restart_and_retry(self):
        await self.bridge.resume_saved_output()
        await self.bridge.stop_audio()
        await self.bridge.resume_saved_output()
        self.assertFalse(self.bridge.capture.active)
        self.assertFalse(Preferences(self.preferences.path).enabled)

    async def test_duplicate_names_do_not_capture_another_device(self):
        self.bridge.capture.outputs.append({"id": 91, "name": "Music"})
        await self.bridge.resume_saved_output()
        self.assertFalse(self.bridge.capture.active)

    async def test_failed_stop_save_does_not_restart_capture_in_memory(self):
        await self.bridge.resume_saved_output()
        with patch.object(self.preferences, "save", side_effect=RuntimeError("fixture")):
            with self.assertRaises(RuntimeError):
                await self.bridge.stop_audio()
        await self.bridge.resume_saved_output()
        self.assertFalse(self.bridge.capture.active)


if __name__ == "__main__":
    unittest.main()
