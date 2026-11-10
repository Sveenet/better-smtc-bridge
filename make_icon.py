"""Generate this project's original waveform icon with the Python standard library."""
from pathlib import Path
import math
import struct
import zlib

size = 64
rows = []
for y in range(size):
    row = bytearray([0])
    for x in range(size):
        wave = 32 + math.sin((x - 10) * .36) * (17 * math.sin(math.pi * min(1, max(0, (x - 8) / 48))) ** 2)
        if 8 <= x <= 56 and abs(y - wave) < 2:
            row.extend((147, 232, 206, 255))
        else:
            row.extend((17, 22, 32, 255))
    rows.append(row)

def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
folder = Path(__file__).parent / "assets"
folder.mkdir(exist_ok=True)
(folder / "icon.png").write_bytes(png)
(folder / "icon.ico").write_bytes(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(png), 22) + png)
