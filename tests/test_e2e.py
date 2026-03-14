"""End-to-end tests: parse real .menu files -> serialize -> re-parse -> compare models.

Tests that the parser and serializer are consistent with each other.
The pipeline is: stock .menu file -> parse -> MenuFile -> serialize -> text -> parse -> MenuFile2
Then we assert MenuFile == MenuFile2.
"""

from __future__ import annotations

import sys
from pathlib import Path

from menu_builder.models import Color, ItemDef, MenuDef, MenuFile, Rect
from menu_builder.parser import parse, parse_file
from menu_builder.serializer import serialize

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DIR = Path(__file__).parent.parent / "ui_mp" / "ui_mp"


def _compare_color(a: Color | None, b: Color | None, context: str) -> list[str]:
    """Compare two colors, return list of differences."""
    if a is None and b is None:
        return []
    if (a is None) != (b is None):
        return [f"{context}: color mismatch (one is None)"]
    diffs = []
    for comp in ("r", "g", "b", "a"):
        va, vb = getattr(a, comp), getattr(b, comp)
        if abs(va - vb) > 0.001:
            diffs.append(f"{context}.{comp}: {va} != {vb}")
    return diffs


def _compare_rect(a: Rect, b: Rect, context: str) -> list[str]:
    diffs = []
    for comp in ("x", "y", "w", "h"):
        va, vb = getattr(a, comp), getattr(b, comp)
        if abs(va - vb) > 0.01:
            diffs.append(f"{context}.{comp}: {va} != {vb}")
    if a.horizontal_align != b.horizontal_align:
        diffs.append(f"{context}.halign: {a.horizontal_align} != {b.horizontal_align}")
    if a.vertical_align != b.vertical_align:
        diffs.append(f"{context}.valign: {a.vertical_align} != {b.vertical_align}")
    return diffs


def _compare_item(a: ItemDef, b: ItemDef, context: str) -> list[str]:
    diffs = []
    # Core identity
    if a.name != b.name:
        diffs.append(f"{context}.name: {a.name!r} != {b.name!r}")
    diffs.extend(_compare_rect(a.rect, b.rect, f"{context}.rect"))
    if a.visible != b.visible:
        diffs.append(f"{context}.visible: {a.visible} != {b.visible}")
    if a.decoration != b.decoration:
        diffs.append(f"{context}.decoration: {a.decoration} != {b.decoration}")
    if a.type != b.type:
        diffs.append(f"{context}.type: {a.type} != {b.type}")
    if a.text != b.text:
        diffs.append(f"{context}.text: {a.text!r} != {b.text!r}")
    if a.style != b.style:
        diffs.append(f"{context}.style: {a.style} != {b.style}")
    # Colors
    diffs.extend(_compare_color(a.forecolor, b.forecolor, f"{context}.forecolor"))
    diffs.extend(_compare_color(a.backcolor, b.backcolor, f"{context}.backcolor"))
    # Events
    if a.action != b.action:
        diffs.append(f"{context}.action: {a.action!r} != {b.action!r}")
    if a.on_focus != b.on_focus:
        diffs.append(f"{context}.on_focus: {a.on_focus!r} != {b.on_focus!r}")
    # Dvar
    if a.dvar != b.dvar:
        diffs.append(f"{context}.dvar: {a.dvar!r} != {b.dvar!r}")
    if a.dvar_test != b.dvar_test:
        diffs.append(f"{context}.dvar_test: {a.dvar_test!r} != {b.dvar_test!r}")
    if a.show_dvar != b.show_dvar:
        diffs.append(f"{context}.show_dvar: {a.show_dvar} != {b.show_dvar}")
    if a.hide_dvar != b.hide_dvar:
        diffs.append(f"{context}.hide_dvar: {a.hide_dvar} != {b.hide_dvar}")
    # Listbox
    if a.feeder != b.feeder:
        diffs.append(f"{context}.feeder: {a.feeder!r} != {b.feeder!r}")
    if a.element_height != b.element_height:
        diffs.append(f"{context}.element_height: {a.element_height} != {b.element_height}")
    return diffs


