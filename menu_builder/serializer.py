"""Serialize menu data model to .menu file format."""

from __future__ import annotations

from menu_builder.models import (
    Color,
    DvarMultiOption,
    ItemDef,
    MenuDef,
    MenuFile,
    Rect,
)

# Maps Python style int values to named constants for cleaner output.
WINDOW_STYLES = {
    0: "WINDOW_STYLE_EMPTY",
    1: "WINDOW_STYLE_FILLED",
    2: "WINDOW_STYLE_GRADIENT",
    3: "WINDOW_STYLE_SHADER",
    4: "WINDOW_STYLE_TEAMCOLOR",
    5: "WINDOW_STYLE_CINEMATIC",
    6: "WINDOW_STYLE_DVAR_SHADER",
}

ITEM_TYPES = {
    0: "ITEM_TYPE_TEXT",
    1: "ITEM_TYPE_BUTTON",
    2: "ITEM_TYPE_RADIOBUTTON",
    3: "ITEM_TYPE_CHECKBOX",
    4: "ITEM_TYPE_EDITFIELD",
    5: "ITEM_TYPE_COMBO",
    6: "ITEM_TYPE_LISTBOX",
    7: "ITEM_TYPE_MODEL",
    8: "ITEM_TYPE_OWNERDRAW",
    9: "ITEM_TYPE_NUMERICFIELD",
    10: "ITEM_TYPE_SLIDER",
    11: "ITEM_TYPE_YESNO",
    12: "ITEM_TYPE_MULTI",
    13: "ITEM_TYPE_DVARENUM",
    14: "ITEM_TYPE_BIND",
    15: "ITEM_TYPE_MENUMODEL",
    16: "ITEM_TYPE_VALIDFILEFIELD",
    17: "ITEM_TYPE_DECIMALFIELD",
    18: "ITEM_TYPE_UPREDITFIELD",
}

TEXT_ALIGNS = {
    0: "ITEM_ALIGN_LEFT",
    1: "ITEM_ALIGN_CENTER",
    2: "ITEM_ALIGN_RIGHT",
}

TEXT_STYLES = {
    0: "ITEM_TEXTSTYLE_NORMAL",
    1: "ITEM_TEXTSTYLE_NORMAL",
    3: "ITEM_TEXTSTYLE_SHADOWED",
    6: "ITEM_TEXTSTYLE_SHADOWEDMORE",
}


def _fmt_float(v: float) -> str:
    """Format a float, dropping unnecessary trailing zeros."""
    if v == int(v):
        return str(int(v))
    # Use up to 4 decimal places, strip trailing zeros
    return f"{v:.4f}".rstrip("0").rstrip(".")


def _fmt_color(c: Color) -> str:
    return f"{_fmt_float(c.r)} {_fmt_float(c.g)} {_fmt_float(c.b)} {_fmt_float(c.a)}"


def _fmt_rect(r: Rect) -> str:
    parts = f"{_fmt_float(r.x)} {_fmt_float(r.y)} {_fmt_float(r.w)} {_fmt_float(r.h)}"
    if r.horizontal_align and r.vertical_align:
        parts += f" {r.horizontal_align} {r.vertical_align}"
    return parts


def _indent(level: int) -> str:
    return "    " * level


def _prop(level: int, key: str, value: str) -> str:
    """Format a single property line with consistent alignment."""
    indent = _indent(level)
    return f"{indent}{key:<24}{value}\n"


def _flag(level: int, key: str) -> str:
    """Format a flag property (keyword with no value)."""
    return f"{_indent(level)}{key}\n"


def _block(level: int, key: str, commands: str) -> str:
    """Format an event handler block."""
    return f"{_indent(level)}{key:<24}{{ {commands} }}\n"


