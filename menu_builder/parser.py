"""Parse .menu files into the data model.

This parser handles the brace-based syntax, quoted strings, and action blocks.
It does NOT expand #define macros — macro references are preserved as-is.
#include directives at the top level are captured; nested includes are skipped.
"""

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

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


class ParseError(Exception):
    """Raised when the parser encounters invalid syntax."""

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        prefix = f"Line {line}: " if line is not None else ""
        super().__init__(f"{prefix}{message}")


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Token types
_T_LBRACE = "{"
_T_RBRACE = "}"
_T_STRING = "STRING"  # quoted string (value without quotes)
_T_WORD = "WORD"  # unquoted token


def _tokenize(source: str) -> list[tuple[str, str, int]]:
    """Tokenize .menu source into (type, value, line_number) tuples.

    Strips comments and preprocessor lines (except #include at the top).
    """
    tokens: list[tuple[str, str, int]] = []
    i = 0
    line = 1
    length = len(source)

    while i < length:
        ch = source[i]

        # Newline
        if ch == "\n":
            line += 1
            i += 1
            continue

        # Whitespace
        if ch in " \t\r":
            i += 1
            continue

        # Line comment: //
        if ch == "/" and i + 1 < length and source[i + 1] == "/":
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Block comment: /* ... */
        if ch == "/" and i + 1 < length and source[i + 1] == "*":
            i += 2
            while i + 1 < length and not (source[i] == "*" and source[i + 1] == "/"):
                if source[i] == "\n":
                    line += 1
                i += 1
            i += 2  # skip */
            continue

        # Backslash comment: \\ ... \\ (section markers)
        if ch == "\\" and i + 1 < length and source[i + 1] == "\\":
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Preprocessor directive
        if ch == "#":
            start = i
            # Read the full directive (may span lines with backslash continuation)
            while i < length and source[i] != "\n":
                if source[i] == "\\" and i + 1 < length and source[i + 1] == "\n":
                    i += 2
                    line += 1
                else:
                    i += 1
            # We skip preprocessor lines in the token stream — the caller
            # extracts the #include header separately before tokenizing.
            continue

        # Braces
        if ch == "{":
            tokens.append((_T_LBRACE, "{", line))
            i += 1
            continue
        if ch == "}":
            tokens.append((_T_RBRACE, "}", line))
            i += 1
            continue

        # Quoted string
        if ch == '"':
            i += 1
            start = i
            while i < length and source[i] != '"':
                if source[i] == "\\" and i + 1 < length:
                    i += 2  # skip escaped char
                else:
                    if source[i] == "\n":
                        line += 1
                    i += 1
            value = source[start:i]
            i += 1  # skip closing quote
            tokens.append((_T_STRING, value, line))
            continue

        # Semicolon inside action blocks — treat as a word
        if ch == ";":
            tokens.append((_T_WORD, ";", line))
            i += 1
            continue

        # Unquoted word (identifier, number, constant)
        if ch not in " \t\r\n{}\"":
            start = i
            while i < length and source[i] not in " \t\r\n{}\"":
                # Allow semicolons to break words only inside braces (handled elsewhere)
                if source[i] == ";":
                    break
                i += 1
            tokens.append((_T_WORD, source[start:i], line))
            continue

        # Skip any other character
        i += 1

    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class _Parser:
    """Stateful parser that walks through a token list."""

    def __init__(self, tokens: list[tuple[str, str, int]]):
        self.tokens = tokens
        self.pos = 0

    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def peek(self) -> tuple[str, str, int] | None:
        if self.at_end():
            return None
        return self.tokens[self.pos]

    def advance(self) -> tuple[str, str, int]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, ttype: str) -> tuple[str, str, int]:
        tok = self.advance()
        if tok[0] != ttype:
            raise ParseError(f"Expected {ttype}, got {tok[0]} ({tok[1]!r})", tok[2])
        return tok

    def read_value(self) -> str:
        """Read the next token as a value (string or word)."""
        tok = self.advance()
        if tok[0] not in (_T_STRING, _T_WORD):
            raise ParseError(f"Expected value, got {tok[0]} ({tok[1]!r})", tok[2])
        return tok[1]

    def read_block(self) -> str:
        """Read a { ... } block and return the raw content as a string.

        Handles nested braces.
        """
        self.expect(_T_LBRACE)
        depth = 1
        parts: list[str] = []
        while not self.at_end() and depth > 0:
            tok = self.advance()
            if tok[0] == _T_LBRACE:
                depth += 1
                parts.append("{")
            elif tok[0] == _T_RBRACE:
                depth -= 1
                if depth > 0:
                    parts.append("}")
            elif tok[0] == _T_STRING:
                parts.append(f'"{tok[1]}"')
            elif tok[1] == ";":
                parts.append(";")
            else:
                parts.append(tok[1])
        result = " ".join(parts)
        return result if result else None

    def read_color(self) -> Color:
        """Read four float tokens as an RGBA color."""
        r = float(self.read_value())
        g = float(self.read_value())
        b = float(self.read_value())
        a = float(self.read_value())
        return Color(r, g, b, a)

    def read_rect(self) -> Rect:
        """Read 4 or 6 tokens as a rect.

        Peeks ahead to determine if alignment constants follow.
        """
        x = float(self.read_value())
        y = float(self.read_value())
        w = float(self.read_value())
        h = float(self.read_value())
        halign = None
        valign = None
        # Check if the next two tokens are alignment constants (not a known keyword)
        if not self.at_end():
            nxt = self.peek()
            if nxt and nxt[0] == _T_WORD and (
                nxt[1].startswith("HORIZONTAL_ALIGN") or nxt[1].isdigit()
            ):
                halign = self.read_value()
                valign = self.read_value()
        return Rect(x, y, w, h, halign, valign)

    def read_show_hide_dvar(self) -> list[str]:
        """Read a showDvar/hideDvar block: { "val1" ; "val2" } or { "val1";"val2" }."""
        self.expect(_T_LBRACE)
        values: list[str] = []
        while not self.at_end():
            tok = self.peek()
            if tok is None or tok[0] == _T_RBRACE:
                break
            t = self.advance()
            if t[1] == ";":
                continue
            # Handle values like "2500";"3000" (tokenizer may keep semicolons attached)
            val = t[1].strip(";").strip('"')
            if val:
                values.append(val)
        self.expect(_T_RBRACE)
        return values

    def read_dvar_float_list(self) -> list[DvarMultiOption]:
        """Read dvarFloatList: { "label" value "label" value ... }."""
        self.expect(_T_LBRACE)
        options: list[DvarMultiOption] = []
        while not self.at_end():
            tok = self.peek()
            if tok is None or tok[0] == _T_RBRACE:
                break
            label = self.read_value()
            value = self.read_value()
            options.append(DvarMultiOption(label, value, is_float=True))
        self.expect(_T_RBRACE)
        return options

    def read_dvar_str_list(self) -> list[DvarMultiOption]:
        """Read dvarStrList: { "label" "value" "label" "value" ... }.

        Commas between pairs are optional and ignored.
        """
        self.expect(_T_LBRACE)
        options: list[DvarMultiOption] = []
        while not self.at_end():
            tok = self.peek()
            if tok is None or tok[0] == _T_RBRACE:
                break
            # Skip commas
            if tok[1] == ",":
                self.advance()
                continue
            label = self.read_value().strip(",")
            # Skip comma between label and value
            if not self.at_end() and self.peek() and self.peek()[1] == ",":
                self.advance()
            value = self.read_value().strip(",")
            options.append(DvarMultiOption(label, value, is_float=False))
        self.expect(_T_RBRACE)
        return options


