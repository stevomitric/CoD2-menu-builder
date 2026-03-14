# CoD2 Menu Builder

A GUI tool (Python + Tkinter) for visually creating `.menu` files for Call of Duty 2.

## .menu File Format Reference

The `.menu` format is a C-like brace syntax with preprocessor support (`#include`, `#define`).
Property names are **case-insensitive** (e.g., `fullScreen` vs `fullscreen`, `onESC` vs `onEsc`).

### Structure

```
#include "ui_mp/menudef.h"

{
    menuDef {
        name        "mymenu"
        rect        0 0 640 480
        visible     0
        fullscreen  0
        style       WINDOW_STYLE_EMPTY
        focuscolor  1 1 1 1

        itemDef {
            name        "my_button"
            rect        10 10 200 30 HORIZONTAL_ALIGN_CENTER VERTICAL_ALIGN_CENTER
            type        ITEM_TYPE_BUTTON
            text        "Click Me"
            forecolor   1 1 1 1
            backcolor   0 0 0 0.8
            visible     1
            action      { play "mouse_click"; open "othermenu" }
        }
    }
}
```

### Key Concepts

- `menuDef` = top-level container (a screen/panel)
- `itemDef` = individual UI elements inside a menu
- `rect` supports both **4 params** (`X Y W H`) and **6 params** (`X Y W H HORIZ_ALIGN VERT_ALIGN`)
- Colors are `R G B A` floats (0.0-1.0)
- Properties are keyword-value pairs (no `=`, no `;`)
- The whole file is wrapped in outer `{ }`
- A single file can contain **multiple menuDefs** within the outer braces
- Boolean values can be `0`/`1` or `MENU_TRUE`/`MENU_FALSE`
- Values can use numeric literals or named constants interchangeably (e.g., `type 1` or `type ITEM_TYPE_BUTTON`)
- `@` prefix on text = localized string reference (e.g., `"@MENU_OK"`)

### Preprocessor

- `#include "ui_mp/menudef.h"` or `#include "ui/menudef.h"` — standard header
- `#include` can appear **inside a menuDef body** (e.g., `#include "ui_mp/menu_background.menu"` for shared items)
- `#include` can appear **inside an itemDef body** (e.g., `#include "ui_mp/button_mainmenu.menu"` for shared item properties)
- **Fragment files** exist that contain no `menuDef` wrapper — just raw properties or bare `itemDef` blocks meant to be `#include`d
- `#define` macros for positions, sizes, colors, scalars: `#define ORIGIN_CHOICE1 80 84`
- Macros compose in rect: `rect OPTIONS_WINDOW_POS OPTIONS_WINDOW_SIZE` expands to 4 values
- Block comments `/* ... */` and line comments `//`

### assetGlobalDef

A special top-level block (not a menuDef) for global asset configuration:
```
assetGlobalDef {
    consoleFont "fonts/consoleFont" 18
    smallFont "fonts/smallFont" 12
    font "fonts/normalFont" 16
    bigFont "fonts/bigFont" 24
    extraBigFont "fonts/extraBigFont" 32
    boldFont "fonts/boldFont" 30
    cursor "ui/assets/3_cursor3"
    gradientBar "ui/assets/gradientbar2.tga"
    itemFocusSound "sound/misc/menu2.wav"
    fadeClamp 1.0
    fadeCycle 1
    fadeAmount 0.1
    fadeInAmount 0.1
    shadowX 5
    shadowY 5
    shadowColor 0.1 0.1 0.1 0.25
}
```

### menuDef Properties

