"""Properties panel — edit selected item or menu properties."""

from __future__ import annotations

import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from typing import Callable

from menu_builder.models import Color, ItemDef, MenuDef, Rect


# Item type options for dropdown
ITEM_TYPES = [
    (0, "TEXT"),
    (1, "BUTTON"),
    (4, "EDITFIELD"),
    (6, "LISTBOX"),
    (9, "NUMERICFIELD"),
    (10, "SLIDER"),
    (11, "YESNO"),
    (12, "MULTI"),
    (13, "DVARENUM"),
    (14, "BIND"),
    (17, "DECIMALFIELD"),
]

WINDOW_STYLES = [
    (0, "EMPTY"),
    (1, "FILLED"),
    (3, "SHADER"),
    (6, "DVAR_SHADER"),
]

TEXT_ALIGNS = [
    (0, "LEFT"),
    (1, "CENTER"),
    (2, "RIGHT"),
]

TEXT_STYLES = [
    (0, "NORMAL"),
    (3, "SHADOWED"),
    (6, "SHADOWEDMORE"),
]


class PropertiesPanel(Frame):
    """Editable properties for the selected item or menu."""

    def __init__(self, parent, on_property_changed: Callable[[], None] | None = None):
        super().__init__(parent)
        self.on_property_changed = on_property_changed
        self.item: ItemDef | None = None
        self.menu: MenuDef | None = None
        self._suppress_events = False

        # Scrollable frame — tk.Canvas needed (no ttk equivalent)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_frame = Frame(canvas)
        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))

        self._vars: dict[str, tk.Variable] = {}
        self._widgets: list[tk.Widget] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, item: ItemDef | None, menu: MenuDef | None):
        self.item = item
        self.menu = menu
        self._rebuild()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _rebuild(self):
        self._suppress_events = True
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()
        self._vars.clear()

        if self.item is not None:
            self._build_item_props()
        elif self.menu is not None:
            self._build_menu_props()

        self._suppress_events = False

    def _add_section(self, title: str):
        lbl = Label(self.scroll_frame, text=title, font=("TkDefaultFont", 10, "bold"))
        lbl.pack(fill=tk.X, padx=5, pady=(10, 2))
        self._widgets.append(lbl)
        sep = Separator(self.scroll_frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=5, pady=2)
        self._widgets.append(sep)

    def _add_entry(self, label: str, key: str, value: str) -> tk.StringVar:
        frame = Frame(self.scroll_frame)
        frame.pack(fill=tk.X, padx=5, pady=1)
        self._widgets.append(frame)

        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=value)
        Entry(frame, textvariable=var, width=20).pack(side=tk.LEFT, fill=tk.X, expand=True)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_checkbox(self, label: str, key: str, value: bool) -> tk.BooleanVar:
        frame = Frame(self.scroll_frame)
        frame.pack(fill=tk.X, padx=5, pady=1)
        self._widgets.append(frame)

        var = tk.BooleanVar(value=value)
        Checkbutton(frame, text=label, variable=var).pack(side=tk.LEFT)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_combo(self, label: str, key: str, options: list[tuple[int, str]], current: int | None) -> tk.StringVar:
        frame = Frame(self.scroll_frame)
        frame.pack(fill=tk.X, padx=5, pady=1)
        self._widgets.append(frame)

        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        display_values = [name for _, name in options]
        var = tk.StringVar()
        for val, name in options:
            if val == current:
                var.set(name)
                break
        Combobox(frame, textvariable=var, values=display_values, state="readonly", width=17).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_color(self, label: str, key: str, color: Color | None) -> tuple[tk.StringVar, ...]:
        frame = Frame(self.scroll_frame)
        frame.pack(fill=tk.X, padx=5, pady=1)
        self._widgets.append(frame)

        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        c = color or Color(0, 0, 0, 0)
        vars_ = []
        for comp, val in [("R", c.r), ("G", c.g), ("B", c.b), ("A", c.a)]:
            v = tk.StringVar(value=f"{val:.2f}")
            Entry(frame, textvariable=v, width=5).pack(side=tk.LEFT, padx=1)
            v.trace_add("write", lambda *_: self._on_change())
            k = f"{key}_{comp.lower()}"
            self._vars[k] = v
            vars_.append(v)
        return tuple(vars_)

    # ------------------------------------------------------------------
    # Item properties
    # ------------------------------------------------------------------

    def _build_item_props(self):
        item = self.item

        self._add_section("Identity")
        self._add_entry("Name", "name", item.name)
        self._add_combo("Type", "type", ITEM_TYPES, item.type)
        self._add_entry("Group", "group", item.group or "")

        self._add_section("Position & Size")
        self._add_entry("X", "rect_x", str(int(item.rect.x)))
        self._add_entry("Y", "rect_y", str(int(item.rect.y)))
        self._add_entry("W", "rect_w", str(int(item.rect.w)))
        self._add_entry("H", "rect_h", str(int(item.rect.h)))

        self._add_section("Text")
        self._add_entry("Text", "text", item.text or "")
        self._add_entry("Scale", "textscale", str(item.textscale) if item.textscale is not None else "")
        self._add_combo("Align", "textalign", TEXT_ALIGNS, item.textalign)
        self._add_entry("Align X", "textalignx", str(item.textalignx) if item.textalignx is not None else "")
        self._add_entry("Align Y", "textaligny", str(item.textaligny) if item.textaligny is not None else "")
        self._add_combo("Style", "textstyle", TEXT_STYLES, item.textstyle)

        self._add_section("Appearance")
        self._add_combo("Win Style", "style", WINDOW_STYLES, item.style)
        self._add_color("Forecolor", "forecolor", item.forecolor)
        self._add_color("Backcolor", "backcolor", item.backcolor)
        self._add_color("Border", "bordercolor", item.bordercolor)
        self._add_entry("Background", "background", item.background or "")

        self._add_section("Flags")
        self._add_checkbox("Visible", "visible", item.visible)
        self._add_checkbox("Decoration", "decoration", item.decoration)
        self._add_checkbox("Autowrapped", "autowrapped", item.autowrapped)

        self._add_section("Behavior")
        self._add_entry("Dvar", "dvar", item.dvar or "")
        self._add_entry("Dvar Test", "dvar_test", item.dvar_test or "")
        self._add_entry("Show Dvar", "show_dvar", "; ".join(item.show_dvar) if item.show_dvar else "")
        self._add_entry("Hide Dvar", "hide_dvar", "; ".join(item.hide_dvar) if item.hide_dvar else "")

        self._add_section("Events")
        self._add_entry("Action", "action", item.action or "")
        self._add_entry("On Focus", "on_focus", item.on_focus or "")
        self._add_entry("Mouse Enter", "mouse_enter", item.mouse_enter or "")
        self._add_entry("Mouse Exit", "mouse_exit", item.mouse_exit or "")

    # ------------------------------------------------------------------
    # Menu properties
    # ------------------------------------------------------------------

    def _build_menu_props(self):
        menu = self.menu

        self._add_section("Menu Properties")
        self._add_entry("Name", "menu_name", menu.name)
        self._add_entry("Rect X", "menu_rect_x", str(int(menu.rect.x)))
        self._add_entry("Rect Y", "menu_rect_y", str(int(menu.rect.y)))
        self._add_entry("Rect W", "menu_rect_w", str(int(menu.rect.w)))
        self._add_entry("Rect H", "menu_rect_h", str(int(menu.rect.h)))

        self._add_section("Appearance")
        self._add_color("Focus Color", "menu_focuscolor", menu.focuscolor)
        self._add_color("Forecolor", "menu_forecolor", menu.forecolor)
        self._add_color("Backcolor", "menu_backcolor", menu.backcolor)
        self._add_entry("Blur World", "menu_blur_world", str(menu.blur_world) if menu.blur_world is not None else "")
        self._add_entry("Sound Loop", "menu_sound_loop", menu.sound_loop or "")

        self._add_section("Flags")
        self._add_checkbox("Visible", "menu_visible", menu.visible)
        self._add_checkbox("Fullscreen", "menu_fullscreen", menu.fullscreen)
        self._add_checkbox("Popup", "menu_popup", menu.popup)

        self._add_section("Events")
        self._add_entry("On Open", "menu_on_open", menu.on_open or "")
        self._add_entry("On Close", "menu_on_close", menu.on_close or "")
        self._add_entry("On ESC", "menu_on_esc", menu.on_esc or "")

    # ------------------------------------------------------------------
    # Apply changes
    # ------------------------------------------------------------------

    def _on_change(self):
        if self._suppress_events:
            return
        if self.item is not None:
            self._apply_item_changes()
        elif self.menu is not None:
            self._apply_menu_changes()
        if self.on_property_changed:
            self.on_property_changed()

    def _get_str(self, key: str) -> str:
        var = self._vars.get(key)
        return var.get() if var else ""

    def _get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(float(self._get_str(key)))
        except (ValueError, TypeError):
            return default

    def _get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self._get_str(key))
        except (ValueError, TypeError):
            return default

    def _get_float_or_none(self, key: str) -> float | None:
        s = self._get_str(key)
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    def _get_bool(self, key: str) -> bool:
        var = self._vars.get(key)
        return var.get() if var else False

    def _get_color(self, key: str) -> Color | None:
        r = self._get_float_or_none(f"{key}_r")
        if r is None:
            return None
        return Color(
            r=r,
            g=self._get_float(f"{key}_g"),
            b=self._get_float(f"{key}_b"),
            a=self._get_float(f"{key}_a", 1.0),
        )

    def _get_combo_int(self, key: str, options: list[tuple[int, str]]) -> int | None:
        display = self._get_str(key)
        for val, name in options:
            if name == display:
                return val
        return None

    def _get_str_or_none(self, key: str) -> str | None:
        s = self._get_str(key)
        return s if s else None

    def _apply_item_changes(self):
        item = self.item
        item.name = self._get_str("name")
        item.type = self._get_combo_int("type", ITEM_TYPES)
        item.group = self._get_str_or_none("group")

        item.rect.x = self._get_float("rect_x")
        item.rect.y = self._get_float("rect_y")
        item.rect.w = self._get_float("rect_w")
        item.rect.h = self._get_float("rect_h")

        item.text = self._get_str_or_none("text")
        item.textscale = self._get_float_or_none("textscale")
        item.textalign = self._get_combo_int("textalign", TEXT_ALIGNS)
        item.textalignx = self._get_int("textalignx") if self._get_str("textalignx") else None
        item.textaligny = self._get_int("textaligny") if self._get_str("textaligny") else None
        item.textstyle = self._get_combo_int("textstyle", TEXT_STYLES)

        item.style = self._get_combo_int("style", WINDOW_STYLES)
        item.forecolor = self._get_color("forecolor")
        item.backcolor = self._get_color("backcolor")
        item.bordercolor = self._get_color("bordercolor")
        item.background = self._get_str_or_none("background")

        item.visible = self._get_bool("visible")
        item.decoration = self._get_bool("decoration")
        item.autowrapped = self._get_bool("autowrapped")

        item.dvar = self._get_str_or_none("dvar")
        item.dvar_test = self._get_str_or_none("dvar_test")
        show = self._get_str("show_dvar")
        item.show_dvar = [v.strip().strip('"') for v in show.split(";")] if show.strip() else []
        hide = self._get_str("hide_dvar")
        item.hide_dvar = [v.strip().strip('"') for v in hide.split(";")] if hide.strip() else []

        item.action = self._get_str_or_none("action")
        item.on_focus = self._get_str_or_none("on_focus")
        item.mouse_enter = self._get_str_or_none("mouse_enter")
        item.mouse_exit = self._get_str_or_none("mouse_exit")

    def _apply_menu_changes(self):
        menu = self.menu
        menu.name = self._get_str("menu_name")
        menu.rect.x = self._get_float("menu_rect_x")
        menu.rect.y = self._get_float("menu_rect_y")
        menu.rect.w = self._get_float("menu_rect_w")
        menu.rect.h = self._get_float("menu_rect_h")

        menu.focuscolor = self._get_color("menu_focuscolor")
        menu.forecolor = self._get_color("menu_forecolor")
        menu.backcolor = self._get_color("menu_backcolor")
        blur = self._get_str("menu_blur_world")
        menu.blur_world = float(blur) if blur else None
        menu.sound_loop = self._get_str_or_none("menu_sound_loop")

        menu.visible = self._get_bool("menu_visible")
        menu.fullscreen = self._get_bool("menu_fullscreen")
        menu.popup = self._get_bool("menu_popup")

        menu.on_open = self._get_str_or_none("menu_on_open")
        menu.on_close = self._get_str_or_none("menu_on_close")
        menu.on_esc = self._get_str_or_none("menu_on_esc")
