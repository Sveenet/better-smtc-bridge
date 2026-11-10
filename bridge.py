"""Launch the original SMTC Bridge base with Better SMTC Bridge additions."""
import argparse
import asyncio
import sys
import atexit
import base64
import configparser
import datetime
import hashlib
import json
import os
import platform
import socket
import tempfile
import threading
import time
import traceback
import webbrowser

# Explicit imports keep dynamically loaded original dependencies in the EXE.
import flask
import flask_cors
import psutil
import pystray
import plyer
from PIL import Image
from artwork import ArtworkCache
import winrt.windows.foundation
import winrt.windows.foundation.collections
import winrt.windows.media
import winrt.windows.media.control
import winrt.windows.storage.streams

from metadata import load_original
from server import APP_NAME, VERSION, Bridge


def main():
    parser = argparse.ArgumentParser(description=APP_NAME + " " + VERSION)
    parser.add_argument("--headless", action="store_true", help="Run without the tray; use the local browser controls.")
    parser.add_argument("--device", type=int, help="Explicitly start the listed WASAPI loopback output index (headless only).")
    parser.add_argument("--allow-origin", action="append", default=[], help="Allow an additional exact widget website origin (headless only).")
    parser.add_argument("--test-port", type=int, default=5000, help=argparse.SUPPRESS)
    parser.add_argument("--version", action="version", version=APP_NAME + " " + VERSION)
    args = parser.parse_args()
    if args.headless:
        async def run():
            bridge = Bridge(args.test_port, args.allow_origin)
            await bridge.run(args.device)
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            return 0
        except Exception as error:
            if sys.stderr:
                print(str(error), file=sys.stderr)
            return 1
    else:
        original = load_original()
        original.PORT = args.test_port
        if original.is_already_running():
            import webbrowser
            webbrowser.open(f"http://127.0.0.1:{args.test_port}/")
            return 0
        original.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
