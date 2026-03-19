"""Import TTF/OTF fonts and convert to CoD2 binary font format.

Requires: pip install Pillow
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

from PIL import Image, ImageFont, ImageDraw


# CoD2 font covers ASCII 32 (space) through 255
_CHAR_RANGE = range(32, 256)

# Atlas dimensions (matching stock CoD2 font atlases)
_ATLAS_W = 512
_ATLAS_H = 1024


def import_ttf(
    ttf_path: Path,
    pixel_height: int,
    output_font_path: Path,
    output_png_path: Path,
    font_name: str | None = None,
    material_name: str | None = None,
) -> tuple[Path, Path]:
    """Convert a TTF/OTF font to CoD2 binary font format + atlas PNG.

    Args:
        ttf_path: Path to the input TTF or OTF file.
        pixel_height: Target pixel height for the font.
        output_font_path: Path for the output CoD2 binary font file.
        output_png_path: Path for the output atlas PNG.
        font_name: Font name string (default: "fonts/<stem>").
        material_name: Material name string (default: "fonts/<stem>_atlas").

    Returns:
        Tuple of (font_path, png_path) for the written files.
    """
    stem = ttf_path.stem
    if font_name is None:
        font_name = f"fonts/{stem}"
    if material_name is None:
        material_name = f"fonts/{stem}_atlas"

    # Load the TTF/OTF
    pil_font = ImageFont.truetype(str(ttf_path), pixel_height)

    # Render each glyph and collect metrics
    glyphs = []
    glyph_images = []

    for code in _CHAR_RANGE:
        ch = chr(code)
        glyph_data = _render_glyph(pil_font, ch, code, pixel_height)
        glyphs.append(glyph_data)
        glyph_images.append(glyph_data.pop("image"))

    # Pack glyphs into atlas
    atlas = _pack_atlas(glyphs, glyph_images)

    # Calculate UV coordinates
    for g in glyphs:
        if g["pixelWidth"] > 0 and g["pixelHeight"] > 0:
            g["s0"] = g["atlas_x"] / _ATLAS_W
            g["t0"] = g["atlas_y"] / _ATLAS_H
            g["s1"] = (g["atlas_x"] + g["pixelWidth"]) / _ATLAS_W
            g["t1"] = (g["atlas_y"] + g["pixelHeight"]) / _ATLAS_H
        else:
            # Space or empty glyph
            g["s0"] = g["t0"] = g["s1"] = g["t1"] = 0.0

    # Write binary font file
    _write_cod2_font(glyphs, pixel_height, font_name, material_name, output_font_path)

    # Save atlas PNG (RGBA: white RGB, alpha = glyph shape)
    atlas.save(str(output_png_path))

    return output_font_path, output_png_path


def _render_glyph(pil_font: ImageFont.FreeTypeFont, ch: str, code: int, pixel_height: int) -> dict:
    """Render a single glyph and return its metrics + image."""
    # Get glyph metrics
    bbox = pil_font.getbbox(ch)
    if bbox is None or (bbox[2] - bbox[0] <= 0 and code != 32):
        # Empty glyph
        return {
            "letter": code, "x0": 0, "y0": 0, "dx": 0,
            "pixelWidth": 0, "pixelHeight": 0,
            "image": None, "atlas_x": 0, "atlas_y": 0,
        }

    # bbox = (left, top, right, bottom) relative to origin
    left, top, right, bottom = bbox
    w = right - left
    h = bottom - top

    # Render to image
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)
    draw.text((-left, -top), ch, font=pil_font, fill=255)

    # Advance width
    advance = pil_font.getlength(ch)

    # x0 = left bearing (offset from pen to glyph start)
    x0 = left
    # y0 = distance from pen position to top of glyph (negative = above)
    y0 = top

    return {
        "letter": code,
        "x0": max(-128, min(127, int(x0))),
        "y0": max(-128, min(127, int(y0))),
        "dx": max(-128, min(127, int(round(advance)))),
        "pixelWidth": w,
        "pixelHeight": h,
        "image": img,
        "atlas_x": 0,
        "atlas_y": 0,
    }


def _pack_atlas(glyphs: list[dict], images: list[Image.Image | None]) -> Image.Image:
    """Pack glyph images into a 512x1024 atlas.

    Uses a simple row-based bin packer.
    """
    atlas = Image.new("RGBA", (_ATLAS_W, _ATLAS_H), (255, 255, 255, 0))

    # Sort glyphs by height (tallest first) for better packing
    indexed = [(i, g, images[i]) for i, g in enumerate(glyphs)]
    indexed.sort(key=lambda x: -(x[1]["pixelHeight"]))

    cursor_x = 1  # 1px padding from edge
    cursor_y = 1
    row_height = 0
    padding = 1  # 1px between glyphs

    for i, g, img in indexed:
        w = g["pixelWidth"]
        h = g["pixelHeight"]

        if w == 0 or h == 0 or img is None:
            continue

        # Check if glyph fits in current row
        if cursor_x + w + padding > _ATLAS_W:
            # Move to next row
            cursor_x = 1
            cursor_y += row_height + padding
            row_height = 0

        if cursor_y + h > _ATLAS_H:
            # Atlas full — shouldn't happen for 224 chars at reasonable sizes
            break

        # Convert greyscale glyph to RGBA (white + alpha)
        rgba = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        for y in range(h):
            for x in range(w):
                a = img.getpixel((x, y))
                if a > 0:
                    rgba.putpixel((x, y), (255, 255, 255, a))

        atlas.paste(rgba, (cursor_x, cursor_y))

        g["atlas_x"] = cursor_x
        g["atlas_y"] = cursor_y

        cursor_x += w + padding
        row_height = max(row_height, h)

    return atlas


def _write_cod2_font(
    glyphs: list[dict],
    pixel_height: int,
    font_name: str,
    material_name: str,
    output_path: Path,
):
    """Write a CoD2 binary font file."""
    num_glyphs = len(glyphs)

    # Header: font_name_offset, pixel_height, num_glyphs, material_offset
    glyph_data_size = 16 + num_glyphs * 24
    font_name_bytes = font_name.encode("ascii") + b"\x00"
    material_name_bytes = material_name.encode("ascii") + b"\x00"

    font_name_offset = glyph_data_size
    material_offset = font_name_offset + len(font_name_bytes)

    data = bytearray()

    # Header
    data.extend(struct.pack("<4i", font_name_offset, pixel_height, num_glyphs, material_offset))

    # Glyph entries
    for g in glyphs:
        data.extend(struct.pack("<H", g["letter"]))
        data.extend(struct.pack("<b", g["x0"]))
        data.extend(struct.pack("<b", g["y0"]))
        data.extend(struct.pack("<b", g["dx"]))
        data.extend(struct.pack("<B", min(255, g["pixelWidth"])))
        data.extend(struct.pack("<B", min(255, g["pixelHeight"])))
        data.extend(b"\x00")  # padding
        data.extend(struct.pack("<4f", g.get("s0", 0), g.get("t0", 0), g.get("s1", 0), g.get("t1", 0)))

    # Footer strings
    data.extend(font_name_bytes)
    data.extend(material_name_bytes)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(data))