| Property | Type | Notes |
|---|---|---|
| `name` | string | Unique identifier; quoted or unquoted |
| `visible` | 0/1 or MENU_TRUE/MENU_FALSE | Initially visible |
| `fullscreen` | 0/1 or MENU_TRUE/MENU_FALSE | Covers entire screen |
| `rect` | 4 or 6 params | X Y W H [HORIZ_ALIGN VERT_ALIGN] |
| `style` | constant or int | WINDOW_STYLE_* |
| `focuscolor` | float4 | Color when items focused; also via macro (GLOBAL_FOCUSED_COLOR) |
| `disablecolor` | float4 | Color when items disabled |
| `backcolor` | float4 | Background color |
| `forecolor` | float4 | Foreground color |
| `bordercolor` | float4 | Border color |
| `border` | int | Border style |
| `blurWorld` | float | Background blur amount (e.g., `5.0`) |
| `soundLoop` | string | Looping sound while open |
| `popup` | flag (no value) | Marks menu as a popup |
| `onOpen` | block `{ }` | Commands on menu open |
| `onClose` | block `{ }` | Commands on menu close |
| `onESC` | block `{ }` | Escape key handler |
| `execKey` | `"key" { commands }` | Menu-level key binding (NOT inside itemDef) |
| `outOfBoundsClick` | flag (no value) | Close menu when clicking outside its rect |

### itemDef Properties

**Positioning & Layout:**

| Property | Type | Notes |
|---|---|---|
| `name` | string | Quoted or unquoted |
| `rect` | 4 or 6 values | X Y W H [HORIZ_ALIGN VERT_ALIGN]; can use macros; supports negative values and floats |
| `origin` | 2 values | X Y offset; often a macro |
| `visible` | 0/1 or MENU_TRUE/MENU_FALSE | |
| `decoration` | flag (no value) | Non-interactive item |
| `autowrapped` | flag (no value) | Text auto-wraps to rect width |
| `group` | string | Group name for batch `setitemcolor`/`show`/`hide` |

**Styling:**

| Property | Type | Notes |
|---|---|---|
| `style` | constant or int | WINDOW_STYLE_* |
| `forecolor` | float4 or macro | Text/foreground color |
| `backcolor` | float4 or macro | Background color |
| `bordercolor` | float4 or macro | Border color |
| `border` | int or macro | Border style |
| `bordersize` | int | Border thickness (1, 2) |
| `outlinecolor` | float4 | Listbox selection/outline color |
| `background` | string | Shader/image path; `$dvarname` prefix = dvar-derived shader |
| `align` | constant | Item alignment (e.g., `HUD_HORIZONTAL`) |
| `textfont` | constant | UI_FONT_NORMAL, UI_FONT_DEFAULT, UI_FONT_BIG |
| `textscale` | float or macro | Font size multiplier |
| `textalign` | constant or int | ITEM_ALIGN_LEFT, ITEM_ALIGN_CENTER, ITEM_ALIGN_RIGHT, ITEM_ALIGN_CENTER2 |
| `textalignx` | int | Horizontal text offset (can be negative) |
| `textaligny` | int | Vertical text offset (can be negative) |
| `textstyle` | constant or int | ITEM_TEXTSTYLE_NORMAL, ITEM_TEXTSTYLE_SHADOWED, ITEM_TEXTSTYLE_SHADOWEDMORE |
| `text` | string | Display text; `@` prefix = localized |

**Behavior & Type:**

| Property | Type | Notes |
|---|---|---|
| `type` | constant or int | ITEM_TYPE_* (see table below) |
| `dvar` | string | Binds item to a game dvar |
| `dvarTest` | string | Dvar name for conditional visibility |
| `showDvar` | block `{ "val" }` | Show when dvar matches; semicolons for multiple: `{ "2500";"3000" }` |
| `hideDvar` | block `{ "val" }` | Hide when dvar matches |
| `dvarFloatList` | block | For ITEM_TYPE_MULTI: `{ "@label" value "@label" value }` |
| `dvarStrList` | block | For ITEM_TYPE_MULTI with string values: `{ "@label", "value", ... }` |
| `dvarEnumList` | string | For ITEM_TYPE_DVARENUM: `"dvarname"` — populates from dvar's valid values |
| `dvarfloat` | string + 3 values | For ITEM_TYPE_SLIDER: `"dvarname" default min max` |
| `focusdvar` | block `{ "val" }` | Set focus on item when dvar matches value |
| `textsavegame` | flag (no value) | Gets text content from current savegame |
| `ownerDraw` | constant | Engine-drawn element (see ownerDraw table) |
| `ownerdrawFlag` | constant | Conditional visibility flag (UI_SHOW_FAVORITESERVERS, etc.) |
| `maxChars` | int | Max characters for edit fields |
| `maxPaintChars` | int | Max visible characters |
| `maxCharsGotoNext` | flag (no value) | Auto-advance when maxChars reached |

