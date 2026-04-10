"""CoD2 font metrics — loads advance widths for text measurement.

No atlas/image loading, just the binary font metrics.
"""

from __future__ import annotations

import struct
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_FONTS_DIR = _PROJECT_ROOT / "fonts" / "default"
_CUSTOM_FONTS_DIR = _PROJECT_ROOT / "fonts" / "custom"

# Maps textfont constant to font file name
_FONT_MAP = {
    "UI_FONT_DEFAULT": "smallFont",
    "UI_FONT_NORMAL": "normalFont",
    "UI_FONT_BIG": "bigFont",
    "UI_FONT_SMALL": "smallFont",
    "UI_FONT_BOLD": "boldFont",
    "UI_FONT_CONSOLE": "consoleFont",
}

_DEFAULT_FONT = "normalFont"


class FontMetrics:
    """Parsed CoD2 font metrics (no images)."""

    def __init__(self, name: str, pixel_height: int, glyphs: dict[int, dict]):
        self.name = name
        self.pixel_height = pixel_height
        self.glyphs = glyphs  # letter code -> {"dx": int, "x0": int, "y0": int, "pixelWidth": int, "pixelHeight": int}

    # Reference height — normalFont's pixelHeight. All fonts normalize to this.
    _REF_HEIGHT = 16

    def text_width(self, text: str) -> float:
        """Width in normalized pixels (as if all fonts had the same height)."""
        norm = self._REF_HEIGHT / self.pixel_height if self.pixel_height > 0 else 1.0
        w = 0.0
        for ch in text:
            g = self.glyphs.get(ord(ch))
            if g:
                w += g["dx"] * norm
            else:
                w += self._REF_HEIGHT * 0.4
        return w

    def measure(self, text: str, textscale: float | None = None) -> float:
        """Width in game pixels at the given textscale."""
        scale = (textscale or 0.25) / 0.25  # normalize: 0.25 = 1x
        return self.text_width(text) * scale


class FontMetricsCache:
    """Loads and caches font metrics."""

    def __init__(self):
        self._cache: dict[str, FontMetrics | None] = {}

    def get(self, textfont: str | None = None) -> FontMetrics | None:
        """Get metrics by textfont constant or font file name."""
        font_name = _FONT_MAP.get(textfont, textfont) if textfont else _DEFAULT_FONT
        if not font_name:
            font_name = _DEFAULT_FONT

        if font_name in self._cache:
            return self._cache[font_name]

        metrics = self._load(font_name)
        self._cache[font_name] = metrics
        return metrics

    def _load(self, font_name: str) -> FontMetrics | None:
        for font_dir in [_DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]:
            path = font_dir / font_name
            if not path.exists():
                continue
            try:
                data = path.read_bytes()
                if len(data) < 16:
                    continue

                _, pixel_height, num_glyphs, _ = struct.unpack_from("<4i", data, 0)
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
                    glyphs[letter] = {"dx": dx, "x0": x0, "y0": y0, "pixelWidth": pw, "pixelHeight": ph}

                return FontMetrics(font_name, pixel_height, glyphs)
            except Exception:
                continue
        return None


# Global instance
metrics_cache = FontMetricsCache()
