"""Live .menu code preview panel with item highlighting."""

from __future__ import annotations

import re
import tkinter as tk
from tkinter.ttk import *  # noqa: F403

from menu_builder.models import ItemDef

# Highlight color — subtle, won't clash with dark background
HIGHLIGHT_BG = "#2a3a4a"


class CodePreview(Frame):
    """Read-only text widget showing the serialized .menu output."""

    def __init__(self, parent):
        super().__init__(parent)

        # tk.Text — no ttk equivalent
        self.text = tk.Text(
            self,
            wrap=tk.NONE,
            font=("Courier", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#d4d4d4",
            selectbackground="#264f78",
            state=tk.DISABLED,
            padx=8,
            pady=4,
        )
        yscroll = Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        xscroll = Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Highlight tag
        self.text.tag_configure("highlight", background=HIGHLIGHT_BG)

        self._content = ""

    def set_text(self, content: str):
        """Replace the preview content."""
        self._content = content
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.configure(state=tk.DISABLED)

    def highlight_item(self, item: ItemDef | None):
        """Scroll to and highlight the itemDef block for the given item."""
        # Clear previous highlight
        self.text.tag_remove("highlight", "1.0", tk.END)

        if item is None or not item.name:
            return

        # Find the itemDef block containing this item's name
        start_line, end_line = self._find_item_block(item.name)
        if start_line is None:
            return

        # Apply highlight
        self.text.tag_add("highlight", f"{start_line}.0", f"{end_line + 1}.0")

        # Scroll to show the item (place it near the top)
        self.text.see(f"{start_line}.0")

    def _find_item_block(self, name: str) -> tuple[int | None, int | None]:
        """Find the line range of the itemDef block with the given name.

        Returns (start_line, end_line) as 1-based line numbers, or (None, None).
        """
        lines = self._content.split("\n")
        # Find the name property line
        name_pattern = re.compile(rf'^\s*name\s+"{re.escape(name)}"\s*$')
        name_line = None
        for i, line in enumerate(lines):
            if name_pattern.match(line):
                name_line = i
                break

        if name_line is None:
            return None, None

        # Walk backwards to find the "itemDef" opening
        start = name_line
        for i in range(name_line - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped == "{":
                continue
            if stripped.lower() == "itemdef":
                start = i
                break
            if stripped and not stripped.startswith("//"):
                break

        # Walk forward to find the matching closing brace
        depth = 0
        end = name_line
        for i in range(start, len(lines)):
            depth += lines[i].count("{") - lines[i].count("}")
            if depth <= 0 and i > start:
                end = i
                break

        # 1-based for tk.Text
        return start + 1, end + 1