**Listbox-specific:**

| Property | Type | Notes |
|---|---|---|
| `elementwidth` | int | Column element width |
| `elementheight` | int | Row height |
| `elementtype` | constant | LISTBOX_TEXT |
| `feeder` | constant | Data source: FEEDER_SERVERS, FEEDER_MODS, FEEDER_ALLMAPS, FEEDER_PLAYER_LIST, FEEDER_SERVERSTATUS, FEEDER_MUTELIST, FEEDER_SAVEGAMES, FEEDER_PLAYER_PROFILES |
| `columns` | multi-line | Column count + definitions (complex multi-line syntax) |
| `notselectable` | flag (no value) | Items can't be selected |

**Event Handlers:**

| Handler | Level | Notes |
|---|---|---|
| `action` | itemDef | Click/activation: `{ play "mouse_click"; open menuname }` |
| `onFocus` | itemDef | Focus gained |
| `leaveFocus` | itemDef | Focus lost |
| `accept` | itemDef | Enter/accept on edit fields |
| `mouseEnter` | itemDef | Mouse hover enter |
| `mouseExit` | itemDef | Mouse hover exit |
| `doubleClick` | itemDef | Double-click on listbox items |

**Commands used inside handlers:**
- `play "sound_name"` — play sound ("mouse_click", "mouse_over")
- `open menuname` / `close menuname` — open/close menus (unquoted name)
- `exec "command"` — console command
- `scriptMenuResponse "value"` — send response to GSC
- `setDvar dvarname "value"` — set a dvar
- `show itemname` / `hide itemname` — show/hide items by name
- `setfocus itemname` — set focus to named item
- `setitemcolor itemname property R G B A` — change item/group color
- `fadein itemname` / `fadeout itemname` — fade transitions
- `ingameclose menuname` — close only when in-game
- `openForGameType "settings_%s"` / `closeForGameType "settings_%s"` — gametype-substituted open/close
- `execnow "command"` — execute console command immediately (not deferred)
- `execOnDvarIntValue dvar value "command"` — exec if dvar equals int value
- `execOnDvarFloatValue dvar value "command"` — exec if dvar equals float value
- `setfocusbydvar "dvarname"` — set focus to item based on dvar value (works with `focusdvar`)
- `savegameshow itemname` / `savegamehide itemname` — show/hide based on savegame state
- `restarthide itemname` — hide based on restart state
- `nextlevel` — load the next level
- `getautoupdate` — trigger auto-update
- `uiScript <command>` — engine UI scripts:
  - `loadControls`, `verifyCDKey`, `getCDKey`
  - `loadArenas`, `StartServer`, `JoinServer`
  - `RefreshServers`, `RefreshFilter`, `UpdateFilter`, `stopRefresh`
  - `ServerStatus`, `ServerSort N`, `closeJoin`
  - `CreateFavorite`, `addFavorite`, `DeleteFavorite`
  - `RunMod`, `loadMods`
  - `voteMap`, `voteTypeMap`, `voteTempBan`, `mutePlayer`
  - `addPlayerProfiles`, `startSingleplayer`
  - `openMenuOnDvar`, `openMenuOnDvarNot`, `closeMenuOnDvar`, `closeMenuOnDvarNot`
  - `update ui_setRate`
  - `quit`, `clearError`
  - `loadSavegames`, `Loadgame`, `Savegame`, `forcesave`, `DelSavegame`, `SavegameSort N`
  - `createPlayerProfile`, `deletePlayerProfile`, `loadPlayerProfile`, `selectActivePlayerProfile`, `sortPlayerProfiles`
  - `getLanguage`, `verifyLanguage`, `updateLanguage`
  - `playerstart`, `startMultiplayer`

