"""Export CoD2 font files to BMFont (.fnt) format."""

from __future__ import annotations

import shutil
import struct
from pathlib import Path


def load_cod2_font(path: Path) -> dict:
    """Load a CoD2 binary font file into a dict."""
    data = path.read_bytes()
    name_offset, pixel_height, num_glyphs, material_offset = struct.unpack_from("<4i", data, 0)

    glyphs = []
    for i in range(num_glyphs):
        offset = 16 + i * 24
        if offset + 24 > len(data):
            break
        letter = struct.unpack_from("<H", data, offset)[0]
        x0 = struct.unpack_from("<b", data, offset + 2)[0]
        y0 = struct.unpack_from("<b", data, offset + 3)[0]
        dx = struct.unpack_from("<b", data, offset + 4)[0]
        pw = struct.unpack_from("<B", data, offset + 5)[0]
        ph = struct.unpack_from("<B", data, offset + 6)[0]
        s0, t0, s1, t1 = struct.unpack_from("<4f", data, offset + 8)
        glyphs.append({
            "letter": letter, "x0": x0, "y0": y0, "dx": dx,
            "pixelWidth": pw, "pixelHeight": ph,
            "s0": s0, "t0": t0, "s1": s1, "t1": t1,
        })

    font_name = material_name = ""
    if name_offset < len(data):
        end = data.index(b"\x00", name_offset)
        font_name = data[name_offset:end].decode("ascii", errors="replace")
    if material_offset < len(data):
        end = data.index(b"\x00", material_offset)
        material_name = data[material_offset:end].decode("ascii", errors="replace")

    return {
        "pixelHeight": pixel_height,
        "numGlyphs": num_glyphs,
        "fontName": font_name,
        "materialName": material_name,
        "glyphs": glyphs,
    }


def export_bmfont(
    font_data: dict,
    atlas_png_path: Path,
    output_dir: Path,
    output_name: str | None = None,
    tex_w: int = 512,
    tex_h: int = 1024,
) -> tuple[Path, Path]:
    """Export a CoD2 font to BMFont text format.

    Args:
        font_data: Parsed font dict (from load_cod2_font).
        atlas_png_path: Path to the atlas PNG image.
        output_dir: Directory to write output files.
        output_name: Base name for output files (default: font name).
        tex_w: Atlas texture width for UV mapping.
        tex_h: Atlas texture height for UV mapping.

    Returns:
        Tuple of (fnt_path, png_path) for the written files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine names
    raw_name = font_data["fontName"].rsplit("/", 1)[-1] if "/" in font_data["fontName"] else font_data["fontName"]
    base_name = output_name or raw_name or "font"
    png_filename = f"{base_name}_0.png"
    fnt_path = output_dir / f"{base_name}.fnt"
    png_path = output_dir / png_filename

    pixel_height = font_data["pixelHeight"]
    glyphs = font_data["glyphs"]

    # Find the baseline (most common -y0 among printable glyphs)
    y0_values = [-g["y0"] for g in glyphs if 33 <= g["letter"] < 127 and g["pixelHeight"] > 0]
    base = max(y0_values) if y0_values else pixel_height

    # Build .fnt content
    lines = []

    # Info line
    lines.append(
        f'info face="{base_name}" size={pixel_height} bold=0 italic=0'
        f" charset=\"\" unicode=1 stretchH=100 smooth=0 aa=1"
        f" padding=0,0,0,0 spacing=1,1 outline=0"
    )

    # Common line
    lines.append(
        f"common lineHeight={pixel_height} base={base}"
        f" scaleW={tex_w} scaleH={tex_h} pages=1 packed=0"
        f" alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4"
    )

    # Page
    lines.append(f'page id=0 file="{png_filename}"')

    # Count non-zero glyphs
    valid_glyphs = [g for g in glyphs if g["pixelWidth"] > 0 or g["letter"] == 32]
    lines.append(f"chars count={len(valid_glyphs)}")

    # Char entries
    for g in valid_glyphs:
        x = int(g["s0"] * tex_w)
        y = int(g["t0"] * tex_h)
        w = int(g["s1"] * tex_w) - x
        h = int(g["t1"] * tex_h) - y

        # For space character, use advance but zero dimensions
        if g["letter"] == 32:
            w = 0
            h = 0

        lines.append(
            f"char id={g['letter']:>4d}"
            f"   x={x:>4d}   y={y:>4d}"
            f"   width={w:>4d}   height={h:>4d}"
            f"   xoffset={g['x0']:>4d}   yoffset={g['y0']:>4d}"
            f"   xadvance={g['dx']:>4d}"
            f"   page=  0   chnl=15"
        )

    # Write .fnt
    fnt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Copy atlas PNG
    shutil.copy2(atlas_png_path, png_path)

    return fnt_path, png_path
