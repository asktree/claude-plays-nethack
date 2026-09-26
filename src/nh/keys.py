"""Key notation: human/LLM-friendly strings -> raw bytes sent to the game.

Plain characters are sent literally. A few bracketed names are special:

    <CR> <Enter> <Ret>   carriage return (confirm, dismiss --More--)
    <Esc>                escape (cancel)
    <Space> <Tab> <BS>   space, tab, backspace
    <C-x>                control-x (e.g. <C-d> kick, <C-x> attributes)
    <M-x>                meta-x, sent as ESC x (prefer #extcmd<CR> instead)
    <lt> <gt>            literal '<' / '>' (rarely needed: a bare '<' or '>'
                         that is not part of a known <Name> is sent literally)

Anything in angle brackets that is not one of these names is sent literally,
so "<" (go up), ">" (go down) and "<>" behave as expected.
"""

from __future__ import annotations

import re

_NAMED = {
    "cr": b"\r",
    "enter": b"\r",
    "ret": b"\r",
    "return": b"\r",
    "esc": b"\x1b",
    "escape": b"\x1b",
    "space": b" ",
    "spc": b" ",
    "tab": b"\t",
    "bs": b"\x08",
    "backspace": b"\x08",
    "del": b"\x7f",
    "lt": b"<",
    "gt": b">",
}

_TOKEN = re.compile(r"<([A-Za-z]+|[CcMm]-.)>")


def parse_keys(s: str) -> bytes:
    """Convert key notation to bytes. Raises ValueError on non-ASCII."""
    out = bytearray()
    i = 0
    while i < len(s):
        if s[i] == "<":
            m = _TOKEN.match(s, i)
            if m:
                name = m.group(1)
                low = name.lower()
                if low in _NAMED:
                    out += _NAMED[low]
                    i = m.end()
                    continue
                if len(name) == 3 and name[1] == "-" and low[0] in "cm":
                    ch = name[2]
                    if low[0] == "c":
                        code = ord(ch.lower()) & 0x1F if ch.isalpha() else ord(ch) & 0x1F
                        out.append(code)
                    else:
                        out += b"\x1b" + ch.encode("ascii")
                    i = m.end()
                    continue
        ch = s[i]
        if ord(ch) > 127:
            raise ValueError(f"non-ASCII key {ch!r} in {s!r}")
        out.append(ord(ch))
        i += 1
    return bytes(out)


_REV = {b"\r": "<CR>", b"\n": "<LF>", b"\x1b": "<Esc>", b" ": "<Space>", b"\t": "<Tab>",
        b"\x08": "<BS>", b"\x7f": "<Del>"}


def describe_bytes(b: bytes) -> str:
    """Inverse of parse_keys, for logs and error messages."""
    parts = []
    for byte in b:
        one = bytes([byte])
        if one in _REV:
            parts.append(_REV[one])
        elif byte < 32:
            parts.append(f"<C-{chr(byte + 96)}>")
        else:
            parts.append(chr(byte))
    return "".join(parts)
