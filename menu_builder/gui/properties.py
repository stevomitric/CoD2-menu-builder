"""Properties panel — edit selected item or menu properties via tabbed notebook."""

from __future__ import annotations

import tkinter as tk
from tkinter.ttk import *  # noqa: F403
from typing import Callable

from pathlib import Path

from menu_builder.models import Color, ItemDef, MenuDef, Rect


# Item type options
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

_TYPE_DISPLAY = {t: n for t, n in ITEM_TYPES}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Available font constants for the font selector
_FONT_OPTIONS = [
    "UI_FONT_DEFAULT",
    "UI_FONT_NORMAL",
    "UI_FONT_BIG",
    "UI_FONT_SMALL",
    "UI_FONT_BOLD",
    "UI_FONT_CONSOLE",
]

# Map constants to font file names (for metrics/rendering)
_FONT_CONSTANTS = {
    "UI_FONT_DEFAULT": "smallFont",
    "UI_FONT_NORMAL": "normalFont",
    "UI_FONT_BIG": "bigFont",
    "UI_FONT_SMALL": "smallFont",
    "UI_FONT_BOLD": "boldFont",
    "UI_FONT_CONSOLE": "consoleFont",
}


_IMAGES_DIR = _PROJECT_ROOT / "images"


def _list_available_images() -> list[str]:
    """List image names from the images/ directory (without extension)."""
    images = ["(none)"]
    if _IMAGES_DIR.is_dir():
        for f in sorted(_IMAGES_DIR.iterdir()):
            if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg") and not f.name.startswith("."):
                images.append(f.stem)
    return images


def _textfont_to_display(textfont: str | None) -> str:
    """Convert a textfont value to its display name."""
    if not textfont:
        return "UI_FONT_NORMAL"
    if textfont in _FONT_OPTIONS:
        return textfont
    return "UI_FONT_NORMAL"


def _display_to_textfont(display: str) -> str | None:
    """Convert a display name back to a textfont value."""
    if display in _FONT_OPTIONS:
        return display
    return None


def _type_display_name(type_id: int | None) -> str:
    if type_id is None:
        return "(none)"
    return _TYPE_DISPLAY.get(type_id, str(type_id))