def _compare_menu(a: MenuDef, b: MenuDef, context: str) -> list[str]:
    diffs = []
    if a.name != b.name:
        diffs.append(f"{context}.name: {a.name!r} != {b.name!r}")
    diffs.extend(_compare_rect(a.rect, b.rect, f"{context}.rect"))
    if a.visible != b.visible:
        diffs.append(f"{context}.visible: {a.visible} != {b.visible}")
    if a.fullscreen != b.fullscreen:
        diffs.append(f"{context}.fullscreen: {a.fullscreen} != {b.fullscreen}")
    if a.popup != b.popup:
        diffs.append(f"{context}.popup: {a.popup} != {b.popup}")
    diffs.extend(_compare_color(a.focuscolor, b.focuscolor, f"{context}.focuscolor"))
    # Event handlers
    if a.on_esc != b.on_esc:
        diffs.append(f"{context}.on_esc: {a.on_esc!r} != {b.on_esc!r}")
    if a.on_open != b.on_open:
        diffs.append(f"{context}.on_open: {a.on_open!r} != {b.on_open!r}")
    if len(a.exec_keys) != len(b.exec_keys):
        diffs.append(f"{context}.exec_keys: {len(a.exec_keys)} != {len(b.exec_keys)}")
    # Items
    if len(a.items) != len(b.items):
        diffs.append(f"{context}.items count: {len(a.items)} != {len(b.items)}")
    else:
        for i, (ia, ib) in enumerate(zip(a.items, b.items)):
            diffs.extend(_compare_item(ia, ib, f"{context}.items[{i}]"))
    return diffs


def _compare_menu_file(a: MenuFile, b: MenuFile) -> list[str]:
    diffs = []
    if len(a.menu_defs) != len(b.menu_defs):
        diffs.append(f"menu_defs count: {len(a.menu_defs)} != {len(b.menu_defs)}")
        return diffs
    for i, (ma, mb) in enumerate(zip(a.menu_defs, b.menu_defs)):
        diffs.extend(_compare_menu(ma, mb, f"menu_defs[{i}]"))
    return diffs


def _round_trip(source: str) -> list[str]:
    """Parse -> serialize -> re-parse, return list of differences."""
    mf1 = parse(source)
    text = serialize(mf1)
    mf2 = parse(text)
    return _compare_menu_file(mf1, mf2)


def _round_trip_file(path: Path) -> list[str]:
    """Parse file -> serialize -> re-parse, return list of differences."""
    mf1 = parse_file(path)
    if not mf1.menu_defs:
        return []  # fragment file, nothing to round-trip
    text = serialize(mf1)
    mf2 = parse(text)
    return _compare_menu_file(mf1, mf2)


# ---------------------------------------------------------------------------
# E2E: Synthetic round-trip tests
# ---------------------------------------------------------------------------