def _parse_item(parser: _Parser) -> ItemDef:
    """Parse an itemDef block."""
    parser.expect(_T_LBRACE)
    item = ItemDef()

    while not parser.at_end():
        tok = parser.peek()
        if tok is None or tok[0] == _T_RBRACE:
            break

        t = parser.advance()
        key = t[1].lower()

        if key == "name":
            item.name = parser.read_value()
        elif key == "rect":
            item.rect = parser.read_rect()
        elif key == "origin":
            ox = float(parser.read_value())
            oy = float(parser.read_value())
            item.origin = (ox, oy)
        elif key == "visible":
            val = parser.read_value()
            item.visible = val not in ("0", "MENU_FALSE")
        elif key == "decoration":
            item.decoration = True
        elif key == "autowrapped":
            item.autowrapped = True
        elif key == "group":
            item.group = parser.read_value()
        elif key == "style":
            item.style = _parse_int_or_const(parser.read_value())
        elif key == "forecolor":
            item.forecolor = parser.read_color()
        elif key == "backcolor":
            item.backcolor = parser.read_color()
        elif key == "bordercolor":
            item.bordercolor = parser.read_color()
        elif key == "border":
            item.border = int(parser.read_value())
        elif key == "bordersize":
            item.bordersize = int(parser.read_value())
        elif key == "outlinecolor":
            item.outlinecolor = parser.read_color()
        elif key == "background":
            item.background = parser.read_value()
        elif key == "align":
            item.align = parser.read_value()
        elif key == "type":
            item.type = _parse_int_or_const(parser.read_value())
        elif key == "text":
            item.text = parser.read_value()
        elif key == "textfont":
            item.textfont = parser.read_value()
        elif key == "textscale":
            item.textscale = float(parser.read_value())
        elif key == "textalign":
            item.textalign = _parse_int_or_const(parser.read_value())
        elif key == "textalignx":
            item.textalignx = int(float(parser.read_value()))
        elif key == "textaligny":
            item.textaligny = int(float(parser.read_value()))
        elif key == "textstyle":
            item.textstyle = _parse_int_or_const(parser.read_value())
        elif key == "dvar":
            item.dvar = parser.read_value()
        elif key == "dvartest":
            item.dvar_test = parser.read_value()
        elif key == "showdvar":
            item.show_dvar = parser.read_show_hide_dvar()
        elif key == "hidedvar":
            item.hide_dvar = parser.read_show_hide_dvar()
        elif key == "dvarfloatlist":
            item.dvar_multi_options = parser.read_dvar_float_list()
        elif key == "dvarstrlist":
            item.dvar_multi_options = parser.read_dvar_str_list()
        elif key == "dvarenumlist":
            item.dvar_enum_list = parser.read_value()
        elif key == "dvarfloat":
            dvar_name = parser.read_value()
            default = float(parser.read_value())
            min_val = float(parser.read_value())
            max_val = float(parser.read_value())
            item.dvar_slider = DvarSlider(dvar_name, default, min_val, max_val)
        elif key == "ownerdraw":
            item.owner_draw = parser.read_value()
        elif key == "ownerdrawflag":
            item.owner_draw_flag = parser.read_value()
        elif key == "maxchars":
            item.max_chars = int(parser.read_value())
        elif key == "maxpaintchars":
            item.max_paint_chars = int(parser.read_value())
        elif key == "maxcharsgotomext" or key == "maxcharsgotoext" or key == "maxcharsgotone" or key == "maxcharsgotoenxt":
            # Handle typo variants — but the correct one is below
            item.max_chars_goto_next = True
        elif key == "maxcharsgotonext":
            item.max_chars_goto_next = True
        elif key == "elementwidth":
            item.element_width = int(float(parser.read_value()))
        elif key == "elementheight":
            item.element_height = int(float(parser.read_value()))
        elif key == "elementtype":
            item.element_type = parser.read_value()
        elif key == "feeder":
            item.feeder = parser.read_value()
        elif key == "columns":
            item.columns = _read_columns(parser)
        elif key == "notselectable":
            item.not_selectable = True
        elif key == "action":
            item.action = parser.read_block()
        elif key == "onfocus":
            item.on_focus = parser.read_block()
        elif key == "leavefocus":
            item.leave_focus = parser.read_block()
        elif key == "accept":
            item.accept = parser.read_block()
        elif key == "mouseenter":
            item.mouse_enter = parser.read_block()
        elif key == "mouseexit":
            item.mouse_exit = parser.read_block()
        elif key == "doubleclick":
            item.double_click = parser.read_block()
        else:
            # Unknown property — skip its value(s) gracefully
            _skip_unknown_value(parser)

    parser.expect(_T_RBRACE)
    return item


