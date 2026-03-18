"""Minimal TGA image reader — supports uncompressed and RLE true-color 32-bit."""

from __future__ import annotations

import struct
from pathlib import Path


class TGAImage:
    """A decoded TGA image with RGBA pixel access."""

    def __init__(self, width: int, height: int, pixels: bytearray):
        self.width = width
        self.height = height
        self.pixels = pixels  # RGBA, row-major, bottom-to-top flipped to top-to-bottom

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        """Get (R, G, B, A) at pixel (x, y)."""
        offset = (y * self.width + x) * 4
        return (
            self.pixels[offset],
            self.pixels[offset + 1],
            self.pixels[offset + 2],
            self.pixels[offset + 3],
        )

    def get_alpha(self, x: int, y: int) -> int:
        """Get alpha value at pixel (x, y)."""
        offset = (y * self.width + x) * 4 + 3
        return self.pixels[offset]


def load_tga(path: str | Path) -> TGAImage:
    """Load a 32-bit TGA file (uncompressed or RLE)."""
    data = Path(path).read_bytes()

    # TGA header (18 bytes)
    id_length = data[0]
    colormap_type = data[1]
    image_type = data[2]
    width = struct.unpack_from("<H", data, 12)[0]
    height = struct.unpack_from("<H", data, 14)[0]
    bpp = data[16]
    descriptor = data[17]

    if bpp != 32:
        raise ValueError(f"Only 32-bit TGA supported, got {bpp}-bit")
    if colormap_type != 0:
        raise ValueError("Color-mapped TGA not supported")

    pixel_start = 18 + id_length
    pixel_count = width * height

    if image_type == 2:
        # Uncompressed true-color
        raw = data[pixel_start: pixel_start + pixel_count * 4]
        pixels = _bgra_to_rgba(raw)
    elif image_type == 10:
        # RLE compressed true-color
        pixels = _decode_rle(data, pixel_start, pixel_count)
    else:
        raise ValueError(f"Unsupported TGA image type: {image_type}")

    # TGA stores rows bottom-to-top by default; flip if needed
    origin_top = (descriptor >> 5) & 1
    if not origin_top:
        pixels = _flip_vertical(pixels, width, height)

    return TGAImage(width, height, pixels)


def _bgra_to_rgba(data: bytes) -> bytearray:
    """Convert BGRA byte sequence to RGBA."""
    out = bytearray(len(data))
    for i in range(0, len(data), 4):
        out[i] = data[i + 2]      # R
        out[i + 1] = data[i + 1]  # G
        out[i + 2] = data[i]      # B
        out[i + 3] = data[i + 3]  # A
    return out


def _decode_rle(data: bytes, offset: int, pixel_count: int) -> bytearray:
    """Decode RLE-compressed 32-bit TGA pixels to RGBA."""
    out = bytearray(pixel_count * 4)
    pos = offset
    out_idx = 0
    remaining = pixel_count

    while remaining > 0 and pos < len(data):
        header = data[pos]
        pos += 1
        count = (header & 0x7F) + 1

        if header & 0x80:
            # RLE packet — one pixel repeated count times
            b, g, r, a = data[pos], data[pos + 1], data[pos + 2], data[pos + 3]
            pos += 4
            for _ in range(count):
                out[out_idx] = r
                out[out_idx + 1] = g
                out[out_idx + 2] = b
                out[out_idx + 3] = a
                out_idx += 4
        else:
            # Raw packet — count pixels
            for _ in range(count):
                out[out_idx] = data[pos + 2]      # R
                out[out_idx + 1] = data[pos + 1]  # G
                out[out_idx + 2] = data[pos]      # B
                out[out_idx + 3] = data[pos + 3]  # A
                pos += 4
                out_idx += 4

        remaining -= count

    return out


def _flip_vertical(pixels: bytearray, width: int, height: int) -> bytearray:
    """Flip image vertically (bottom-to-top -> top-to-bottom)."""
    row_size = width * 4
    out = bytearray(len(pixels))
    for y in range(height):
        src_offset = (height - 1 - y) * row_size
        dst_offset = y * row_size
        out[dst_offset: dst_offset + row_size] = pixels[src_offset: src_offset + row_size]
    return out
