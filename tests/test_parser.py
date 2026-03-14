"""Tests for the menu parser."""

from menu_builder.parser import parse
from menu_builder.serializer import serialize


def test_minimal_menu():
    """Parse a minimal menu."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        visible 0
        fullscreen 0
        rect 0 0 640 480
    }
}
'''
    mf = parse(source)
    assert len(mf.menu_defs) == 1
    assert mf.menu_defs[0].name == "test"
    assert mf.menu_defs[0].rect.w == 640
    assert mf.menu_defs[0].rect.h == 480


def test_item_parsing():
    """Parse a menu with items."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "btn"
            rect 10 20 200 30
            type ITEM_TYPE_BUTTON
            text "@MENU_OK"
            forecolor 1 1 1 1
            visible 1
            action { play "mouse_click"; close test }
        }
    }
}
'''
    mf = parse(source)
    menu = mf.menu_defs[0]
    assert len(menu.items) == 1
    item = menu.items[0]
    assert item.name == "btn"
    assert item.type == 1  # ITEM_TYPE_BUTTON
    assert item.text == "@MENU_OK"
    assert item.forecolor.r == 1.0
    assert item.action is not None
    assert "mouse_click" in item.action


def test_rect_with_alignment():
    """Parse rect with 6 parameters."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "bg"
            rect 0 0 640 480 HORIZONTAL_ALIGN_FULLSCREEN VERTICAL_ALIGN_FULLSCREEN
            visible 1
        }
    }
}
'''
    mf = parse(source)
    item = mf.menu_defs[0].items[0]
    assert item.rect.horizontal_align == "HORIZONTAL_ALIGN_FULLSCREEN"
    assert item.rect.vertical_align == "VERTICAL_ALIGN_FULLSCREEN"


def test_event_handlers():
    """Parse menu and item event handlers."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480
        onOpen { setDvar cl_bypassMouseInput "1" }
        onClose { setDvar cl_bypassMouseInput "0" }
        onESC { close test }
        execKey "1" { close test; open other }

        itemDef {
            name "btn"
            rect 0 0 100 20
            visible 1
            action { play "mouse_click" }
            onFocus { play "mouse_over" }
            mouseEnter { setitemcolor btn backcolor 1 1 1 0.3 }
            mouseExit { setitemcolor btn backcolor 0 0 0 0 }
        }
    }
}
'''
    mf = parse(source)
    menu = mf.menu_defs[0]
    assert "cl_bypassMouseInput" in menu.on_open
    assert "cl_bypassMouseInput" in menu.on_close
    assert "close test" in menu.on_esc
    assert len(menu.exec_keys) == 1
    assert menu.exec_keys[0].key == "1"
    item = menu.items[0]
    assert "mouse_click" in item.action
    assert "mouse_over" in item.on_focus
    assert item.mouse_enter is not None
    assert item.mouse_exit is not None


def test_dvar_test_show_hide():
    """Parse dvarTest with showDvar/hideDvar."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "enabled"
            rect 0 0 100 20
            visible 1
            dvartest "ui_allow_weapon"
            showDvar { "1" }
        }

        itemDef {
            name "multi_match"
            rect 0 0 100 20
            visible 1
            dvartest "rate"
            showDvar { "2500";"3000";"4000" }
        }
    }
}
'''
    mf = parse(source)
    items = mf.menu_defs[0].items
    assert items[0].show_dvar == ["1"]
    assert items[1].show_dvar == ["2500", "3000", "4000"]


def test_dvar_float_list():
    """Parse ITEM_TYPE_MULTI with dvarFloatList."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "voice"
            rect 0 0 320 13
            type ITEM_TYPE_MULTI
            dvar "cl_voice"
            dvarFloatList { "@MENU_OFF" 0 "@MENU_ON" 1 }
            visible 1
        }
    }
}
'''
    mf = parse(source)
    item = mf.menu_defs[0].items[0]
    assert item.type == 12
    assert len(item.dvar_multi_options) == 2
    assert item.dvar_multi_options[0].label == "@MENU_OFF"
    assert item.dvar_multi_options[1].label == "@MENU_ON"


