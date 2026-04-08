"""Image Assets Manager — import, preview, and export images for CoD2 menus."""

from __future__ import annotations

import shutil
import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from tkinter import filedialog, messagebox
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_IMAGES_DIR = _PROJECT_ROOT / "images"


class ImageAssets(tk.Toplevel):
    """Standalone window for managing image assets."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Image Assets")
        self.geometry("800x500")
        self.minsize(700, 400)

        self._preview_photo: tk.PhotoImage | None = None
        self._selected_path: Path | None = None

        # --- Menu Bar ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Image...", command=self._import_image)
        file_menu.add_command(label="Export to IWI...", command=self._export_iwi)
        file_menu.add_separator()
        file_menu.add_command(label="Delete Selected", command=self._delete_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.destroy)

        # --- Main Layout ---
        main_pane = PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: Image list
        left_frame = LabelFrame(main_pane, text="Images")
        main_pane.add(left_frame, weight=1)

        list_frame = Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.image_list = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scroll = Scrollbar(list_frame, orient=tk.VERTICAL, command=self.image_list.yview)
        self.image_list.configure(yscrollcommand=scroll.set)
        self.image_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_list.bind("<<ListboxSelect>>", self._on_select)

        # Buttons below list
        btn_frame = Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        Button(btn_frame, text="Import", command=self._import_image).pack(side=tk.LEFT, padx=2)
        Button(btn_frame, text="Export IWI", command=self._export_iwi).pack(side=tk.LEFT, padx=2)
        Button(btn_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)

        # Right: Preview
        right_frame = LabelFrame(main_pane, text="Preview")
        main_pane.add(right_frame, weight=2)

        # Image info
        self._info_var = tk.StringVar(value="Select an image")
        Label(right_frame, textvariable=self._info_var, foreground="#444444").pack(
            padx=8, pady=4, anchor=tk.W
        )

        # Preview canvas
        self.preview_canvas = tk.Canvas(right_frame, bg="#1e1e1e", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # --- Status Bar ---
        self._status_var = tk.StringVar(value=f"Images directory: {_IMAGES_DIR}")
        Label(self, textvariable=self._status_var, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4)
        )

        # Ensure images dir exists
        _IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Load image list
        self._refresh_list()

    # ------------------------------------------------------------------
    # Image list
    # ------------------------------------------------------------------

    def _refresh_list(self):
        self.image_list.delete(0, tk.END)
        if not _IMAGES_DIR.is_dir():
            return

        for f in sorted(_IMAGES_DIR.iterdir()):
            if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg") and not f.name.startswith("."):
                self.image_list.insert(tk.END, f.name)

        count = self.image_list.size()
        self._status_var.set(f"{count} image(s) in {_IMAGES_DIR}")

    def _get_selected(self) -> Path | None:
        sel = self.image_list.curselection()
        if not sel:
            return None
        name = self.image_list.get(sel[0])
        return _IMAGES_DIR / name

    def _on_select(self, event):
        path = self._get_selected()
        if path is None:
            return
        self._selected_path = path
        self._show_preview(path)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _show_preview(self, path: Path):
        self.preview_canvas.delete("all")
        self._preview_photo = None

        try:
            self._preview_photo = tk.PhotoImage(file=str(path), master=self)
            w = self._preview_photo.width()
            h = self._preview_photo.height()

            self._info_var.set(f"{path.name}  —  {w} x {h}  —  {path.stat().st_size // 1024} KB")

            # Fit image to canvas
            canvas_w = self.preview_canvas.winfo_width()
            canvas_h = self.preview_canvas.winfo_height()
            if canvas_w > 10 and canvas_h > 10:
                cx, cy = canvas_w // 2, canvas_h // 2
            else:
                cx, cy = 200, 200

            self.preview_canvas.create_image(cx, cy, image=self._preview_photo, anchor=tk.CENTER)

        except tk.TclError:
            # tkinter PhotoImage only supports PNG/GIF natively, not JPG
            self._info_var.set(f"{path.name}  —  {path.stat().st_size // 1024} KB  (preview not available for JPG)")
            self.preview_canvas.create_text(
                200, 100, text="Preview not available\n(JPG — use PNG for preview)",
                fill="#666666", font=("TkDefaultFont", 11), anchor=tk.CENTER,
            )

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def _import_image(self):
        paths = filedialog.askopenfilenames(
            title="Import Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("All files", "*.*")],
        )
        if not paths:
            return

        _IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        imported = 0
        for p in paths:
            src = Path(p)
            dst = _IMAGES_DIR / src.name
            if dst.exists():
                overwrite = messagebox.askyesno(
                    "Overwrite?", f"{src.name} already exists. Overwrite?", parent=self,
                )
                if not overwrite:
                    continue
            shutil.copy2(src, dst)
            imported += 1

        self._refresh_list()
        self._status_var.set(f"Imported {imported} image(s)")

    # ------------------------------------------------------------------
    # Export to IWI
    # ------------------------------------------------------------------

    def _export_iwi(self):
        path = self._get_selected()
        if path is None:
            messagebox.showinfo("Info", "Select an image to export.", parent=self)
            return

        output = filedialog.asksaveasfilename(
            title="Export to IWI",
            defaultextension=".iwi",
            initialfile=path.stem + ".iwi",
            filetypes=[("IWI Image", "*.iwi"), ("All files", "*.*")],
            parent=self,
        )
        if not output:
            return

        try:
            from menu_builder.iwi_converter import image_to_iwi
            iwi_path = image_to_iwi(path, Path(output))
            self._status_var.set(f"Exported: {iwi_path.name} ({iwi_path.stat().st_size // 1024} KB)")
            messagebox.showinfo("Export Complete", f"Saved to:\n{iwi_path}", parent=self)
        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                "quicktex not found.\nInstall with: pip install quicktex",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _delete_selected(self):
        path = self._get_selected()
        if path is None:
            messagebox.showinfo("Info", "Select an image to delete.", parent=self)
            return

        confirm = messagebox.askyesno("Delete?", f"Delete {path.name}?", parent=self)
        if not confirm:
            return

        try:
            path.unlink()
            self.preview_canvas.delete("all")
            self._preview_photo = None
            self._info_var.set("Select an image")
            self._refresh_list()
            self._status_var.set(f"Deleted: {path.name}")
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
