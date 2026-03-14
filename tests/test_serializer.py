"""Tests for the menu serializer."""

from menu_builder.models import (
    Color,
    DvarMultiOption,
    DvarSlider,
    ExecKey,
    ItemDef,
    MenuDef,
    MenuFile,
    Rect,
)
from menu_builder.serializer import serialize


def test_minimal_menu():
    """A menu with no items produces valid structure."""
    mf = MenuFile(
        menu_defs=[
            MenuDef(name="empty_menu", rect=Rect(0, 0, 640, 480)),
        ]
    )
    output = serialize(mf)
    assert '#include "ui_mp/menudef.h"' in output
    assert 'name' in output
    assert '"empty_menu"' in output
    assert "menuDef" in output
    # Verify brace balance
    assert output.count("{") == output.count("}")


def test_button_item():
    """A simple button item serializes correctly."""
    item = ItemDef(
        name="btn_ok",
        rect=Rect(200, 300, 200, 30, "HORIZONTAL_ALIGN_CENTER", "VERTICAL_ALIGN_CENTER"),
        type=1,  # ITEM_TYPE_BUTTON
        text="@MENU_OK",
        textscale=0.3,
        textalign=1,  # ITEM_ALIGN_CENTER
        forecolor=Color(0.9, 0.9, 0.9, 1.0),
        visible=True,
        action='play "mouse_click"; close my_menu',
        on_focus='play "mouse_over"',
    )
    mf = MenuFile(
        menu_defs=[
            MenuDef(
                name="test_menu",
                rect=Rect(0, 0, 640, 480),
                focuscolor=Color(1, 1, 1, 1),
                on_esc="close test_menu",
                items=[item],
            )
        ]
    )
    output = serialize(mf)
    assert "ITEM_TYPE_BUTTON" in output
    assert '"@MENU_OK"' in output
    assert "ITEM_ALIGN_CENTER" in output
    assert "HORIZONTAL_ALIGN_CENTER" in output
    assert 'play "mouse_click"' in output
    assert output.count("{") == output.count("}")


def test_quickmessage_style():
    """Reproduce a quickmessage-style menu with execKeys."""
    menu = MenuDef(
        name="quickmessage",
        rect=Rect(0, 0, 640, 480),
        focuscolor=Color(1, 1, 1, 1),
        on_open='setDvar cl_bypassMouseInput "1"',
        on_close='setDvar cl_bypassMouseInput "0"',
        on_esc="close quickmessage",
        exec_keys=[
            ExecKey("1", "close quickmessage; open quickcommands"),
            ExecKey("2", "close quickmessage; open quickstatements"),
        ],
        items=[
            ItemDef(
                name="window_background",
                rect=Rect(0, 0, 224, 192),
                style=1,
                backcolor=Color(0, 0, 0, 0.7975),
                visible=True,
                decoration=True,
            ),
            ItemDef(
                name="title",
                rect=Rect(0, 0, 224, 192),
                type=0,
                text="@QUICKMESSAGE_QUICK_MESSAGE",
                textscale=0.35,
                textalign=1,
                visible=True,
                decoration=True,
            ),
        ],
    )
    mf = MenuFile(menu_defs=[menu])
    output = serialize(mf)
    assert 'execKey "1"' in output
    assert 'execKey "2"' in output
    assert "decoration" in output
    assert "WINDOW_STYLE_FILLED" in output
    assert output.count("{") == output.count("}")