def _parse_menu(parser: _Parser) -> MenuDef:
    """Parse a menuDef block."""
    parser.expect(_T_LBRACE)
    menu = MenuDef()

    while not parser.at_end():
        tok = parser.peek()
        if tok is None or tok[0] == _T_RBRACE:
            break

        t = parser.advance()
        key = t[1].lower()

        if key == "name":
            menu.name = parser.read_value()
        elif key == "visible":
            val = parser.read_value()
            menu.visible = val not in ("0", "MENU_FALSE")
        elif key == "fullscreen":
            val = parser.read_value()
            menu.fullscreen = val not in ("0", "MENU_FALSE")
        elif key == "rect":
            menu.rect = parser.read_rect()
        elif key == "style":
            menu.style = _parse_int_or_const(parser.read_value())
        elif key == "focuscolor":
            menu.focuscolor = parser.read_color()
        elif key == "disablecolor":
            menu.disablecolor = parser.read_color()
        elif key == "forecolor":
            menu.forecolor = parser.read_color()
        elif key == "backcolor":
            menu.backcolor = parser.read_color()
        elif key == "bordercolor":
            menu.bordercolor = parser.read_color()
        elif key == "border":
            menu.border = int(parser.read_value())
        elif key == "blurworld":
            menu.blur_world = float(parser.read_value())
        elif key == "soundloop":
            menu.sound_loop = parser.read_value()
        elif key == "popup":
            menu.popup = True
        elif key == "outofboundsclick":
            menu.out_of_bounds_click = True
        elif key == "onopen":
            menu.on_open = parser.read_block()
        elif key == "onclose":
            menu.on_close = parser.read_block()
        elif key == "onesc":
            menu.on_esc = parser.read_block()
        elif key == "execkey":
            key_char = parser.read_value()
            commands = parser.read_block()
            menu.exec_keys.append(ExecKey(key_char, commands))
        elif key == "itemdef":
            menu.items.append(_parse_item(parser))
        else:
            # Unknown menu property — skip its value(s)
            _skip_unknown_value(parser)

    parser.expect(_T_RBRACE)
    return menu


