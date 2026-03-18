# Call of Duty 2 — Font File Format Reference

Research derived from binary analysis of stock CoD2 font files and community documentation.

---

## Overview

CoD2 uses bitmap fonts stored as a binary glyph definition file (no extension) paired with a TGA texture atlas. The format is shared across the IW engine lineage (CoD1 through CoD5+).

Each font file defines character metrics and UV coordinates into a shared texture atlas. The engine renders text by sampling glyph rectangles from the atlas and tinting them with `forecolor`.

---

## Binary Structure

### Header (16 bytes)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | int32 | `fontNameOffset` | Byte offset to the font name string (= 16 + numGlyphs * 24) |
| 4 | int32 | `pixelHeight` | Font pixel height (e.g., 16 for normalFont) |
| 8 | int32 | `numGlyphs` | Number of glyph entries (typically 254) |
| 12 | int32 | `materialOffset` | Byte offset to the material/texture name string |

### Glyph Entry (24 bytes each, immediately after header)

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | uint16 | `letter` | Character code (ASCII 32-255) |
| 2 | int8 | `x0` | Left margin/bearing (horizontal offset from pen position) |
| 3 | int8 | `y0` | Top margin from baseline (signed; negative values push glyph up) |
| 4 | int8 | `dx` | Advance width (pen movement after rendering, includes spacing) |
| 5 | int8 | `pixelWidth` | Glyph bitmap width in pixels |
| 6 | int8 | `pixelHeight` | Glyph bitmap height in pixels |
| 7 | byte | (padding) | Always 0x00 |
| 8 | float32 | `s0` | UV left (normalized 0.0-1.0) |
| 12 | float32 | `t0` | UV top (normalized 0.0-1.0) |
| 16 | float32 | `s1` | UV right (normalized 0.0-1.0) |
| 20 | float32 | `t1` | UV bottom (normalized 0.0-1.0) |

### Footer (after all glyph entries)

Two null-terminated ASCII strings:
1. Font name path (e.g., `fonts/normalFont`)
2. Material/texture name path (e.g., `fonts/gamefonts`)

The header offsets point to these strings:
- `fontNameOffset = 16 + (24 * numGlyphs)`
- `materialOffset = fontNameOffset + len(fontName) + 1`

---

## In-Memory Struct (from OpenAssetTools)

```cpp
struct Glyph {
    uint16_t letter;
    char x0;       // left margin
    char y0;       // top margin (signed)
    char dx;       // advance width
    char pixelWidth;
    char pixelHeight;
    float s0, t0;  // UV top-left
    float s1, t1;  // UV bottom-right
};

struct Font_s {
    const char* fontName;
    int pixelHeight;
    int glyphCount;
    Material* material;
    Material* glowMaterial;  // CoD4+ only, not in CoD2
    Glyph* glyphs;
};
```

---

## Texture Atlas

- **Format**: 32-bit RGBA TGA (RLE compressed on disk)
- **Alpha-only rendering**: RGB channels are all white (1.0, 1.0, 1.0). Only the alpha channel contains glyph shapes. The engine multiplies by `forecolor` at runtime for tinting.
- **Stock textures**:
  - `gamefonts.tga` (512x512) — shared by normalFont, smallFont, bigFont, boldFont, extraBigFont, consoleFont
  - `devfonts.tga` (256x128) — shared by smallDevFont, bigDevFont
  - `qerFont.tga` (128x64) — used by qerFont (Radiant editor font)
- **UV mapping**: `pixel_x = s * texture_width`, `pixel_y = t * texture_height`
- **Material chain**: Font file → material name → .iwi texture (IWI = Infinity Ward Image, DXT5 compressed)

---

## Stock Fonts

| Font File | Pixel Height | Glyphs | Texture | Used For |
|-----------|-------------|--------|---------|----------|
| normalFont | 16 | 254 | gamefonts | Default UI text (UI_FONT_NORMAL) |
| smallFont | 12 | 254 | gamefonts | Small text (UI_FONT_DEFAULT) |
| bigFont | 24 | 254 | gamefonts | Large text (UI_FONT_BIG) |
| boldFont | 30 | 254 | gamefonts | Bold headings |
| extraBigFont | 32 | 254 | gamefonts | Extra large text |
| consoleFont | 18 | 254 | gamefonts | Console/debug text |
| smallDevFont | — | ~98 | devfonts | Dev/editor font |
| bigDevFont | — | ~98 | devfonts | Dev/editor font |
| qerFont | — | ~98 | qerFont | Radiant editor |

---

## Existing Tools

- **Idioma** (DTZxPorter) — closed-source TTF-to-CoD converter for CoD4/WaW. Generates all 7 font files + 1024x2048 TGA atlas.
- **OpenAssetTools** (Laupetin) — open-source C++ tools with verified struct definitions: https://github.com/Laupetin/OpenAssetTools
- **IWI library** (mauserzjeh) — Go library for IWI image format: https://github.com/mauserzjeh/iwi
- **No Python-based converter exists** publicly.

---

## Conversion Plan

### TTF/OTF → CoD2

1. Render each glyph (ASCII 32-255) from TTF using Pillow + FreeType
2. Pack glyphs into a power-of-2 texture atlas
3. Create alpha-only image (white RGB, glyph shapes in alpha)
4. Calculate UV coordinates and glyph metrics (bearing, advance, size)
5. Write binary font file (header + glyphs + footer strings)
6. Save TGA texture atlas

### CoD2 → Editor Display

1. Read binary font file (parse header, glyphs, footer)
2. Load TGA texture, extract glyph bitmaps from UV rectangles
3. Render text in the visual editor using glyph bitmaps

---

## References

- [Zeroy Wiki — Font System](https://wiki.zeroy.com/index.php?title=Call_of_Duty:_Font_System)
- [Creating CoD Fonts Tutorial — itsmods.com](https://www.itsmods.com/forum/Thread-Tutorial-Creating-call-of-duty-fonts-from-stock.html)
- [Idioma Font Tool — Modme Forums](https://forum.modme.co/wiki/threads/2453.html)
- [OpenAssetTools IW3 Assets](https://github.com/Laupetin/OpenAssetTools/blob/main/src/Common/Game/IW3/IW3_Assets.h)
- [CFGFactory Custom Fonts Tutorial](https://cfgfactory.com/tutorials/show/23)
