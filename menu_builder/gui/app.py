"""Main application window — assembles all GUI panels."""

from __future__ import annotations

import copy
import sys
import tkinter as tk
from tkinter.ttk import *  # noqa: F403 — override tk widgets with themed versions
from tkinter import filedialog, messagebox

from menu_builder.models import MenuDef, MenuFile, ItemDef, Rect, Color
from menu_builder.serializer import serialize
from menu_builder.parser import parse_file
from menu_builder.gui.canvas import MenuCanvas
from menu_builder.gui.tree import MenuTree
from menu_builder.gui.properties import PropertiesPanel
from menu_builder.gui.code_preview import CodePreview


# Item types available in the Add Item menu
_ADD_ITEM_TYPES = [
    (1,  "Button"),
    (0,  "Text"),
    (4,  "Edit Field"),
    (6,  "Listbox"),
    (9,  "Numeric Field"),
    (10, "Slider"),
    (11, "Yes/No"),
    (12, "Multi"),
    (14, "Key Bind"),
]

# Display names for status messages
_TYPE_DISPLAY = {t: n for t, n in _ADD_ITEM_TYPES}


class App(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("CoD2 Menu Builder")
        self.geometry("1024x700")
        self.minsize(1024, 600)

        # --- Theme ---
        self._setup_theme()

        # --- Data ---
        self.menu_file = MenuFile(
            menu_defs=[MenuDef(name="new_menu", rect=Rect(0, 0, 640, 480))]
        )
        self.current_menu_index = 0
        self.selected_item: ItemDef | None = None
        self._clipboard: ItemDef | None = None

        # --- Menu Bar ---
        self._build_menu_bar()

        # --- Layout ---
        # Main horizontal split: left (notebook) | right (tree + properties)
        self.main_pane = PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: Editor LabelFrame containing Notebook
        editor_frame = LabelFrame(self.main_pane, text="Editor")
        self.main_pane.add(editor_frame, weight=4)

        self.notebook = Notebook(editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Visual Editor
        canvas_frame = Frame(self.notebook)
        self.notebook.add(canvas_frame, text="  Visual Editor  ")

        self.canvas = MenuCanvas(
            canvas_frame,
            on_select=self._on_canvas_select,
            on_item_moved=self._on_item_moved,
            on_item_resized=self._on_item_resized,
            on_request_add=self._add_item,
            on_request_delete=self._delete_selected,
            on_request_duplicate=self._duplicate_selected,
            on_request_bring_front=self._bring_to_front,
            on_request_send_back=self._send_to_back,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Textual Viewer
        code_frame = Frame(self.notebook)
        self.notebook.add(code_frame, text="  Textual Viewer  ")

        self.code_preview = CodePreview(code_frame)
        self.code_preview.pack(fill=tk.BOTH, expand=True)

        # Update code when switching to code tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Right: tree + properties (vertical split) — narrower, fixed initial width
        right_pane = PanedWindow(self.main_pane, orient=tk.VERTICAL, width=280)
        self.main_pane.add(right_pane, weight=0)

        tree_frame = LabelFrame(right_pane, text="Menu Structure")
        right_pane.add(tree_frame, weight=1)

        self.tree = MenuTree(
            tree_frame,
            on_select_menu=self._on_tree_select_menu,
            on_select_item=self._on_tree_select_item,
        )
        self.tree.pack(fill=tk.BOTH, expand=True)

        props_frame = LabelFrame(right_pane, text="Properties")
        right_pane.add(props_frame, weight=2)

        self.properties = PropertiesPanel(
            props_frame,
            on_property_changed=self._on_property_changed,
        )
        self.properties.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready")
        Label(self, textvariable=self.status_var, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4)
        )

        # --- Initial state ---
        self._refresh_all()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _build_menu_bar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._file_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._file_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save As...", command=self._file_save_as, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Menu", command=self._add_menu)

        # Add Item submenu — pick item type
        add_item_menu = tk.Menu(edit_menu, tearoff=0)
        edit_menu.add_cascade(label="Add Item", menu=add_item_menu)
        for type_id, type_name in _ADD_ITEM_TYPES:
            add_item_menu.add_command(
                label=type_name,
                command=lambda t=type_id: self._add_item(t),
            )
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self._copy_selected, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._paste_item, accelerator="Ctrl+V")
        edit_menu.add_command(label="Duplicate", command=self._duplicate_selected, accelerator="Ctrl+D")
        edit_menu.add_separator()
        edit_menu.add_command(label="Bring to Front", command=self._bring_to_front)
        edit_menu.add_command(label="Send to Back", command=self._send_to_back)
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete Selected", command=self._delete_selected, accelerator="Delete")
        edit_menu.add_command(label="Delete Menu", command=self._delete_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        for name in sorted(Style().theme_names()):
            theme_menu.add_command(
                label=name,
                command=lambda t=name: self._set_theme(t),
            )

        # Keybindings
        self.bind_all("<Control-n>", lambda e: self._file_new())
        self.bind_all("<Control-o>", lambda e: self._file_open())
        self.bind_all("<Control-s>", lambda e: self._file_save_as())
        self.bind_all("<Control-i>", lambda e: self._add_item())
        self.bind_all("<Control-c>", lambda e: self._copy_selected())
        self.bind_all("<Control-v>", lambda e: self._paste_item())
        self.bind_all("<Control-d>", lambda e: self._duplicate_selected())
        self.bind_all("<Delete>", lambda e: self._delete_selected())

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _setup_theme(self):
        """Configure ttk theme — modern look on all platforms."""
        style = Style(self)
        available = style.theme_names()

        # Platform-specific best theme
        if sys.platform == "win32":
            preferred = ["vista", "winnative", "xpnative", "clam"]
        elif sys.platform == "darwin":
            preferred = ["aqua", "clam"]
        else:
            preferred = ["clam", "alt"]

        for theme in preferred:
            if theme in available:
                style.theme_use(theme)
                break

        # LabelFrame: not bold, blue on Windows (matches native look)
        if sys.platform == "win32":
            style.configure("TLabelframe.Label", foreground="#003399")
        else:
            style.configure("TLabelframe.Label", foreground="#336699")

        style.configure("Treeview", rowheight=22)

    def _set_theme(self, theme_name: str):
        """Switch ttk theme at runtime."""
        Style(self).theme_use(theme_name)
        self._set_status(f"Theme: {theme_name}")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _file_new(self):
        self.menu_file = MenuFile(
            menu_defs=[MenuDef(name="new_menu", rect=Rect(0, 0, 640, 480))]
        )
        self.current_menu_index = 0
        self.selected_item = None
        self._refresh_all()
        self._set_status("New file created")

    def _file_open(self):
        path = filedialog.askopenfilename(
            title="Open .menu file",
            filetypes=[("Menu files", "*.menu"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.menu_file = parse_file(path)
            if not self.menu_file.menu_defs:
                messagebox.showwarning("Warning", "File is a fragment (no menuDefs found).")
                return
            self.current_menu_index = 0
            self.selected_item = None
            self._refresh_all()
            total_items = sum(len(m.items) for m in self.menu_file.menu_defs)
            self._set_status(f"Opened: {len(self.menu_file.menu_defs)} menu(s), {total_items} item(s)")
        except Exception as e:
            messagebox.showerror("Parse Error", str(e))

    def _file_save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save .menu file",
            defaultextension=".menu",
            filetypes=[("Menu files", "*.menu"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            text = serialize(self.menu_file)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._set_status(f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ------------------------------------------------------------------
    # Edit operations
    # ------------------------------------------------------------------

    def _add_menu(self):
        idx = len(self.menu_file.menu_defs) + 1
        menu = MenuDef(name=f"menu_{idx}", rect=Rect(0, 0, 640, 480))
        self.menu_file.menu_defs.append(menu)
        self.current_menu_index = len(self.menu_file.menu_defs) - 1
        self.selected_item = None
        self._refresh_all()
        self._set_status(f"Added menu: {menu.name}")

    def _delete_menu(self):
        if len(self.menu_file.menu_defs) <= 1:
            messagebox.showinfo("Info", "Cannot delete the last menu.")
            return
        name = self.menu_file.menu_defs[self.current_menu_index].name
        del self.menu_file.menu_defs[self.current_menu_index]
        self.current_menu_index = min(self.current_menu_index, len(self.menu_file.menu_defs) - 1)
        self.selected_item = None
        self._refresh_all()
        self._set_status(f"Deleted menu: {name}")

    def _add_item(self, item_type: int = 1):
        if not self.menu_file.menu_defs:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        idx = len(menu.items) + 1
        type_name = _TYPE_DISPLAY.get(item_type, "item").lower()
        item = ItemDef(
            name=f"{type_name}_{idx}",
            rect=Rect(10, 10 + (idx - 1) * 35, 200, 30),
            type=item_type,
            style=0,  # WINDOW_STYLE_EMPTY
            text=f"{_TYPE_DISPLAY.get(item_type, 'Item')} {idx}",
            forecolor=Color(1, 1, 1, 1),
            backcolor=Color(0, 0, 0, 1),
            bordercolor=Color(0, 0, 0, 1),
            visible=True,
        )
        menu.items.append(item)
        self.selected_item = item
        self._refresh_all()
        self._set_status(f"Added {_TYPE_DISPLAY.get(item_type, 'item')}: {item.name}")

    def _delete_selected(self):
        if self.selected_item is None:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        if self.selected_item in menu.items:
            name = self.selected_item.name
            menu.items.remove(self.selected_item)
            self.selected_item = None
            self._refresh_all()
            self._set_status(f"Deleted item: {name}")

    def _copy_selected(self):
        if self.selected_item is None:
            return
        self._clipboard = copy.deepcopy(self.selected_item)
        self._set_status(f"Copied: {self.selected_item.name}")

    def _paste_item(self):
        if self._clipboard is None or not self.menu_file.menu_defs:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        item = copy.deepcopy(self._clipboard)
        item.rect.x += 20
        item.rect.y += 20
        item.name = f"{item.name}_copy"
        menu.items.append(item)
        self.selected_item = item
        self._refresh_all()
        self._set_status(f"Pasted: {item.name}")

    def _duplicate_selected(self):
        if self.selected_item is None or not self.menu_file.menu_defs:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        item = copy.deepcopy(self.selected_item)
        item.rect.x += 20
        item.rect.y += 20
        item.name = f"{self.selected_item.name}_dup"
        menu.items.append(item)
        self.selected_item = item
        self._refresh_all()
        self._set_status(f"Duplicated: {item.name}")

    def _bring_to_front(self):
        if self.selected_item is None:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        if self.selected_item in menu.items:
            menu.items.remove(self.selected_item)
            menu.items.append(self.selected_item)
            self._refresh_all()

    def _send_to_back(self):
        if self.selected_item is None:
            return
        menu = self.menu_file.menu_defs[self.current_menu_index]
        if self.selected_item in menu.items:
            menu.items.remove(self.selected_item)
            menu.items.insert(0, self.selected_item)
            self._refresh_all()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_canvas_select(self, item: ItemDef | None):
        prev = self.selected_item
        self.selected_item = item
        self.tree.select_item(item)
        if item is not prev:
            self.properties.load(item, self._current_menu())
        if item:
            self._set_status(f"Selected: {item.name} ({int(item.rect.x)}, {int(item.rect.y)}) {int(item.rect.w)}x{int(item.rect.h)}")

    def _on_item_moved(self, item: ItemDef, x: float, y: float):
        item.rect.x = x
        item.rect.y = y
        self.properties.sync_from_model()
        self._refresh_code()
        self._set_status(f"{item.name}: moved to ({int(x)}, {int(y)})")

    def _on_item_resized(self, item: ItemDef, w: float, h: float):
        item.rect.w = w
        item.rect.h = h
        self.properties.sync_from_model()
        self._refresh_code()
        self._set_status(f"{item.name}: resized to {int(w)}x{int(h)}")

    def _on_tree_select_menu(self, index: int):
        prev_index = self.current_menu_index
        prev_item = self.selected_item
        self.current_menu_index = index
        self.selected_item = None
        self._refresh_canvas()
        self._refresh_code()
        if index != prev_index or prev_item is not None:
            self.properties.load(None, self._current_menu())
        menu = self._current_menu()
        if menu:
            self._set_status(f"Menu: {menu.name} ({len(menu.items)} items)")

    def _on_tree_select_item(self, item: ItemDef):
        prev = self.selected_item
        self.selected_item = item
        self.canvas.select_item(item)
        if item is not prev:
            self.properties.load(item, self._current_menu())

    def _on_property_changed(self):
        self._refresh_canvas()
        self._refresh_tree_labels()
        self._refresh_code()

    def _on_tab_changed(self, event):
        """Refresh code preview when switching to the code tab."""
        current = self.notebook.index(self.notebook.select())
        if current == 1:  # Code tab
            self._refresh_code()
            self.code_preview.highlight_item(self.selected_item)

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    def _current_menu(self) -> MenuDef | None:
        if not self.menu_file.menu_defs:
            return None
        return self.menu_file.menu_defs[self.current_menu_index]

    def _refresh_all(self):
        self._refresh_tree()
        self._refresh_canvas()
        self._refresh_code()
        self.properties.load(self.selected_item, self._current_menu())

    def _refresh_tree(self):
        self.tree.load(self.menu_file, self.current_menu_index, self.selected_item)

    def _refresh_tree_labels(self):
        self.tree.update_labels()

    def _refresh_canvas(self):
        self.canvas.load(self._current_menu(), self.selected_item)

    def _refresh_code(self):
        text = serialize(self.menu_file)
        self.code_preview.set_text(text)

    def _set_status(self, msg: str):
        self.status_var.set(msg)