def _read_columns(parser: _Parser) -> str:
    """Read column definition — first token is count, then count * 3 values."""
    parts: list[str] = []
    count_str = parser.read_value()
    parts.append(count_str)
    try:
        count = int(count_str)
    except ValueError:
        return count_str
    for _ in range(count * 3):
        if parser.at_end():
            break
        tok = parser.peek()
        if tok is None or tok[0] in (_T_LBRACE, _T_RBRACE):
            break
        # Stop if we hit a known keyword (means columns definition ended)
        if tok[0] == _T_WORD and tok[1].lower() in _KNOWN_ITEM_KEYWORDS:
            break
        parts.append(parser.read_value())
    return " ".join(parts)


# Known item keywords to detect end of column definitions
_KNOWN_ITEM_KEYWORDS = {
    "name", "rect", "origin", "visible", "decoration", "autowrapped", "group",
    "style", "forecolor", "backcolor", "bordercolor", "border", "bordersize",
    "outlinecolor", "background", "align", "type", "text", "textfont",
    "textscale", "textalign", "textalignx", "textaligny", "textstyle",
    "dvar", "dvartest", "showdvar", "hidedvar", "dvarfloatlist", "dvarstrlist",
    "dvarenumlist", "dvarfloat", "ownerdraw", "ownerdrawflag", "maxchars",
    "maxpaintchars", "maxcharsgotonext", "elementwidth", "elementheight",
    "elementtype", "feeder", "columns", "notselectable",
    "action", "onfocus", "leavefocus", "accept", "mouseenter", "mouseexit",
    "doubleclick", "itemdef",
}


def _skip_unknown_value(parser: _Parser) -> None:
    """Skip the value(s) of an unknown property."""
    if parser.at_end():
        return
    tok = parser.peek()
    if tok is None:
        return
    if tok[0] == _T_LBRACE:
        # It's a block — read and discard
        parser.read_block()
    elif tok[0] in (_T_STRING, _T_WORD):
        # Skip single value token — but don't consume known keywords
        if tok[0] == _T_WORD and tok[1].lower() in (
            _KNOWN_ITEM_KEYWORDS | {"menudef", "itemdef", "assetglobaldef"}
        ):
            return
        parser.advance()


