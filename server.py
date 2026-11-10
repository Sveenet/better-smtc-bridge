"""Loopback-only HTTP and WebSocket service. There are no outbound requests."""
import asyncio
import json
import secrets
import time
from urllib.parse import urlsplit

from aiohttp import web, WSMsgType

from audio import OutputCapture
from metadata import Metadata
from prefs import Preferences

APP_NAME = "Better SMTC Bridge"
VERSION = "1.0.0"
TRUSTED_ORIGINS = {"https://creator-suite-amv.pages.dev", "https://widgets.nutty.gg"}


def origin_allowed(origin, extra=()):
    if origin is None or origin in TRUSTED_ORIGINS or origin in extra:
        return True
    try:
        parsed = urlsplit(origin)
        return (parsed.scheme in {"http", "https"} and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
                and not parsed.username and not parsed.password and not parsed.path and not parsed.query and not parsed.fragment)
    except ValueError:
        return False


class Bridge:
    def __init__(self, port=5000, allowed_origins=(), metadata_reader=None, on_stop=None, preferences=None):
        self.port = port
        self.allowed_origins = allowed_origins
        self.token = secrets.token_urlsafe(32)
        self.capture = None
        self.metadata = Metadata(metadata_reader)
        self.clients = set()
        self.stopped = asyncio.Event()
        self.runner = None
        self.pump = None
        self.latest_level = 0.0
        self.started = False
        self.error = None
        self.closing = False
        self.on_stop = on_stop
        self.audio_lock = asyncio.Lock()
        self.preferences = preferences if preferences is not None else Preferences()
        self.resume_task = None
        self.audio_message = None

    def health(self):
        return {"application": APP_NAME, "version": VERSION, "port": self.port,
                "ready": self.started and not self.closing,
                "audio_connected": bool(self.capture and self.capture.active),
                "metadata_available": self.metadata.available,
                "device": self.capture.device if self.capture else None,
                "level": self.latest_level, "clients": len(self.clients),
                "saved_output": self.preferences.output_name,
                "audio_enabled": self.preferences.enabled, "configured": self.preferences.configured,
                "audio_message": self.audio_message}

    @web.middleware
    async def guard(self, request, handler):
        if self.closing:
            raise web.HTTPServiceUnavailable(text="The bridge is closing.")
        try:
            host = urlsplit("http://" + request.host).hostname
        except ValueError:
            host = None
        if host not in {"127.0.0.1", "localhost", "::1"} or request.remote not in {"127.0.0.1", "::1"}:
            raise web.HTTPForbidden(text="This service is local to this computer.")
        origin = request.headers.get("Origin")
        if not origin_allowed(origin, self.allowed_origins):
            raise web.HTTPForbidden(text="This website is not allowed to access this bridge.")
        # Control tokens are only served by the local page, never cross-origin.
        if request.path in {"/", "/control", "/devices", "/sessions"} and origin and origin not in {
            f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}:
            raise web.HTTPForbidden(text="Open the controls on this computer.")
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if not secrets.compare_digest(request.headers.get("X-Bridge-Token", ""), self.token):
                raise web.HTTPForbidden(text="Open the local bridge controls to change audio capture.")
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)
        if not response.prepared:
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Private-Network"] = "true"
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    async def devices(self):
        async with self.audio_lock:
            return await asyncio.to_thread(self.capture.devices)

    async def set_device(self, index):
        async with self.audio_lock:
            await asyncio.to_thread(self.capture.start, index)
            try:
                self.preferences.save(self.capture.device["name"], True)
            except RuntimeError:
                self.preferences.enabled = False
                await asyncio.to_thread(self.capture.stop)
                raise
            self.audio_message = None

    async def stop_audio(self):
        async with self.audio_lock:
            self.preferences.enabled = False
            await asyncio.to_thread(self.capture.stop)
            if self.preferences.configured:
                self.preferences.save(self.preferences.output_name, False)
            self.audio_message = None
        self.latest_level = 0

    async def resume_saved_output(self):
        async with self.audio_lock:
            if not self.preferences.enabled or not self.preferences.configured or self.capture.active:
                return
            try:
                devices = await asyncio.to_thread(self.capture.devices)
                matches = [device for device in devices if device["name"] == self.preferences.output_name]
                if len(matches) != 1:
                    self.audio_message = "Waiting for your saved audio output. It will reconnect automatically."
                    return
                await asyncio.to_thread(self.capture.start, matches[0]["id"])
                self.audio_message = None
            except (OSError, ValueError, RuntimeError):
                self.audio_message = "Your saved output is unavailable. Retrying automatically."

    async def watch_saved_output(self):
        while True:
            await asyncio.sleep(5)
            await self.resume_saved_output()

    async def route_health(self, request):
        return web.json_response(self.health())

    async def route_metadata(self, request):
        return web.json_response(await self.metadata.read())

    async def route_sessions(self, request):
        import html
        payload = await self.metadata.read()
        names = sorted({session["source_app_id"] for session in payload.get("sessions", [])})
        items = "".join(f"<li>{html.escape(name)}</li>" for name in names) or "<li>No active audio sources found.</li>"
        return web.Response(text="<body style='background:#121212;color:white;font-family:sans-serif;padding:20px'><h3>Active Audio Sources:</h3><ul>" + items + "</ul></body>", content_type="text/html")

    async def route_devices(self, request):
        return web.json_response({"devices": await self.devices(),
                                  "active_device": self.capture.device if self.capture.active else None,
                                  "saved_output": self.preferences.output_name})

    async def route_start(self, request):
        try:
            data = await request.json()
            if (not isinstance(data, dict) or not isinstance(data.get("device"), int)
                    or isinstance(data.get("device"), bool) or not 0 <= data["device"] <= 65535):
                raise ValueError("Select an audio output first.")
            await self.set_device(data["device"])
            return web.json_response(self.health())
        except (ValueError, OSError, RuntimeError) as error:
            return web.json_response({"error": str(error)}, status=400)

    async def route_stop(self, request):
        try:
            await self.stop_audio()
            return web.json_response(self.health())
        except RuntimeError as error:
            return web.json_response({"error": str(error)}, status=500)

    async def route_quit(self, request):
        asyncio.get_running_loop().call_later(.1, self.stopped.set)
        return web.json_response({"stopping": True})

    async def route_control(self, request):
        from pathlib import Path
        page = Path(__file__).with_name("control.html").read_text(encoding="utf-8")
        return web.Response(text=page.replace("__BRIDGE_TOKEN__", self.token), content_type="text/html",
                            headers={"Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"})

    async def route_ws(self, request):
        ws = web.WebSocketResponse(heartbeat=15, timeout=.1, max_msg_size=1024, compress=False)
        await ws.prepare(request)
        self.clients.add(ws)
        if self.closing:
            self.clients.discard(ws)
            await ws.close()
            return ws
        await ws.send_json(self.capture.frame())
        try:
            async for message in ws:
                if message.type in {WSMsgType.ERROR, WSMsgType.CLOSE}:
                    break
                # This stream is read-only: clients cannot ask it to capture audio.
        finally:
            self.clients.discard(ws)
        return ws

    async def broadcast(self):
        last_status = 0
        while True:
            started = time.monotonic()
            payload = self.capture.frame()
            self.latest_level = payload.get("level", 0)
            if payload["type"] == "audio-frame" or started - last_status >= 1:
                if payload["type"] == "status":
                    last_status = started
                encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False)

                async def send(client):
                    try:
                        await asyncio.wait_for(client.send_str(encoded), timeout=.1)
                    except (ConnectionError, asyncio.TimeoutError, RuntimeError):
                        self.clients.discard(client)
                        await client.close()

                await asyncio.gather(*(send(client) for client in tuple(self.clients)))
            await asyncio.sleep(max(0, 1 / 30 - (time.monotonic() - started)))

    async def run(self, device=None):
        import winrt.runtime
        winrt.runtime.init_apartment(winrt.runtime.ApartmentType.MULTI_THREADED)
        try:
            app = web.Application(middlewares=[self.guard], client_max_size=2048)
            app.add_routes([web.get("/", self.route_control), web.get("/control", self.route_control),
                            web.get("/health", self.route_health), web.get("/devices", self.route_devices),
                            web.get("/now-playing", self.route_metadata), web.get("/sessions", self.route_sessions),
                            web.get("/audio", self.route_ws), web.post("/api/start", self.route_start),
                            web.post("/api/stop", self.route_stop), web.post("/api/quit", self.route_quit),
                            web.options("/{tail:.*}", self.route_health)])
            self.runner = web.AppRunner(app, access_log=None, shutdown_timeout=2)
            await self.runner.setup()
            self.capture = await asyncio.to_thread(OutputCapture)
            try:
                await web.TCPSite(self.runner, "127.0.0.1", self.port).start()
                if self.port == 0:
                    self.port = self.runner.addresses[0][1]
            except OSError:
                self.error = (f"Port {self.port} is already in use. Close the original SMTC Bridge "
                              "(including its tray icon), then open Better SMTC Bridge again.")
                raise RuntimeError(self.error) from None
            if device is not None:
                await self.set_device(device)
            else:
                await self.resume_saved_output()
            self.pump = asyncio.create_task(self.broadcast())
            self.resume_task = asyncio.create_task(self.watch_saved_output())
            self.started = True
            await self.stopped.wait()
            self.closing = True
            if self.on_stop:
                self.on_stop()
        finally:
            self.closing = True
            self.started = False
            if self.resume_task:
                self.resume_task.cancel()
                await asyncio.gather(self.resume_task, return_exceptions=True)
            if self.pump:
                self.pump.cancel()
                await asyncio.gather(self.pump, return_exceptions=True)
            for client in tuple(self.clients):
                await client.close()
            if self.capture:
                await asyncio.to_thread(self.capture.close)
            if self.runner:
                await self.runner.cleanup()
            winrt.runtime.uninit_apartment()