### Item Types

| Constant | Value | Seen in files | Description |
|---|---|---|---|
| ITEM_TYPE_TEXT | 0 | Yes | Static text / labels |
| ITEM_TYPE_BUTTON | 1 | Yes | Clickable button |
| ITEM_TYPE_RADIOBUTTON | 2 | No | Radio button |
| ITEM_TYPE_CHECKBOX | 3 | No | Checkbox |
| ITEM_TYPE_EDITFIELD | 4 | Yes | Text input |
| ITEM_TYPE_COMBO | 5 | No | Dropdown |
| ITEM_TYPE_LISTBOX | 6 | Yes | Scrollable list |
| ITEM_TYPE_MODEL | 7 | No | 3D model display |
| ITEM_TYPE_OWNERDRAW | 8 | No | Engine-drawn custom |
| ITEM_TYPE_NUMERICFIELD | 9 | Yes | Numeric input |
| ITEM_TYPE_SLIDER | 10 | Yes | Slider control |
| ITEM_TYPE_YESNO | 11 | Yes | Yes/No toggle |
| ITEM_TYPE_MULTI | 12 | Yes | Multiple-choice |
| ITEM_TYPE_DVARENUM | 13 | Yes | Dvar enumeration (options_graphics) |
| ITEM_TYPE_BIND | 14 | Yes | Key binding |
| ITEM_TYPE_MENUMODEL | 15 | No | Menu model |
| ITEM_TYPE_VALIDFILEFIELD | 16 | Yes | Validated file input (save_load, playerprofile) |
| ITEM_TYPE_DECIMALFIELD | 17 | Yes | Decimal/float input (options_look) |
| ITEM_TYPE_UPREDITFIELD | 18 | Yes | Uppercase-only edit field (cdkey) |

### WINDOW_STYLE Constants

| Constant | Value | Seen in files |
|---|---|---|
| WINDOW_STYLE_EMPTY | 0 | Yes |
| WINDOW_STYLE_FILLED | 1 | Yes |
| WINDOW_STYLE_GRADIENT | 2 | No |
| WINDOW_STYLE_SHADER | 3 | Yes |
| WINDOW_STYLE_TEAMCOLOR | 4 | No |
| WINDOW_STYLE_CINEMATIC | 5 | No |
| WINDOW_STYLE_DVAR_SHADER | 6 | Yes — shader name from dvar |
| WINDOW_STYLE_LOADBAR | ? | Yes — loading progress bar |

### Alignment Constants

**Horizontal:** HORIZONTAL_ALIGN_SUBLEFT, HORIZONTAL_ALIGN_LEFT, HORIZONTAL_ALIGN_CENTER, HORIZONTAL_ALIGN_RIGHT, HORIZONTAL_ALIGN_FULLSCREEN, HORIZONTAL_ALIGN_NOSCALE, HORIZONTAL_ALIGN_TO640, HORIZONTAL_ALIGN_CENTER_SAFEAREA, HORIZONTAL_ALIGN_DEFAULT

**Vertical:** VERTICAL_ALIGN_SUBTOP, VERTICAL_ALIGN_TOP, VERTICAL_ALIGN_CENTER, VERTICAL_ALIGN_BOTTOM, VERTICAL_ALIGN_FULLSCREEN, VERTICAL_ALIGN_NOSCALE, VERTICAL_ALIGN_TO480, VERTICAL_ALIGN_CENTER_SAFEAREA, VERTICAL_ALIGN_DEFAULT

Numeric literals also used (e.g., `4 4`).

