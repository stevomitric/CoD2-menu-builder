"""Export CoD2 font files to TTF or OTF format using fontTools.

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

    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return []

    grid = []
    for py in range(y0, y1):
        row = []
        for px in range(x0, x1):
            alpha = atlas.get_pixel(px, py)[3] if atlas.channels == 4 else atlas.get_brightness(px, py)
            row.append(alpha >= _ALPHA_THRESHOLD)
        grid.append(row)
    return grid


def _draw_bitmap_glyph(pen, grid: list[list[bool]], x_bearing: int, y_top: int, scale: int):
    """Draw a bitmap glyph using the pen interface. Each on-pixel = a square.

    Args:
        pen: The glyph pen to draw into.
        grid: 2D bitmap (grid[0] = top row of glyph).
        x_bearing: X offset from pen position (font units).
        y_top: Y coordinate of the top of the glyph (font units, positive = above baseline).
        scale: Font units per pixel.
    """
    if not grid:
        return

    h = len(grid)
    w = len(grid[0]) if h > 0 else 0

    for y in range(h):
        for x in range(w):
            if not grid[y][x]:
                continue
            # grid[y] is row y from top. In font coords, top is at y_top,
            # each row goes downward (decreasing Y).
            fx0 = x_bearing + x * scale
            fy_top = y_top - y * scale
            fx1 = fx0 + scale
            fy_bottom = fy_top - scale
            # Clockwise winding for TrueType
            pen.moveTo((fx0, fy_bottom))
            pen.lineTo((fx0, fy_top))
            pen.lineTo((fx1, fy_top))
            pen.lineTo((fx1, fy_bottom))
            pen.closePath()


def _build_font(
    font_path: Path,
    atlas_png_path: Path,
    output_path: Path,
    is_ttf: bool,
    tex_w: int,
    tex_h: int,
) -> Path:
    """Shared builder for TTF and OTF export."""
    font_data = load_cod2_font(font_path)
    atlas = load_png(atlas_png_path)

    pixel_height = font_data["pixelHeight"]
    raw_name = font_data["fontName"].rsplit("/", 1)[-1] if "/" in font_data["fontName"] else font_data["fontName"]
    family_name = raw_name or "CoD2Font"

    units_per_pixel = 64
    upm = pixel_height * units_per_pixel

    # Build glyph names and char map
    glyph_order = [".notdef"]
    char_map = {}
    glyph_metrics = {".notdef": (upm // 2, 0)}
    glyph_data_list = []

    for g in font_data["glyphs"]:
        letter = g["letter"]
        if letter < 1:
            continue
        glyph_name = f"uni{letter:04X}"
        glyph_order.append(glyph_name)
        char_map[letter] = glyph_name
        glyph_metrics[glyph_name] = (g["dx"] * units_per_pixel, g["x0"] * units_per_pixel)
        grid = _extract_glyph_bitmap(atlas, g, tex_w, tex_h)
        glyph_data_list.append((glyph_name, g, grid))

    fb = FontBuilder(upm, isTTF=is_ttf)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(char_map)

    if is_ttf:
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        pen_glyphs = {}
        pen = TTGlyphPen(None)
        pen_glyphs[".notdef"] = pen.glyph()

        for glyph_name, g, grid in glyph_data_list:
            pen = TTGlyphPen(None)
            if grid and g["pixelWidth"] > 0:
                x_bearing = g["x0"] * units_per_pixel
                y_top = -g["y0"] * units_per_pixel  # y0 is negative, negate to get positive font-coord
                _draw_bitmap_glyph(pen, grid, x_bearing, y_top, units_per_pixel)
            pen_glyphs[glyph_name] = pen.glyph()

        fb.setupGlyf(pen_glyphs)
    else:
        from fontTools.pens.t2CharStringPen import T2CharStringPen
        charstrings = {}

        for glyph_name, g, grid in glyph_data_list:
            width = g["dx"] * units_per_pixel
            pen = T2CharStringPen(width, None)
            if grid and g["pixelWidth"] > 0:
                x_bearing = g["x0"] * units_per_pixel
                y_top = -g["y0"] * units_per_pixel
                _draw_bitmap_glyph(pen, grid, x_bearing, y_top, units_per_pixel)
            charstrings[glyph_name] = pen.getCharString()

        # .notdef
        notdef_pen = T2CharStringPen(upm // 2, None)
        charstrings[".notdef"] = notdef_pen.getCharString()

        fb.setupCFF(
            psName=family_name,
            fontInfo={},
            charStringsDict=charstrings,
            privateDict={},
        )

    # Compute ascent/descent from actual glyph y0 values
    max_ascent = 0
    max_descent = 0
    for g in font_data["glyphs"]:
        if g["pixelHeight"] == 0:
            continue
        top = -g["y0"]  # pixels above baseline
        bottom = -g["y0"] - g["pixelHeight"]  # negative = below baseline
        max_ascent = max(max_ascent, top)
        max_descent = min(max_descent, bottom)
    ascent = (max_ascent + 1) * units_per_pixel  # +1 for padding
    descent = (max_descent - 1) * units_per_pixel  # -1 for padding

    fb.setupHorizontalMetrics(glyph_metrics)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)

    # Name table — Windows requires IDs 0-6
    version_str = "Version 1.0"
    unique_id = f"{family_name}-Regular"
    fb.setupNameTable({
        "familyName": family_name,
        "styleName": "Regular",
        "uniqueFontIdentifier": unique_id,
        "fullName": f"{family_name} Regular",
        "version": version_str,
        "psName": family_name.replace(" ", ""),
    })

    fb.setupOS2(
        sTypoAscender=ascent,
        sTypoDescender=descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=abs(descent),  # must be positive
        fsType=0,  # installable embedding
        usWeightClass=400,
        usWidthClass=5,
    )
    fb.setupPost()
    fb.setupHead(unitsPerEm=upm, created=3600000000, modified=3600000000)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fb.font.save(str(output_path))
    return output_path


def export_ttf(
    font_path: Path,
    atlas_png_path: Path,
    output_path: Path,
    tex_w: int = 512,
    tex_h: int = 1024,
) -> Path:
    """Export a CoD2 font to TTF (TrueType) format."""
    return _build_font(font_path, atlas_png_path, output_path, is_ttf=True, tex_w=tex_w, tex_h=tex_h)


def export_otf(
    font_path: Path,
    atlas_png_path: Path,
    output_path: Path,
    tex_w: int = 512,
    tex_h: int = 1024,
) -> Path:
    """Export a CoD2 font to OTF (OpenType/CFF) format."""
    return _build_font(font_path, atlas_png_path, output_path, is_ttf=False, tex_w=tex_w, tex_h=tex_h)