def serialize_item(item: ItemDef, level: int = 2) -> str:
    """Serialize a single itemDef."""
    lines = f"{_indent(level)}itemDef\n{_indent(level)}{{\n"
    lv = level + 1

    # --- Positioning & Layout ---
    if item.name:
        lines += _prop(lv, "name", f'"{item.name}"')
    lines += _prop(lv, "rect", _fmt_rect(item.rect))
    if item.origin:
        lines += _prop(lv, "origin", f"{_fmt_float(item.origin[0])} {_fmt_float(item.origin[1])}")
    if item.visible:
        lines += _prop(lv, "visible", "1")
    else:
        lines += _prop(lv, "visible", "0")
    if item.decoration:
        lines += _flag(lv, "decoration")
    if item.autowrapped:
        lines += _flag(lv, "autowrapped")
    if item.group:
        lines += _prop(lv, "group", item.group)

    # --- Styling ---
    if item.style is not None:
        lines += _prop(lv, "style", WINDOW_STYLES.get(item.style, str(item.style)))
    if item.forecolor:
        lines += _prop(lv, "forecolor", _fmt_color(item.forecolor))
    if item.backcolor:
        lines += _prop(lv, "backcolor", _fmt_color(item.backcolor))
    if item.bordercolor:
        lines += _prop(lv, "bordercolor", _fmt_color(item.bordercolor))
    if item.border is not None:
        lines += _prop(lv, "border", str(item.border))
    if item.bordersize is not None:
        lines += _prop(lv, "bordersize", str(item.bordersize))
    if item.outlinecolor:
        lines += _prop(lv, "outlinecolor", _fmt_color(item.outlinecolor))
    if item.background:
        lines += _prop(lv, "background", f'"{item.background}"')
    if item.align:
        lines += _prop(lv, "align", item.align)

    # --- Text ---
    if item.type is not None:
        lines += _prop(lv, "type", ITEM_TYPES.get(item.type, str(item.type)))
    if item.text is not None:
        lines += _prop(lv, "text", f'"{item.text}"')
    if item.textfont:
        lines += _prop(lv, "textfont", item.textfont)
    if item.textscale is not None:
        lines += _prop(lv, "textscale", _fmt_float(item.textscale))
    if item.textalign is not None:
        lines += _prop(lv, "textalign", TEXT_ALIGNS.get(item.textalign, str(item.textalign)))
    if item.textalignx is not None:
        lines += _prop(lv, "textalignx", str(item.textalignx))
    if item.textaligny is not None:
        lines += _prop(lv, "textaligny", str(item.textaligny))
    if item.textstyle is not None:
        lines += _prop(lv, "textstyle", TEXT_STYLES.get(item.textstyle, str(item.textstyle)))

    # --- Behavior ---
    if item.dvar:
        lines += _prop(lv, "dvar", f'"{item.dvar}"')
    if item.dvar_test:
        lines += _prop(lv, "dvarTest", f'"{item.dvar_test}"')
    if item.show_dvar:
        vals = "; ".join(f'"{v}"' for v in item.show_dvar)
        lines += _prop(lv, "showDvar", f"{{ {vals} }}")
    if item.hide_dvar:
        vals = "; ".join(f'"{v}"' for v in item.hide_dvar)
        lines += _prop(lv, "hideDvar", f"{{ {vals} }}")
    if item.dvar_multi_options:
        lines += _serialize_dvar_multi(lv, item.dvar_multi_options)
    if item.dvar_slider:
        s = item.dvar_slider
        lines += _prop(
            lv,
            "dvarFloat",
            f'"{s.dvar}" {_fmt_float(s.default)} {_fmt_float(s.min)} {_fmt_float(s.max)}',
        )
    if item.dvar_enum_list:
        lines += _prop(lv, "dvarEnumList", f'"{item.dvar_enum_list}"')
    if item.owner_draw:
        lines += _prop(lv, "ownerdraw", item.owner_draw)
    if item.owner_draw_flag:
        lines += _prop(lv, "ownerdrawFlag", item.owner_draw_flag)
    if item.max_chars is not None:
        lines += _prop(lv, "maxChars", str(item.max_chars))
    if item.max_paint_chars is not None:
        lines += _prop(lv, "maxPaintChars", str(item.max_paint_chars))
    if item.max_chars_goto_next:
        lines += _flag(lv, "maxCharsGotoNext")

    # --- Listbox ---
    if item.element_width is not None:
        lines += _prop(lv, "elementwidth", str(item.element_width))
    if item.element_height is not None:
        lines += _prop(lv, "elementheight", str(item.element_height))
    if item.element_type:
        lines += _prop(lv, "elementtype", item.element_type)
    if item.feeder:
        lines += _prop(lv, "feeder", item.feeder)
    if item.columns:
        lines += _prop(lv, "columns", item.columns)
    if item.not_selectable:
        lines += _flag(lv, "notselectable")

    # --- Event Handlers ---
    if item.action:
        lines += _block(lv, "action", item.action)
    if item.on_focus:
        lines += _block(lv, "onFocus", item.on_focus)
    if item.leave_focus:
        lines += _block(lv, "leaveFocus", item.leave_focus)
    if item.accept:
        lines += _block(lv, "accept", item.accept)
    if item.mouse_enter:
        lines += _block(lv, "mouseEnter", item.mouse_enter)
    if item.mouse_exit:
        lines += _block(lv, "mouseExit", item.mouse_exit)
    if item.double_click:
        lines += _block(lv, "doubleClick", item.double_click)

    lines += f"{_indent(level)}}}\n"
    return lines


