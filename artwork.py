"""Additional bounded, memory-only artwork cache for the original SMTC reader."""
import base64
from collections import OrderedDict
import time

from winrt.windows.storage.streams import DataReader


class ArtworkCache:
    def __init__(self):
        self.artwork = OrderedDict()

    async def get(self, app_id, media):
        key = (app_id, media.title, media.artist, media.album_title)
        cached = self.artwork.get(key)
        if cached and time.monotonic() - cached[0] < 15:
            self.artwork.move_to_end(key)
            return cached[1]
        thumbnail = await self.thumbnail(media.thumbnail)
        if thumbnail:
            self.artwork[key] = (time.monotonic(), thumbnail)
            self.artwork.move_to_end(key)
            while len(self.artwork) > 32:
                self.artwork.popitem(last=False)
        else:
            self.artwork.pop(key, None)
        return thumbnail

    async def thumbnail(self, reference):
        if reference is None:
            return None
        stream = reader = None
        try:
            stream = await reference.open_read_async()
            if not 0 < stream.size <= 5 * 1024 * 1024:
                return None
            reader = DataReader(stream.get_input_stream_at(0))
            count = await reader.load_async(stream.size)
            contents = bytearray(count)
            reader.read_bytes(contents)
            mime = stream.content_type or "image/jpeg"
            if mime not in {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif"}:
                mime = "image/jpeg"
            return "data:" + mime + ";base64," + base64.b64encode(contents).decode("ascii")
        except Exception:
            return None
        finally:
            if reader is not None:
                reader.close()
            if stream is not None:
                stream.close()
