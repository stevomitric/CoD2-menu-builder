"""Menu structure tree view — menuDef > itemDef hierarchy."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from menu_builder.models import ItemDef, MenuDef, MenuFile


# Item type names for display
_TYPE_NAMES = {
    0: "TEXT",
    1: "BUTTON",
    4: "EDITFIELD",
    6: "LISTBOX",
    9: "NUMERICFIELD",
    10: "SLIDER",
    11: "YESNO",
    12: "MULTI",
    13: "DVARENUM",
    14: "BIND",
    16: "VALIDFILE",
    17: "DECIMAL",
    18: "UPREDITFIELD",
}


class MenuTree(ttk.Frame):
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
        self._item_to_node: dict[int, str] = {}  # id(ItemDef) -> tree node id
        self._suppress_select = False

        # Treeview
        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, menu_file: MenuFile, current_menu_index: int = 0, selected_item: ItemDef | None = None):
        """Rebuild the tree from the menu file."""
        self._suppress_select = True
        self.menu_file = menu_file
        self._node_to_menu_index.clear()
        self._node_to_item.clear()
        self._item_to_node.clear()

        # Clear tree
        for child in self.tree.get_children():
            self.tree.delete(child)

        if not menu_file or not menu_file.menu_defs:
            self._suppress_select = False
            return

        # Build tree
        for i, menu in enumerate(menu_file.menu_defs):
            menu_label = f"menuDef: {menu.name or '(unnamed)'}"
            menu_node = self.tree.insert("", tk.END, text=menu_label, open=(i == current_menu_index))
            self._node_to_menu_index[menu_node] = i

            for item in menu.items:
                type_name = _TYPE_NAMES.get(item.type, "")
                item_label = item.name or "(unnamed)"
                if type_name:
                    item_label += f"  [{type_name}]"
                item_node = self.tree.insert(menu_node, tk.END, text=item_label)
                self._node_to_item[item_node] = item
                self._item_to_node[id(item)] = item_node

        # Restore selection
        if selected_item is not None:
            self.select_item(selected_item)
        elif current_menu_index < len(menu_file.menu_defs):
            # Select the menu node
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

        # Check if it's a menu node
        if node in self._node_to_menu_index:
            idx = self._node_to_menu_index[node]
            if self.on_select_menu:
                self.on_select_menu(idx)
            return

        # Check if it's an item node
        if node in self._node_to_item:
            item = self._node_to_item[node]
            if self.on_select_item:
                self.on_select_item(item)