def _serialize_dvar_multi(level: int, options: list[DvarMultiOption]) -> str:
    """Serialize dvarFloatList or dvarStrList."""
    if not options:
        return ""
    is_float = options[0].is_float
    if is_float:
        pairs = " ".join(f'"{opt.label}" {opt.value}' for opt in options)
        return _prop(level, "dvarFloatList", f"{{ {pairs} }}")
    else:
        pairs = " ".join(f'"{opt.label}" "{opt.value}"' for opt in options)
        return _prop(level, "dvarStrList", f"{{ {pairs} }}")


def serialize_menu(menu: MenuDef, level: int = 1) -> str:
    """Serialize a single menuDef."""
    lines = f"{_indent(level)}menuDef\n{_indent(level)}{{\n"
    lv = level + 1

    # --- Properties ---
    if menu.name:
        lines += _prop(lv, "name", f'"{menu.name}"')
    lines += _prop(lv, "visible", "1" if menu.visible else "0")
    lines += _prop(lv, "fullscreen", "1" if menu.fullscreen else "0")
    lines += _prop(lv, "rect", _fmt_rect(menu.rect))

    if menu.style is not None:
        lines += _prop(lv, "style", WINDOW_STYLES.get(menu.style, str(menu.style)))
    if menu.focuscolor:
        lines += _prop(lv, "focusColor", _fmt_color(menu.focuscolor))
    if menu.disablecolor:
        lines += _prop(lv, "disablecolor", _fmt_color(menu.disablecolor))
    if menu.forecolor:
        lines += _prop(lv, "forecolor", _fmt_color(menu.forecolor))
    if menu.backcolor:
        lines += _prop(lv, "backcolor", _fmt_color(menu.backcolor))
    if menu.bordercolor:
        lines += _prop(lv, "bordercolor", _fmt_color(menu.bordercolor))
    if menu.border is not None:
        lines += _prop(lv, "border", str(menu.border))
    if menu.blur_world is not None:
        lines += _prop(lv, "blurWorld", _fmt_float(menu.blur_world))
    if menu.sound_loop is not None:
        lines += _prop(lv, "soundLoop", f'"{menu.sound_loop}"')
    if menu.popup:
        lines += _flag(lv, "popup")
    if menu.out_of_bounds_click:
        lines += _flag(lv, "outOfBoundsClick")

    # --- Event Handlers ---
    if menu.on_open:
        lines += _block(lv, "onOpen", menu.on_open)
    if menu.on_close:
        lines += _block(lv, "onClose", menu.on_close)
    if menu.on_esc:
        lines += _block(lv, "onESC", menu.on_esc)
    for ek in menu.exec_keys:
        lines += f'{_indent(lv)}execKey "{ek.key}" {{ {ek.commands} }}\n'

    # --- Items ---
    if menu.items:
        lines += "\n"
        for item in menu.items:
            lines += serialize_item(item, level=lv)
            lines += "\n"

    lines += f"{_indent(level)}}}\n"
    return lines


def serialize(menu_file: MenuFile) -> str:
    """Serialize a complete MenuFile to .menu file format."""
    lines = f'#include "{menu_file.include}"\n\n'
    lines += "{\n"

    for i, menu in enumerate(menu_file.menu_defs):
        if i > 0:
            lines += "\n"
        lines += serialize_menu(menu)

    lines += "}\n"
    return lines