def test_dvar_multi():
    """ITEM_TYPE_MULTI with dvarFloatList."""
    item = ItemDef(
        name="cl_voice",
        type=12,
        dvar="cl_voice",
        dvar_multi_options=[
            DvarMultiOption("@MENU_OFF", "0", is_float=True),
            DvarMultiOption("@MENU_ON", "1", is_float=True),
        ],
        rect=Rect(0, 0, 320, 13),
        visible=True,
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    assert "ITEM_TYPE_MULTI" in output
    assert "dvarFloatList" in output
    assert '"@MENU_OFF" 0' in output
    assert '"@MENU_ON" 1' in output


def test_dvar_str_list():
    """ITEM_TYPE_MULTI with dvarStrList."""
    item = ItemDef(
        name="snd_output",
        type=12,
        dvar="snd_output",
        dvar_multi_options=[
            DvarMultiOption("@MENU_DEFAULT", "default", is_float=False),
            DvarMultiOption("@MENU_HEADPHONES", "headphones", is_float=False),
        ],
        rect=Rect(0, 0, 320, 13),
        visible=True,
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    assert "dvarStrList" in output
    assert '"@MENU_DEFAULT" "default"' in output


def test_slider():
    """ITEM_TYPE_SLIDER with dvarFloat."""
    item = ItemDef(
        name="volume",
        type=10,
        dvar_slider=DvarSlider("snd_volume", 0.8, 0, 1),
        rect=Rect(0, 0, 320, 13),
        visible=True,
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    assert "ITEM_TYPE_SLIDER" in output
    assert "dvarFloat" in output
    assert '"snd_volume"' in output


def test_listbox():
    """ITEM_TYPE_LISTBOX with feeder and columns."""
    item = ItemDef(
        name="server_list",
        type=6,
        rect=Rect(10, 50, 600, 300),
        element_height=20,
        element_type="LISTBOX_TEXT",
        feeder="FEEDER_SERVERS",
        columns="4 2 50 20",
        visible=True,
        double_click='play "mouse_click"; uiScript JoinServer',
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    assert "ITEM_TYPE_LISTBOX" in output
    assert "FEEDER_SERVERS" in output
    assert "LISTBOX_TEXT" in output
    assert "doubleClick" in output


def test_conditional_visibility():
    """Items with dvarTest + showDvar/hideDvar."""
    enabled = ItemDef(
        name="weapon_mp40",
        type=1,
        text="MP40",
        rect=Rect(10, 50, 200, 20),
        forecolor=Color(1, 1, 1, 1),
        visible=True,
        dvar_test="ui_allow_mp40",
        show_dvar=["1"],
        action='scriptMenuResponse "mp40"',
    )
    disabled = ItemDef(
        name="weapon_mp40_off",
        type=0,
        text="MP40",
        rect=Rect(10, 50, 200, 20),
        forecolor=Color(0.5, 0.5, 0.5, 0.5),
        visible=True,
        decoration=True,
        dvar_test="ui_allow_mp40",
        show_dvar=["0"],
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[enabled, disabled])])
    output = serialize(mf)
    assert 'showDvar' in output
    assert '{ "1" }' in output
    assert '{ "0" }' in output


def test_multiple_show_dvar_values():
    """showDvar with multiple semicolon-separated values."""
    item = ItemDef(
        name="rate_item",
        rect=Rect(0, 0, 100, 20),
        visible=True,
        dvar_test="rate",
        show_dvar=["2500", "3000", "4000"],
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    assert '"2500"; "3000"; "4000"' in output


def test_multiple_menus_in_file():
    """A file with multiple menuDefs."""
    mf = MenuFile(
        menu_defs=[
            MenuDef(name="ingame", rect=Rect(0, 0, 640, 480)),
            MenuDef(name="leavegame", rect=Rect(100, 100, 300, 200), popup=True),
        ]
    )
    output = serialize(mf)
    assert '"ingame"' in output
    assert '"leavegame"' in output
    assert "popup" in output
    assert output.count("menuDef") == 2
    assert output.count("{") == output.count("}")


def test_float_formatting():
    """Floats are formatted cleanly (no unnecessary trailing zeros)."""
    item = ItemDef(
        name="test",
        rect=Rect(0, 0, 640, 480),
        forecolor=Color(0.9, 0.9, 0.9, 1.0),
        textscale=0.24,
        visible=True,
    )
    mf = MenuFile(menu_defs=[MenuDef(name="test", items=[item])])
    output = serialize(mf)
    # Should not have "1.0000" or "0.9000"
    assert "1.0000" not in output
    assert "0.9000" not in output
    assert "0.9 0.9 0.9 1" in output


if __name__ == "__main__":
    import sys

    # Run all test functions
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