class PropertiesPanel(Frame):
    """Tabbed properties editor for items and menus."""

    def __init__(self, parent, on_property_changed: Callable[[], None] | None = None):
        super().__init__(parent)
        self.on_property_changed = on_property_changed
        self.item: ItemDef | None = None
        self.menu: MenuDef | None = None
        self._suppress_events = False
        self._vars: dict[str, tk.Variable] = {}

        # Notebook fills the panel
        self.notebook = Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Placeholder shown when nothing is selected
        self._empty_label = Label(self, text="Select an item or menu", foreground="#999999", anchor=tk.CENTER)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, item: ItemDef | None, menu: MenuDef | None):
        """Full rebuild — call when the selected item/menu changes."""
        self.item = item
        self.menu = menu
        self._rebuild()

    def sync_from_model(self):
        """Update displayed values from the current model without rebuilding.

        Call this when the model changed externally (drag, resize) but the
        same item is still selected — avoids tab flicker.
        """
        self._suppress_events = True
        if self.item is not None:
            self._sync_item_values()
        elif self.menu is not None:
            self._sync_menu_values()
        self._suppress_events = False

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _rebuild(self):
        self._suppress_events = True
        self._vars.clear()

        # Clear all tabs
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)

        if self.item is not None:
            self._empty_label.pack_forget()
            self.notebook.pack(fill=tk.BOTH, expand=True)
            self._build_item_props()
        elif self.menu is not None:
            self._empty_label.pack_forget()
            self.notebook.pack(fill=tk.BOTH, expand=True)
            self._build_menu_props()
        else:
            self.notebook.pack_forget()
            self._empty_label.pack(fill=tk.BOTH, expand=True)

        self._suppress_events = False

    def _make_tab(self, title: str) -> Frame:
        """Create a tab and return its content frame."""
        frame = Frame(self.notebook, padding=4)
        self.notebook.add(frame, text=f"  {title}  ")
        return frame

    # ------------------------------------------------------------------
    # Widget helpers — all take a parent frame
    # ------------------------------------------------------------------

    def _add_section(self, parent: Frame, title: str):
        Label(parent, text=title, font=("TkDefaultFont", 9, "bold")).pack(
            fill=tk.X, padx=5, pady=(8, 2)
        )
        Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

    def _add_readonly(self, parent: Frame, label: str, value: str):
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        Label(frame, text=value, foreground="#666666").pack(side=tk.LEFT)

    def _add_entry(self, parent: Frame, label: str, key: str, value: str) -> tk.StringVar:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=value)
        Entry(frame, textvariable=var, width=20).pack(side=tk.LEFT, fill=tk.X, expand=True)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_checkbox(self, parent: Frame, label: str, key: str, value: bool) -> tk.BooleanVar:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        var = tk.BooleanVar(value=value)
        Checkbutton(frame, text=label, variable=var).pack(side=tk.LEFT)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_combo(self, parent: Frame, label: str, key: str, options: list[tuple[int, str]], current: int | None) -> tk.StringVar:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
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

    def _add_entry_disabled(self, parent: Frame, label: str, value: str):
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=value)
        Entry(frame, textvariable=var, width=20, state="disabled").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _add_spinbox(self, parent: Frame, label: str, key: str, value: int, from_: int, to: int) -> tk.StringVar:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=str(value))
        Spinbox(frame, textvariable=var, from_=from_, to=to, width=5).pack(side=tk.LEFT)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_image_combo(self, parent: Frame, label: str, key: str, current: str | None):
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        images = _list_available_images()
        display = current if current and current in images else "(none)"
        var = tk.StringVar(value=display)
        Combobox(frame, textvariable=var, values=images, state="readonly", width=20).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var

    def _add_font_combo(self, parent: Frame, label: str, key: str, current: str | None):
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=_textfont_to_display(current))
        Combobox(frame, textvariable=var, values=_FONT_OPTIONS, state="readonly", width=20).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var

    def _add_decimal_spinbox(self, parent: Frame, label: str, key: str, value: float, from_: float, to: float, increment: float) -> tk.StringVar:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        var = tk.StringVar(value=f"{value:.2f}")
        Spinbox(frame, textvariable=var, from_=from_, to=to, increment=increment, width=7, format="%.2f").pack(side=tk.LEFT)
        var.trace_add("write", lambda *_: self._on_change())
        self._vars[key] = var
        return var

    def _add_color(self, parent: Frame, label: str, key: str, color: Color | None, default_alpha: float = 0.0) -> tuple[tk.StringVar, ...]:
        frame = Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=1)
        Label(frame, text=label, width=12).pack(side=tk.LEFT)
        c = color or Color(0, 0, 0, default_alpha)
        vars_ = []
        for comp, val in [("R", c.r), ("G", c.g), ("B", c.b), ("A", c.a)]:
            v = tk.StringVar(value=f"{val:.2f}")
            Entry(frame, textvariable=v, width=5).pack(side=tk.LEFT, padx=1)
            v.trace_add("write", lambda *_: self._on_change())
            self._vars[f"{key}_{comp.lower()}"] = v
            vars_.append(v)
        return tuple(vars_)

    # ------------------------------------------------------------------
    # Item properties — 4 tabs
    # ------------------------------------------------------------------

    def _build_item_props(self):
        item = self.item

        # --- General ---
        tab = self._make_tab("General")

        self._add_section(tab, "Identity")
        self._add_entry(tab, "Name", "name", item.name)
        self._add_readonly(tab, "Type", _type_display_name(item.type))
        self._add_entry(tab, "Group", "group", item.group or "")

        self._add_section(tab, "Position & Size")
        self._add_entry(tab, "X", "rect_x", str(int(item.rect.x)))
        self._add_entry(tab, "Y", "rect_y", str(int(item.rect.y)))
        self._add_entry(tab, "W", "rect_w", str(int(item.rect.w)))
        self._add_entry(tab, "H", "rect_h", str(int(item.rect.h)))

        self._add_section(tab, "Flags")
        self._add_checkbox(tab, "Visible", "visible", item.visible)
        self._add_checkbox(tab, "Decoration", "decoration", item.decoration)
        self._add_checkbox(tab, "Autowrapped", "autowrapped", item.autowrapped)

        # --- Style ---
        tab = self._make_tab("Style")

        self._add_section(tab, "Window")
        self._add_combo(tab, "Style", "style", WINDOW_STYLES, item.style)
        self._add_image_combo(tab, "Background", "background", item.background)

        self._add_section(tab, "Colors")
        self._add_color(tab, "Forecolor", "forecolor", item.forecolor)
        self._add_color(tab, "Backcolor", "backcolor", item.backcolor, default_alpha=1.0)

        self._add_section(tab, "Border")
        self._add_checkbox(tab, "Border", "border", item.border is not None and item.border > 0)
        self._add_spinbox(tab, "Thickness", "bordersize", item.bordersize or 1, 1, 5)
        self._add_color(tab, "Color", "bordercolor", item.bordercolor, default_alpha=1.0)

        # --- Text ---
        tab = self._make_tab("Text")

        self._add_section(tab, "Content")
        self._add_entry(tab, "Text", "text", item.text or "")

        self._add_section(tab, "Font")
        self._add_font_combo(tab, "Font", "textfont", item.textfont)
        self._add_decimal_spinbox(tab, "Scale", "textscale", item.textscale or 0.25, 0.1, 1.0, 0.05)

        self._add_section(tab, "Alignment")
        self._add_combo(tab, "Align", "textalign", TEXT_ALIGNS, item.textalign)
        self._add_entry(tab, "Align X", "textalignx", str(item.textalignx) if item.textalignx is not None else "")
        self._add_entry(tab, "Align Y", "textaligny", str(item.textaligny) if item.textaligny is not None else "")

        self._add_section(tab, "Rendering")
        self._add_combo(tab, "Text Style", "textstyle", TEXT_STYLES, item.textstyle)

        # --- Events ---
        tab = self._make_tab("Events")

        self._add_section(tab, "Handlers")
        self._add_entry(tab, "Action", "action", item.action or "")
        self._add_entry(tab, "On Focus", "on_focus", item.on_focus or "")
        self._add_entry(tab, "Mouse Enter", "mouse_enter", item.mouse_enter or "")
        self._add_entry(tab, "Mouse Exit", "mouse_exit", item.mouse_exit or "")

        self._add_section(tab, "Dvar Binding")
        self._add_entry(tab, "Dvar", "dvar", item.dvar or "")
        self._add_entry(tab, "Dvar Test", "dvar_test", item.dvar_test or "")
        self._add_entry(tab, "Show Dvar", "show_dvar", "; ".join(item.show_dvar) if item.show_dvar else "")
        self._add_entry(tab, "Hide Dvar", "hide_dvar", "; ".join(item.hide_dvar) if item.hide_dvar else "")

    # ------------------------------------------------------------------
    # Menu properties — 3 tabs
    # ------------------------------------------------------------------

    def _build_menu_props(self):
        menu = self.menu

        # --- General ---
        tab = self._make_tab("General")

        self._add_section(tab, "Identity")
        self._add_entry(tab, "Name", "menu_name", menu.name)

        self._add_section(tab, "Position & Size")
        self._add_entry(tab, "X", "menu_rect_x", str(int(menu.rect.x)))
        self._add_entry(tab, "Y", "menu_rect_y", str(int(menu.rect.y)))
        self._add_entry(tab, "W", "menu_rect_w", str(int(menu.rect.w)))
        self._add_entry(tab, "H", "menu_rect_h", str(int(menu.rect.h)))

        self._add_section(tab, "Flags")
        self._add_checkbox(tab, "Visible", "menu_visible", menu.visible)
        self._add_checkbox(tab, "Fullscreen", "menu_fullscreen", menu.fullscreen)
        self._add_checkbox(tab, "Popup", "menu_popup", menu.popup)

        # --- Style ---
        tab = self._make_tab("Style")

        self._add_section(tab, "Colors")
        self._add_color(tab, "Focus Color", "menu_focuscolor", menu.focuscolor)
        self._add_color(tab, "Forecolor", "menu_forecolor", menu.forecolor)
        self._add_color(tab, "Backcolor", "menu_backcolor", menu.backcolor)

        self._add_section(tab, "Effects")
        self._add_entry(tab, "Blur World", "menu_blur_world", str(menu.blur_world) if menu.blur_world is not None else "")
        self._add_entry(tab, "Sound Loop", "menu_sound_loop", menu.sound_loop or "")

        # --- Events ---
        tab = self._make_tab("Events")

        self._add_section(tab, "Handlers")
        self._add_entry(tab, "On Open", "menu_on_open", menu.on_open or "")
        self._add_entry(tab, "On Close", "menu_on_close", menu.on_close or "")
        self._add_entry(tab, "On ESC", "menu_on_esc", menu.on_esc or "")

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

    def _set_combo_display(self, key: str, options: list[tuple[int, str]], value: int):
        """Set a combo var to the display name for a value, suppressing events."""
        for val, name in options:
            if val == value:
                self._suppress_events = True
                self._set_var(key, name)
                self._suppress_events = False
                return

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
        item.group = self._get_str_or_none("group")

        item.rect.x = self._get_float("rect_x")
        item.rect.y = self._get_float("rect_y")
        item.rect.w = self._get_float("rect_w")
        item.rect.h = self._get_float("rect_h")

        item.visible = self._get_bool("visible")
        item.decoration = self._get_bool("decoration")
        item.autowrapped = self._get_bool("autowrapped")

        item.style = self._get_combo_int("style", WINDOW_STYLES)
        bg = self._get_str("background")
        item.background = bg if bg and bg != "(none)" else None
        # Auto-set style to SHADER when an image is selected
        if item.background and item.style != 3:
            item.style = 3  # WINDOW_STYLE_SHADER
            self._set_combo_display("style", WINDOW_STYLES, 3)
        # Clear background when style is not SHADER
        if item.style != 3 and item.background:
            item.background = None
            self._set_var("background", "(none)")
        item.forecolor = self._get_color("forecolor")
        item.backcolor = self._get_color("backcolor")

        item.border = 1 if self._get_bool("border") else None
        item.bordersize = self._get_int("bordersize", 1)
        item.bordercolor = self._get_color("bordercolor")

        item.text = self._get_str_or_none("text")
        item.textfont = _display_to_textfont(self._get_str("textfont"))
        item.textscale = self._get_float_or_none("textscale")
        item.textalign = self._get_combo_int("textalign", TEXT_ALIGNS)
        item.textalignx = self._get_int("textalignx") if self._get_str("textalignx") else None
        item.textaligny = self._get_int("textaligny") if self._get_str("textaligny") else None
        item.textstyle = self._get_combo_int("textstyle", TEXT_STYLES)

        item.action = self._get_str_or_none("action")
        item.on_focus = self._get_str_or_none("on_focus")
        item.mouse_enter = self._get_str_or_none("mouse_enter")
        item.mouse_exit = self._get_str_or_none("mouse_exit")

        item.dvar = self._get_str_or_none("dvar")
        item.dvar_test = self._get_str_or_none("dvar_test")
        show = self._get_str("show_dvar")
        item.show_dvar = [v.strip().strip('"') for v in show.split(";")] if show.strip() else []
        hide = self._get_str("hide_dvar")
        item.hide_dvar = [v.strip().strip('"') for v in hide.split(";")] if hide.strip() else []

    def _apply_menu_changes(self):
        menu = self.menu
        menu.name = self._get_str("menu_name")
        menu.rect.x = self._get_float("menu_rect_x")
        menu.rect.y = self._get_float("menu_rect_y")
        menu.rect.w = self._get_float("menu_rect_w")
        menu.rect.h = self._get_float("menu_rect_h")

        menu.visible = self._get_bool("menu_visible")
        menu.fullscreen = self._get_bool("menu_fullscreen")
        menu.popup = self._get_bool("menu_popup")

        menu.focuscolor = self._get_color("menu_focuscolor")
        menu.forecolor = self._get_color("menu_forecolor")
        menu.backcolor = self._get_color("menu_backcolor")
        blur = self._get_str("menu_blur_world")
        menu.blur_world = float(blur) if blur else None
        menu.sound_loop = self._get_str_or_none("menu_sound_loop")

        menu.on_open = self._get_str_or_none("menu_on_open")
        menu.on_close = self._get_str_or_none("menu_on_close")
        menu.on_esc = self._get_str_or_none("menu_on_esc")

    # ------------------------------------------------------------------
    # Sync values from model (no rebuild)
    # ------------------------------------------------------------------

    def _set_var(self, key: str, value: str):
        """Set a var's value if it exists, without triggering _on_change."""
        var = self._vars.get(key)
        if var is not None:
            var.set(value)

    def _set_color_vars(self, key: str, color: Color | None):
        c = color or Color(0, 0, 0, 0)
        self._set_var(f"{key}_r", f"{c.r:.2f}")
        self._set_var(f"{key}_g", f"{c.g:.2f}")
        self._set_var(f"{key}_b", f"{c.b:.2f}")
        self._set_var(f"{key}_a", f"{c.a:.2f}")

    def _sync_item_values(self):
        item = self.item
        if item is None:
            return
        self._set_var("name", item.name)
        self._set_var("group", item.group or "")
        self._set_var("rect_x", str(int(item.rect.x)))
        self._set_var("rect_y", str(int(item.rect.y)))
        self._set_var("rect_w", str(int(item.rect.w)))
        self._set_var("rect_h", str(int(item.rect.h)))
        self._set_var("text", item.text or "")
        self._set_var("textscale", f"{item.textscale:.2f}" if item.textscale is not None else "0.25")
        self._set_var("textalignx", str(item.textalignx) if item.textalignx is not None else "")
        self._set_var("textaligny", str(item.textaligny) if item.textaligny is not None else "")
        self._set_color_vars("forecolor", item.forecolor)
        self._set_color_vars("backcolor", item.backcolor)
        self._set_var("bordersize", str(item.bordersize or 1))
        self._set_color_vars("bordercolor", item.bordercolor)
        self._set_var("dvar", item.dvar or "")
        self._set_var("dvar_test", item.dvar_test or "")
        self._set_var("show_dvar", "; ".join(item.show_dvar) if item.show_dvar else "")
        self._set_var("hide_dvar", "; ".join(item.hide_dvar) if item.hide_dvar else "")
        self._set_var("action", item.action or "")
        self._set_var("on_focus", item.on_focus or "")
        self._set_var("mouse_enter", item.mouse_enter or "")
        self._set_var("mouse_exit", item.mouse_exit or "")

    def _sync_menu_values(self):
        menu = self.menu
        if menu is None:
            return
        self._set_var("menu_name", menu.name)
        self._set_var("menu_rect_x", str(int(menu.rect.x)))
        self._set_var("menu_rect_y", str(int(menu.rect.y)))
        self._set_var("menu_rect_w", str(int(menu.rect.w)))
        self._set_var("menu_rect_h", str(int(menu.rect.h)))
        self._set_var("menu_blur_world", str(menu.blur_world) if menu.blur_world is not None else "")
        self._set_var("menu_sound_loop", menu.sound_loop or "")
        self._set_color_vars("menu_focuscolor", menu.focuscolor)
        self._set_color_vars("menu_forecolor", menu.forecolor)
        self._set_color_vars("menu_backcolor", menu.backcolor)
        self._set_var("menu_on_open", menu.on_open or "")
        self._set_var("menu_on_close", menu.on_close or "")
        self._set_var("menu_on_esc", menu.on_esc or "")
