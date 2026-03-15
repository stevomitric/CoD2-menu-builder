"""Menu structure tree view — menuDef > itemDef hierarchy."""

from __future__ import annotations

import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from typing import Callable

from menu_builder.models import ItemDef, MenuDef, MenuFile


# Item type display: (name, icon_color_hex)
_TYPE_INFO: dict[int | None, tuple[str, str]] = {
    0:  ("TEXT",         "#6688AA"),
    1:  ("BUTTON",       "#88AA66"),
    4:  ("EDITFIELD",    "#AA8866"),
    6:  ("LISTBOX",      "#8866AA"),
    9:  ("NUMERICFIELD", "#AA6688"),
    10: ("SLIDER",       "#66AA88"),
    11: ("YESNO",        "#AAAA66"),
    12: ("MULTI",        "#66AAAA"),
    13: ("DVARENUM",     "#AA88AA"),
    14: ("BIND",         "#AA66AA"),
    16: ("VALIDFILE",    "#88AAAA"),
    17: ("DECIMAL",      "#AAAA88"),
    18: ("UPREDITFIELD", "#AA8888"),
    None: ("",           "#666666"),
}

# Menu icon color
_MENU_ICON_COLOR = "#5588CC"


def _create_icon(root: tk.Misc, color: str, size: int = 12) -> tk.PhotoImage:
    """Create a small solid-color square icon."""
    img = tk.PhotoImage(width=size, height=size, master=root)
    # Fill with color (border 1px darker)
    img.put(color, to=(0, 0, size, size))
    # Simple 1px border effect — darken edges
    dark = _darken(color)
    for i in range(size):
        img.put(dark, to=(i, 0, i + 1, 1))          # top
        img.put(dark, to=(i, size - 1, i + 1, size))  # bottom
        img.put(dark, to=(0, i, 1, i + 1))            # left
        img.put(dark, to=(size - 1, i, size, i + 1))  # right
    return img


def _darken(hex_color: str, factor: float = 0.6) -> str:
    """Darken a hex color."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


class MenuTree(Frame):
    """Tree view showing menuDef > itemDef hierarchy."""

    def __init__(
        self,
        parent,
        on_select_menu: Callable[[int], None] | None = None,
        on_select_item: Callable[[ItemDef], None] | None = None,
    ):
        super().__init__(parent)
        self.on_select_menu = on_select_menu
        self.on_select_item = on_select_item

        self.menu_file: MenuFile | None = None
        self._node_to_menu_index: dict[str, int] = {}
        self._node_to_item: dict[str, ItemDef] = {}
        self._item_to_node: dict[int, str] = {}
        self._suppress_select = False

        # Icons (created lazily after widget is mapped to a root window)
        self._icons: dict[int | None, tk.PhotoImage] = {}
        self._menu_icon: tk.PhotoImage | None = None
        self._icons_ready = False

        self.tree = Treeview(self, show="tree", selectmode="browse")
        scroll = Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ------------------------------------------------------------------
    # Icons
    # ------------------------------------------------------------------

    def _ensure_icons(self):
        """Create icons once the widget has a root window."""
        if self._icons_ready:
            return
        try:
            root = self.winfo_toplevel()
            self._menu_icon = _create_icon(root, _MENU_ICON_COLOR, 12)
            for type_id, (_, color) in _TYPE_INFO.items():
                self._icons[type_id] = _create_icon(root, color, 10)
            self._icons_ready = True
        except tk.TclError:
            pass

    def _get_item_icon(self, item_type: int | None) -> tk.PhotoImage | None:
        return self._icons.get(item_type, self._icons.get(None))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, menu_file: MenuFile, current_menu_index: int = 0, selected_item: ItemDef | None = None):
        """Rebuild the tree from the menu file."""
        self._ensure_icons()
        self._suppress_select = True
        self.menu_file = menu_file
        self._node_to_menu_index.clear()
        self._node_to_item.clear()
        self._item_to_node.clear()

        for child in self.tree.get_children():
            self.tree.delete(child)

        if not menu_file or not menu_file.menu_defs:
            self._suppress_select = False
            return

        for i, menu in enumerate(menu_file.menu_defs):
            menu_label = f"menuDef: {menu.name or '(unnamed)'}"
            menu_node = self.tree.insert(
                "", tk.END, text=menu_label,
                open=(i == current_menu_index),
                image=self._menu_icon or "",
            )
            self._node_to_menu_index[menu_node] = i

            for item in menu.items:
                type_name = _TYPE_INFO.get(item.type, _TYPE_INFO[None])[0]
                item_label = item.name or "(unnamed)"
                if type_name:
                    item_label += f"  [{type_name}]"
                item_node = self.tree.insert(
                    menu_node, tk.END, text=item_label,
                    image=self._get_item_icon(item.type) or "",
                )
                self._node_to_item[item_node] = item
                self._item_to_node[id(item)] = item_node

        if selected_item is not None:
            self.select_item(selected_item)
        elif current_menu_index < len(menu_file.menu_defs):
            menu_nodes = self.tree.get_children()
            if current_menu_index < len(menu_nodes):
                self.tree.selection_set(menu_nodes[current_menu_index])

        self._suppress_select = False

    def select_item(self, item: ItemDef | None):
        """Programmatically select an item in the tree."""
        self._suppress_select = True
        if item is None:
            self.tree.selection_set()
        else:
            node_id = self._item_to_node.get(id(item))
            if node_id:
                self.tree.selection_set(node_id)
                self.tree.see(node_id)
        self._suppress_select = False

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_select(self, event):
        if self._suppress_select:
            return

        selection = self.tree.selection()
        if not selection:
            return

        node = selection[0]

        if node in self._node_to_menu_index:
            idx = self._node_to_menu_index[node]
            if self.on_select_menu:
                self.on_select_menu(idx)
            return

        if node in self._node_to_item:
            item = self._node_to_item[node]
            if self.on_select_item:
                self.on_select_item(item)