### ownerDraw Constants (from real files)

**HUD elements (hud.menu):** CG_MANTLE_HINT, CG_CURSORHINT, CG_PLAYER_STANCE, CG_PLAYER_WEAPON_NAME, CG_PLAYER_AMMO_VALUE, CG_PLAYER_AMMO_BACKDROP, CG_PLAYER_WEAPON_MODE_ICON, CG_PLAYER_BAR_HEALTH_BACK, CG_PLAYER_BAR_HEALTH, CG_PLAYER_LOW_HEALTH_OVERLAY, CG_PLAYER_COMPASS_BACK, CG_PLAYER_COMPASS, CG_PLAYER_COMPASS_POINTERS, CG_PLAYER_COMPASS_FRIENDS, CG_OFFHAND_WEAPON_ICON_FRAG, CG_OFFHAND_WEAPON_AMMO_FRAG, CG_OFFHAND_WEAPON_NAME_FRAG, CG_OFFHAND_WEAPON_ICON_SMOKE, CG_OFFHAND_WEAPON_AMMO_SMOKE, CG_OFFHAND_WEAPON_NAME_SMOKE, UI_AMITALKING, UI_TALKER1-4

**SP HUD elements (ui/hud.menu):** CG_HOLD_BREATH_HINT, CG_INVALID_CMD_HINT, CG_TANK_BODY_DIR, CG_TANK_BARREL_DIR, CG_PLAYER_COMPASS_ACTORS, CG_PLAYER_COMPASS_TANKS, CG_DEADQUOTE, CG_MISSION_OBJECTIVE_LIST, CG_MISSION_OBJECTIVE_HEADER

**UI elements:** UI_KEYBINDSTATUS, UI_RECORDLEVEL, UI_NETSOURCE, UI_JOINGAMETYPE, UI_SERVERREFRESHDATE, UI_NETGAMETYPE, UI_STARTMAPCINEMATIC, UI_GLINFO, UI_SAVEGAME_SHOT, UI_SAVEGAMENAME, UI_LOADPROFILING

### Game Integration

- Menu files live in `ui/` or `ui_mp/` directories (`ui_mp/scriptmenus/` for custom script menus)
- `#include` path can be `"ui_mp/menudef.h"` or `"ui/menudef.h"`
- Menus are loaded via GSC: `precacheMenu(game["menu_ingame"])`
- `scriptMenuResponse` bridges menus to GSC game logic
- Packaged into IWD files (renamed ZIP archives) in the `main/` folder

### Useful References

- [Zeroy Wiki - Menu Modding Basics (CoD5, very similar to CoD2)](https://wiki.zeroy.com/index.php?title=Call_of_Duty_5:_Menu_Modding_Basics)
- [Zeroy Wiki - Menu Scripting](https://wiki.zeroy.com/index.php?title=Call_of_Duty_5:_Menu_Scripting)
- [CoD4 Menu Builder (web-based, similar format)](https://sheepwizard.github.io/COD4-MENU-BUILDER/)
- [killtube.org CoD2 menu threads](https://killtube.org/showthread.php?1082-CoD2-create-functions-in-menu-files!)

## Development Plan

### Phase 1: Data Model & Serializer (start here)
1. Define Python classes for `MenuDef`, `ItemDef`, and their properties
2. Build serializer: data model -> valid `.menu` file output
3. Build parser: existing `.menu` files -> data model
4. Collect sample `.menu` files for testing round-trip correctness

### Phase 2: GUI (Tkinter)
5. Canvas-based visual editor (640x480 coordinate space, drag/resize items)
6. Properties panel (side panel to edit selected item properties)
7. Menu tree view (menuDef > itemDef hierarchy)
8. Live preview of generated `.menu` code

### Phase 3: Polish
9. Import/export existing `.menu` files
10. Templates for common patterns (popups, settings sliders, team selection)
11. Validation (missing fields, invalid values)
