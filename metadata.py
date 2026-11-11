"""Serve nutty's original SMTC function through one shared async lock."""
import asyncio
import importlib.machinery
import importlib.util
from pathlib import Path
import sys


def load_original():
    name = "smtc_bridge_original"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).with_name("smtc-bridge.pyw")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class Metadata:
    def __init__(self, reader=None):
        self.reader = reader
        self.lock = asyncio.Lock()
        self.available = False

    async def read(self):
        async with self.lock:
            if self.reader is None:
                self.reader = load_original().get_all_media_info
            result = await self.reader()
            self.available = "error" not in result
            return {**result, "app_version": "1.0.1", "bridge_version": "1.0.1",
                    "upstream_version": "1.0.1", "bridge_name": "Better SMTC Bridge"}
