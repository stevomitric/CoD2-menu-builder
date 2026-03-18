"""Font Editor — view, edit, and convert CoD2 bitmap fonts."""

from __future__ import annotations

import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from tkinter import filedialog, messagebox
from pathlib import Path


class FontEditor(tk.Toplevel):
    """Standalone window for viewing and editing CoD2 font files."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Font Editor")
        self.geometry("900x600")
        self.minsize(800, 500)

        self._font_data: dict | None = None  # Parsed font data
        self._texture_image: tk.PhotoImage | None = None

        # --- Menu Bar ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Font...", command=self._open_font)
        file_menu.add_command(label="Import TTF/OTF...", command=self._import_ttf, state=tk.DISABLED)
        file_menu.add_separator()
        file_menu.add_command(label="Export Font...", command=self._export_font, state=tk.DISABLED)
        file_menu.add_command(label="Export TGA...", command=self._export_tga, state=tk.DISABLED)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)

        # --- Main Layout ---
        main_pane = PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: Font info + glyph list
        left_frame = LabelFrame(main_pane, text="Font")
        main_pane.add(left_frame, weight=1)

        # Font info section
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

        # Glyph list
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

        # Right: Preview area
        right_pane = PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=2)

        # Texture atlas preview
        atlas_frame = LabelFrame(right_pane, text="Texture Atlas")
        right_pane.add(atlas_frame, weight=2)

        self.atlas_canvas = tk.Canvas(
            atlas_frame, bg="#2a2a2a", highlightthickness=0
        )
        self.atlas_canvas.pack(fill=tk.BOTH, expand=True)

        # Glyph detail + text preview
        detail_frame = LabelFrame(right_pane, text="Preview")
        right_pane.add(detail_frame, weight=1)

        # Glyph detail info
        self._detail_frame = Frame(detail_frame)
        self._detail_frame.pack(fill=tk.X, padx=4, pady=4)

        detail_row = Frame(self._detail_frame)
        detail_row.pack(fill=tk.X)
        Label(detail_row, text="Selected:").pack(side=tk.LEFT)
        self._detail_var = tk.StringVar(value="No glyph selected")
        Label(detail_row, textvariable=self._detail_var, foreground="#444444").pack(
            side=tk.LEFT, padx=8
        )

        # UV info
        uv_row = Frame(self._detail_frame)
        uv_row.pack(fill=tk.X)
        Label(uv_row, text="UV:").pack(side=tk.LEFT)
        self._uv_var = tk.StringVar(value="—")
        Label(uv_row, textvariable=self._uv_var, foreground="#444444").pack(
            side=tk.LEFT, padx=8
        )

        Separator(detail_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=4)

        # Text preview input
        preview_row = Frame(detail_frame)
        preview_row.pack(fill=tk.X, padx=4, pady=2)
        Label(preview_row, text="Preview text:").pack(side=tk.LEFT)
        self._preview_text_var = tk.StringVar(value="The quick brown fox")
        Entry(preview_row, textvariable=self._preview_text_var, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=4
        )

        # Text render preview canvas
        self.preview_canvas = tk.Canvas(
            detail_frame, bg="#1a1a1a", height=60, highlightthickness=0
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._preview_text_var.trace_add("write", lambda *_: self._update_preview())

        # --- Status Bar ---
        self._status_var = tk.StringVar(value="Open a font file to begin")
        Label(self, textvariable=self._status_var, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4)
        )

        # Try loading stock fonts on open
        self._try_load_stock()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _open_font(self):
        path = filedialog.askopenfilename(
            title="Open CoD2 Font File",
            filetypes=[("Font files", "*"), ("All files", "*.*")],
        )
        if path:
            self._load_font(Path(path))

    def _import_ttf(self):
        messagebox.showinfo("Not Yet", "TTF/OTF import will be implemented soon.")

    def _export_font(self):
        messagebox.showinfo("Not Yet", "Font export will be implemented soon.")

    def _export_tga(self):
        messagebox.showinfo("Not Yet", "TGA export will be implemented soon.")

    # ------------------------------------------------------------------
    # Font loading
    # ------------------------------------------------------------------

    def _try_load_stock(self):
        """Try to load the stock normalFont on startup."""
        pkg_dir = Path(__file__).resolve().parent.parent
        project_root = pkg_dir.parent
        stock = project_root / "fonts" / "normalFont"
        if stock.exists():
            self._load_font(stock)

    def _load_font(self, path: Path):
        import struct

        try:
            data = path.read_bytes()
            if len(data) < 16:
                messagebox.showerror("Error", "File too small to be a font file.")
                return

            # Parse header
            name_offset, pixel_height, num_glyphs, material_offset = struct.unpack_from("<4i", data, 0)

            # Parse glyphs
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
                    "letter": letter,
                    "x0": x0, "y0": y0, "dx": dx,
                    "pixelWidth": pw, "pixelHeight": ph,
                    "s0": s0, "t0": t0, "s1": s1, "t1": t1,
                })

            # Parse footer strings
            font_name = ""
            material_name = ""
            if name_offset < len(data):
                end = data.index(b"\x00", name_offset)
                font_name = data[name_offset:end].decode("ascii", errors="replace")
            if material_offset < len(data):
                end = data.index(b"\x00", material_offset)
                material_name = data[material_offset:end].decode("ascii", errors="replace")

            self._font_data = {
                "path": path,
                "pixelHeight": pixel_height,
                "numGlyphs": num_glyphs,
                "fontName": font_name,
                "materialName": material_name,
                "glyphs": glyphs,
            }

            # Update UI
            self._info_labels["Name"].set(font_name)
            self._info_labels["Pixel Height"].set(str(pixel_height))
            self._info_labels["Glyphs"].set(str(num_glyphs))
            self._info_labels["Texture"].set(material_name)

            self._populate_glyph_list()
            self._status_var.set(f"Loaded: {path.name} ({num_glyphs} glyphs, {pixel_height}px)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load font: {e}")

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

        ch, code = values[0], values[1]
        # Find the glyph data
        code_int = int(code)
        glyph = None
        for g in self._font_data["glyphs"]:
            if g["letter"] == code_int:
                glyph = g
                break

        if glyph:
            self._detail_var.set(
                f"'{ch}' (code {code_int})  —  "
                f"advance={glyph['dx']}  size={glyph['pixelWidth']}x{glyph['pixelHeight']}  "
                f"bearing=({glyph['x0']}, {glyph['y0']})"
            )
            self._uv_var.set(
                f"s0={glyph['s0']:.4f}  t0={glyph['t0']:.4f}  "
                f"s1={glyph['s1']:.4f}  t1={glyph['t1']:.4f}"
            )

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self):
        """Render preview text using glyph metrics (placeholder — shows boxes)."""
        self.preview_canvas.delete("all")
        if not self._font_data:
            return

        text = self._preview_text_var.get()
        if not text:
            return

        glyphs_by_code = {g["letter"]: g for g in self._font_data["glyphs"]}
        px = 10
        py = 30
        height = self._font_data["pixelHeight"]

        for ch in text:
            code = ord(ch)
            g = glyphs_by_code.get(code)
            if not g:
                px += 8  # space for unknown
                continue

            w = g["pixelWidth"]
            h = g["pixelHeight"]
            x0 = g["x0"]
            y0 = g["y0"]

            # Draw glyph bounding box (placeholder until we render from texture)
            gx = px + x0
            gy = py + y0
            if w > 0 and h > 0:
                self.preview_canvas.create_rectangle(
                    gx, gy, gx + w, gy + h,
                    outline="#5588aa", fill="#2a3a4a",
                )
                self.preview_canvas.create_text(
                    gx + w / 2, gy + h / 2, text=ch,
                    fill="#aaccee", font=("TkDefaultFont", max(7, h - 2)),
                    anchor=tk.CENTER,
                )

            px += g["dx"]

        # Baseline indicator
        self.preview_canvas.create_line(
            10, py, px + 10, py, fill="#884444", dash=(2, 2)
        )
