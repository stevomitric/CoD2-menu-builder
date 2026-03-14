"""Data model for CoD2 .menu files (multiplayer-focused)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Color:
    """RGBA color with float components (0.0 - 1.0)."""

    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0


@dataclass
class Rect:
    """Position and size, with optional alignment anchors."""

    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    horizontal_align: str | None = None
    vertical_align: str | None = None


@dataclass
class DvarMultiOption:
    """A single option in a ITEM_TYPE_MULTI choice list."""

    label: str = ""
    value: str = ""
    is_float: bool = True  # True = dvarFloatList, False = dvarStrList


@dataclass
class DvarSlider:
    """Slider binding: dvar name with default, min, and max."""

    dvar: str = ""
    default: float = 0.0
    min: float = 0.0
    max: float = 1.0


@dataclass
class ExecKey:
    """A menu-level key binding."""

    key: str = ""
    commands: str = ""


# ---------------------------------------------------------------------------
# ItemDef
# ---------------------------------------------------------------------------


@dataclass
class ItemDef:
    """A single UI element within a menuDef."""

    # --- Positioning & Layout ---
    name: str = ""
    rect: Rect = field(default_factory=Rect)
    origin: tuple[float, float] | None = None
    visible: bool = True
    decoration: bool = False
    autowrapped: bool = False
    group: str | None = None

    # --- Styling ---
    style: int | None = None
    forecolor: Color | None = None
    backcolor: Color | None = None
    bordercolor: Color | None = None
    border: int | None = None
    bordersize: int | None = None
    outlinecolor: Color | None = None
    background: str | None = None
    align: str | None = None

    # --- Text ---
    text: str | None = None
    textfont: str | None = None
    textscale: float | None = None
    textalign: int | None = None
    textalignx: int | None = None
    textaligny: int | None = None
    textstyle: int | None = None

    # --- Type & Behavior ---
    type: int | None = None
    dvar: str | None = None
    dvar_test: str | None = None
    show_dvar: list[str] = field(default_factory=list)
    hide_dvar: list[str] = field(default_factory=list)
    dvar_multi_options: list[DvarMultiOption] = field(default_factory=list)
    dvar_slider: DvarSlider | None = None
    dvar_enum_list: str | None = None
    owner_draw: str | None = None
    owner_draw_flag: str | None = None
    max_chars: int | None = None
    max_paint_chars: int | None = None
    max_chars_goto_next: bool = False

    # --- Listbox ---
    element_width: int | None = None
    element_height: int | None = None
    element_type: str | None = None
    feeder: str | None = None
    columns: str | None = None  # raw column definition string
    not_selectable: bool = False

    # --- Event Handlers (raw command strings) ---
    action: str | None = None
    on_focus: str | None = None
    leave_focus: str | None = None
    accept: str | None = None
    mouse_enter: str | None = None
    mouse_exit: str | None = None
    double_click: str | None = None


# ---------------------------------------------------------------------------
# MenuDef
# ---------------------------------------------------------------------------


@dataclass
class MenuDef:
    """A single menu screen/panel."""

    # --- Properties ---
    name: str = ""
    visible: bool = False
    fullscreen: bool = False
    rect: Rect = field(default_factory=Rect)
    style: int | None = None
    focuscolor: Color | None = None
    disablecolor: Color | None = None
    forecolor: Color | None = None
    backcolor: Color | None = None
    bordercolor: Color | None = None
    border: int | None = None
    blur_world: float | None = None
    sound_loop: str | None = None
    popup: bool = False
    out_of_bounds_click: bool = False

    # --- Event Handlers ---
    on_open: str | None = None
    on_close: str | None = None
    on_esc: str | None = None
    exec_keys: list[ExecKey] = field(default_factory=list)

    # --- Items ---
    items: list[ItemDef] = field(default_factory=list)


# ---------------------------------------------------------------------------
# MenuFile (top-level)
# ---------------------------------------------------------------------------


@dataclass
class MenuFile:
    """A complete .menu file."""

    include: str = "ui_mp/menudef.h"
    menu_defs: list[MenuDef] = field(default_factory=list)
