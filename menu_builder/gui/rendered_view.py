"""Rendered view — game-like preview of the menu with bitmap fonts and images."""

from __future__ import annotations

import struct
import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from pathlib import Path

from menu_builder.models import ItemDef, MenuDef, Color

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_IMAGES_DIR = _PROJECT_ROOT / "images"
_DEFAULT_FONTS_DIR = _PROJECT_ROOT / "fonts" / "default"
_CUSTOM_FONTS_DIR = _PROJECT_ROOT / "fonts" / "custom"

CANVAS_W = 640
CANVAS_H = 480

# Maps textfont constant to font file name
_FONT_MAP = {
    "UI_FONT_DEFAULT": "smallFont",
    "UI_FONT_NORMAL": "normalFont",
    "UI_FONT_BIG": "bigFont",
    "UI_FONT_SMALL": "smallFont",
    "UI_FONT_BOLD": "boldFont",
    "UI_FONT_CONSOLE": "consoleFont",
    None: "normalFont",
}


def _color_to_hex(c: Color | None, fallback: str = "#ffffff") -> str:
    if c is None:
        return fallback
    r = max(0, min(255, int(c.r * 255)))
    g = max(0, min(255, int(c.g * 255)))
    b = max(0, min(255, int(c.b * 255)))
    return f"#{r:02x}{g:02x}{b:02x}"