# Mapping from named constants to integer values
_CONST_MAP: dict[str, int] = {
    # Window styles
    "WINDOW_STYLE_EMPTY": 0,
    "WINDOW_STYLE_FILLED": 1,
    "WINDOW_STYLE_GRADIENT": 2,
    "WINDOW_STYLE_SHADER": 3,
    "WINDOW_STYLE_TEAMCOLOR": 4,
    "WINDOW_STYLE_CINEMATIC": 5,
    "WINDOW_STYLE_DVAR_SHADER": 6,
    # Item types
    "ITEM_TYPE_TEXT": 0,
    "ITEM_TYPE_BUTTON": 1,
    "ITEM_TYPE_RADIOBUTTON": 2,
    "ITEM_TYPE_CHECKBOX": 3,
    "ITEM_TYPE_EDITFIELD": 4,
    "ITEM_TYPE_COMBO": 5,
    "ITEM_TYPE_LISTBOX": 6,
    "ITEM_TYPE_MODEL": 7,
    "ITEM_TYPE_OWNERDRAW": 8,
    "ITEM_TYPE_NUMERICFIELD": 9,
    "ITEM_TYPE_SLIDER": 10,
    "ITEM_TYPE_YESNO": 11,
    "ITEM_TYPE_MULTI": 12,
    "ITEM_TYPE_DVARENUM": 13,
    "ITEM_TYPE_BIND": 14,
    "ITEM_TYPE_MENUMODEL": 15,
    "ITEM_TYPE_VALIDFILEFIELD": 16,
    "ITEM_TYPE_DECIMALFIELD": 17,
    "ITEM_TYPE_UPREDITFIELD": 18,
    # Text alignment
    "ITEM_ALIGN_LEFT": 0,
    "ITEM_ALIGN_CENTER": 1,
    "ITEM_ALIGN_RIGHT": 2,
    # Text style
    "ITEM_TEXTSTYLE_NORMAL": 0,
    "ITEM_TEXTSTYLE_SHADOWED": 3,
    "ITEM_TEXTSTYLE_SHADOWEDMORE": 6,
}


def _parse_int_or_const(value: str) -> int:
    """Convert a value to int, resolving named constants."""
    if value in _CONST_MAP:
        return _CONST_MAP[value]
    try:
        return int(value)
    except ValueError:
        try:
            return int(float(value))
        except ValueError:
            # Unknown constant — return 0 as fallback
            return 0


def _extract_include(source: str) -> str:
    """Extract the #include header path from the source."""
    match = re.search(r'#include\s+"([^"]+)"', source)
    if match:
        return match.group(1)
    return "ui_mp/menudef.h"


def _collect_defines(source: str) -> dict[str, str]:
    """Extract all #define macros from source text."""
    defines: dict[str, str] = {}
    lines = source.split("\n")
    i = 0
    while i < len(lines):
        stripped = lines[i].lstrip()
        if stripped.startswith("#define"):
            full = stripped
            while full.rstrip().endswith("\\") and i + 1 < len(lines):
                i += 1
                full = full.rstrip().rstrip("\\") + " " + lines[i].strip()
            m = re.match(r"#define\s+(\w+)\s+(.*)", full)
            if m:
                defines[m.group(1)] = m.group(2).strip()
        i += 1
    return defines


def _preprocess(source: str, include_dirs: list[Path] | None = None) -> str:
    """Expand #define macros and strip preprocessor directives.

    Resolves #include directives by loading defines from referenced headers.
    Performs iterative expansion so macros that reference other macros resolve.
    """
    defines: dict[str, str] = {}

    # Resolve #include headers to collect their defines
    if include_dirs:
        for match in re.finditer(r'#include\s+"([^"]+)"', source):
            inc_path = match.group(1)
            for base in include_dirs:
                full = base / inc_path
                if full.exists():
                    header_src = full.read_text(encoding="utf-8", errors="replace")
                    defines.update(_collect_defines(header_src))
                    break

    # Collect defines from the file itself (override header defines)
    defines.update(_collect_defines(source))

    # Strip all preprocessor lines, preserving line count
    lines = source.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("#"):
            result.append("")
            while line.rstrip().endswith("\\") and i + 1 < len(lines):
                i += 1
                line = lines[i]
                result.append("")
        else:
            result.append(line)
        i += 1

    text = "\n".join(result)

    # Expand macros iteratively
    if defines:
        sorted_names = sorted(defines.keys(), key=len, reverse=True)
        pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted_names) + r")\b")
        for _ in range(10):  # max expansion depth
            new_text = pattern.sub(lambda m: defines[m.group(1)], text)
            if new_text == text:
                break
            text = new_text

    return text


