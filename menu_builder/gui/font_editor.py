"""Font Editor — view, edit, and convert CoD2 bitmap fonts."""

from __future__ import annotations

import struct
import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from tkinter import filedialog, messagebox
from pathlib import Path

# Project root (fonts/ directory lives here)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_FONTS_DIR = _PROJECT_ROOT / "fonts" / "default"
_CUSTOM_FONTS_DIR = _PROJECT_ROOT / "fonts" / "custom"
_ALL_FONT_DIRS = [_DEFAULT_FONTS_DIR, _CUSTOM_FONTS_DIR]


def _glyph_rect(glyph: dict, tex_w: int, tex_h: int) -> tuple[int, int, int, int]:
    """Get pixel rect (x0, y0, x1, y1) for a glyph on the atlas.

    Uses floor (int) mapping on the IWI texture dimensions.
    """
    return (
        int(glyph["s0"] * tex_w),
        int(glyph["t0"] * tex_h),
        int(glyph["s1"] * tex_w),
        int(glyph["t1"] * tex_h),
    )


class FontEditor(tk.Toplevel):
    """Standalone window for viewing and editing CoD2 font files."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Font Editor")
        self.geometry("900x600")
        self.minsize(800, 500)

        self._font_data: dict | None = None
        self._atlas_photo: tk.PhotoImage | None = None
        self._atlas_w = 0  # texture dimensions (from PNG)
        self._atlas_h = 0
        self._glyph_images: dict[tuple, tk.PhotoImage] = {}
        self._selected_glyph: dict | None = None

        # --- Menu Bar ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Font...", command=self._open_font)
        file_menu.add_command(label="Import TTF/OTF...", command=self._import_ttf)
        file_menu.add_separator()
        file_menu.add_command(label="Export BMFont...", command=self._export_bmfont)
        file_menu.add_command(label="Export TTF...", command=self._export_ttf)
        file_menu.add_command(label="Export OTF...", command=self._export_otf)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)

        # --- Font selector ---
        select_frame = Frame(self)
        select_frame.pack(fill=tk.X, padx=8, pady=(4, 0))
        Label(select_frame, text="Font:").pack(side=tk.LEFT)

        all_fonts = self._list_all_fonts()
        default_font = "normalFont" if "normalFont" in all_fonts else (all_fonts[0] if all_fonts else "")
        self._font_combo_var = tk.StringVar(value=default_font)
        self._font_combo = Combobox(
            select_frame, textvariable=self._font_combo_var,
            values=all_fonts, state="readonly", width=30,
        )
        self._font_combo.pack(side=tk.LEFT, padx=4)
        self._font_combo.bind("<<ComboboxSelected>>", self._on_font_combo_changed)

        # --- Main Layout ---
        main_pane = PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: Font info + glyph list
        left_frame = LabelFrame(main_pane, text="Font")
        main_pane.add(left_frame, weight=1)

        info_frame = Frame(left_frame)
        info_frame.pack(fill=tk.X, padx=4, pady=4)

        self._info_labels: dict[str, tk.StringVar] = {}
        for label_text in ["Name", "Pixel Height", "Glyphs", "Texture"]:
            row = Frame(info_frame)
            row.pack(fill=tk.X, pady=1)
            Label(row, text=f"{label_text}:", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            Label(row, textvariable=var, foreground="#444444").pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._info_labels[label_text] = var

        Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=4)

        Label(left_frame, text="Glyphs", font=("TkDefaultFont", 9, "bold")).pack(
            anchor=tk.W, padx=4
        )

        list_frame = Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        columns = ("char", "code", "dx", "w", "h", "x0", "y0")
        self.glyph_tree = Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.glyph_tree.heading("char", text="Char")
        self.glyph_tree.heading("code", text="Code")
        self.glyph_tree.heading("dx", text="Adv")
        self.glyph_tree.heading("w", text="W")
        self.glyph_tree.heading("h", text="H")
        self.glyph_tree.heading("x0", text="X0")
        self.glyph_tree.heading("y0", text="Y0")

        for col in columns:
            self.glyph_tree.column(col, width=45, minwidth=35, anchor=tk.CENTER)
        self.glyph_tree.column("char", width=50)

        scroll = Scrollbar(list_frame, orient=tk.VERTICAL, command=self.glyph_tree.yview)
        self.glyph_tree.configure(yscrollcommand=scroll.set)
        self.glyph_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.glyph_tree.bind("<<TreeviewSelect>>", self._on_glyph_select)

        # Right: Atlas + preview
        right_pane = PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=2)

        # Texture atlas
        atlas_frame = LabelFrame(right_pane, text="Texture Atlas")
        right_pane.add(atlas_frame, weight=2)

        atlas_scroll_frame = Frame(atlas_frame)
        atlas_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.atlas_canvas = tk.Canvas(atlas_scroll_frame, bg="#1e1e1e", highlightthickness=0)
        atlas_vscroll = Scrollbar(atlas_scroll_frame, orient=tk.VERTICAL, command=self.atlas_canvas.yview)
        atlas_hscroll = Scrollbar(atlas_frame, orient=tk.HORIZONTAL, command=self.atlas_canvas.xview)
        self.atlas_canvas.configure(yscrollcommand=atlas_vscroll.set, xscrollcommand=atlas_hscroll.set)

        self.atlas_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        atlas_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        atlas_hscroll.pack(fill=tk.X)

        # Preview
        detail_frame = LabelFrame(right_pane, text="Preview")
        right_pane.add(detail_frame, weight=1)

        self._detail_frame = Frame(detail_frame)
        self._detail_frame.pack(fill=tk.X, padx=4, pady=4)

        detail_row = Frame(self._detail_frame)
        detail_row.pack(fill=tk.X)
        Label(detail_row, text="Selected:").pack(side=tk.LEFT)
        self._detail_var = tk.StringVar(value="No glyph selected")
        Label(detail_row, textvariable=self._detail_var, foreground="#444444").pack(side=tk.LEFT, padx=8)

        uv_row = Frame(self._detail_frame)
        uv_row.pack(fill=tk.X)
        Label(uv_row, text="UV:").pack(side=tk.LEFT)
        self._uv_var = tk.StringVar(value="—")
        Label(uv_row, textvariable=self._uv_var, foreground="#444444").pack(side=tk.LEFT, padx=8)

        Separator(detail_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=4)

        preview_row = Frame(detail_frame)
        preview_row.pack(fill=tk.X, padx=4, pady=2)
        Label(preview_row, text="Preview text:").pack(side=tk.LEFT)
        self._preview_text_var = tk.StringVar(value="The quick brown fox")
        Entry(preview_row, textvariable=self._preview_text_var, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )

        self.preview_canvas = tk.Canvas(detail_frame, bg="#1a1a1a", height=80, highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._preview_text_var.trace_add("write", lambda *_: self._update_preview())

        # --- Status Bar ---
        self._status_var = tk.StringVar(value="Select a font to begin")
        Label(self, textvariable=self._status_var, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4)
        )

        # Load default font
        if default_font:
            self._load_font_by_name(default_font)

    # ------------------------------------------------------------------
    # Stock fonts
    # ------------------------------------------------------------------

    def _list_all_fonts(self) -> list[str]:
        """List all fonts from default/ and custom/ directories.

        Custom fonts are prefixed with [C] in the display list.
        """
        fonts = []
        if _DEFAULT_FONTS_DIR.is_dir():
            for f in sorted(_DEFAULT_FONTS_DIR.iterdir()):
                if f.is_file() and f.suffix not in (".tga", ".png") and not f.name.startswith("."):
                    fonts.append(f.name)
        if _CUSTOM_FONTS_DIR.is_dir():
            for f in sorted(_CUSTOM_FONTS_DIR.iterdir()):
                if f.is_file() and f.suffix not in (".tga", ".png") and not f.name.startswith("."):
                    fonts.append(f"[C] {f.name}")
        return fonts

    def _resolve_font_path(self, display_name: str) -> Path | None:
        """Resolve a display name (possibly [C] prefixed) to a file path."""
        if display_name.startswith("[C] "):
            name = display_name[4:]
            path = _CUSTOM_FONTS_DIR / name
        else:
            path = _DEFAULT_FONTS_DIR / display_name
        return path if path.exists() else None

    def _load_font_by_name(self, display_name: str):
        path = self._resolve_font_path(display_name)
        if path:
            self._load_font(path)

    def _on_font_combo_changed(self, event):
        name = self._font_combo_var.get()
        if name:
            self._load_font_by_name(name)

    def _refresh_font_list(self):
        """Refresh the font combo with current default + custom fonts."""
        fonts = self._list_all_fonts()
        self._font_combo["values"] = fonts

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _open_font(self):
        """Open a CoD2 font with a dialog for font file + glyph map PNG."""
        dlg = tk.Toplevel(self)
        dlg.title("Open Font")
        dlg.geometry("450x160")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        result = {"confirmed": False, "font_path": "", "png_path": ""}

        # Font file row
        row1 = Frame(dlg)
        row1.pack(fill=tk.X, padx=10, pady=(10, 2))
        Label(row1, text="Font file:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        font_var = tk.StringVar()
        Entry(row1, textvariable=font_var, width=30, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _browse_font():
            p = filedialog.askopenfilename(
                parent=dlg, title="Select CoD2 font file",
                filetypes=[("All files", "*.*")],
            )
            if p:
                font_var.set(p)

        Button(row1, text="Browse", command=_browse_font).pack(side=tk.LEFT, padx=4)

        # Glyph map PNG row
        row2 = Frame(dlg)
        row2.pack(fill=tk.X, padx=10, pady=2)
        Label(row2, text="Glyph map:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        png_var = tk.StringVar()
        Entry(row2, textvariable=png_var, width=30, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _browse_png():
            p = filedialog.askopenfilename(
                parent=dlg, title="Select glyph atlas PNG",
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
            )
            if p:
                png_var.set(p)

        Button(row2, text="Browse", command=_browse_png).pack(side=tk.LEFT, padx=4)

        Label(dlg, text="Glyph map is the atlas PNG with all character images",
              foreground="#888888", font=("TkDefaultFont", 8)).pack(padx=10, anchor=tk.W)

        # Buttons
        btn_frame = Frame(dlg)
        btn_frame.pack(pady=10)

        def _on_open():
            if not font_var.get():
                messagebox.showerror("Error", "Please select a font file.", parent=dlg)
                return
            result["confirmed"] = True
            result["font_path"] = font_var.get()
            result["png_path"] = png_var.get()
            dlg.destroy()

        Button(btn_frame, text="Open", command=_on_open).pack(side=tk.LEFT, padx=4)
        Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side=tk.LEFT, padx=4)

        self.wait_window(dlg)

        if not result["confirmed"]:
            return

        import shutil

        font_src = Path(result["font_path"])
        font_name = font_src.name

        # Copy font file into fonts/custom/
        _CUSTOM_FONTS_DIR.mkdir(parents=True, exist_ok=True)
        font_dst = _CUSTOM_FONTS_DIR / font_name
        shutil.copy2(font_src, font_dst)

        # Copy PNG atlas into fonts/custom/
        if result["png_path"]:
            png_src = Path(result["png_path"])
            shutil.copy2(png_src, _CUSTOM_FONTS_DIR / png_src.name)

        # Refresh font list, select the new font, and load it
        self._refresh_font_list()
        display_name = f"[C] {font_name}"
        self._font_combo_var.set(display_name)
        self._load_font(font_dst)
        self._status_var.set(f"Opened: {font_name} (saved to fonts/custom/)")

    def _import_ttf(self):
        """Open import dialog: font file + glyph map PNG + pixel height."""
        dlg = tk.Toplevel(self)
        dlg.title("Import Font")
        dlg.geometry("450x200")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        result = {"confirmed": False, "font_path": "", "png_path": "", "size": "16"}

        # Font file row
        row1 = Frame(dlg)
        row1.pack(fill=tk.X, padx=10, pady=(10, 2))
        Label(row1, text="Font file:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        font_var = tk.StringVar()
        Entry(row1, textvariable=font_var, width=30, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _browse_font():
            p = filedialog.askopenfilename(
                parent=dlg, title="Select TTF/OTF font",
                filetypes=[("Font files", "*.ttf *.otf"), ("All files", "*.*")],
            )
            if p:
                font_var.set(p)

        Button(row1, text="Browse", command=_browse_font).pack(side=tk.LEFT, padx=4)

        # Glyph map PNG row
        row2 = Frame(dlg)
        row2.pack(fill=tk.X, padx=10, pady=2)
        Label(row2, text="Glyph map:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        png_var = tk.StringVar()
        Entry(row2, textvariable=png_var, width=30, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _browse_png():
            p = filedialog.askopenfilename(
                parent=dlg, title="Select glyph atlas PNG",
                filetypes=[("PNG images", "*.png"), ("All files", "*.*")],
            )
            if p:
                png_var.set(p)

        Button(row2, text="Browse", command=_browse_png).pack(side=tk.LEFT, padx=4)

        # Note about glyph map
        Label(dlg, text="Glyph map is the atlas PNG containing all character images",
              foreground="#888888", font=("TkDefaultFont", 8)).pack(padx=10, anchor=tk.W)

        # Pixel height row
        row3 = Frame(dlg)
        row3.pack(fill=tk.X, padx=10, pady=2)
        Label(row3, text="Pixel height:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        size_var = tk.StringVar(value="16")
        Spinbox(row3, textvariable=size_var, from_=6, to=72, width=5).pack(side=tk.LEFT)

        # Buttons
        btn_frame = Frame(dlg)
        btn_frame.pack(pady=10)

        def _on_import():
            if not font_var.get():
                messagebox.showerror("Error", "Please select a font file.", parent=dlg)
                return
            result["confirmed"] = True
            result["font_path"] = font_var.get()
            result["png_path"] = png_var.get()
            result["size"] = size_var.get()
            dlg.destroy()

        Button(btn_frame, text="Import", command=_on_import).pack(side=tk.LEFT, padx=4)
        Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side=tk.LEFT, padx=4)

        self.wait_window(dlg)

        if not result["confirmed"]:
            return

        try:
            pixel_height = int(result["size"])
        except ValueError:
            messagebox.showerror("Error", "Invalid pixel height.")
            return

        if pixel_height < 6 or pixel_height > 72:
            messagebox.showerror("Error", "Pixel height must be between 6 and 72.")
            return

        ttf_path = Path(result["font_path"])
        png_path = result["png_path"]

        # Ensure custom dir exists
        _CUSTOM_FONTS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            from menu_builder.font_import import import_ttf
            stem = ttf_path.stem
            font_out, png_out = import_ttf(
                ttf_path=ttf_path,
                pixel_height=pixel_height,
                output_font_path=_CUSTOM_FONTS_DIR / stem,
                output_png_path=_CUSTOM_FONTS_DIR / f"{stem}_atlas.png",
            )

            # If user provided a custom glyph map PNG, copy it over the generated one
            if png_path:
                import shutil
                shutil.copy2(png_path, png_out)

            self._status_var.set(f"Imported: {font_out.name}")
            messagebox.showinfo("Import Complete", f"Font saved to fonts/custom/\n{font_out.name}\n{png_out.name}")

            # Refresh font list and load the new font
            self._refresh_font_list()
            display_name = f"[C] {stem}"
            self._font_combo_var.set(display_name)
            self._load_font(font_out)
        except ImportError:
            messagebox.showerror("Error", "Pillow package required.\nInstall with: pip install Pillow")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _export_bmfont(self):
        if not self._font_data:
            messagebox.showinfo("Info", "No font loaded.")
            return

        output_dir = filedialog.askdirectory(title="Select output directory for BMFont export")
        if not output_dir:
            return

        # Find the atlas PNG
        material = self._font_data["materialName"]
        tex_name = material.rsplit("/", 1)[-1] if "/" in material else material
        atlas_path = None
        font_dir = self._font_data["path"].parent if "path" in self._font_data else _DEFAULT_FONTS_DIR
        for search_dir in [font_dir] + _ALL_FONT_DIRS:
            candidate = search_dir / f"{tex_name}.png"
            if candidate.exists():
                atlas_path = candidate
                break

        if atlas_path is None:
            messagebox.showerror("Error", f"Atlas PNG not found for {tex_name}")
            return

        try:
            from menu_builder.font_export import export_bmfont
            fnt_path, png_path = export_bmfont(
                self._font_data,
                atlas_png_path=atlas_path,
                output_dir=Path(output_dir),
                tex_w=self._atlas_w or 512,
                tex_h=self._atlas_h or 1024,
            )
            self._status_var.set(f"Exported: {fnt_path.name} + {png_path.name}")
            messagebox.showinfo("Export Complete", f"Saved to:\n{fnt_path}\n{png_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_ttf(self):
        self._export_vector_font("ttf")

    def _export_otf(self):
        self._export_vector_font("otf")

    def _export_vector_font(self, fmt: str):
        if not self._font_data or "path" not in self._font_data:
            messagebox.showinfo("Info", "No font loaded.")
            return

        atlas_path = self._find_atlas_png()
        if atlas_path is None:
            return

        ext = f".{fmt}"
        label = fmt.upper()
        raw_name = self._font_data["fontName"].rsplit("/", 1)[-1]
        output_path = filedialog.asksaveasfilename(
            title=f"Export {label}",
            defaultextension=ext,
            initialfile=f"{raw_name}{ext}",
            filetypes=[(f"{label} Font", f"*{ext}"), ("All files", "*.*")],
        )
        if not output_path:
            return

        try:
            if fmt == "ttf":
                from menu_builder.font_ttf_export import export_ttf
                result = export_ttf(
                    font_path=self._font_data["path"],
                    atlas_png_path=atlas_path,
                    output_path=Path(output_path),
                    tex_w=self._atlas_w or 512,
                    tex_h=self._atlas_h or 1024,
                )
            else:
                from menu_builder.font_ttf_export import export_otf
                result = export_otf(
                    font_path=self._font_data["path"],
                    atlas_png_path=atlas_path,
                    output_path=Path(output_path),
                    tex_w=self._atlas_w or 512,
                    tex_h=self._atlas_h or 1024,
                )
            self._status_var.set(f"Exported {label}: {result.name}")
            messagebox.showinfo("Export Complete", f"Saved to:\n{result}")
        except ImportError:
            messagebox.showerror("Error", "fonttools package required.\nInstall with: pip install fonttools")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _find_atlas_png(self) -> Path | None:
        """Find the atlas PNG for the current font."""
        material = self._font_data["materialName"]
        tex_name = material.rsplit("/", 1)[-1] if "/" in material else material
        font_dir = self._font_data["path"].parent
        for search_dir in [font_dir] + _ALL_FONT_DIRS:
            candidate = search_dir / f"{tex_name}.png"
            if candidate.exists():
                return candidate
        messagebox.showerror("Error", f"Atlas PNG not found for {tex_name}")
        return None

    # ------------------------------------------------------------------
    # Font loading
    # ------------------------------------------------------------------

    def _load_font(self, path: Path):
        try:
            data = path.read_bytes()
            if len(data) < 16:
                messagebox.showerror("Error", "File too small to be a font file.")
                return

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

            self._font_data = {
                "path": path, "pixelHeight": pixel_height,
                "numGlyphs": num_glyphs, "fontName": font_name,
                "materialName": material_name, "glyphs": glyphs,
            }

            self._load_atlas(path.parent, material_name)

            self._info_labels["Name"].set(font_name)
            self._info_labels["Pixel Height"].set(str(pixel_height))
            self._info_labels["Glyphs"].set(str(num_glyphs))
            self._info_labels["Texture"].set(material_name)

            self._glyph_images.clear()
            self._selected_glyph = None
            self._populate_glyph_list()
            self._render_atlas()
            self._update_preview()
            self._status_var.set(f"Loaded: {path.name} ({num_glyphs} glyphs, {pixel_height}px)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load font: {e}")

    def _load_atlas(self, font_dir: Path, material_name: str):
        """Load the atlas PNG (IWI-converted) for the font."""
        self._atlas_photo = None
        self._atlas_w = 0
        self._atlas_h = 0

        tex_name = material_name.rsplit("/", 1)[-1] if "/" in material_name else material_name
        for search_dir in [font_dir] + _ALL_FONT_DIRS:
            img_path = search_dir / f"{tex_name}.png"
            if img_path.exists():
                self._atlas_photo = tk.PhotoImage(file=str(img_path), master=self)
                self._atlas_w = self._atlas_photo.width()
                self._atlas_h = self._atlas_photo.height()
                return

    # ------------------------------------------------------------------
    # Atlas rendering
    # ------------------------------------------------------------------

    def _render_atlas(self):
        self.atlas_canvas.delete("all")
        if self._atlas_photo is None:
            self.atlas_canvas.create_text(
                200, 100, text="No atlas PNG found", fill="#666666", font=("TkDefaultFont", 12),
            )
            return

        self.atlas_canvas.create_image(0, 0, anchor=tk.NW, image=self._atlas_photo)
        self.atlas_canvas.configure(scrollregion=(0, 0, self._atlas_w, self._atlas_h))

    def _highlight_glyph_on_atlas(self, glyph: dict):
        self._render_atlas()
        if self._atlas_photo is None or self._atlas_w == 0:
            return

        x0, y0, x1, y1 = _glyph_rect(glyph, self._atlas_w, self._atlas_h)

        self.atlas_canvas.create_rectangle(
            x0 - 1, y0 - 1, x1 + 1, y1 + 1,
            outline="#ff4444", width=2,
        )

        # Scroll to show the glyph
        if self._atlas_h > 0:
            self.atlas_canvas.yview_moveto(max(0, (y0 - 20)) / self._atlas_h)

    # ------------------------------------------------------------------
    # Glyph list
    # ------------------------------------------------------------------

    def _populate_glyph_list(self):
        self.glyph_tree.delete(*self.glyph_tree.get_children())
        if not self._font_data:
            return

        for g in self._font_data["glyphs"]:
            letter = g["letter"]
            ch = chr(letter) if 32 <= letter < 127 else f"\\x{letter:02x}"
            self.glyph_tree.insert("", tk.END, values=(
                ch, letter, g["dx"], g["pixelWidth"], g["pixelHeight"],
                g["x0"], g["y0"],
            ))

    def _on_glyph_select(self, event):
        selection = self.glyph_tree.selection()
        if not selection:
            return
        values = self.glyph_tree.item(selection[0], "values")
        if not values:
            return

        ch, code = values[0], int(values[1])
        glyph = None
        for g in self._font_data["glyphs"]:
            if g["letter"] == code:
                glyph = g
                break

        if glyph:
            self._selected_glyph = glyph
            self._detail_var.set(
                f"'{ch}' (code {code})  —  "
                f"advance={glyph['dx']}  size={glyph['pixelWidth']}x{glyph['pixelHeight']}  "
                f"bearing=({glyph['x0']}, {glyph['y0']})"
            )
            self._uv_var.set(
                f"s0={glyph['s0']:.4f}  t0={glyph['t0']:.4f}  "
                f"s1={glyph['s1']:.4f}  t1={glyph['t1']:.4f}"
            )
            self._highlight_glyph_on_atlas(glyph)

    # ------------------------------------------------------------------
    # Text preview
    # ------------------------------------------------------------------

    def _get_glyph_image(self, letter: int, scale: int = 2) -> tk.PhotoImage | None:
        """Extract a glyph from the atlas PNG as a PhotoImage."""
        cache_key = (letter, scale)
        if cache_key in self._glyph_images:
            return self._glyph_images[cache_key]
        if self._atlas_photo is None or self._font_data is None:
            return None

        glyph = None
        for g in self._font_data["glyphs"]:
            if g["letter"] == letter:
                glyph = g
                break
        if glyph is None:
            return None

        x0, y0, x1, y1 = _glyph_rect(glyph, self._atlas_w, self._atlas_h)
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            return None

        # Crop from the atlas PhotoImage
        try:
            cropped = tk.PhotoImage(width=w, height=h, master=self)
            # Copy pixel region from atlas
            cropped.tk.call(cropped, "copy", self._atlas_photo,
                            "-from", x0, y0, x1, y1)
            if scale > 1:
                cropped = cropped.zoom(scale, scale)
            self._glyph_images[cache_key] = cropped
            return cropped
        except Exception:
            return None

    def _update_preview(self):
        """Render preview text using actual glyph bitmaps from the atlas."""
        self.preview_canvas.delete("all")
        if not self._font_data:
            return

        text = self._preview_text_var.get()
        if not text:
            return

        scale = 2
        glyphs_by_code = {g["letter"]: g for g in self._font_data["glyphs"]}
        px = 10
        py = 50

        for ch in text:
            code = ord(ch)
            g = glyphs_by_code.get(code)
            if not g:
                px += 8 * scale
                continue

            img = self._get_glyph_image(code, scale)
            if img:
                gx = px + g["x0"] * scale
                gy = py + g["y0"] * scale
                self.preview_canvas.create_image(gx, gy, anchor=tk.NW, image=img)

            px += g["dx"] * scale

        # Baseline indicator
        self.preview_canvas.create_line(10, py, px + 10, py, fill="#884444", dash=(2, 2))