def test_roundtrip_simple_button_menu():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "mymenu"
        visible 0
        fullscreen 0
        rect 0 0 640 480
        focuscolor 1 1 1 1
        onESC { close mymenu }

        itemDef {
            name "bg"
            rect 0 0 640 480
            style WINDOW_STYLE_FILLED
            backcolor 0 0 0 0.8
            visible 1
            decoration
        }

        itemDef {
            name "btn_ok"
            rect 200 300 200 30
            type ITEM_TYPE_BUTTON
            text "@MENU_OK"
            textscale .3
            textalign ITEM_ALIGN_CENTER
            forecolor 1 1 1 1
            visible 1
            action { play "mouse_click"; close mymenu }
            onFocus { play "mouse_over" }
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_multi_menu_file():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "ingame"
        visible 0
        fullscreen 0
        rect 0 0 640 480
        focuscolor 1 1 1 1
        onESC { close ingame }

        itemDef {
            name "btn_leave"
            rect 10 10 200 20
            type ITEM_TYPE_BUTTON
            text "Leave"
            visible 1
            action { open leavegame }
        }
    }

    menuDef {
        name "leavegame"
        visible 0
        fullscreen 0
        rect 100 150 300 200
        popup
        blurWorld 5.0
        focuscolor 1 1 1 1
        onESC { close leavegame }

        itemDef {
            name "title"
            rect 0 0 300 30
            type ITEM_TYPE_TEXT
            text "Are you sure?"
            forecolor 1 1 1 1
            visible 1
            decoration
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_dvar_conditional():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "weapons"
        rect 0 0 640 480

        itemDef {
            name "mp40_enabled"
            rect 10 50 200 20
            type ITEM_TYPE_BUTTON
            text "MP40"
            forecolor 1 1 1 1
            visible 1
            dvartest "ui_allow_mp40"
            showDvar { "1" }
            action { scriptMenuResponse "mp40" }
        }

        itemDef {
            name "mp40_disabled"
            rect 10 50 200 20
            type ITEM_TYPE_TEXT
            text "MP40"
            forecolor 0.5 0.5 0.5 0.5
            visible 1
            decoration
            dvartest "ui_allow_mp40"
            showDvar { "0" }
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_exec_keys():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "quickmsg"
        rect 0 0 640 480
        focuscolor 1 1 1 1
        onOpen { setDvar cl_bypassMouseInput "1" }
        onClose { setDvar cl_bypassMouseInput "0" }
        onESC { close quickmsg }
        execKey "1" { close quickmsg; open commands }
        execKey "2" { close quickmsg; open statements }
        execKey "3" { close quickmsg; open responses }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_listbox():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "serverlist"
        rect 0 0 640 480

        itemDef {
            name "servers"
            rect 10 50 600 300
            type ITEM_TYPE_LISTBOX
            style WINDOW_STYLE_FILLED
            backcolor 0.1 0.1 0.1 0.5
            outlinecolor 0.5 0.5 0.5 0.5
            elementheight 20
            elementtype LISTBOX_TEXT
            feeder FEEDER_SERVERS
            columns 4 2 50 20
            visible 1
            doubleClick { play "mouse_click"; uiScript JoinServer }
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_slider_and_multi():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "audio"
        rect 0 0 640 480

        itemDef {
            name "volume"
            rect 0 0 320 13
            type ITEM_TYPE_SLIDER
            dvarFloat "snd_volume" 0.8 0 1
            visible 1
        }

        itemDef {
            name "quality"
            rect 0 20 320 13
            type ITEM_TYPE_MULTI
            dvar "snd_quality"
            dvarFloatList { "@LOW" 0 "@MEDIUM" 1 "@HIGH" 2 }
            visible 1
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


def test_roundtrip_aligned_rects():
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "hud"
        rect 0 0 640 480

        itemDef {
            name "compass"
            rect 0 0 160 160 HORIZONTAL_ALIGN_LEFT VERTICAL_ALIGN_TOP
            visible 1
            decoration
        }

        itemDef {
            name "ammo"
            rect -10 -10 0 0 HORIZONTAL_ALIGN_RIGHT VERTICAL_ALIGN_BOTTOM
            visible 1
            decoration
        }
    }
}
'''
    diffs = _round_trip(source)
    assert diffs == [], "Round-trip diffs:\n" + "\n".join(diffs)


# ---------------------------------------------------------------------------
# E2E: Stock file round-trip tests
# ---------------------------------------------------------------------------


def _test_stock_file(filename: str, subdir: str = "") -> None:
    """Helper to round-trip a stock file."""
    path = SAMPLE_DIR / subdir / filename
    if not path.exists():
        print(f"  SKIP {filename} (not found at {path})")
        return
    diffs = _round_trip_file(path)
    assert diffs == [], "Round-trip diffs for " + filename + ":\n" + "\n".join(diffs)


def test_stock_wm_quickmessage():
    _test_stock_file("wm_quickmessage.menu")


def test_stock_quickcommands():
    _test_stock_file("quickcommands.menu", "scriptmenus")


def test_stock_ingame():
    _test_stock_file("ingame.menu", "scriptmenus")


def test_stock_callvote():
    _test_stock_file("callvote.menu", "scriptmenus")


def test_stock_team_americangerman():
    _test_stock_file("team_americangerman.menu", "scriptmenus")


def test_stock_weapon_american():
    _test_stock_file("weapon_american.menu", "scriptmenus")


def test_stock_createserver():
    _test_stock_file("createserver.menu")


def test_stock_joinserver():
    _test_stock_file("joinserver.menu")


def test_stock_hud():
    _test_stock_file("hud.menu")


def test_stock_settings_sd():
    _test_stock_file("settings_sd.menu")


def test_stock_options_multi():
    _test_stock_file("options_multi.menu")


def test_stock_main():
    _test_stock_file("main.menu")


def test_stock_connect():
    _test_stock_file("connect.menu")


def test_stock_filter():
    _test_stock_file("filter.menu")


def test_stock_cdkey():
    _test_stock_file("cdkey.menu")


# ---------------------------------------------------------------------------
# Brace balance test across all stock files
# ---------------------------------------------------------------------------


def test_all_stock_files_brace_balance():
    """Every stock file that parses should serialize with balanced braces."""
    if not SAMPLE_DIR.exists():
        return
    failures = []
    for f in sorted(SAMPLE_DIR.rglob("*.menu")):
        try:
            mf = parse_file(f)
            if not mf.menu_defs:
                continue
            output = serialize(mf)
            opens = output.count("{")
            closes = output.count("}")
            if opens != closes:
                failures.append(f"{f.name}: {opens} opens, {closes} closes")
        except Exception as e:
            failures.append(f"{f.name}: exception: {e}")
    assert failures == [], "Brace balance failures:\n" + "\n".join(failures)


if __name__ == "__main__":
    passed = 0
    failed = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