def _is_fragment(source: str) -> bool:
    """Detect if a .menu file is a fragment (no outer { } wrapper).

    Fragment files start directly with itemDef or property keywords,
    without the standard outer braces.
    """
    # Strip comments and whitespace, find the first meaningful token
    cleaned = re.sub(r"//[^\n]*", "", source)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"#[^\n]*", "", cleaned)
    cleaned = cleaned.strip()
    # If it doesn't start with {, it's a fragment
    return not cleaned.startswith("{")


def parse(source: str, include_dirs: list[str | Path] | None = None) -> MenuFile:
    """Parse a .menu file source string into a MenuFile model.

    Args:
        source: The .menu file content.
        include_dirs: Directories to search for #include headers.

    Handles both complete .menu files and fragment files (no outer braces).
    Fragment files are returned as a MenuFile with no menuDefs.
    """
    include = _extract_include(source)
    inc_paths = [Path(d) for d in include_dirs] if include_dirs else _stock_dirs()
    cleaned = _preprocess(source, inc_paths)
    tokens = _tokenize(cleaned)
    parser = _Parser(tokens)

    menu_file = MenuFile(include=include)

    if parser.at_end():
        return menu_file

    # Fragment files (no outer braces) — skip them, they're #include snippets
    if _is_fragment(source):
        return menu_file

    parser.expect(_T_LBRACE)

    while not parser.at_end():
        tok = parser.peek()
        if tok is None or tok[0] == _T_RBRACE:
            break

        t = parser.advance()
        key = t[1].lower()

        if key == "menudef":
            menu_file.menu_defs.append(_parse_menu(parser))
        elif key == "assetglobaldef":
            # Skip assetGlobalDef blocks (not part of our MP editor model)
            parser.read_block()
        else:
            _skip_unknown_value(parser)

    if not parser.at_end():
        parser.expect(_T_RBRACE)

    return menu_file


def parse_file(path: str | Path, include_dirs: list[str | Path] | None = None) -> MenuFile:
    """Parse a .menu file from disk.

    If include_dirs is not provided, walks up parent directories to find
    a location where the #include header resolves.
    """
    p = Path(path).resolve()
    source = p.read_text(encoding="utf-8", errors="replace")
    if include_dirs is None:
        include_dirs = _find_include_dirs(p, source)
    return parse(source, include_dirs)


def _stock_dirs() -> list[Path]:
    """Return search paths for bundled stock menu files.

    The stock ui/ and ui_mp/ directories live at the project root.
    Since #include paths look like "ui_mp/menudef.h", the search
    base needs to be the project root (parent of ui_mp/).
    """
    pkg_dir = Path(__file__).resolve().parent  # menu_builder/
    project_root = pkg_dir.parent
    # The project root is the search base (contains ui_mp/ and ui/)
    if (project_root / "ui_mp").is_dir() or (project_root / "ui").is_dir():
        return [project_root]
    return []


def _find_include_dirs(file_path: Path, source: str) -> list[Path]:
    """Auto-detect include search directories by walking up from the file.

    Looks for directories where the #include "path" resolves to an actual file.
    Falls back to bundled stock ui/ and ui_mp/ directories.
    """
    match = re.search(r'#include\s+"([^"]+)"', source)
    if not match:
        return [file_path.parent]

    inc_path = match.group(1)
    dirs: list[Path] = []
    # Walk up from file's directory looking for a dir where the include resolves
    current = file_path.parent
    for _ in range(6):  # max depth
        if (current / inc_path).exists():
            dirs.append(current)
            break
        # Also check sibling directories (e.g., ui_mp file referencing ui/menudef.h)
        if current.parent != current:
            for sibling in current.parent.iterdir():
                if sibling.is_dir() and sibling != current and (sibling / inc_path).exists():
                    dirs.append(sibling)
                    break
        if dirs:
            break
        if current.parent == current:
            break
        current = current.parent

    # Fallback: try bundled stock directories
    if not dirs:
        for stock_dir in _stock_dirs():
            if (stock_dir / inc_path).exists():
                dirs.append(stock_dir)
                break

    if not dirs:
        dirs.append(file_path.parent)
    return dirs