class _FontAtlas:
    """Loaded font atlas for rendering glyphs."""

    def __init__(self, font_name: str, master: tk.Misc):
        self.glyphs: dict[int, dict] = {}
        self.pixel_height = 16
        self.atlas_photo: tk.PhotoImage | None = None
        self.atlas_w = 0
        self.atlas_h = 0
        self._master = master
        self._glyph_cache: dict[int, tk.PhotoImage] = {}

        font_path = self._find_font(font_name)
        if not font_path:
            return

        # Parse font binary
        data = font_path.read_bytes()
        if len(data) < 16:
            return
        _, pixel_height, num_glyphs, material_offset = struct.unpack_from("<4i", data, 0)
        self.pixel_height = pixel_height

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
            self.glyphs[letter] = {
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
        for d in [font_path.parent, _DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]:
            p = d / f"{tex_name}.png"
            if p.exists():
                try:
                    self.atlas_photo = tk.PhotoImage(file=str(p), master=master)
                    self.atlas_w = self.atlas_photo.width()
                    self.atlas_h = self.atlas_photo.height()
                except Exception:
                    pass
                break

    def _find_font(self, name: str) -> Path | None:
        for d in [_DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]:
            p = d / name
            if p.exists():
                return p
        return None

    def get_glyph_image(self, letter: int) -> tk.PhotoImage | None:
        """Crop a single glyph from the atlas."""
        if letter in self._glyph_cache:
            return self._glyph_cache[letter]
        if self.atlas_photo is None:
            return None
        g = self.glyphs.get(letter)
        if not g or g["pixelWidth"] <= 0:
            return None

        x0 = int(g["s0"] * self.atlas_w)
        y0 = int(g["t0"] * self.atlas_h)
        x1 = int(g["s1"] * self.atlas_w)
        y1 = int(g["t1"] * self.atlas_h)
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            return None

        try:
            crop = tk.PhotoImage(width=w, height=h, master=self._master)
            crop.tk.call(crop, "copy", self.atlas_photo, "-from", x0, y0, x1, y1)
            self._glyph_cache[letter] = crop
            return crop
        except Exception:
            return None


class RenderedView(Frame):
    """Game-like rendered preview of the menu."""

    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_configure)

        self.menu: MenuDef | None = None
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

        # Background image
        self._bg_photo: tk.PhotoImage | None = None
        self._bg_scaled: tk.PhotoImage | None = None

        # Font atlases (lazy loaded)
        self._font_atlases: dict[str, _FontAtlas] = {}

        # Image cache for shader backgrounds
        self._image_cache: dict[str, tk.PhotoImage] = {}

        # Keep refs to prevent GC
        self._render_images: list[tk.PhotoImage] = []

        # Load background
        bg_path = _DATA_DIR / "cod2dx9.png"
        if bg_path.exists():
            try:
                self._bg_photo = tk.PhotoImage(file=str(bg_path), master=self)
            except Exception:
                pass

    def load(self, menu: MenuDef | None):
        self.menu = menu
        self._redraw()

    def _get_font_atlas(self, textfont: str | None) -> _FontAtlas | None:
        font_name = _FONT_MAP.get(textfont, textfont) if textfont else _FONT_MAP[None]
        if not font_name:
            font_name = "normalFont"
        if font_name not in self._font_atlases:
            self._font_atlases[font_name] = _FontAtlas(font_name, self)
        atlas = self._font_atlases[font_name]
        return atlas if atlas.atlas_photo else None

    def _get_item_image(self, name: str) -> tk.PhotoImage | None:
        """Load an image from ./images/ for shader backgrounds."""
        if name in self._image_cache:
            return self._image_cache[name]
        for ext in (".png", ".jpg", ".jpeg"):
            p = _IMAGES_DIR / f"{name}{ext}"
            if p.exists():
                try:
                    img = tk.PhotoImage(file=str(p), master=self)
                    self._image_cache[name] = img
                    return img
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    def _calc_transform(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        sx = cw / CANVAS_W
        sy = ch / CANVAS_H
        self._scale = min(sx, sy)
        self._offset_x = (cw - CANVAS_W * self._scale) / 2
        self._offset_y = (ch - CANVAS_H * self._scale) / 2

    def _to_screen(self, x: float, y: float) -> tuple[float, float]:
        return x * self._scale + self._offset_x, y * self._scale + self._offset_y

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _on_configure(self, event):
        self._redraw()

    def _redraw(self):
        self.canvas.delete("all")
        self._render_images.clear()
        self._calc_transform()

        # Background
        self._draw_background()

        if self.menu is None:
            return

        # Draw items
        for item in self.menu.items:
            if not item.visible:
                continue
            self._draw_item(item)

    def _draw_background(self):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if self._bg_photo is None:
            self.canvas.create_rectangle(0, 0, cw, ch, fill="#1a1a1a", outline="")
            return

        bg_w = self._bg_photo.width()
        bg_h = self._bg_photo.height()

        # Scale to cover the entire canvas (may crop, never letterbox)
        scale_x = cw / bg_w
        scale_y = ch / bg_h
        cover_scale = max(scale_x, scale_y)

        try:
            if cover_scale >= 1:
                zoom = max(1, int(cover_scale + 0.99))
                scaled = self._bg_photo.zoom(zoom, zoom)
            else:
                sub = max(1, int(1 / cover_scale))
                scaled = self._bg_photo.subsample(sub, sub)

            self._bg_scaled = scaled
            self.canvas.create_image(cw // 2, ch // 2, image=scaled, anchor=tk.CENTER)
        except Exception:
            self.canvas.create_rectangle(0, 0, cw, ch, fill="#1a1a1a", outline="")

    def _draw_item(self, item: ItemDef):
        r = item.rect
        ox, oy = item.origin if item.origin else (0, 0)
        ix, iy = r.x + ox, r.y + oy
        x0, y0 = self._to_screen(ix, iy)
        x1, y1 = self._to_screen(ix + r.w, iy + r.h)

        # FILLED background
        if item.style == 1 and item.backcolor:
            fill = _color_to_hex(item.backcolor)
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

        # SHADER background image
        if item.style == 3 and item.background:
            self._draw_shader_image(item, x0, y0, x1, y1)

        # Border
        if item.border and item.border > 0:
            bc = _color_to_hex(item.bordercolor, "#ffffff")
            bw = max(1, int((item.bordersize or 1) * self._scale))
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="", outline=bc, width=bw)

        # Text
        if item.text:
            self._draw_text(item, x0, y0, x1, y1)

    def _draw_shader_image(self, item: ItemDef, x0: float, y0: float, x1: float, y1: float):
        """Draw a shader/image background, scaled to fit the item rect."""
        img = self._get_item_image(item.background)
        if img is None:
            return

        iw, ih = img.width(), img.height()
        tw = max(1, int(x1 - x0))
        th = max(1, int(y1 - y0))

        # Scale to fit
        try:
            display = img
            if iw > tw or ih > th:
                sub = max(1, max(iw // tw, ih // th))
                display = img.subsample(sub, sub)
            elif tw > iw * 2 or th > ih * 2:
                zoom = min(tw // max(1, iw), th // max(1, ih))
                if zoom > 1:
                    display = img.zoom(zoom, zoom)

            self._render_images.append(display)
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            self.canvas.create_image(cx, cy, image=display, anchor=tk.CENTER)
        except Exception:
            pass

    def _draw_text(self, item: ItemDef, x0: float, y0: float, x1: float, y1: float):
        """Render text using bitmap font glyphs, with tkinter fallback."""
        text = item.text
        if text.startswith("@"):
            text = text[1:]
        if not text:
            return

        tc = _color_to_hex(item.forecolor)

        atlas = self._get_font_atlas(item.textfont)

        # Try bitmap font rendering
        if atlas is not None:
            rendered = self._draw_text_bitmap(text, item, atlas, x0, y0, x1, y1)
            if rendered:
                return

        # Fallback: tkinter text (always works)
        # CoD2 text positioning: rect top-left is anchor, text draws above
        ax = x0 + (item.textalignx or 0) * self._scale
        ay = y0 + (item.textaligny or 0) * self._scale

        align = item.textalign
        if align == 1:  # CENTER
            tx = ax
            anchor = tk.S
        elif align == 2:  # RIGHT
            tx = ax
            anchor = tk.SE
        else:  # LEFT (default)
            tx = ax
            anchor = tk.SW

        font_size = max(8, int(10 * self._scale * ((item.textscale or 0.25) / 0.25)))
        self.canvas.create_text(
            tx, ay, text=text, fill=tc,
            font=("TkDefaultFont", font_size),
            anchor=anchor,
        )

    def _draw_text_bitmap(
        self, text: str, item: ItemDef, atlas: _FontAtlas,
        x0: float, y0: float, x1: float, y1: float,
    ) -> bool:
        """Try to render text with bitmap glyphs. Returns True if successful."""
        base_scale = (item.textscale or 0.25) / 0.25
        glyph_scale = self._scale * base_scale
        zoom = max(1, int(round(glyph_scale)))

        # Calculate total text width for alignment
        total_w = 0.0
        for ch in text:
            g = atlas.glyphs.get(ord(ch))
            if g:
                total_w += g["dx"] * glyph_scale

        # CoD2 text positioning: anchor = rect top-left + textalign offsets
        # Text draws ABOVE the anchor Y, glyph y0 is negative (above baseline)
        ax = x0 + (item.textalignx or 0) * self._scale
        ay = y0 + (item.textaligny or 0) * self._scale

        align = item.textalign
        if align == 1:  # CENTER — anchor is center of text
            pen_x = ax - total_w / 2
        elif align == 2:  # RIGHT — text ends at anchor
            pen_x = ax - total_w
        else:  # LEFT (default) — pen starts at anchor
            pen_x = ax

        # Baseline Y — glyphs use y0 (negative = above baseline)
        # ay is the baseline, glyphs draw above it
        pen_y = ay

        any_rendered = False
        for ch in text:
            code = ord(ch)
            g = atlas.glyphs.get(code)
            if g is None:
                pen_x += atlas.pixel_height * 0.4 * glyph_scale
                continue

            if g["pixelWidth"] > 0:
                glyph_img = atlas.get_glyph_image(code)
                if glyph_img:
                    try:
                        scaled = glyph_img.zoom(zoom, zoom) if zoom > 1 else glyph_img
                        self._render_images.append(scaled)
                        gx = pen_x + g["x0"] * glyph_scale
                        gy = pen_y + g["y0"] * glyph_scale
                        self.canvas.create_image(gx, gy, image=scaled, anchor=tk.NW)
                        any_rendered = True
                    except Exception:
                        pass

            pen_x += g["dx"] * glyph_scale

        return any_rendered
