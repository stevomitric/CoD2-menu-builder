# Call of Duty 2 — .menu File Format Reference

A comprehensive reference for the `.menu` file format used by the IW engine in Call of Duty 2, derived from analysis of the complete set of stock SP and MP menu files.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Preprocessor](#preprocessor)
4. [assetGlobalDef](#assetglobaldef)
5. [menuDef](#menudef)
6. [itemDef](#itemdef)
7. [Item Types](#item-types)
8. [Event Handlers](#event-handlers)
9. [Action Commands](#action-commands)
10. [Constants Reference](#constants-reference)
11. [Patterns & Techniques](#patterns--techniques)
12. [Game Integration](#game-integration)
13. [External References](#external-references)

---

## Overview

The `.menu` format is a plain-text configuration language used by the IW engine (CoD1 through CoD5+) to define user interface screens. Files use a C-like brace syntax and are preprocessed with support for `#include`, `#define`, and block/line comments.

**Key characteristics:**
- Property names are **case-insensitive** (`fullScreen` = `fullscreen`, `onESC` = `onEsc`)
- Properties are keyword-value pairs — no `=` sign, no semicolons (except inside action blocks)
- Colors are always `R G B A` as floats from `0.0` to `1.0`
- Boolean values can be `0`/`1` or the constants `MENU_TRUE`/`MENU_FALSE`
- Named constants and numeric literals are interchangeable (e.g., `type ITEM_TYPE_BUTTON` and `type 1` are identical)
- Localized string references use an `@` prefix (e.g., `"@MENU_OK"`)
- The game's virtual coordinate space is **640x480**

---

## File Structure

Every `.menu` file follows this general structure:

```c
#include "ui_mp/menudef.h"    // or "ui/menudef.h" for singleplayer

{
    menuDef {
        // menu-level properties
        name        "my_menu"
        rect        0 0 640 480
        visible     0
        fullscreen  0

        itemDef {
            // item-level properties
        }

        itemDef {
            // another item
        }
    }

    menuDef {
        // a second menu in the same file (allowed)
    }
}
```

### Rules

- The entire file content (after `#include`) is wrapped in a single pair of outer `{ }` braces.
- Inside the outer braces, one or more `menuDef` blocks define individual menus.
- Each `menuDef` contains properties and zero or more `itemDef` blocks.
- A single file **can contain multiple `menuDef` blocks**. For example, `ingame.menu` contains both the `ingame` menu and the `leavegame` popup, and `callvote.menu` contains four separate menus.

### Fragment Files

Some `.menu` files are **fragments** — they don't have the outer `{ }` wrapper or a `menuDef` block. They are designed to be `#include`d into other files:

- **Item property fragments** (e.g., `button_mainmenu.menu`) — contain raw property lines to be included inside an `itemDef` body.
- **Item collection fragments** (e.g., `menu_background.menu`, `safearea.menu`, `bars.menu`) — contain bare `itemDef` blocks to be included inside a `menuDef` body.
- **Navigation fragments** (e.g., `navcontrols.menu`, `navcontrols_prev.menu`) — reusable navigation button sets.

---

## Preprocessor

The engine preprocessor runs before parsing and supports:

### `#include`

```c
#include "ui_mp/menudef.h"          // standard MP header (defines all constants)
#include "ui/menudef.h"             // standard SP header
#include "ui_mp/menu_background.menu"   // include inside a menuDef body
#include "ui_mp/button_mainmenu.menu"   // include inside an itemDef body
#include "ui/bars.menu"             // include shared items
#include "ui/safearea.menu"         // include safe area markers
```

Includes can appear at **any nesting level**: top-level, inside a `menuDef`, or inside an `itemDef`.

### `#define`

Macros are used extensively for reusable values:

```c
// Position and size macros
#define ORIGIN_CHOICE1          80 84
#define OPTIONS_WINDOW_POS      5 75
#define OPTIONS_WINDOW_SIZE     360 325
#define OPTIONS_BIND_SIZE       320 13

// Color macros
#define GLOBAL_FOCUSED_COLOR    .98 .827 .58 1
#define GLOBAL_DISABLED_COLOR   .5 .5 .5 1
#define POPMENU_HEADER_COLOR    1 .825 .52 1

// Scalar macros
#define GLOBAL_TEXTSCALE        0.25
#define COMPASS_SIZE            160

// Alignment macros
#define MAIN_RECT_HORZALIGN     HORIZONTAL_ALIGN_DEFAULT
#define MAIN_RECT_VERTALIGN     VERTICAL_ALIGN_DEFAULT
```

Macros can compose within a single property:
```c
rect OPTIONS_WINDOW_POS OPTIONS_WINDOW_SIZE
// expands to: rect 5 75 360 325
```

### Comments

```c
// Line comment
/* Block comment spanning
   multiple lines */
\\ Section marker \\    // backslash-style section dividers (treated as comments)
```

---

## assetGlobalDef

A special top-level block (peer to `menuDef`, not nested inside one) that configures global UI assets. Typically found in `main.menu` and `hud.menu`. Multiple `assetGlobalDef` blocks can exist across files and they merge.

```c
assetGlobalDef {
    // Font definitions: "path" size
    consoleFont     "fonts/consoleFont" 18
    smallFont       "fonts/smallFont" 12
    font            "fonts/normalFont" 16
    bigFont         "fonts/bigFont" 24
    extraBigFont    "fonts/extraBigFont" 32
    boldFont        "fonts/boldFont" 30

    // UI assets
    cursor          "ui/assets/3_cursor3"
    gradientBar     "ui/assets/gradientbar2.tga"
    itemFocusSound  "sound/misc/menu2.wav"

    // Fade behavior
    fadeClamp       1.0         // max alpha for fades
    fadeCycle       1           // cycle duration
    fadeAmount      0.1         // alpha change per cycle (fadeout)
    fadeInAmount    0.1         // alpha change per cycle (fadein)

    // Text shadow
    shadowX         5
    shadowY         5
    shadowColor     0.1 0.1 0.1 0.25
}
```

---

## menuDef

A `menuDef` defines a single menu screen or panel. All properties are optional except `name`.

### Properties

| Property | Type | Description |
|---|---|---|
| `name` | `string` | Unique identifier for the menu. Used by `open`/`close` commands. Can be quoted or unquoted. |
| `visible` | `0\|1` or `MENU_TRUE\|MENU_FALSE` | Whether the menu is initially visible when loaded. |
| `fullscreen` | `0\|1` or `MENU_TRUE\|MENU_FALSE` | Whether the menu covers the entire screen. Fullscreen menus typically block input to menus behind them. |
| `rect` | `x y w h` or `x y w h halign valign` | Position and size of the menu in the 640x480 coordinate space. The optional 5th and 6th parameters specify alignment anchoring (see [Alignment Constants](#alignment-constants)). |
| `style` | `WINDOW_STYLE_*` or `int` | Visual rendering style (see [Window Style Constants](#window-style-constants)). |
| `focuscolor` | `r g b a` | Color applied to focused items. Often set via a macro like `GLOBAL_FOCUSED_COLOR`. |
| `disablecolor` | `r g b a` | Color applied to disabled items. |
| `forecolor` | `r g b a` | Default foreground/text color for items in this menu. |
| `backcolor` | `r g b a` | Background fill color of the menu rect. |
| `bordercolor` | `r g b a` | Border color of the menu rect. |
| `border` | `int` | Border style. |
| `blurWorld` | `float` | Amount to blur the game world behind this menu (e.g., `5.0`). Creates a depth-of-field effect. |
| `soundLoop` | `string` | Sound alias to loop while this menu is open (e.g., `"music_mainmenu_mp"`). Empty string `""` for none. |
| `popup` | *(flag, no value)* | Marks this menu as a popup. Popups render on top of other menus and typically have `blurWorld` or a semi-transparent background. |
| `outOfBoundsClick` | *(flag, no value)* | Closes the menu when the user clicks outside its rect. |

### Event Handlers

| Handler | Syntax | Description |
|---|---|---|
| `onOpen` | `{ commands }` | Executed when the menu is opened. |
| `onClose` | `{ commands }` | Executed when the menu is closed. |
| `onESC` | `{ commands }` | Executed when the user presses Escape while this menu has focus. |
| `execKey` | `"key" { commands }` | Binds a keyboard key at the menu level (not inside an itemDef). Multiple `execKey` entries can exist. |

**Example with all handlers:**
```c
menuDef {
    name        "quickmessage"
    visible     0
    fullscreen  0
    rect        0 0 640 480
    focuscolor  1 1 1 1

    onOpen  { setDvar cl_bypassMouseInput "1" }
    onClose { setDvar cl_bypassMouseInput "0" }
    onESC   { close quickmessage }

    execKey "1" { close quickmessage; open quickcommands }
    execKey "2" { close quickmessage; open quickstatements }
    execKey "3" { close quickmessage; open quickresponses }
}
```

---

## itemDef

An `itemDef` defines a single UI element within a menu. Items are rendered in the order they appear (later items draw on top of earlier ones).

### Positioning & Layout

| Property | Type | Description |
|---|---|---|
| `name` | `string` | Identifier for this item. Used by `show`/`hide`/`setitemcolor`/`setfocus` commands. Quoted or unquoted. |
| `rect` | `x y w h` or `x y w h halign valign` | Position and size relative to the menu (or screen, depending on alignment). Supports negative values, floats, and macros. A width/height of `0` means the engine auto-sizes (used with `ownerDraw`). |
| `origin` | `x y` | Additional offset applied to the item's position. Often a macro like `ORIGIN_QUICKMESSAGEWINDOW`. |
| `visible` | `0\|1` or `MENU_TRUE\|MENU_FALSE` | Whether the item is initially visible. Can be toggled at runtime with `show`/`hide`. |
| `decoration` | *(flag)* | Marks the item as non-interactive. It cannot receive focus, be clicked, or be tabbed to. Used for backgrounds, labels, and decorative elements. |
| `autowrapped` | *(flag)* | Text automatically wraps to fit within the item's rect width. |
| `group` | `string` | Assigns the item to a named group. Groups allow batch operations like `setitemcolor grpName backcolor 1 1 1 1`. |
| `align` | `constant` | Item alignment mode (e.g., `HUD_HORIZONTAL`). |

### Styling

| Property | Type | Description |
|---|---|---|
| `style` | `WINDOW_STYLE_*` or `int` | Visual rendering style. |
| `forecolor` | `r g b a` or macro | Text/foreground color. |
| `backcolor` | `r g b a` or macro | Background fill color. |
| `bordercolor` | `r g b a` or macro | Border color. |
| `border` | `int` or macro | Border style. |
| `bordersize` | `int` | Border thickness in pixels (e.g., `1`, `2`). |
| `outlinecolor` | `r g b a` | Selection/outline color for listbox items. |
| `background` | `string` | Shader or image path (e.g., `"gradient"`, `"gfx/icons/weapon.tga"`). Use `$dvarname` to read the shader name from a dvar at runtime (e.g., `"$levelBriefing"`). |

### Text

| Property | Type | Description |
|---|---|---|
| `text` | `string` | Display text. Use `@` prefix for localized strings (e.g., `"@MENU_OK"` looks up the `MENU_OK` key in the localization files). |
| `textfont` | `constant` | Font selection: `UI_FONT_NORMAL`, `UI_FONT_DEFAULT`, `UI_FONT_BIG`. |
| `textscale` | `float` or macro | Font size multiplier (e.g., `.24`, `.3`, `GLOBAL_TEXTSCALE`). |
| `textalign` | `constant` or `int` | Horizontal text alignment: `ITEM_ALIGN_LEFT` (0), `ITEM_ALIGN_CENTER` (1), `ITEM_ALIGN_RIGHT` (2), `ITEM_ALIGN_CENTER2`. |
| `textalignx` | `int` | Horizontal text offset in pixels (can be negative). |
| `textaligny` | `int` | Vertical text offset in pixels (can be negative). |
| `textstyle` | `constant` or `int` | Text rendering style: `ITEM_TEXTSTYLE_NORMAL`, `ITEM_TEXTSTYLE_SHADOWED`, `ITEM_TEXTSTYLE_SHADOWEDMORE`. |
| `textsavegame` | *(flag)* | Retrieves text content from the current savegame (SP only). |

### Behavior & Data Binding

| Property | Type | Description |
|---|---|---|
| `type` | `ITEM_TYPE_*` or `int` | The item type, which determines rendering and interaction behavior. See [Item Types](#item-types). |
| `dvar` | `string` | Binds the item to a game dvar. For input items (EDITFIELD, SLIDER, YESNO, MULTI), the item reads/writes this dvar. For display items, it shows the dvar's current value. |
| `dvarTest` | `string` | Specifies a dvar to test for conditional visibility. Used with `showDvar`/`hideDvar`. |
| `showDvar` | `{ "value" }` | Show this item only when the `dvarTest` dvar matches the given value. Multiple values separated by semicolons: `{ "2500";"3000";"4000" }`. |
| `hideDvar` | `{ "value" }` | Hide this item when the `dvarTest` dvar matches the given value. Inverse of `showDvar`. |
| `focusdvar` | `{ "value" }` | When used with `setfocusbydvar`, this item receives focus if the dvar's current value matches. |
| `dvarFloatList` | `{ "label" value ... }` | For `ITEM_TYPE_MULTI`: defines choices as label-value pairs where values are floats. Example: `{ "@MENU_OFF" 0 "@MENU_ON" 1 "@MENU_REFLECT" 2 }`. |
| `dvarStrList` | `{ "label", "value", ... }` | For `ITEM_TYPE_MULTI`: defines choices as label-value pairs where values are strings. Note the commas. |
| `dvarEnumList` | `"dvarname"` | For `ITEM_TYPE_DVARENUM`: the item's choices are populated from the dvar's valid enumeration values (e.g., `"r_mode"` for screen resolutions). |
| `dvarfloat` | `"name" default min max` | For `ITEM_TYPE_SLIDER`: binds to a dvar with a default value and min/max range. Example: `"winvoice_mic_reclevel" 65535 0 65535`. |
| `ownerDraw` | `constant` | Designates this item as engine-drawn. The constant identifies what the engine renders (e.g., `CG_PLAYER_AMMO_VALUE`, `UI_NETSOURCE`). See [ownerDraw Constants](#ownerdraw-constants). |
| `ownerdrawFlag` | `constant` | Conditional visibility flag based on engine state. Example: `UI_SHOW_FAVORITESERVERS` shows the item only when the server browser is in favorites mode. |
| `maxChars` | `int` | Maximum number of characters allowed in edit fields. |
| `maxPaintChars` | `int` | Maximum number of characters visible at once (items wider than this will scroll). |
| `maxCharsGotoNext` | *(flag)* | When `maxChars` is reached, automatically advance focus to the next item. Used for CD key entry fields. |

### Listbox-Specific Properties

| Property | Type | Description |
|---|---|---|
| `elementwidth` | `int` | Width of list elements. |
| `elementheight` | `int` | Height of each row in pixels (e.g., `15`, `16`, `20`, `24`). |
| `elementtype` | `constant` | Element rendering type. Only `LISTBOX_TEXT` is seen in practice. |
| `feeder` | `constant` | Data source that populates the list. See [Feeder Constants](#feeder-constants). |
| `columns` | *multi-line* | Column layout definition. First value is column count, followed by column specs. Complex syntax that can span multiple lines. Example: `columns 4 2 50 20` followed by `60 40 10` on the next line. |
| `notselectable` | *(flag)* | Items in the list cannot be selected. |

---

## Item Types

| Constant | Value | Description | Key Properties |
|---|---|---|---|
| `ITEM_TYPE_TEXT` | 0 | Static text label. Non-interactive unless given an `action`. | `text`, `textalign`, `textscale` |
| `ITEM_TYPE_BUTTON` | 1 | Clickable button. | `text`, `action`, `onFocus`, `mouseEnter` |
| `ITEM_TYPE_RADIOBUTTON` | 2 | Radio button (not seen in stock files). | |
| `ITEM_TYPE_CHECKBOX` | 3 | Checkbox (not seen in stock files). | |
| `ITEM_TYPE_EDITFIELD` | 4 | Text input field. | `dvar`, `maxChars`, `maxPaintChars` |
| `ITEM_TYPE_COMBO` | 5 | Dropdown combo box (not seen in stock files). | |
| `ITEM_TYPE_LISTBOX` | 6 | Scrollable list with columns. | `feeder`, `elementheight`, `columns`, `doubleClick` |
| `ITEM_TYPE_MODEL` | 7 | 3D model display (not seen in stock files). | |
| `ITEM_TYPE_OWNERDRAW` | 8 | Engine-drawn custom element (not seen in stock files). | |
| `ITEM_TYPE_NUMERICFIELD` | 9 | Numeric-only input field. | `dvar`, `maxChars` |
| `ITEM_TYPE_SLIDER` | 10 | Horizontal slider control. | `dvarfloat` |
| `ITEM_TYPE_YESNO` | 11 | Yes/No toggle bound to a dvar. | `dvar` |
| `ITEM_TYPE_MULTI` | 12 | Multiple-choice selector. Cycles through options on click. | `dvar`, `dvarFloatList` or `dvarStrList` |
| `ITEM_TYPE_DVARENUM` | 13 | Dropdown populated from a dvar's valid enum values. | `dvarEnumList` |
| `ITEM_TYPE_BIND` | 14 | Key binding control. Click to rebind. | `dvar` (the command to bind) |
| `ITEM_TYPE_MENUMODEL` | 15 | Menu-embedded 3D model (not seen in stock files). | |
| `ITEM_TYPE_VALIDFILEFIELD` | 16 | Text input that only accepts valid filename characters. | `dvar`, `maxChars`, `accept` |
| `ITEM_TYPE_DECIMALFIELD` | 17 | Decimal/float number input. | `dvar`, `maxChars` |
| `ITEM_TYPE_UPREDITFIELD` | 18 | Uppercase-only text input. Used for CD key entry. | `dvar`, `maxChars`, `maxCharsGotoNext` |

---

## Event Handlers

Event handlers are blocks of commands enclosed in `{ }`. Commands within a block are separated by `;`.

### Menu-Level

| Handler | Syntax | Trigger |
|---|---|---|
| `onOpen` | `{ commands }` | Menu is opened |
| `onClose` | `{ commands }` | Menu is closed |
| `onESC` | `{ commands }` | Escape key pressed |
| `execKey` | `"key" { commands }` | Specified key pressed (menu must have focus) |

### Item-Level

| Handler | Syntax | Trigger |
|---|---|---|
| `action` | `{ commands }` | Item is clicked/activated |
| `onFocus` | `{ commands }` | Item gains focus (keyboard/tab navigation) |
| `leaveFocus` | `{ commands }` | Item loses focus |
| `accept` | `{ commands }` | Enter key pressed on an edit field |
| `mouseEnter` | `{ commands }` | Mouse cursor enters the item's rect |
| `mouseExit` | `{ commands }` | Mouse cursor leaves the item's rect |
| `doubleClick` | `{ commands }` | Item is double-clicked (primarily for listboxes) |

### Example: Button with Full Event Handling

```c
itemDef {
    name        "btn_join"
    rect        200 300 200 30
    type        ITEM_TYPE_BUTTON
    text        "@MP_JOIN_GAME"
    textscale   .3
    textalign   ITEM_ALIGN_CENTER
    textalignx  100
    textaligny  22
    forecolor   .9 .9 .9 1
    visible     1
    action      { play "mouse_click"; close joinserver; uiScript JoinServer }
    onFocus     { play "mouse_over"; setitemcolor btn_join backcolor 1 1 1 0.3 }
    mouseEnter  { setitemcolor btn_join bordercolor 1 1 1 1 }
    mouseExit   { setitemcolor btn_join bordercolor .5 .5 .5 .5 }
}
```

---

## Action Commands

These commands can be used inside any event handler block.

### Menu Navigation

| Command | Syntax | Description |
|---|---|---|
| `open` | `open menuname` | Opens a menu by name (unquoted). |
| `close` | `close menuname` | Closes a menu by name. |
| `ingameclose` | `ingameclose menuname` | Closes a menu only when in-game (no-op at main menu). |
| `openForGameType` | `openForGameType "pattern_%s"` | Opens a menu with `%s` replaced by the current gametype name. |
| `closeForGameType` | `closeForGameType "pattern_%s"` | Closes a menu with gametype substitution. |

### Sound

| Command | Syntax | Description |
|---|---|---|
| `play` | `play "alias"` | Plays a sound. Common: `"mouse_click"`, `"mouse_over"`. |

### Console Commands

| Command | Syntax | Description |
|---|---|---|
| `exec` | `exec "command"` | Executes a console command (may be deferred to next frame). |
| `execnow` | `execnow "command"` | Executes a console command immediately. |
| `execOnDvarIntValue` | `execOnDvarIntValue dvar value "cmd"` | Executes command only if dvar equals the specified integer. |
| `execOnDvarFloatValue` | `execOnDvarFloatValue dvar value "cmd"` | Executes command only if dvar equals the specified float. |

### Dvar Manipulation

| Command | Syntax | Description |
|---|---|---|
| `setDvar` | `setDvar name "value"` | Sets a dvar to a value. |

### Item Manipulation

| Command | Syntax | Description |
|---|---|---|
| `show` | `show name` | Shows a hidden item by name. |
| `hide` | `hide name` | Hides a visible item by name. |
| `fadein` | `fadein name` | Fades in an item. |
| `fadeout` | `fadeout name` | Fades out an item. |
| `setfocus` | `setfocus name` | Sets keyboard focus to the named item. |
| `setfocusbydvar` | `setfocusbydvar "dvar"` | Sets focus to the item whose `focusdvar` matches the dvar's current value. |
| `setitemcolor` | `setitemcolor name prop r g b a` | Changes a color property on an item or group. `prop` is `forecolor`, `backcolor`, `bordercolor`, etc. When `name` is a group name, all items in that group are affected. |

### Game State

| Command | Syntax | Description |
|---|---|---|
| `scriptMenuResponse` | `scriptMenuResponse "value"` | Sends a response string to GSC code. The GSC `menuResponse` callback receives this value. |
| `savegameshow` | `savegameshow name` | Shows item only if a savegame exists. |
| `savegamehide` | `savegamehide name` | Hides item if a savegame exists. |
| `restarthide` | `restarthide name` | Hides item based on restart state. |
| `nextlevel` | `nextlevel` | Loads the next level/mission. |
| `getautoupdate` | `getautoupdate` | Triggers the auto-update download. |

### uiScript Commands

`uiScript` invokes engine-level UI operations. Syntax: `uiScript command` or `uiScript command argument`.

**General:**
- `quit` — quit the game
- `clearError` — clear error state
- `startSingleplayer` / `startMultiplayer` — switch game mode
- `playerstart` — start the game/mission from pregame screen

**Controls:**
- `loadControls` — reload control bindings to defaults

**CD Key:**
- `verifyCDKey` — validate entered CD key
- `getCDKey` — load current CD key into edit fields

**Server Browser:**
- `RefreshServers` / `RefreshFilter` / `UpdateFilter` / `stopRefresh` — server list operations
- `JoinServer` / `closeJoin` — join selected server
- `ServerStatus` — query server status
- `ServerSort N` — sort by column N
- `CreateFavorite` / `addFavorite` / `DeleteFavorite` — favorite server management

**Server Creation:**
- `loadArenas` — load available maps
- `StartServer` — launch server with current settings

**Voting:**
- `voteMap` / `voteTypeMap` / `voteTempBan` / `mutePlayer` — in-game voting actions

**Mods:**
- `RunMod` / `loadMods` — mod management

**Save/Load (SP):**
- `loadSavegames` / `Loadgame` / `Savegame` / `forcesave` / `DelSavegame` — save/load operations
- `SavegameSort N` — sort savegame list by column

**Player Profiles:**
- `createPlayerProfile` / `deletePlayerProfile` / `loadPlayerProfile` / `selectActivePlayerProfile` / `sortPlayerProfiles` — profile management
- `addPlayerProfiles` — add to profile list

**Language:**
- `getLanguage` / `verifyLanguage` / `updateLanguage` — language settings

**Conditional Operations:**
- `openMenuOnDvar` / `openMenuOnDvarNot` — open a menu conditionally based on dvar value
- `closeMenuOnDvar` / `closeMenuOnDvarNot` — close a menu conditionally
- `update ui_setRate` — update rate setting UI

---

## Constants Reference

### Window Style Constants

| Constant | Value | Description |
|---|---|---|
| `WINDOW_STYLE_EMPTY` | 0 | No background rendering. |
| `WINDOW_STYLE_FILLED` | 1 | Solid color fill using `backcolor`. |
| `WINDOW_STYLE_GRADIENT` | 2 | Gradient fill. |
| `WINDOW_STYLE_SHADER` | 3 | Renders the `background` shader/image. |
| `WINDOW_STYLE_TEAMCOLOR` | 4 | Fills with the player's team color. |
| `WINDOW_STYLE_CINEMATIC` | 5 | Renders a cinematic/video. |
| `WINDOW_STYLE_DVAR_SHADER` | 6 | Like SHADER, but reads the shader name from the `dvar` property at runtime. |
| `WINDOW_STYLE_LOADBAR` | 7(?) | Engine-drawn loading progress bar. |

### Alignment Constants

Used as the 5th and 6th parameters of `rect` to control how an item is anchored on screen.

**Horizontal:**

| Constant | Description |
|---|---|
| `HORIZONTAL_ALIGN_SUBLEFT` | Left edge of the physical screen (ignores 4:3 safe area). |
| `HORIZONTAL_ALIGN_LEFT` | Left edge of the viewable/safe area. |
| `HORIZONTAL_ALIGN_CENTER` | Horizontal center of the screen. |
| `HORIZONTAL_ALIGN_RIGHT` | Right edge of the viewable/safe area. |
| `HORIZONTAL_ALIGN_FULLSCREEN` | Stretches to full screen width, ignoring safe area. |
| `HORIZONTAL_ALIGN_NOSCALE` | Uses exact pixel coordinates, no scaling. |
| `HORIZONTAL_ALIGN_TO640` | Scales coordinates into the 0-640 range. |
| `HORIZONTAL_ALIGN_CENTER_SAFEAREA` | Center of the safe area. |
| `HORIZONTAL_ALIGN_DEFAULT` | Engine default alignment. |

**Vertical:**

| Constant | Description |
|---|---|
| `VERTICAL_ALIGN_SUBTOP` | Top edge of the physical screen. |
| `VERTICAL_ALIGN_TOP` | Top edge of the viewable/safe area. |
| `VERTICAL_ALIGN_CENTER` | Vertical center of the screen. |
| `VERTICAL_ALIGN_BOTTOM` | Bottom edge of the viewable/safe area. |
| `VERTICAL_ALIGN_FULLSCREEN` | Stretches to full screen height. |
| `VERTICAL_ALIGN_NOSCALE` | Uses exact pixel coordinates. |
| `VERTICAL_ALIGN_TO480` | Scales coordinates into the 0-480 range. |
| `VERTICAL_ALIGN_CENTER_SAFEAREA` | Center of the safe area. |
| `VERTICAL_ALIGN_DEFAULT` | Engine default alignment. |

### Text Alignment Constants

| Constant | Value | Description |
|---|---|---|
| `ITEM_ALIGN_LEFT` | 0 | Left-aligned text. |
| `ITEM_ALIGN_CENTER` | 1 | Center-aligned text. |
| `ITEM_ALIGN_RIGHT` | 2 | Right-aligned text. |
| `ITEM_ALIGN_CENTER2` | ? | Alternate center alignment. |

### Text Style Constants

| Constant | Description |
|---|---|
| `ITEM_TEXTSTYLE_NORMAL` | Plain text, no effects. |
| `ITEM_TEXTSTYLE_SHADOWED` | Text with a drop shadow. |
| `ITEM_TEXTSTYLE_SHADOWEDMORE` | Text with a heavier/larger shadow. |

### Font Constants

| Constant | Description |
|---|---|
| `UI_FONT_DEFAULT` | Default font (usually normalFont). |
| `UI_FONT_NORMAL` | Normal weight font. |
| `UI_FONT_BIG` | Larger font. |

### Feeder Constants

Feeders provide dynamic data to `ITEM_TYPE_LISTBOX` items.

| Constant | Description |
|---|---|
| `FEEDER_SERVERS` | Server browser list. |
| `FEEDER_ALLMAPS` | Available maps. |
| `FEEDER_MODS` | Available mods. |
| `FEEDER_PLAYER_LIST` | Player list. |
| `FEEDER_SERVERSTATUS` | Server status details. |
| `FEEDER_MUTELIST` | Mutable player list. |
| `FEEDER_SAVEGAMES` | Savegame list (SP). |
| `FEEDER_PLAYER_PROFILES` | Player profile list. |

### ownerDraw Constants

Engine-drawn elements referenced by the `ownerDraw` property.

**HUD — Weapons & Ammo:**
- `CG_PLAYER_WEAPON_NAME` — current weapon name
- `CG_PLAYER_AMMO_VALUE` — ammo count text
- `CG_PLAYER_AMMO_BACKDROP` — ammo counter background
- `CG_PLAYER_WEAPON_MODE_ICON` — weapon fire mode icon
- `CG_OFFHAND_WEAPON_ICON_FRAG` / `CG_OFFHAND_WEAPON_AMMO_FRAG` / `CG_OFFHAND_WEAPON_NAME_FRAG` — frag grenade
- `CG_OFFHAND_WEAPON_ICON_SMOKE` / `CG_OFFHAND_WEAPON_AMMO_SMOKE` / `CG_OFFHAND_WEAPON_NAME_SMOKE` — smoke grenade

**HUD — Health & Status:**
- `CG_PLAYER_BAR_HEALTH_BACK` — health bar background
- `CG_PLAYER_BAR_HEALTH` — health bar fill
- `CG_PLAYER_LOW_HEALTH_OVERLAY` — low health screen overlay
- `CG_PLAYER_STANCE` — stance indicator (stand/crouch/prone)

**HUD — Compass:**
- `CG_PLAYER_COMPASS_BACK` — compass background
- `CG_PLAYER_COMPASS` — compass face
- `CG_PLAYER_COMPASS_POINTERS` — objective pointers on compass
- `CG_PLAYER_COMPASS_FRIENDS` — friendly player markers (MP)
- `CG_PLAYER_COMPASS_ACTORS` — friendly NPC markers (SP)
- `CG_PLAYER_COMPASS_TANKS` — tank markers (SP)

**HUD — Hints:**
- `CG_MANTLE_HINT` — mantle prompt
- `CG_CURSORHINT` — context-sensitive cursor hint
- `CG_HOLD_BREATH_HINT` — hold breath prompt (SP, sniping)
- `CG_INVALID_CMD_HINT` — invalid command hint

**HUD — Vehicles:**
- `CG_TANK_BODY_DIR` — tank body direction indicator
- `CG_TANK_BARREL_DIR` — tank barrel direction indicator

**HUD — Communication:**
- `UI_AMITALKING` — local voice chat indicator
- `UI_TALKER1` through `UI_TALKER4` — remote voice chat indicators

**HUD — Misc:**
- `CG_DEADQUOTE` — death quote text
- `CG_MISSION_OBJECTIVE_LIST` — mission objective checklist (SP)
- `CG_MISSION_OBJECTIVE_HEADER` — mission objective header (SP)

**UI — Menus:**
- `UI_KEYBINDSTATUS` — key binding status text
- `UI_RECORDLEVEL` — voice recording level meter
- `UI_NETSOURCE` — network source selector
- `UI_JOINGAMETYPE` — gametype filter
- `UI_SERVERREFRESHDATE` — server refresh timestamp
- `UI_NETGAMETYPE` — gametype selector
- `UI_STARTMAPCINEMATIC` — map preview cinematic
- `UI_GLINFO` — GL/driver info text
- `UI_SAVEGAME_SHOT` — savegame screenshot preview
- `UI_SAVEGAMENAME` — savegame name display
- `UI_LOADPROFILING` — load profiling info

---

## Patterns & Techniques

### Conditional Visibility with dvarTest

Create two versions of an item at the same position — one for enabled, one for disabled — using `dvarTest` + `showDvar`:

```c
// Enabled version — shown when weapon is allowed
itemDef {
    name        "weapon_mp40"
    text        "MP40"
    rect        10 50 200 20
    forecolor   1 1 1 1
    visible     1
    dvartest    "ui_allow_mp40"
    showDvar    { "1" }
    action      { scriptMenuResponse "mp40" }
}

// Disabled version — shown when weapon is disallowed
itemDef {
    name        "weapon_mp40_disabled"
    text        "MP40"
    rect        10 50 200 20
    forecolor   .5 .5 .5 .5
    visible     1
    decoration
    dvartest    "ui_allow_mp40"
    showDvar    { "0" }
}
```

Multiple values can be matched with semicolons:
```c
showdvar    { "2500";"3000";"4000" }
```

### Reusable Item Templates via #include

A fragment file like `button_mainmenu.menu` defines shared button properties:
```c
// button_mainmenu.menu (fragment — no braces)
name        "button"
type        ITEM_TYPE_BUTTON
textfont    UI_FONT_NORMAL
textscale   .35
textstyle   ITEM_TEXTSTYLE_SHADOWED
style       WINDOW_STYLE_FILLED
```

Used inside an itemDef:
```c
itemDef {
    #include "ui_mp/button_mainmenu.menu"
    rect        100 200 200 30
    text        "@MENU_JOIN_GAME"
    action      { open joinserver }
    onFocus     { play "mouse_over" }
}
```

### Group-Based Color Changes

Use `group` and `setitemcolor` for tab-like interfaces:

```c
// Tab buttons
itemDef {
    name    "tab_general"
    group   "grpTabs"
    action  {
        setitemcolor grpTabs backcolor 0.3 0.3 0.3 1;   // reset all tabs
        setitemcolor tab_general backcolor 1 1 1 1;       // highlight active
        show grpGeneral;
        hide grpAdvanced;
    }
}
```

### Dynamic Shader from Dvar

Use `WINDOW_STYLE_DVAR_SHADER` to display an image whose name comes from a dvar:

```c
itemDef {
    style   WINDOW_STYLE_DVAR_SHADER
    dvar    "ui_background"         // dvar contains the shader name
    rect    0 0 640 480
}
```

Or use the `$` prefix in `background`:
```c
itemDef {
    style       WINDOW_STYLE_SHADER
    background  "$levelBriefing"    // reads shader name from "levelBriefing" dvar
}
```

### Focus-Based Dvar Selection

Use `focusdvar` + `setfocusbydvar` for items that should auto-select based on a dvar value:

```c
menuDef {
    onOpen { setfocusbydvar "g_gameskill" }

    itemDef {
        text        "Easy"
        focusdvar   { "0" }
        action      { setdvar g_gameskill "0" }
    }
    itemDef {
        text        "Normal"
        focusdvar   { "1" }
        action      { setdvar g_gameskill "1" }
    }
}
```

---

## Game Integration

### File Locations

| Path | Purpose |
|---|---|
| `ui/` | Single-player menus |
| `ui_mp/` | Multiplayer menus |
| `ui_mp/scriptmenus/` | Custom script-triggered menus (MP) |
| `ui/scriptmenus/` | Custom script-triggered menus (SP) |
| `ui/menudef.h` / `ui_mp/menudef.h` | Constant definitions header |

### Loading Menus from GSC

```c
// In maps/mp/gametypes/_menus.gsc
precacheMenu(game["menu_ingame"]);    // preload menu for use

// Opening a menu for a player
self openMenu(game["menu_ingame"]);

// Handling menu responses
menuResponse(menu, response) {
    if (response == "endgame") {
        // handle end game
    }
}
```

### Packaging

Menu files are packaged into IWD files (renamed `.zip` archives) placed in the game's `main/` directory. The engine reads from all IWD files, with later-numbered files taking priority.

---

## External References

- [Zeroy Wiki — Menu Modding Basics (CoD5)](https://wiki.zeroy.com/index.php?title=Call_of_Duty_5:_Menu_Modding_Basics) — Most comprehensive menu format reference; CoD5 shares nearly the same syntax as CoD2.
- [Zeroy Wiki — Menu Scripting (CoD5)](https://wiki.zeroy.com/index.php?title=Call_of_Duty_5:_Menu_Scripting) — Detailed scripting reference.
- [CoD4 Menu Builder](https://sheepwizard.github.io/COD4-MENU-BUILDER/) — Web-based visual editor for a very similar format.
- [killtube.org — CoD2 menu files](https://killtube.org/showthread.php?1082-CoD2-create-functions-in-menu-files!) — Practical examples and community discussion.
- [Editing the Main Menu (ModDB)](https://www.moddb.com/games/call-of-duty-2/tutorials/editing-the-main-menu) — Step-by-step tutorial.
- [CoD2 Mod Tools](https://www.moddb.com/games/call-of-duty-2/downloads/call-of-duty-2-mod-tools) — Official mod tools from Activision.
