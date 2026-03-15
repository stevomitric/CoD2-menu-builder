"""Live .menu code preview panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class CodePreview(ttk.Frame):
    """Read-only text widget showing the serialized .menu output."""

    def __init__(self, parent):
        super().__init__(parent)

        # Text widget with scrollbar
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
        yscroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        xscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def set_text(self, content: str):
        """Replace the preview content."""
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.configure(state=tk.DISABLED)
