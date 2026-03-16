"""Visual editor canvas — 640x480 coordinate space with drag/resize."""

from __future__ import annotations

import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from typing import Callable

from menu_builder.models import ItemDef, MenuDef, Color

# Canvas draws at 1:1 with the game's 640x480 coordinate space.
CANVAS_W = 640
CANVAS_H = 480
GRID_SIZE = 10

# Visual constants
SELECT_COLOR = "#FFD700"
HANDLE_SIZE = 6
MIN_ITEM_SIZE = 10

# Blueprint color palette
BP_BG = "#1a3a5c"          # deep blueprint blue (canvas surround)
BP_AREA_BG = "#1e4470"     # slightly lighter (640x480 area)
BP_GRID_FINE = "#25537f"   # fine grid lines (every 10px)
BP_GRID_MAJOR = "#3a6a9a"  # major grid lines (every 50px)
BP_BORDER = "#4a88bb"      # 640x480 border

# Item type display config: (label_prefix, default_outline_color)
_TYPE_STYLES: dict[int | None, tuple[str, str]] = {
    0:  ("T",  "#6688AA"),   # TEXT
    1:  ("B",  "#88AA66"),   # BUTTON
    4:  ("E",  "#AA8866"),   # EDITFIELD
    6:  ("L",  "#8866AA"),   # LISTBOX
    9:  ("N",  "#AA6688"),   # NUMERICFIELD
    10: ("S",  "#66AA88"),   # SLIDER
    11: ("Y",  "#AAAA66"),   # YESNO
    12: ("M",  "#66AAAA"),   # MULTI
    14: ("K",  "#AA66AA"),   # BIND
    None: ("?", "#666666"),
}

# Item types for the Add Item context menu
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


