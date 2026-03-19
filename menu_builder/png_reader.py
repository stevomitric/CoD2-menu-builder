"""Minimal PNG reader — extracts RGBA pixel data without external dependencies."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


class PNGImage:
    """A decoded PNG image with pixel access."""

    def __init__(self, width: int, height: int, pixels: bytes, channels: int):
        self.width = width
        self.height = height
        self.pixels = pixels
        self.channels = channels  # 1=grey, 2=grey+alpha, 3=RGB, 4=RGBA

    def get_pixel(self, x: int, y: int) -> tuple[int, ...]:
        offset = (y * self.width + x) * self.channels
        return tuple(self.pixels[offset: offset + self.channels])

    def get_brightness(self, x: int, y: int) -> int:
        """Get pixel brightness (0-255). Uses R channel for RGB/RGBA, grey for others."""
        p = self.get_pixel(x, y)
        return p[0]


def load_png(path: str | Path) -> PNGImage:
    """Load a PNG file into a PNGImage."""
    data = Path(path).read_bytes()

    # Verify PNG signature
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a valid PNG file")

    # Parse chunks
    pos = 8
    width = height = 0
    bit_depth = color_type = 0
    compressed = bytearray()

    while pos < len(data):
        length = struct.unpack(">I", data[pos: pos + 4])[0]
        chunk_type = data[pos + 4: pos + 8]
        chunk_data = data[pos + 8: pos + 8 + length]
        pos += 12 + length  # 4 len + 4 type + data + 4 crc

        if chunk_type == b"IHDR":
            width = struct.unpack(">I", chunk_data[0:4])[0]
            height = struct.unpack(">I", chunk_data[4:8])[0]
            bit_depth = chunk_data[8]
            color_type = chunk_data[9]
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8:
        raise ValueError(f"Only 8-bit PNG supported, got {bit_depth}-bit")

    # Channels from color_type
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"Unsupported color type: {color_type}")

    # Decompress
    raw = zlib.decompress(bytes(compressed))

    # Unfilter scanlines
    stride = width * channels
    pixels = bytearray(height * stride)

    src = 0
    for y in range(height):
        filter_type = raw[src]
        src += 1
        row_start = y * stride
        prev_row_start = (y - 1) * stride if y > 0 else -1

        for x in range(stride):
            raw_byte = raw[src]
            src += 1

            a = pixels[row_start + x - channels] if x >= channels else 0
            b = pixels[prev_row_start + x] if prev_row_start >= 0 else 0
            c = pixels[prev_row_start + x - channels] if prev_row_start >= 0 and x >= channels else 0

            if filter_type == 0:  # None
                pixels[row_start + x] = raw_byte
            elif filter_type == 1:  # Sub
                pixels[row_start + x] = (raw_byte + a) & 0xFF
            elif filter_type == 2:  # Up
                pixels[row_start + x] = (raw_byte + b) & 0xFF
            elif filter_type == 3:  # Average
                pixels[row_start + x] = (raw_byte + (a + b) // 2) & 0xFF
            elif filter_type == 4:  # Paeth
                pixels[row_start + x] = (raw_byte + _paeth(a, b, c)) & 0xFF

    return PNGImage(width, height, bytes(pixels), channels)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    return c
