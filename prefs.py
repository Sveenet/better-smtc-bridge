"""Per-user audio preferences. No device indices, media or secrets are stored."""
import json
import os
from pathlib import Path
import tempfile


class Preferences:
    def __init__(self, path=None):
        local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        self.path = Path(path) if path else local / "BetterSMTCBridge" / "settings.json"
        self.output_name = None
        self.enabled = False
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (isinstance(data, dict) and data.get("schema") == 1
                    and isinstance(data.get("output_name"), str) and 0 < len(data["output_name"]) <= 1024
                    and isinstance(data.get("enabled"), bool)):
                self.output_name = data["output_name"]
                self.enabled = data["enabled"]
        except (OSError, ValueError):
            pass

    @property
    def configured(self):
        return self.output_name is not None

    def save(self, output_name, enabled):
        data = {"schema": 1, "output_name": output_name, "enabled": bool(enabled)}
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix="settings-", suffix=".tmp",
                                             dir=self.path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
            self.output_name, self.enabled = output_name, bool(enabled)
        except OSError:
            raise RuntimeError("The audio preference could not be saved. Check your local app-data folder permissions.") from None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