def _color_to_hex(c: Color | None, fallback: str = "#333333") -> str:
    """Convert a Color to a Tk hex string."""
    if c is None:
        return fallback
    r = max(0, min(255, int(c.r * 255)))
    g = max(0, min(255, int(c.g * 255)))
    b = max(0, min(255, int(c.b * 255)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _text_color_for_bg(c: Color | None) -> str:
    """Pick white or black text depending on background brightness."""
    if c is None:
        return "#FFFFFF"
    lum = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b
    return "#000000" if lum > 0.5 else "#FFFFFF"


class MenuCanvas(Frame):
    """Canvas-based visual editor for menu items."""

    def __init__(
        self,
        parent,
        on_select: Callable[[ItemDef | None], None] | None = None,
        on_item_moved: Callable[[ItemDef, float, float], None] | None = None,
        on_item_resized: Callable[[ItemDef, float, float], None] | None = None,
        on_request_add: Callable[[int], None] | None = None,
        on_request_delete: Callable[[], None] | None = None,
        on_request_duplicate: Callable[[], None] | None = None,
        on_request_bring_front: Callable[[], None] | None = None,
        on_request_send_back: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.on_select = on_select
        self.on_item_moved = on_item_moved
        self.on_item_resized = on_item_resized
        self.on_request_add = on_request_add
        self.on_request_delete = on_request_delete
        self.on_request_duplicate = on_request_duplicate
        self.on_request_bring_front = on_request_bring_front
        self.on_request_send_back = on_request_send_back

        self.menu: MenuDef | None = None
        self.selected_item: ItemDef | None = None
        self._item_ids: dict[int, ItemDef] = {}  # canvas id -> ItemDef
        self._drag_data: dict = {}
        self._resize_data: dict = {}

        # tk.Canvas has no ttk equivalent
        self.canvas = tk.Canvas(
            self,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=BP_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Configure>", self._on_configure)

        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, menu: MenuDef | None, selected: ItemDef | None = None):
        self.menu = menu
        self.selected_item = selected
        self._redraw()

    def select_item(self, item: ItemDef | None):
        self.selected_item = item
        self._redraw()

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

    def _to_menu(self, sx: float, sy: float) -> tuple[float, float]:
        return (sx - self._offset_x) / self._scale, (sy - self._offset_y) / self._scale

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _redraw(self):
        self.canvas.delete("all")
        self._item_ids.clear()
        self._calc_transform()

        # Draw 640x480 blueprint area
        x0, y0 = self._to_screen(0, 0)
        x1, y1 = self._to_screen(CANVAS_W, CANVAS_H)
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=BP_AREA_BG, outline=BP_BORDER, width=2)

        self._draw_grid()

        if self.menu is None:
            return

        # Draw items (first = lowest z-order)
        for item in self.menu.items:
            self._draw_item(item)

        # Selection handles on top
        if self.selected_item is not None:
            self._draw_selection(self.selected_item)

    def _draw_grid(self):
        # Fine grid (every GRID_SIZE pixels)
        for gx in range(0, CANVAS_W + 1, GRID_SIZE):
            sx0, sy0 = self._to_screen(gx, 0)
            sx1, sy1 = self._to_screen(gx, CANVAS_H)
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill=BP_GRID_FINE, width=1)
        for gy in range(0, CANVAS_H + 1, GRID_SIZE):
            sx0, sy0 = self._to_screen(0, gy)
            sx1, sy1 = self._to_screen(CANVAS_W, gy)
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill=BP_GRID_FINE, width=1)

        # Major grid (every 50px) — brighter lines
        for gx in range(0, CANVAS_W + 1, GRID_SIZE * 5):
            sx0, sy0 = self._to_screen(gx, 0)
            sx1, sy1 = self._to_screen(gx, CANVAS_H)
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill=BP_GRID_MAJOR, width=1)
        for gy in range(0, CANVAS_H + 1, GRID_SIZE * 5):
            sx0, sy0 = self._to_screen(0, gy)
            sx1, sy1 = self._to_screen(CANVAS_W, gy)
            self.canvas.create_line(sx0, sy0, sx1, sy1, fill=BP_GRID_MAJOR, width=1)

    def _draw_item(self, item: ItemDef):
        r = item.rect
        x0, y0 = self._to_screen(r.x, r.y)
        x1, y1 = self._to_screen(r.x + r.w, r.y + r.h)
        hidden = not item.visible

        type_style = _TYPE_STYLES.get(item.type, _TYPE_STYLES[None])
        type_badge, type_outline = type_style

        fill = _color_to_hex(item.backcolor, "#333333")
        outline = _color_to_hex(item.bordercolor, type_outline)

        # Hidden items: dashed outline, stippled fill, dimmed colors
        is_filled = item.style == 1 or item.backcolor is not None
        if hidden:
            rect_id = self.canvas.create_rectangle(
                x0, y0, x1, y1, fill=fill if is_filled else "",
                outline="#556677", dash=(4, 4), stipple="gray25" if is_filled else "",
            )
        elif is_filled:
            rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline)
        else:
            rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill="", outline="#7ab0d4", dash=(3, 2))

        self._item_ids[rect_id] = item

        # Decoration indicator
        if item.decoration:
            self.canvas.create_line(x0, y0, x0 + 8 * self._scale, y0, fill="#888888", width=2)

        # Type badge (top-left)
        badge_color = "#556677" if hidden else type_outline
        self.canvas.create_text(
            x0 + 3, y0 + 2, text=type_badge, fill=badge_color,
            font=("TkDefaultFont", max(6, int(7 * self._scale)), "bold"),
            anchor=tk.NW,
        )

        # Hidden indicator (top-right)
        if hidden:
            self.canvas.create_text(
                x1 - 3, y0 + 2, text="H", fill="#886644",
                font=("TkDefaultFont", max(6, int(7 * self._scale)), "bold"),
                anchor=tk.NE,
            )

        # Text label
        if item.text or item.name:
            label = item.text or item.name
            if label.startswith("@"):
                label = label[1:]
            tc = "#556677" if hidden else _color_to_hex(item.forecolor, _text_color_for_bg(item.backcolor))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            font_size = max(8, int(10 * self._scale))
            text_id = self.canvas.create_text(
                cx, cy, text=label, fill=tc,
                font=("TkDefaultFont", font_size),
                anchor=tk.CENTER,
            )
            self._item_ids[text_id] = item

    def _draw_selection(self, item: ItemDef):
        r = item.rect
        x0, y0 = self._to_screen(r.x, r.y)
        x1, y1 = self._to_screen(r.x + r.w, r.y + r.h)

        self.canvas.create_rectangle(
            x0 - 1, y0 - 1, x1 + 1, y1 + 1,
            outline=SELECT_COLOR, width=2,
        )

        # Resize handle (bottom-right)
        hs = HANDLE_SIZE
        self.canvas.create_rectangle(
            x1 - hs, y1 - hs, x1 + hs, y1 + hs,
            fill=SELECT_COLOR, outline=SELECT_COLOR, tags="resize_handle",
        )

        # Position info
        info = f"({int(r.x)}, {int(r.y)}) {int(r.w)}x{int(r.h)}"
        self.canvas.create_text(
            x0, y0 - 4, text=info, fill=SELECT_COLOR,
            font=("TkDefaultFont", max(7, int(8 * self._scale))),
            anchor=tk.SW,
        )

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _hit_test(self, sx: float, sy: float) -> ItemDef | None:
        """Find the top-most item whose bounding box contains (sx, sy)."""
        if self.menu is None:
            return None
        # Walk items in reverse (last drawn = top-most)
        for item in reversed(self.menu.items):
            r = item.rect
            x0, y0 = self._to_screen(r.x, r.y)
            x1, y1 = self._to_screen(r.x + r.w, r.y + r.h)
            if x0 <= sx <= x1 and y0 <= sy <= y1:
                return item
        return None

    def _on_configure(self, event):
        self._redraw()

    def _on_click(self, event):
        self._drag_data.clear()
        self._resize_data.clear()

        sx, sy = event.x, event.y

        # Check resize handle
        if self.selected_item is not None:
            r = self.selected_item.rect
            hx, hy = self._to_screen(r.x + r.w, r.y + r.h)
            if abs(sx - hx) <= HANDLE_SIZE + 2 and abs(sy - hy) <= HANDLE_SIZE + 2:
                self._resize_data = {
                    "item": self.selected_item,
                    "start_sx": sx,
                    "start_sy": sy,
                    "orig_w": r.w,
                    "orig_h": r.h,
                }
                return

        # Find clicked item by bounding box (top-most = last in list)
        item = self._hit_test(sx, sy)

        self.selected_item = item
        if self.on_select:
            self.on_select(item)

        if item is not None:
            mx, my = self._to_menu(sx, sy)
            self._drag_data = {
                "item": item,
                "offset_x": mx - item.rect.x,
                "offset_y": my - item.rect.y,
            }

        self._redraw()

    def _on_drag(self, event):
        sx, sy = event.x, event.y

        if self._resize_data:
            item = self._resize_data["item"]
            dx = (sx - self._resize_data["start_sx"]) / self._scale
            dy = (sy - self._resize_data["start_sy"]) / self._scale
            new_w = max(MIN_ITEM_SIZE, self._resize_data["orig_w"] + dx)
            new_h = max(MIN_ITEM_SIZE, self._resize_data["orig_h"] + dy)
            new_w = round(new_w / GRID_SIZE) * GRID_SIZE
            new_h = round(new_h / GRID_SIZE) * GRID_SIZE
            item.rect.w = new_w
            item.rect.h = new_h
            self._redraw()
            return

        if self._drag_data:
            item = self._drag_data["item"]
            mx, my = self._to_menu(sx, sy)
            new_x = mx - self._drag_data["offset_x"]
            new_y = my - self._drag_data["offset_y"]
            new_x = round(new_x / GRID_SIZE) * GRID_SIZE
            new_y = round(new_y / GRID_SIZE) * GRID_SIZE
            item.rect.x = new_x
            item.rect.y = new_y
            self._redraw()

    def _on_release(self, event):
        if self._resize_data:
            item = self._resize_data["item"]
            if self.on_item_resized:
                self.on_item_resized(item, item.rect.w, item.rect.h)
            self._resize_data.clear()
        elif self._drag_data:
            item = self._drag_data["item"]
            if self.on_item_moved:
                self.on_item_moved(item, item.rect.x, item.rect.y)
            self._drag_data.clear()

    def _on_right_click(self, event):
        """Show context menu on right-click."""
        item = self._hit_test(event.x, event.y)

        if item is not None and item != self.selected_item:
            self.selected_item = item
            if self.on_select:
                self.on_select(item)
            self._redraw()

        # tk.Menu — no ttk equivalent
        ctx = tk.Menu(self, tearoff=0)

        # Add Item submenu
        add_menu = tk.Menu(ctx, tearoff=0)
        ctx.add_cascade(label="Add Item", menu=add_menu)
        for type_id, type_name in _ADD_ITEM_TYPES:
            add_menu.add_command(
                label=type_name,
                command=lambda t=type_id: self._ctx_add(t),
            )

        if self.selected_item is not None:
            ctx.add_command(label="Duplicate", command=self._ctx_duplicate)
            ctx.add_separator()
            ctx.add_command(label="Bring to Front", command=self._ctx_bring_front)
            ctx.add_command(label="Send to Back", command=self._ctx_send_back)
            ctx.add_separator()
            ctx.add_command(label="Delete", command=self._ctx_delete)
        ctx.tk_popup(event.x_root, event.y_root)

    def _ctx_add(self, item_type: int = 1):
        if self.on_request_add:
            self.on_request_add(item_type)

    def _ctx_delete(self):
        if self.on_request_delete:
            self.on_request_delete()

    def _ctx_duplicate(self):
        if self.on_request_duplicate:
            self.on_request_duplicate()

    def _ctx_bring_front(self):
        if self.on_request_bring_front:
            self.on_request_bring_front()

    def _ctx_send_back(self):
        if self.on_request_send_back:
            self.on_request_send_back()
