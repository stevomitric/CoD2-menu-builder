"""CoD2 bitmap font renderer — renders text using font atlas glyphs.

Loads font files + atlas PNGs and renders text strings to tk.PhotoImage.
Caches rendered text images for performance.
"""

from __future__ import annotations

import struct
import tkinter as tk
from pathlib import Path


# Font directories
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_FONTS_DIR = _PROJECT_ROOT / "fonts" / "default"
_CUSTOM_FONTS_DIR = _PROJECT_ROOT / "fonts" / "custom"

# Maps textfont constant to font file name
_FONT_MAP = {
    "UI_FONT_DEFAULT": "smallFont",
    "UI_FONT_NORMAL": "normalFont",
    "UI_FONT_BIG": "bigFont",
}

# Default font if none specified
_DEFAULT_FONT = "normalFont"


class FontData:
    """Parsed CoD2 font with glyph metrics and atlas."""

    def __init__(self, name: str, pixel_height: int, glyphs: dict[int, dict], atlas_path: Path | None):
        self.name = name
        self.pixel_height = pixel_height
        self.glyphs = glyphs  # letter code -> glyph dict
        self.atlas_path = atlas_path
        self.atlas_photo: tk.PhotoImage | None = None
        self.atlas_w = 0
        self.atlas_h = 0
        self._loaded = False

    def ensure_atlas(self, master: tk.Misc):
        """Load the atlas PhotoImage (lazy, once per font)."""
        if self._loaded:
            return
        self._loaded = True
        if self.atlas_path and self.atlas_path.exists():
            try:
                self.atlas_photo = tk.PhotoImage(file=str(self.atlas_path), master=master)
                self.atlas_w = self.atlas_photo.width()
                self.atlas_h = self.atlas_photo.height()
            except Exception:
                pass

    def text_width(self, text: str, scale: float = 1.0) -> float:
        """Calculate the pixel width of a text string."""
        w = 0.0
        for ch in text:
            g = self.glyphs.get(ord(ch))
            if g:
                w += g["dx"] * scale
            else:
                w += self.pixel_height * 0.5 * scale  # fallback for unknown chars
        return w


