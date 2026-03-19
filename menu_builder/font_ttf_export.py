"""Export CoD2 font files to TTF format using fontTools.

Converts bitmap glyphs to vector outlines by tracing pixel edges.
The result is a pixel font that looks correct at the original size.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.fontBuilder import FontBuilder

from menu_builder.font_export import load_cod2_font
from menu_builder.png_reader import load_png, PNGImage

# Threshold for treating a pixel as "on" (0-255 alpha)
_ALPHA_THRESHOLD = 80


def _extract_glyph_bitmap(
    atlas: PNGImage, glyph: dict, tex_w: int, tex_h: int,
) -> list[list[bool]]:
    """Extract a glyph's bitmap as a 2D grid of on/off pixels."""
    x0 = int(glyph["s0"] * tex_w)
    y0 = int(glyph["t0"] * tex_h)
    x1 = int(glyph["s1"] * tex_w)
    y1 = int(glyph["t1"] * tex_h)
    w, h = x1 - x0, y1 - y0

    if w <= 0 or h <= 0:
        return []

    grid = []
    for py in range(y0, y1):
        row = []
        for px in range(x0, x1):
            alpha = atlas.get_pixel(px, py)[3] if atlas.channels == 4 else atlas.get_brightness(px, py)
            row.append(alpha >= _ALPHA_THRESHOLD)
        grid.append(row)
    return grid


def _draw_bitmap_glyph(pen, grid: list[list[bool]], x_offset: int, y_offset: int, scale: int):
    """Draw a bitmap glyph using the pen interface. Each on-pixel = a square."""
    if not grid:
        return

    h = len(grid)
    w = len(grid[0]) if h > 0 else 0

    for y in range(h):
        for x in range(w):
            if not grid[y][x]:
                continue
            # Font coords: y increases upward, bitmap y increases downward
            x0 = x_offset + x * scale
            y0 = y_offset + (h - y - 1) * scale
            x1 = x0 + scale
            y1 = y0 + scale
            pen.moveTo((x0, y0))
            pen.lineTo((x1, y0))
            pen.lineTo((x1, y1))
            pen.lineTo((x0, y1))
            pen.closePath()


def export_ttf(
    font_path: Path,
    atlas_png_path: Path,
    output_path: Path,
    tex_w: int = 512,
    tex_h: int = 1024,
) -> Path:
    """Export a CoD2 font to TTF format.

    Args:
        font_path: Path to CoD2 binary font file.
        atlas_png_path: Path to the atlas PNG (IWI-converted).
        output_path: Path for the output .ttf file.
        tex_w: Atlas texture width for UV mapping.
        tex_h: Atlas texture height for UV mapping.

    Returns:
        Path to the written TTF file.
    """
    font_data = load_cod2_font(font_path)
    atlas = load_png(atlas_png_path)

    pixel_height = font_data["pixelHeight"]
    raw_name = font_data["fontName"].rsplit("/", 1)[-1] if "/" in font_data["fontName"] else font_data["fontName"]
    family_name = raw_name or "CoD2Font"

    # Scale: font units per pixel. UPM = pixel_height * scale
    units_per_pixel = 64
    upm = pixel_height * units_per_pixel

    # Build glyph names and char map
    glyph_order = [".notdef"]
    char_map = {}
    glyph_metrics = {".notdef": (upm // 2, 0)}
    glyph_data_list = []  # (glyph_name, glyph_dict, grid)

    for g in font_data["glyphs"]:
        letter = g["letter"]
        if letter < 1:
            continue
        glyph_name = f"uni{letter:04X}"
        glyph_order.append(glyph_name)
        char_map[letter] = glyph_name

        advance = g["dx"] * units_per_pixel
        lsb = g["x0"] * units_per_pixel
        glyph_metrics[glyph_name] = (advance, lsb)

        grid = _extract_glyph_bitmap(atlas, g, tex_w, tex_h)
        glyph_data_list.append((glyph_name, g, grid))

    # Create font builder
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(char_map)

    # Draw all glyphs using TTGlyphPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen_glyphs = {}

    # .notdef — empty glyph
    pen = TTGlyphPen(None)
    pen_glyphs[".notdef"] = pen.glyph()

    for glyph_name, g, grid in glyph_data_list:
        pen = TTGlyphPen(None)

        if grid and g["pixelWidth"] > 0:
            x_offset = g["x0"] * units_per_pixel
            y_offset = g["y0"] * units_per_pixel
            glyph_h = len(grid)
            _draw_bitmap_glyph(pen, grid, x_offset, y_offset + glyph_h * units_per_pixel, units_per_pixel)

        pen_glyphs[glyph_name] = pen.glyph()

    fb.setupGlyf(pen_glyphs)

    # Ascent/descent
    ascent = int(pixel_height * 0.85 * units_per_pixel)
    descent = int(-pixel_height * 0.15 * units_per_pixel)

    fb.setupHorizontalMetrics(glyph_metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({"familyName": family_name, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=0)
    fb.setupPost()
    fb.setupHead(unitsPerEm=upm)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fb.font.save(str(output_path))
    return output_path