def test_slider():
    """Parse ITEM_TYPE_SLIDER with dvarFloat."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "vol"
            rect 0 0 320 13
            type ITEM_TYPE_SLIDER
            dvarFloat "snd_volume" 0.8 0 1
            visible 1
        }
    }
}
'''
    mf = parse(source)
    item = mf.menu_defs[0].items[0]
    assert item.type == 10
    assert item.dvar_slider is not None
    assert item.dvar_slider.dvar == "snd_volume"
    assert item.dvar_slider.default == 0.8


def test_decoration_and_flags():
    """Parse flag properties (no value)."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        rect 0 0 640 480
        popup

        itemDef {
            name "bg"
            rect 0 0 100 100
            decoration
            autowrapped
            visible 1
        }
    }
}
'''
    mf = parse(source)
    assert mf.menu_defs[0].popup is True
    item = mf.menu_defs[0].items[0]
    assert item.decoration is True
    assert item.autowrapped is True


def test_multiple_menus():
    """Parse file with multiple menuDefs."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "menu1"
        rect 0 0 640 480
    }
    menuDef {
        name "menu2"
        rect 100 100 300 200
        popup
    }
}
'''
    mf = parse(source)
    assert len(mf.menu_defs) == 2
    assert mf.menu_defs[0].name == "menu1"
    assert mf.menu_defs[1].name == "menu2"
    assert mf.menu_defs[1].popup is True


def test_macro_expansion():
    """Macros defined in the file are expanded."""
    source = '''
#include "ui_mp/menudef.h"
#define MY_COLOR 0.9 0.9 0.9 1
#define MY_POS 10 20
#define MY_SIZE 200 30
{
    menuDef {
        name "test"
        rect 0 0 640 480

        itemDef {
            name "btn"
            rect MY_POS MY_SIZE
            forecolor MY_COLOR
            visible 1
        }
    }
}
'''
    mf = parse(source)
    item = mf.menu_defs[0].items[0]
    assert item.rect.x == 10
    assert item.rect.y == 20
    assert item.rect.w == 200
    assert item.rect.h == 30
    assert item.forecolor.r == 0.9


def test_fragment_file():
    """Fragment files (no outer braces) return empty MenuFile."""
    source = '''
name "button"
type ITEM_TYPE_BUTTON
textfont UI_FONT_NORMAL
'''
    mf = parse(source)
    assert len(mf.menu_defs) == 0


def test_case_insensitive():
    """Property names are case-insensitive."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "test"
        fullScreen 0
        RECT 0 0 640 480
        focusColor 1 1 1 1
        onESC { close test }
    }
}
'''
    mf = parse(source)
    menu = mf.menu_defs[0]
    assert menu.name == "test"
    assert menu.focuscolor is not None
    assert menu.on_esc is not None


def test_round_trip():
    """Parse then serialize produces valid output."""
    source = '''
#include "ui_mp/menudef.h"
{
    menuDef {
        name "roundtrip"
        visible 0
        fullscreen 0
        rect 0 0 640 480
        focuscolor 1 1 1 1
        onESC { close roundtrip }

        itemDef {
            name "bg"
            rect 0 0 640 480
            style WINDOW_STYLE_FILLED
            backcolor 0 0 0 0.8
            visible 1
            decoration
        }

        itemDef {
            name "btn"
            rect 200 300 200 30
            type ITEM_TYPE_BUTTON
            text "OK"
            visible 1
            action { close roundtrip }
        }
    }
}
'''
    mf = parse(source)
    output = serialize(mf)
    # Re-parse the output
    mf2 = parse(output)
    assert len(mf2.menu_defs) == 1
    assert mf2.menu_defs[0].name == "roundtrip"
    assert len(mf2.menu_defs[0].items) == 2
    assert mf2.menu_defs[0].items[0].decoration is True
    assert mf2.menu_defs[0].items[1].type == 1


if __name__ == "__main__":
    import sys

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