class FontCache:
    """Loads and caches CoD2 fonts and rendered text images."""

    def __init__(self):
        self._fonts: dict[str, FontData] = {}
        self._text_cache: dict[tuple, tk.PhotoImage] = {}
        self._master: tk.Misc | None = None

    def init(self, master: tk.Misc):
        """Initialize with a tk root (needed for PhotoImage creation)."""
        self._master = master

    def get_font(self, textfont: str | None) -> FontData | None:
        """Get a FontData by textfont constant name or font file name."""
        # Resolve constant to file name
        font_name = _FONT_MAP.get(textfont, textfont) if textfont else _DEFAULT_FONT
        if not font_name:
            font_name = _DEFAULT_FONT

        if font_name in self._fonts:
            return self._fonts[font_name]

        # Try to load
        font_data = self._load_font(font_name)
        if font_data:
            self._fonts[font_name] = font_data
        return font_data

    def render_text(
        self,
        text: str,
        textfont: str | None = None,
        scale: float = 1.0,
        color_hex: str = "#ffffff",
    ) -> tk.PhotoImage | None:
        """Render a text string to a PhotoImage using the specified font.

        Returns a cached image if available.
        """
        if not text or self._master is None:
            return None

        font_name = _FONT_MAP.get(textfont, textfont) if textfont else _DEFAULT_FONT
        cache_key = (text, font_name, round(scale, 3), color_hex)
        if cache_key in self._text_cache:
            return self._text_cache[cache_key]

        font = self.get_font(textfont)
        if font is None:
            return None

        font.ensure_atlas(self._master)
        if font.atlas_photo is None:
            return None

        img = self._render(font, text, scale, color_hex)
        if img:
            self._text_cache[cache_key] = img
        return img

    def clear_cache(self):
        """Clear the rendered text cache (call when fonts change)."""
        self._text_cache.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_font(self, font_name: str) -> FontData | None:
        """Load a font file from default/ or custom/ directories."""
        for font_dir in [_DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]:
            font_path = font_dir / font_name
            if not font_path.exists():
                continue

            try:
                data = font_path.read_bytes()
                if len(data) < 16:
                    continue

                name_offset, pixel_height, num_glyphs, material_offset = struct.unpack_from("<4i", data, 0)

                glyphs = {}
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
                    glyphs[letter] = {
                        "x0": x0, "y0": y0, "dx": dx,
                        "pixelWidth": pw, "pixelHeight": ph,
                        "s0": s0, "t0": t0, "s1": s1, "t1": t1,
                    }

                # Find atlas PNG
                material_name = ""
                if material_offset < len(data):
                    end = data.index(b"\x00", material_offset)
                    material_name = data[material_offset:end].decode("ascii", errors="replace")

                tex_name = material_name.rsplit("/", 1)[-1] if "/" in material_name else material_name
                atlas_path = None
                for search_dir in [font_dir, _DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]:
                    candidate = search_dir / f"{tex_name}.png"
                    if candidate.exists():
                        atlas_path = candidate
                        break

                return FontData(font_name, pixel_height, glyphs, atlas_path)

            except Exception:
                continue

        return None

    def _render(self, font: FontData, text: str, scale: float, color_hex: str) -> tk.PhotoImage | None:
        """Render text to a PhotoImage by compositing glyph crops from the atlas."""
        if font.atlas_photo is None or not self._master:
            return None

        # Calculate total dimensions
        total_w = 0
        max_ascent = 0
        max_descent = 0
        glyph_layout = []  # (glyph, x_pos)

        for ch in text:
            g = font.glyphs.get(ord(ch))
            if g is None:
                total_w += int(font.pixel_height * 0.5)
                continue
            glyph_layout.append((g, total_w))
            top = -g["y0"]
            bottom = -g["y0"] - g["pixelHeight"]
            max_ascent = max(max_ascent, top)
            max_descent = min(max_descent, bottom)
            total_w += g["dx"]

        if total_w <= 0:
            return None

        img_h = (max_ascent - max_descent)
        baseline_y = max_ascent  # baseline is max_ascent pixels from the top

        if img_h <= 0 or total_w <= 0:
            return None

        # Scale dimensions
        sw = max(1, int(total_w * scale))
        sh = max(1, int(img_h * scale))

        # Create output image
        img = tk.PhotoImage(width=sw, height=sh, master=self._master)
        # Make it fully transparent initially
        img.put("black", to=(0, 0, sw, sh))
        img.transparency_set(0, 0, True)  # won't work for all — use blank

        # Composite each glyph
        for g, x_pos in glyph_layout:
            pw = g["pixelWidth"]
            ph = g["pixelHeight"]
            if pw <= 0 or ph <= 0:
                continue

            # UV -> pixel rect in atlas
            gx0 = int(g["s0"] * font.atlas_w)
            gy0 = int(g["t0"] * font.atlas_h)
            gx1 = int(g["s1"] * font.atlas_w)
            gy1 = int(g["t1"] * font.atlas_h)
            gw = gx1 - gx0
            gh = gy1 - gy0
            if gw <= 0 or gh <= 0:
                continue

            # Crop glyph from atlas
            try:
                crop = tk.PhotoImage(width=gw, height=gh, master=self._master)
                crop.tk.call(crop, "copy", font.atlas_photo, "-from", gx0, gy0, gx1, gy1)

                # Scale the crop
                if scale != 1.0:
                    zoom = max(1, int(round(scale)))
                    if zoom > 1:
                        crop = crop.zoom(zoom, zoom)

                # Position: x = x_pos + x0, y = baseline_y + y0 (y0 is negative)
                dst_x = int((x_pos + g["x0"]) * scale)
                dst_y = int((baseline_y + g["y0"]) * scale)

                if dst_x >= 0 and dst_y >= 0 and dst_x < sw and dst_y < sh:
                    img.tk.call(img, "copy", crop, "-to", dst_x, dst_y)
            except Exception:
                continue

        return img


# Global font cache instance
font_cache = FontCache()
