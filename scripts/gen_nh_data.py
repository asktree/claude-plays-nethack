#!/usr/bin/env python3
"""Regenerate the NetHack 3.6.7 game-data JSON in src/nh/data/ from C sources.

    python scripts/gen_nh_data.py ~/src/nh367-data/NetHack-3.6.7
    python scripts/gen_nh_data.py SRC --out src/nh/data [--no-mail] [--cc-check]

SRC is an unpacked nethack-367-src.tgz (the directory holding src/ and
include/).  No table is hand-transcribed: src/monst.c, src/objects.c and
src/drawing.c are run through a small C preprocessor written here (object-
and function-like macros, #if/#ifdef/#else, the recursive
`#include "objects.c"` second pass of objects.c) against the macros and
enums of the headers they include, and the resulting brace initializers
are evaluated as C constant expressions (zapcolors[] from decl.c and
explcolors[] from mapglyph.c likewise).  No C compiler is needed.
Algorithms are ported by hand and cited: mstrength() (makedefs.c),
description shuffling (o_init.c), item naming (objnam.c xname()); the
display_rules / tty_color_rendering notes in features.json summarise
mapglyph.c and win/tty/termcap.c.

Build configuration mirrors a stock Unix tty build: TEXTCOLOR and MAIL are
defined (MAIL adds the "mail daemon" monster and the "mail" scroll, which
shifts later indices by one; pass --no-mail for builds without it), CHARON
is not.

Outputs: monsters.json, objects.json, glyph_index.json, features.json.
--cc-check additionally compiles monst.c/objects.c with the system C
compiler and verifies every struct field against this parser.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Any, Callable, Iterable

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
      (?P<ws>\s+)
    | (?P<id>[A-Za-z_]\w*)
    | (?P<num>\.?\d(?:[eEpP][+-]|[\w.])*)
    | (?P<str>"(?:[^"\\\n]|\\.)*")
    | (?P<chr>'(?:[^'\\\n]|\\.)*')
    | (?P<punct>\.\.\.|<<=|>>=|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^]=|\#\#
                |[][(){}<>?:;,.~!%^&*+=|/\#-])
    | (?P<other>.)
    """,
    re.X,
)


class Tok:
    """A preprocessing token; `hide` is the macro hide-set (Prosser)."""

    __slots__ = ("kind", "val", "hide")

    def __init__(self, kind: str, val: str, hide: frozenset = frozenset()):
        self.kind = kind
        self.val = val
        self.hide = hide

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Tok({self.kind},{self.val!r})"


def tokenize(text: str) -> list[Tok]:
    toks: list[Tok] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        assert m is not None
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        if kind == "other":
            kind = "punct"
        toks.append(Tok(kind, m.group()))
    return toks


def _strip_comments(text: str) -> str:
    """Replace /* */ and // comments by a space, leaving literals intact."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            if j < n and text[j] == c:
                out.append(text[i : j + 1])
                i = j + 1
            else:  # stray apostrophe (e.g. inside #if 0 prose): keep going
                out.append(c)
                i += 1
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise SyntaxError("unterminated comment")
            out.append(" ")
            i = j + 2
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def logical_lines(text: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\\\n", "")
    return _strip_comments(text).split("\n")


# ---------------------------------------------------------------------------
# Constant-expression evaluator (C semantics on Python ints)
# ---------------------------------------------------------------------------

_BINOPS = {
    "||": 1, "&&": 2, "|": 3, "^": 4, "&": 5, "==": 6, "!=": 6,
    "<": 7, ">": 7, "<=": 7, ">=": 7, "<<": 8, ">>": 8,
    "+": 9, "-": 9, "*": 10, "/": 10, "%": 10,
}
_TYPE_WORDS = {
    "char", "signed", "unsigned", "short", "int", "long", "const", "void",
    "uchar", "schar", "xchar", "boolean", "aligntyp", "genericptr_t",
}
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\",
            "'": "'", '"': '"', "a": "\a", "b": "\b", "f": "\f", "v": "\v",
            "?": "?"}


def _unescape(body: str) -> str:
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        nxt = body[i + 1]
        if nxt in "01234567":
            m = re.match(r"[0-7]{1,3}", body[i + 1 :])
            out.append(chr(int(m.group(), 8)))
            i += 1 + len(m.group())
        elif nxt == "x":
            m = re.match(r"[0-9A-Fa-f]+", body[i + 2 :])
            out.append(chr(int(m.group(), 16)))
            i += 2 + len(m.group())
        else:
            out.append(_ESCAPES[nxt])
            i += 2
    return "".join(out)


def _c_div(a: int, b: int) -> int:
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _parse_int(s: str) -> int:
    s = s.rstrip("uUlL")
    if s.lower().startswith("0x"):
        return int(s, 16)
    if len(s) > 1 and s.startswith("0"):
        return int(s, 8)
    return int(s)


class ConstEval:
    """Evaluate one C constant expression given as a token list."""

    def __init__(self, toks: list[Tok], resolve: Callable[[str], Any]):
        self.toks = toks
        self.i = 0
        self.resolve = resolve

    def eval(self) -> Any:
        if not self.toks:
            raise SyntaxError("empty expression")
        v = self._expr(0)
        if self.i != len(self.toks):
            raise SyntaxError(
                "trailing tokens: " + " ".join(t.val for t in self.toks[self.i :]))
        return v

    def _peek(self) -> Tok | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _next(self) -> Tok:
        if self.i >= len(self.toks):
            raise SyntaxError("unexpected end of expression")
        t = self.toks[self.i]
        self.i += 1
        return t

    def _expect(self, val: str) -> None:
        t = self._next()
        if t.val != val:
            raise SyntaxError(f"expected {val!r}, got {t.val!r}")

    def _expr(self, minp: int) -> Any:
        left = self._unary()
        while True:
            t = self._peek()
            if t is None or t.kind != "punct":
                return left
            if t.val == "?":
                if minp > 0:
                    return left
                self._next()
                a = self._expr(0)
                self._expect(":")
                b = self._expr(0)
                left = a if left else b
                continue
            p = _BINOPS.get(t.val)
            if p is None or p < minp:
                return left
            self._next()
            left = self._apply(t.val, left, self._expr(p + 1))

    @staticmethod
    def _apply(op: str, a: int, b: int) -> int:
        if op == "||":
            return int(bool(a) or bool(b))
        if op == "&&":
            return int(bool(a) and bool(b))
        if op == "|":
            return a | b
        if op == "^":
            return a ^ b
        if op == "&":
            return a & b
        if op == "==":
            return int(a == b)
        if op == "!=":
            return int(a != b)
        if op == "<":
            return int(a < b)
        if op == ">":
            return int(a > b)
        if op == "<=":
            return int(a <= b)
        if op == ">=":
            return int(a >= b)
        if op == "<<":
            return a << b
        if op == ">>":
            return a >> b
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return _c_div(a, b)
        if op == "%":
            return a - b * _c_div(a, b)
        raise SyntaxError(op)

    def _is_cast(self) -> bool:
        j = self.i
        seen = False
        while j < len(self.toks) and self.toks[j].kind == "id" \
                and self.toks[j].val in _TYPE_WORDS:
            j += 1
            seen = True
        while seen and j < len(self.toks) and self.toks[j].val == "*":
            j += 1
        return seen and j < len(self.toks) and self.toks[j].val == ")"

    def _unary(self) -> Any:
        t = self._next()
        if t.kind == "punct":
            if t.val == "(":
                if self._is_cast():
                    pointer = False
                    while self._peek().val != ")":
                        pointer |= self._next().val == "*"
                    self._next()
                    v = self._unary()
                    return None if pointer and v == 0 else v
                v = self._expr(0)
                self._expect(")")
                return v
            if t.val == "-":
                return -self._unary()
            if t.val == "+":
                return self._unary()
            if t.val == "!":
                return int(not self._unary())
            if t.val == "~":
                return ~self._unary()
            raise SyntaxError(f"unexpected {t.val!r}")
        if t.kind == "num":
            return _parse_int(t.val)
        if t.kind == "chr":
            s = _unescape(t.val[1:-1])
            if len(s) != 1:
                raise SyntaxError(f"bad char literal {t.val}")
            return ord(s)
        if t.kind == "str":
            s = _unescape(t.val[1:-1])
            while (nxt := self._peek()) is not None and nxt.kind == "str":
                s += _unescape(self._next().val[1:-1])
            return s
        if t.kind == "id":
            return self.resolve(t.val)
        raise SyntaxError(f"unexpected token {t.val!r}")


# ---------------------------------------------------------------------------
# Preprocessor
# ---------------------------------------------------------------------------


class Macro:
    __slots__ = ("name", "params", "body")

    def __init__(self, name: str, params: list[str] | None, body: list[Tok]):
        self.name = name
        self.params = params
        self.body = body


class PreprocessError(Exception):
    pass


_DEFINE_RE = re.compile(r"\s*define\s+([A-Za-z_]\w*)(\(([^)]*)\))?(.*)$", re.S)


class Preprocessor:
    """Just enough of a C preprocessor for NetHack's data tables."""

    def __init__(self) -> None:
        self.macros: dict[str, Macro] = {}
        self.out: list[Tok] = []
        self._depth = 0

    def define(self, name: str, value: str = "1") -> None:
        self.macros[name] = Macro(name, None, tokenize(value))

    # -- expansion ---------------------------------------------------------
    def expand(self, toks: Iterable[Tok]) -> list[Tok]:
        out: list[Tok] = []
        stream = deque(toks)
        macros = self.macros
        while stream:
            t = stream.popleft()
            m = macros.get(t.val) if t.kind == "id" else None
            if m is None or t.val in t.hide:
                out.append(t)
                continue
            if m.params is None:
                hs = t.hide | {t.val}
                stream.extendleft(
                    reversed([Tok(b.kind, b.val, b.hide | hs) for b in m.body]))
                continue
            if not stream or stream[0].val != "(" or stream[0].kind != "punct":
                out.append(t)  # function-like name without args: not a call
                continue
            args, rparen = self._collect_args(stream, t.val)
            if len(args) != len(m.params) and not (m.params == [] and args == [[]]):
                raise PreprocessError(
                    f"macro {t.val} wants {len(m.params)} args, got {len(args)}")
            hs = (t.hide & rparen.hide) | {t.val}
            stream.extendleft(reversed(self._subst(m, args, hs)))
        return out

    @staticmethod
    def _collect_args(stream: deque, name: str) -> tuple[list[list[Tok]], Tok]:
        stream.popleft()  # '('
        depth = 0
        args: list[list[Tok]] = [[]]
        while stream:
            t = stream.popleft()
            if t.kind == "punct":
                if t.val == "(":
                    depth += 1
                elif t.val == ")":
                    if depth == 0:
                        return args, t
                    depth -= 1
                elif t.val == "," and depth == 0:
                    args.append([])
                    continue
            args[-1].append(t)
        raise PreprocessError(f"unterminated invocation of {name}")

    def _subst(self, m: Macro, args: list[list[Tok]], hs: frozenset) -> list[Tok]:
        index = {p: i for i, p in enumerate(m.params or [])}
        cache: dict[int, list[Tok]] = {}
        out: list[Tok] = []
        for b in m.body:
            if b.kind == "punct" and b.val in ("#", "##"):
                raise PreprocessError(f"# / ## in macro {m.name} not supported")
            k = index.get(b.val) if b.kind == "id" else None
            if k is None:
                out.append(b)
            else:
                if k not in cache:
                    cache[k] = self.expand(args[k])
                out.extend(cache[k])
        return [Tok(t.kind, t.val, t.hide | hs) for t in out]

    # -- directives --------------------------------------------------------
    def _eval_if(self, toks: list[Tok]) -> bool:
        res: list[Tok] = []
        i = 0
        while i < len(toks):
            t = toks[i]
            if t.kind == "id" and t.val == "defined":
                if toks[i + 1].val == "(":
                    name, i = toks[i + 2].val, i + 4
                else:
                    name, i = toks[i + 1].val, i + 2
                res.append(Tok("num", "1" if name in self.macros else "0"))
            else:
                res.append(t)
                i += 1
        res = [Tok("num", "0") if t.kind == "id" else t for t in self.expand(res)]
        return bool(ConstEval(res, lambda n: 0).eval())

    def run(self, path: Path) -> list[Tok]:
        self._depth += 1
        if self._depth > 4:
            raise PreprocessError("include recursion too deep")
        try:
            self._process(path)
        finally:
            self._depth -= 1
        return self.out

    def _process(self, path: Path) -> None:
        stack: list[list[bool]] = []  # [parent_active, taken, current]
        active = True
        pending: list[Tok] = []

        def flush() -> None:
            self.out.extend(self.expand(pending))
            pending.clear()

        text = path.read_text(encoding="latin-1")
        for line in logical_lines(text):
            s = line.lstrip()
            if not s.startswith("#"):
                if active:
                    pending.extend(tokenize(line))
                continue
            rest = s[1:]
            toks = tokenize(rest)
            d = toks[0].val if toks else ""
            args = toks[1:]
            if d in ("if", "ifdef", "ifndef"):
                if not active:
                    stack.append([False, True, False])
                else:
                    if d == "ifdef":
                        cond = args[0].val in self.macros
                    elif d == "ifndef":
                        cond = args[0].val not in self.macros
                    else:
                        cond = self._eval_if(args)
                    stack.append([True, cond, cond])
            elif d == "elif":
                top = stack[-1]
                if top[0] and not top[1]:
                    top[2] = self._eval_if(args)
                    top[1] = top[2]
                else:
                    top[2] = False
            elif d == "else":
                top = stack[-1]
                top[2] = top[0] and not top[1]
                top[1] = True
            elif d == "endif":
                stack.pop()
            elif active:
                if d == "define":
                    flush()
                    m = _DEFINE_RE.match(rest)
                    if m is None:
                        raise PreprocessError(f"bad #define: {rest!r}")
                    params = None
                    if m.group(2):
                        params = [p.strip() for p in m.group(3).split(",")
                                  if p.strip()]
                        if any(p == "..." for p in params):
                            raise PreprocessError("variadic macros unsupported")
                    self.macros[m.group(1)] = Macro(
                        m.group(1), params, tokenize(m.group(4)))
                elif d == "undef":
                    flush()
                    self.macros.pop(args[0].val, None)
                elif d == "include":
                    flush()
                    target = args[0].val.strip('"') if args and args[0].kind == "str" else ""
                    if target == path.name:  # objects.c includes itself
                        self.run(path)
                elif d == "error":
                    raise PreprocessError(f"#error in {path.name}: {rest}")
                # #pragma, #line, null directive: ignored
            active = all(fr[2] for fr in stack)
        if stack:
            raise PreprocessError(f"unterminated #if in {path}")
        flush()


# ---------------------------------------------------------------------------
# Header symbol tables and initializer parsing
# ---------------------------------------------------------------------------


class Leaf:
    """An initializer leaf: the tokens of one expression."""

    __slots__ = ("toks",)

    def __init__(self, toks: list[Tok]):
        self.toks = toks


def parse_braced(toks: list[Tok], i: int) -> tuple[list, int]:
    if toks[i].val != "{":
        raise SyntaxError("expected {")
    i += 1
    items: list = []
    while True:
        if toks[i].val == "}":
            return items, i + 1
        if toks[i].val == "{":
            item, i = parse_braced(toks, i)
        else:
            expr: list[Tok] = []
            depth = 0
            while True:
                t = toks[i]
                if t.kind == "punct":
                    if t.val in ("(", "["):
                        depth += 1
                    elif t.val in (")", "]"):
                        depth -= 1
                    elif depth == 0 and t.val in (",", "}"):
                        break
                expr.append(t)
                i += 1
            item = Leaf(expr)
        items.append(item)
        if toks[i].val == ",":
            i += 1
        elif toks[i].val != "}":
            raise SyntaxError(f"unexpected {toks[i].val!r} in initializer")


def find_initializer(toks: list[Tok], name: str) -> list:
    for i, t in enumerate(toks):
        if t.kind == "id" and t.val == name and i + 1 < len(toks) \
                and toks[i + 1].val == "[":
            j = i + 2
            while toks[j].val != "]":
                j += 1
            if toks[j + 1].val == "=" and toks[j + 2].val == "{":
                return parse_braced(toks, j + 2)[0]
    raise KeyError(f"initializer for {name}[] not found")


def parse_enums(toks: list[Tok], resolve: Callable[[str], Any]) -> dict[str, int]:
    consts: dict[str, int] = {}

    def res(name: str) -> Any:
        return consts[name] if name in consts else resolve(name)

    i = 0
    while i < len(toks):
        if toks[i].kind == "id" and toks[i].val == "enum":
            j = i + 1
            if toks[j].kind == "id":
                j += 1
            if toks[j].val == "{":
                j += 1
                val = -1
                while toks[j].val != "}":
                    name = toks[j].val
                    j += 1
                    if toks[j].val == "=":
                        j += 1
                        expr = []
                        while toks[j].val not in (",", "}"):
                            expr.append(toks[j])
                            j += 1
                        val = ConstEval(expr, res).eval()
                    else:
                        val += 1
                    if name in consts and consts[name] != val:
                        raise ValueError(f"conflicting enum {name}")
                    consts[name] = val
                    if toks[j].val == ",":
                        j += 1
                i = j
        i += 1
    return consts


class Source:
    """One preprocessed .c file plus the symbol tables it was compiled with."""

    def __init__(self, root: Path, cfile: str, headers: list[str],
                 defines: dict[str, str]):
        self.root = root
        pp = Preprocessor()
        for k, v in defines.items():
            pp.define(k, v)
        for h in headers:
            pp.run(root / "include" / h)
        header_toks = pp.out
        self.header_macros = dict(pp.macros)
        self.enums = parse_enums(header_toks, self._unknown)
        pp.out = []
        self.toks = pp.run(root / "src" / cfile)

    def array(self, cfile: str, name: str) -> list:
        """Evaluate a flat `name[...] = { ... };` initializer from another
        .c file against this Source's header macros (the file itself is not
        preprocessed, so the array must not depend on its local macros)."""
        text = "\n".join(logical_lines(
            (self.root / "src" / cfile).read_text(encoding="latin-1")))
        m = re.search(rf"\b{name}\s*\[[^\]]*\]\s*=\s*\{{", text)
        if m is None:
            raise KeyError(f"{name}[] not found in {cfile}")
        body = text[m.end() - 1 : text.index("};", m.end()) + 1]
        pp = Preprocessor()
        pp.macros = dict(self.header_macros)
        return [self.value(x) for x in parse_braced(pp.expand(tokenize(body)), 0)[0]]

    @staticmethod
    def _unknown(name: str) -> Any:
        raise NameError(f"unresolved identifier {name!r}")

    def resolve(self, name: str) -> Any:
        if name in self.enums:
            return self.enums[name]
        raise NameError(f"unresolved identifier {name!r}")

    def value(self, item: Any) -> Any:
        """Evaluate a parsed initializer item (Leaf or nested list)."""
        if isinstance(item, Leaf):
            return ConstEval(item.toks, self.resolve).eval()
        return [self.value(x) for x in item]

    def macro_value(self, name: str) -> Any:
        m = self.header_macros[name]
        if m.params is not None:
            raise ValueError(f"{name} is function-like")
        hp = Preprocessor()
        hp.macros = self.header_macros
        return ConstEval(hp.expand([Tok("id", name)]), self.resolve).eval()

    def constants(self, prefix: str, exclude: Iterable[str] = ()) -> dict[str, int]:
        """name -> value for object-like header macros/enums with a prefix,
        in definition order."""
        skip = set(exclude)
        out: dict[str, int] = {}
        for name, m in self.header_macros.items():
            if name.startswith(prefix) and name not in skip and m.params is None \
                    and m.body:
                try:
                    v = self.macro_value(name)
                except (NameError, SyntaxError, KeyError):
                    continue
                if isinstance(v, int):
                    out[name] = v
        for name, v in self.enums.items():
            if name.startswith(prefix) and name not in skip:
                out[name] = v
        return out


# ---------------------------------------------------------------------------
# Decoding helpers
# ---------------------------------------------------------------------------

COLOR_NAMES = {
    0: "black", 1: "red", 2: "green", 3: "brown", 4: "blue", 5: "magenta",
    6: "cyan", 7: "gray", 8: "no_color", 9: "orange", 10: "bright_green",
    11: "yellow", 12: "bright_blue", 13: "bright_magenta", 14: "bright_cyan",
    15: "white",
}


def invert(consts: dict[str, int]) -> dict[int, str]:
    inv: dict[int, str] = {}
    for name, v in consts.items():
        inv.setdefault(v, name)
    return inv


def decode_bits(value: int, singles: dict[str, int],
                composites: dict[str, int] | None = None) -> list[str]:
    composites = composites or {}
    names = [n for n, b in singles.items() if value & b]
    names += [n for n, b in composites.items() if value & b == b]
    covered = 0
    for n in names:
        covered |= singles.get(n, composites.get(n, 0))
    if value & ~covered:
        raise ValueError(f"undecoded bits {value & ~covered:#x} in {value:#x}")
    return names


def split_flags(consts: dict[str, int]) -> tuple[dict[str, int], dict[str, int]]:
    singles = {n: v for n, v in consts.items() if v and v & (v - 1) == 0}
    composites = {n: v for n, v in consts.items() if v and v & (v - 1)}
    return singles, composites


def c_ident(name: str) -> str:
    return "".join(c.upper() if c.isalpha() and c.isascii() else "_" for c in name)


def alignment_name(a: int) -> str:
    if a == -128:
        return "unaligned"  # A_NONE (Moloch)
    return "chaotic" if a < 0 else "lawful" if a > 0 else "neutral"


# ---------------------------------------------------------------------------
# Monsters
# ---------------------------------------------------------------------------

MON_FIELDS = ["mname", "mlet", "mlevel", "mmove", "ac", "mr", "maligntyp",
              "geno", "mattk", "cwt", "cnutrit", "msound", "msize", "mresists",
              "mconveys", "mflags1", "mflags2", "mflags3", "difficulty",
              "mcolor"]


def mstrength(m: dict, K: dict[str, int]) -> int:
    """Port of mstrength()/ranged_attk() from util/makedefs.c.

    The function was removed from makedefs in 3.6.2, when the value became
    the literal `difficulty` field of MON() in monst.c; this is the 3.6.0 /
    3.6.1 code (identical in both), kept to cross-check those literals."""
    atk_mask = (1 << K["AT_BREA"]) | (1 << K["AT_SPIT"]) | (1 << K["AT_GAZE"])

    def ranged_attk() -> bool:
        for at, _ad, _n, _d in m["mattk"]:
            if at >= K["AT_WEAP"] or atk_mask & (1 << at):
                return True
        return False

    tmp = m["mlevel"]
    if tmp > 49:  # special fixed hp monster
        tmp = _c_div(2 * (tmp - 6), 4)
    n = int(bool(m["geno"] & K["G_SGROUP"]))
    n += int(bool(m["geno"] & K["G_LGROUP"])) << 1
    if ranged_attk():
        n += 1
    n += m["ac"] < 4
    n += m["ac"] < 0
    n += m["mmove"] >= 18
    for at, _ad, _n, _d in m["mattk"]:
        n += at > 0
        n += at == K["AT_MAGC"]
        n += at == K["AT_WEAP"] and bool(m["mflags2"] & K["M2_STRONG"])
    special = {K[x] for x in ("AD_DRLI", "AD_STON", "AD_DRST", "AD_DRDX",
                              "AD_DRCO", "AD_WERE")}
    for _at, ad, dn, dd in m["mattk"]:
        if ad in special:
            n += 2
        elif m["mname"] != "grid bug":
            n += ad != K["AD_PHYS"]
        n += dd * dn > 23
    if m["mname"] == "leprechaun":
        n -= 2
    if n == 0:
        tmp -= 1
    elif n >= 6:
        tmp += n // 2
    else:
        tmp += n // 3 + 1
    return tmp if tmp >= 0 else 0


def build_monsters(src: Source, monsyms: list[dict]) -> tuple[list[dict], list[dict]]:
    raw_items = find_initializer(src.toks, "mons")
    raws: list[dict] = []
    for item in raw_items:
        vals = src.value(item)
        if len(vals) != len(MON_FIELDS):
            raise ValueError(f"monster entry has {len(vals)} fields: {vals[:1]}")
        rec = dict(zip(MON_FIELDS, vals))
        if len(rec["mattk"]) != 6 or any(len(a) != 4 for a in rec["mattk"]):
            raise ValueError(f"bad attack matrix for {rec['mname']}")
        rec["mattk"] = [tuple(a) for a in rec["mattk"]]
        raws.append(rec)
    if raws[-1]["mname"] != "" or raws[-1]["mlet"] != 0:
        raise ValueError("mons[] terminator missing")
    raws.pop()

    K = {}
    for p in ("AT_", "AD_", "G_", "M2_"):
        K.update(src.constants(p))
    at_names = invert(src.constants("AT_", exclude=["AT_ANY"]))
    ad_names = invert(src.constants("AD_", exclude=["AD_ANY"]))
    ms_names = invert(src.constants("MS_", exclude=["MS_ANIMAL", "MS_ORC"]))
    mz_names = invert(src.constants("MZ_", exclude=["MZ_HUMAN"]))
    mr = src.constants("MR_")
    m1s, m1c = split_flags(src.constants("M1_"))
    m2s, m2c = split_flags(src.constants("M2_"))
    m3s, m3c = split_flags(src.constants("M3_"))
    geno_flags = {n: src.constants("G_")[n] for n in
                  ("G_UNIQ", "G_NOHELL", "G_HELL", "G_NOGEN", "G_SGROUP",
                   "G_LGROUP", "G_GENO", "G_NOCORPSE")}
    g_freq = K["G_FREQ"]
    cls_by_val = {src.enums[k]: k for k in
                  _enum_names(src, "monsym.h", "mon_class_types")}

    out: list[dict] = []
    for idx, r in enumerate(raws):
        geno = r["geno"]
        gnames = decode_bits(geno & ~g_freq, geno_flags)
        pm = "PM_" + ("HUMAN_" if r["mlet"] == src.enums["S_HUMAN"]
                      and r["mname"].startswith("were") else "") + c_ident(r["mname"])
        attacks = []
        for slot, (at, ad, dn, dd) in enumerate(r["mattk"]):
            if (at, ad, dn, dd) == (0, 0, 0, 0):
                continue
            attacks.append({
                "slot": slot,
                "type": at_names[at],
                "damage_type": ad_names[ad],
                "dice": f"{dn}d{dd}",
                "n": dn,
                "d": dd,
            })
        filled = [s["slot"] for s in attacks]
        if filled != list(range(len(filled))):
            raise ValueError(f"non-contiguous attacks for {r['mname']}")
        sym = monsyms[r["mlet"]]["char"]
        rec = {
            "index": idx,
            "name": r["mname"],
            "pm": pm,
            "symbol": sym,
            "class": cls_by_val[r["mlet"]],
            "class_value": r["mlet"],
            "color": COLOR_NAMES[r["mcolor"]],
            "color_value": r["mcolor"],
            "level": r["mlevel"],
            "speed": r["mmove"],
            "ac": r["ac"],
            "mr": r["mr"],
            "alignment": r["maligntyp"],
            "alignment_name": alignment_name(r["maligntyp"]),
            "geno": {"value": geno, "flags": gnames, "frequency": geno & g_freq},
            "attacks": attacks,
            "weight": r["cwt"],
            "nutrition": r["cnutrit"],
            "sound": ms_names[r["msound"]],
            "size": mz_names[r["msize"]],
            "size_value": r["msize"],
            "resistances": decode_bits(r["mresists"], mr),
            "conveys": decode_bits(r["mconveys"], mr),
            "flags1": decode_bits(r["mflags1"], m1s, m1c),
            "flags2": decode_bits(r["mflags2"], m2s, m2c),
            "flags3": decode_bits(r["mflags3"], m3s, m3c),
            "flags_raw": [r["mflags1"], r["mflags2"], r["mflags3"]],
            "difficulty": r["difficulty"],
            "difficulty_mstrength": mstrength(r, K),
        }
        out.append(rec)
    return out, raws


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------

OBJ_FIELDS = ["oc_name_idx", "oc_descr_idx", "oc_uname", "oc_name_known",
              "oc_merge", "oc_uses_known", "oc_pre_discovered", "oc_magic",
              "oc_charged", "oc_unique", "oc_nowish", "oc_big", "oc_tough",
              "oc_dir", "oc_material", "oc_subtyp", "oc_oprop", "oc_class",
              "oc_delay", "oc_color", "oc_prob", "oc_weight", "oc_cost",
              "oc_wsdam", "oc_wldam", "oc_oc1", "oc_oc2", "oc_nutrition"]

# C types of struct objclass fields (bitfield width or (lo, hi) range),
# used to verify nothing in objects.c overflows its field.
OBJ_FIELD_RANGES = {
    "oc_name_known": (0, 1), "oc_merge": (0, 1), "oc_uses_known": (0, 1),
    "oc_pre_discovered": (0, 1), "oc_magic": (0, 1), "oc_charged": (0, 1),
    "oc_unique": (0, 1), "oc_nowish": (0, 1), "oc_big": (0, 1),
    "oc_tough": (0, 1), "oc_dir": (0, 3), "oc_material": (0, 31),
    "oc_subtyp": (-128, 127), "oc_oprop": (0, 255), "oc_class": (-128, 127),
    "oc_delay": (-128, 127), "oc_color": (0, 255), "oc_prob": (-32768, 32767),
    "oc_weight": (0, 65535), "oc_cost": (-32768, 32767),
    "oc_wsdam": (-128, 127), "oc_wldam": (-128, 127), "oc_oc1": (-128, 127),
    "oc_oc2": (-128, 127), "oc_nutrition": (0, 65535),
}

SHUFFLE_WHOLE_CLASSES = ["AMULET_CLASS", "POTION_CLASS", "RING_CLASS",
                         "SCROLL_CLASS", "SPBOOK_CLASS", "WAND_CLASS",
                         "VENOM_CLASS"]
# o_init.c init_objects(): each game, turquoise/aquamarine take sapphire's
# description+colour with probability 1/2; fluorite stays violet or becomes
# sapphire/diamond/emerald-coloured, 1/4 each.
GEM_VARIANTS = {"TURQUOISE": ["SAPPHIRE"], "AQUAMARINE": ["SAPPHIRE"],
                "FLUORITE": ["SAPPHIRE", "DIAMOND", "EMERALD"]}
SHUFFLE_ARMOR_RANGES = [("helmet", "HELMET", "HELM_OF_TELEPATHY"),
                        ("gloves", "LEATHER_GLOVES", "GAUNTLETS_OF_DEXTERITY"),
                        ("cloak", "CLOAK_OF_PROTECTION", "CLOAK_OF_DISPLACEMENT"),
                        ("boots", "SPEED_BOOTS", "LEVITATION_BOOTS")]


def otyp_constant(name: str | None, cls: str, material: str | None) -> str | None:
    """onames.h constant as util/makedefs.c do_objs() writes it."""
    if name is None:
        return None
    nam = c_ident(name)
    prefix = {"WAND_CLASS": "WAN_", "RING_CLASS": "RIN_", "POTION_CLASS": "POT_",
              "SPBOOK_CLASS": "SPE_", "SCROLL_CLASS": "SCR_"}.get(cls, "")
    if cls == "AMULET_CLASS" and material == "PLASTIC":
        return "FAKE_AMULET_OF_YENDOR"
    if cls == "GEM_CLASS" and material == "GLASS":
        return None  # makedefs writes these as comments only
    return prefix + nam[: 26 if prefix else 30]  # makedefs limit()


_GEMSTONE_NO_SUFFIX = {"DILITHIUM_CRYSTAL", "RUBY", "DIAMOND", "SAPPHIRE",
                       "BLACK_OPAL", "EMERALD", "OPAL"}


def xname(o: dict, identified: bool, appearance: str | None = None) -> str | None:
    """Singular name as objnam.c xname() prints it for a seen (dknown) item
    with no user-assigned 'called' name.  identified=False gives the
    pre-identification name (oc_name_known items keep their real name);
    `appearance` overrides the description (for shuffled classes)."""
    actual = o["name"]
    dn = appearance or o["appearance"] or actual
    nn = identified or o["name_known"]
    cls, otyp = o["class"], o["otyp"]
    if nn and actual is None:
        return None  # extra-description placeholder, never generated
    if cls == "AMULET_CLASS":
        if otyp in ("AMULET_OF_YENDOR", "FAKE_AMULET_OF_YENDOR"):
            return actual if identified else dn
        return actual if nn else f"{dn} amulet"
    if cls in ("WEAPON_CLASS", "VENOM_CLASS", "TOOL_CLASS"):
        return ("pair of " if otyp == "LENSES" else "") + (actual if nn else dn)
    if cls == "ARMOR_CLASS":
        if o["armor"]["category"] == "ARM_SUIT" and actual and \
                actual.endswith("dragon scales"):
            return f"set of {actual}"
        pre = "pair of " if o["armor"]["category"] in ("ARM_BOOTS", "ARM_GLOVES") else ""
        return pre + (actual if nn else dn)
    if cls == "POTION_CLASS":
        return f"potion of {actual}" if nn else f"{dn} potion"
    if cls == "SCROLL_CLASS":
        if nn:
            return f"scroll of {actual}"
        return f"scroll labeled {dn}" if o["magic"] else f"{dn} scroll"
    if cls == "WAND_CLASS":
        return f"wand of {actual}" if nn else f"{dn} wand"
    if cls == "RING_CLASS":
        return f"ring of {actual}" if nn else f"{dn} ring"
    if cls == "SPBOOK_CLASS":
        if otyp == "SPE_NOVEL":
            return actual if nn else f"{dn} book"
        if nn:
            return actual if otyp == "SPE_BOOK_OF_THE_DEAD" else f"spellbook of {actual}"
        return f"{dn} spellbook"
    if cls == "GEM_CLASS":
        if not nn:
            return f"{dn} {'stone' if o['material'] == 'MINERAL' else 'gem'}"
        gemstone = otyp == "FLINT" or (o["material"] == "GEMSTONE"
                                       and otyp not in _GEMSTONE_NO_SUFFIX)
        return actual + (" stone" if gemstone else "")
    return actual  # food, coins, rocks, ball, chain, strange object


def build_objects(src: Source, oc_syms: list[dict]) -> tuple[list[dict], dict, list]:
    descr = [src.value(x) for x in find_initializer(src.toks, "obj_descr")]
    items = [src.value(x) for x in find_initializer(src.toks, "objects")]
    if len(descr) != len(items):
        raise ValueError("obj_descr[] and objects[] lengths differ")
    raws = []
    for (name, desc), vals in zip(descr, items):
        if len(vals) != len(OBJ_FIELDS):
            raise ValueError(f"object {name!r} has {len(vals)} fields")
        rec = dict(zip(OBJ_FIELDS, vals))
        for f, (lo, hi) in OBJ_FIELD_RANGES.items():
            if not lo <= rec[f] <= hi:
                raise ValueError(f"{name}: {f}={rec[f]} overflows its C field")
        raws.append((name, desc, rec))
    ill = src.enums["ILLOBJ_CLASS"]
    num = next(i for i in range(1, len(raws)) if raws[i][2]["oc_class"] == ill)
    if raws[num][0] is not None:
        raise ValueError("objects[] terminator missing")
    raws = raws[:num]  # NUM_OBJECTS, as makedefs/o_init count them

    cls_names = {src.enums[k]: k for k in
                 _enum_names(src, "objclass.h", "obj_class_types")}
    mat_names = {src.enums[k]: k for k in
                 _enum_names(src, "objclass.h", "obj_material_types")}
    arm_names = {src.enums[k]: k for k in
                 _enum_names(src, "objclass.h", "obj_armor_types")}
    skill_names = {src.enums[k]: k for k in _enum_names(src, "skills.h", "p_skills")
                   if k != "P_NUM_SKILLS"}
    prop_names = invert({k: src.enums[k] for k in _enum_names(src, "prop.h", "prop_types")})
    K = {k: src.macro_value(k) for k in ("NODIR", "IMMEDIATE", "RAY", "PIERCE",
                                          "SLASH", "WHACK")}
    dir_names = {0: None, K["NODIR"]: "NODIR", K["IMMEDIATE"]: "IMMEDIATE",
                 K["RAY"]: "RAY"}

    objs: list[dict] = []
    for idx, (name, desc, r) in enumerate(raws):
        cls = cls_names[r["oc_class"]]
        material = mat_names.get(r["oc_material"])
        o: dict[str, Any] = {
            "index": idx,
            "name": name,
            "appearance": desc,
            "otyp": otyp_constant(name, cls, material),
            "class": cls,
            "class_symbol": oc_syms[r["oc_class"]]["char"],
            "color": COLOR_NAMES[r["oc_color"]],
            "color_value": r["oc_color"],
            "cost": r["oc_cost"],
            "weight": r["oc_weight"],
            "prob": r["oc_prob"],
            "material": material,
            "magic": bool(r["oc_magic"]),
            "merge": bool(r["oc_merge"]),
            "charged": bool(r["oc_charged"]),
            "unique": bool(r["oc_unique"]),
            "nowish": bool(r["oc_nowish"]),
            "name_known": bool(r["oc_name_known"]),
            "uses_known": bool(r["oc_uses_known"]),
            "property": prop_names.get(r["oc_oprop"]),
            "shuffle_group": None,
            "raw": {k: r[k] for k in OBJ_FIELDS[3:]},
        }
        skill = r["oc_subtyp"]
        is_weptool = cls == "TOOL_CLASS" and skill != 0
        if cls == "WEAPON_CLASS" or is_weptool or (cls == "GEM_CLASS" and skill):
            dmg = [n for n, b in (("pierce", K["PIERCE"]), ("slash", K["SLASH"]))
                   if r["oc_dir"] & b] or ["whack"]
            lo = src.enums
            if cls in ("WEAPON_CLASS", "GEM_CLASS") and \
                    -lo["P_CROSSBOW"] <= skill <= -lo["P_BOW"]:
                kind = "ammo"
            elif cls in ("WEAPON_CLASS", "TOOL_CLASS") and \
                    -lo["P_BOOMERANG"] <= skill <= -lo["P_DART"]:
                kind = "missile"
            elif cls == "WEAPON_CLASS" and lo["P_BOW"] <= skill <= lo["P_CROSSBOW"]:
                kind = "launcher"
            else:
                kind = "melee"
            o["weapon"] = {
                "small_damage": f"d{r['oc_wsdam']}",
                "large_damage": f"d{r['oc_wldam']}",
                "sdam": r["oc_wsdam"],
                "ldam": r["oc_wldam"],
                "to_hit": r["oc_oc1"],
                "skill": ("-" if skill < 0 else "") + skill_names[abs(skill)],
                "skill_value": skill,
                "kind": kind,
                "damage_types": dmg,
                "bimanual": bool(r["oc_big"]) and cls != "GEM_CLASS",
            }
        if cls == "ARMOR_CLASS":
            o["armor"] = {
                "ac": r["oc_oc1"],
                "mc": r["oc_oc2"],
                "category": arm_names[r["oc_subtyp"]],
                "delay": r["oc_delay"],
                "bulky": bool(r["oc_big"]),
            }
        if cls == "FOOD_CLASS":
            o["food"] = {"nutrition": r["oc_nutrition"], "delay": r["oc_delay"]}
        if cls == "WAND_CLASS":
            o["wand"] = {"direction": dir_names[r["oc_dir"]]}
        if cls == "SPBOOK_CLASS":
            o["spellbook"] = {
                "level": r["oc_oc2"],
                "direction": dir_names[r["oc_dir"]],
                "school": skill_names[r["oc_subtyp"]] if r["oc_subtyp"] else None,
                "delay": r["oc_delay"],
            }
        if cls == "RING_CLASS":
            o["ring"] = {"chargeable": bool(r["oc_charged"]), "hard": bool(r["oc_tough"])}
        if cls == "GEM_CLASS":
            o["gem"] = {"hard": bool(r["oc_tough"]), "glass": material == "GLASS",
                        "value": r["oc_cost"]}
        objs.append(o)

    # o_init.c init_objects(): a class whose probabilities sum to 0 (rings)
    # gets (1000 + i - first) / (last - first) each at game start
    first: dict[str, int] = {}
    count: dict[str, int] = {}
    total: dict[str, int] = {}
    for o in objs:
        first.setdefault(o["class"], o["index"])
        count[o["class"]] = count.get(o["class"], 0) + 1
        total[o["class"]] = total.get(o["class"], 0) + o["prob"]
    for o in objs:
        c = o["class"]
        o["effective_prob"] = o["prob"] if total[c] else \
            (1000 + o["index"] - first[c]) // count[c]

    by_otyp = {o["otyp"]: o["index"] for o in objs if o["otyp"]}
    shuffle = compute_shuffle_groups(objs, by_otyp)
    for o in objs:
        o["full_name"] = xname(o, True)
        # for shuffled classes this is only the *default* appearance; the
        # per-game one is any of shuffle_groups[group]["appearances"]
        o["unidentified_name"] = xname(o, False)
    for k, g in shuffle.items():
        rep = objs[g["first"]]
        for a in g["appearances"]:
            a["unidentified_name"] = xname(rep, False, a["appearance"])
        names = [objs[i]["full_name"] for i in g.pop("members")]
        shuffle[k] = {**{f: g[f] for f in ("class", "first", "last",
                                           "materials_shuffled")},
                      "names": names, "appearances": g["appearances"]}
    # stable key order: identity first, effective_prob after prob, raw last
    head = ["index", "name", "full_name", "appearance", "unidentified_name", "otyp"]
    out = []
    for o in objs:
        rec = {k: o[k] for k in head}
        for k, v in o.items():
            if k in head or k in ("raw", "effective_prob"):
                continue
            rec[k] = v
            if k == "prob":
                rec["effective_prob"] = o["effective_prob"]
        rec["raw"] = o["raw"]
        out.append(rec)
    return out, shuffle, raws


def _enum_names(src: Source, header: str, enum: str) -> list[str]:
    """Constant names of `enum <enum> {...}` in include/<header>."""
    text = (src.root / "include" / header).read_text(encoding="latin-1")
    m = re.search(rf"enum\s+{enum}\s*\{{(.*?)\}}", _strip_comments(text), re.S)
    return re.findall(r"([A-Za-z_]\w*)\s*=", m.group(1))


def compute_shuffle_groups(objs: list[dict], by_otyp: dict[str, int]) -> dict:
    """Replicates o_init.c obj_shuffle_range()/shuffle_all()."""
    bases: dict[str, int] = {}
    for o in objs:
        bases.setdefault(o["class"], o["index"])
    groups: dict[str, dict] = {}

    def add(key: str, lo: int, hi: int, domaterial: bool) -> None:
        members = [o for o in objs[lo : hi + 1] if not o["name_known"]]
        groups[key] = {
            "class": objs[lo]["class"],
            "first": lo,
            "last": hi,
            "materials_shuffled": domaterial,
            "members": [o["index"] for o in members if o["name"]],
            "appearances": [
                {"appearance": o["appearance"], "color": o["color"],
                 "color_value": o["color_value"], "material": o["material"]}
                for o in members],
        }
        for o in members:
            o["shuffle_group"] = key

    keys = {"AMULET_CLASS": "amulet", "POTION_CLASS": "potion",
            "RING_CLASS": "ring", "SCROLL_CLASS": "scroll",
            "SPBOOK_CLASS": "spellbook", "WAND_CLASS": "wand",
            "VENOM_CLASS": "venom"}
    for cls in SHUFFLE_WHOLE_CLASSES:
        lo = bases[cls]
        hi = lo
        while hi + 1 < len(objs) and objs[hi + 1]["class"] == cls:
            hi += 1
        if cls == "POTION_CLASS":  # potion of water keeps "clear"
            hi = by_otyp["POT_WATER"] - 1
        elif cls in ("AMULET_CLASS", "SCROLL_CLASS", "SPBOOK_CLASS"):
            i = lo
            while objs[i]["class"] == cls and not objs[i]["unique"] and objs[i]["magic"]:
                i += 1
            hi = i - 1
        add(keys[cls], lo, hi, True)
    for key, a, b in SHUFFLE_ARMOR_RANGES:
        add(key, by_otyp[a], by_otyp[b], False)
    return groups


# ---------------------------------------------------------------------------
# drawing.c: default symbols
# ---------------------------------------------------------------------------


def build_drawing(src: Source) -> dict:
    def syms(name: str, fields: list[str]) -> list[dict]:
        out = []
        for item in find_initializer(src.toks, name):
            vals = src.value(item)
            rec = dict(zip(fields, vals))
            if "char" in rec:
                rec["char"] = chr(rec["char"]) if rec["char"] else ""
            out.append(rec)
        return out

    return {
        "oc_syms": syms("def_oc_syms", ["char", "name", "explain"]),
        "monsyms": syms("def_monsyms", ["char", "name", "explain"]),
        "warnsyms": syms("def_warnsyms", ["char", "explanation", "color"]),
        "defsyms": syms("defsyms", ["char", "explanation", "color"]),
    }


# ---------------------------------------------------------------------------
# glyph index / features
# ---------------------------------------------------------------------------

def key(ch: str, color: int) -> str:
    return f"{ch}|{color}"


def gem_variants(objects: list[dict]) -> dict:
    """Per-game (description, colour) possibilities for GEM_VARIANTS."""
    by_otyp = {o["otyp"]: o for o in objects if o["otyp"]}
    out = {}
    for gem, donors in GEM_VARIANTS.items():
        opts = [by_otyp[gem]] + [by_otyp[d] for d in donors]
        out[by_otyp[gem]["name"]] = [
            {"appearance": o["appearance"], "color": o["color"],
             "color_value": o["color_value"], "chance": 1 / len(opts)}
            for o in opts]
    return out


def build_glyph_index(monsters: list[dict], objects: list[dict],
                      shuffle: dict, features: dict) -> dict:
    mons: dict[str, list[str]] = {}
    by_char: dict[str, list[str]] = {}
    for m in monsters:
        mons.setdefault(key(m["symbol"], m["color_value"]), []).append(m["name"])
        by_char.setdefault(m["symbol"], []).append(m["name"])

    objs: dict[str, list[dict]] = {}
    statue_color = next(o["color_value"] for o in objects if o["otyp"] == "STATUE")
    boulder_char = features["other_symbols"]["boulder"]["char"]
    for o in objects:
        if o["name"] is None and o["shuffle_group"] is None:
            continue
        if o["otyp"] in ("STATUE", "CORPSE"):
            continue  # drawn in the monster's letter/colour: "statues"/"corpses"
        ch = boulder_char if o["otyp"] == "BOULDER" else o["class_symbol"]
        if o["shuffle_group"]:
            # colour belongs to the appearance; identity is any group member
            entry = {"appearance": o["appearance"],
                     "unidentified_name": o["unidentified_name"],
                     "shuffle_group": o["shuffle_group"]}
        else:
            entry = {"name": o["full_name"]}
            if o["unidentified_name"] != o["full_name"]:
                entry["unidentified_name"] = o["unidentified_name"]
        objs.setdefault(key(ch, o["color_value"]), []).append(entry)
    by_otyp = {o["otyp"]: o for o in objects if o["otyp"]}
    for gem, donors in GEM_VARIANTS.items():
        for d in donors:
            donor = by_otyp[d]
            k = key(donor["class_symbol"], donor["color_value"])
            objs.setdefault(k, []).append(
                {"name": by_otyp[gem]["full_name"],
                 "unidentified_name": donor["unidentified_name"],
                 "variant": f"per-game recolour, chance 1/{len(donors) + 1}"})
    corpses: dict[str, list[str]] = {}
    corpse_char = by_otyp["CORPSE"]["class_symbol"]
    for m in monsters:
        if "G_NOCORPSE" not in m["geno"]["flags"]:
            corpses.setdefault(key(corpse_char, m["color_value"]), []).append(m["name"])
    statues: dict[str, list[str]] = {}
    for m in monsters:
        statues.setdefault(key(m["symbol"], statue_color), []).append(m["name"])
    feats: dict[str, list[str]] = {}
    for f in features["cmap"]:
        if f["char"] and f["explanation"]:
            feats.setdefault(key(f["char"], f["color_value"]), []).append(f["id"])
    special = {
        key(features["other_symbols"]["invisible"]["char"], 8):
            "remembered, unseen, creature (SYM_INVISIBLE)",
        key(by_otyp["STRANGE_OBJECT"]["class_symbol"],
            by_otyp["STRANGE_OBJECT"]["color_value"]):
            "strange object: what a mimic imitating an object usually looks like",
    }
    for w in features["warnings"]:
        special[key(w["char"], w["color_value"])] = f"warning level {w['level']}: {w['explanation']}"
    return {
        "_doc": ("Keys are '<char>|<color>' with NetHack CLR_* numbers "
                 "(0 black .. 7 gray, 8 no_color, 9 orange .. 15 white) as drawn "
                 "by a default-symbol tty build. See README.md for how tty "
                 "escapes map to these numbers (gray and no_color look the same)."),
        "monsters": dict(sorted(mons.items())),
        "monsters_by_char": dict(sorted(by_char.items())),
        "objects": dict(sorted(objs.items())),
        "shuffle_groups": {k: {"class": v["class"], "names": v["names"],
                               "appearances": [a["appearance"] for a in v["appearances"]]}
                           for k, v in shuffle.items()},
        "corpses": dict(sorted(corpses.items())),
        "statues": dict(sorted(statues.items())),
        "features": dict(sorted(feats.items())),
        "special": special,
    }


def _zap_and_explosion_colors(src: Source) -> tuple[list[dict], list[dict]]:
    """decl.c zapcolors[] indexed by zap.c ZT_* (= AD_* - 1) and mapglyph.c
    explcolors[] indexed by hack.h enum explosion_types."""
    zap = src.array("decl.c", "zapcolors")
    zap_text = (src.root / "src" / "zap.c").read_text(encoding="latin-1")
    ad = src.constants("AD_")
    zt = {ad[a] - 1: n for n, a in re.findall(
        r"#define ZT_(\w+) \((AD_\w+) - 1\)", zap_text)}
    expl = src.array("mapglyph.c", "explcolors")
    hack = _strip_comments((src.root / "include" / "hack.h").read_text(encoding="latin-1"))
    names = re.search(r"enum\s+explosion_types\s*\{(.*?)\}", hack, re.S).group(1)
    ex = {int(v): n for n, v in re.findall(r"EXPL_(\w+)\s*=\s*(\d+)", names)}
    return ([{"type": zt[i], "color": COLOR_NAMES[c], "color_value": c}
             for i, c in enumerate(zap)],
            [{"type": ex[i], "color": COLOR_NAMES[c], "color_value": c}
             for i, c in enumerate(expl)])


def build_features(src: Source, drawing: dict, objects: list[dict]) -> dict:
    E = src.enums
    zap_colors, explosion_colors = _zap_and_explosion_colors(src)
    screen = {E[k]: k for k in _enum_names(src, "rm.h", "screen_symbols")}
    traps = {E[k]: k for k in _enum_names(src, "trap.h", "trap_types")}
    mclass = {E[k]: k for k in _enum_names(src, "monsym.h", "mon_class_types")}
    oclass = {E[k]: k for k in _enum_names(src, "objclass.h", "obj_class_types")}

    def category(i: int) -> str:
        if i <= E["S_trwall"]:
            return "stone" if i == E["S_stone"] else "wall"
        if i <= E["S_hcdoor"]:
            return "door"
        if i in (E["S_bars"], E["S_tree"]):
            return "obstacle"
        if i <= E["S_darkroom"]:
            return "floor"
        if i <= E["S_litcorr"]:
            return "corridor"
        if i <= E["S_dnladder"]:
            return "stairs"
        if i <= E["S_fountain"]:
            return "furniture"
        if i <= E["S_water"]:
            return "terrain"
        if i <= E["S_vibrating_square"]:
            return "trap"
        if i <= E["S_goodpos"]:
            return "effect"
        if i <= E["S_sw_br"]:
            return "swallow"
        return "explosion"

    cmap = []
    for i, d in enumerate(drawing["defsyms"]):
        rec = {
            "index": i,
            "id": screen[i],
            "char": d["char"],
            "color": COLOR_NAMES[d["color"]],
            "color_value": d["color"],
            "explanation": d["explanation"],
            "category": category(i),
        }
        if rec["category"] == "trap" and i != E["S_vibrating_square"]:
            rec["trap_type"] = i - E["S_arrow_trap"] + 1
        elif i == E["S_vibrating_square"]:
            rec["trap_type"] = E["VIBRATING_SQUARE"]
        cmap.append(rec)
    trap_list = []
    for rec in cmap:
        if "trap_type" in rec:
            trap_list.append({
                "trap_type": rec["trap_type"], "id": traps[rec["trap_type"]],
                "cmap": rec["id"], "name": rec["explanation"], "char": rec["char"],
                "color": rec["color"], "color_value": rec["color_value"]})
    by_glyph: dict[str, list[str]] = {}
    for rec in cmap:
        if rec["category"] not in ("effect", "swallow", "explosion"):
            by_glyph.setdefault(key(rec["char"], rec["color_value"]), []).append(
                f"{rec['id']}: {rec['explanation']}")
    by_otyp = {o["otyp"]: o for o in objects if o["otyp"]}
    return {
        "_doc": "Default tty (non-DECgraphics) map symbols from src/drawing.c.",
        "cmap": cmap,
        "traps": trap_list,
        "by_glyph": dict(sorted(by_glyph.items())),
        "warnings": [{"level": i, "char": w["char"], "color": COLOR_NAMES[w["color"]],
                      "color_value": w["color"], "explanation": w["explanation"]}
                     for i, w in enumerate(drawing["warnsyms"])],
        "other_symbols": {
            "boulder": {"char": drawing["oc_syms"][E["ROCK_CLASS"]]["char"],
                        "color": by_otyp["BOULDER"]["color"],
                        "color_value": by_otyp["BOULDER"]["color_value"],
                        "note": "SYM_BOULDER defaults to the ROCK_CLASS symbol; "
                                "the 'boulder' option commonly overrides it (e.g. '0')."},
            "invisible": {"char": chr(src.macro_value("DEF_INVISIBLE")),
                          "color": "no_color", "color_value": 8,
                          "note": "remembered, unseen monster marker"},
        },
        "object_classes": [
            {"class": oclass[i], "value": i, "char": s["char"], "name": s["name"], "explain": s["explain"]}
            for i, s in enumerate(drawing["oc_syms"]) if i],
        "monster_classes": [
            {"class": mclass[i], "value": i, "char": s["char"], "explain": s["explain"]}
            for i, s in enumerate(drawing["monsyms"]) if i],
        "zap_colors": zap_colors,
        "explosion_colors": explosion_colors,
        "display_rules": DISPLAY_RULES,
        "tty_color_rendering": TTY_COLORS,
    }


DISPLAY_RULES = [
    "Monsters: default class letter in the species colour (mapglyph.c); pets, "
    "detected and ridden monsters look the same unless hilite_pet/use_inverse "
    "(reverse video) is on.",
    "The hero is drawn with the role's monster glyph (every role is a white "
    "'@'); with the showrace option it is the race's letter instead ('@' "
    "human/elf, 'h' dwarf, 'G' gnome, 'o' orc) forced to white "
    "(HI_DOMESTIC); while polymorphed, the new form's glyph and colour.",
    "Statues are drawn with the monster's class letter in the statue object "
    "colour (white) - see glyph_index 'statues'.",
    "Corpses are drawn as '%' in the colour of the dead monster - see "
    "glyph_index 'corpses'.",
    "Boulders use SYM_BOULDER (default '`', the ROCK_CLASS symbol).",
    "Remembered unseen monsters are 'I' (no colour).",
    "Warning numbers '0'-'5' replace unseen monsters when the hero has Warning.",
    "Lit corridors: with the lit_corridor option, S_litcorr shares '#' with "
    "S_corr, so mapglyph() draws it in white instead of gray.",
    "S_darkroom ('.' black) is remembered-but-unlit room floor (dark_room "
    "option, on by default).",
    "Engulfed: the eight S_sw_* symbols surround the hero in the engulfer's "
    "colour. Zaps and explosions use zap_colors / explosion_colors.",
    "Ghosts and shades use S_GHOST whose default symbol is ' ' (blank).",
    "Shuffled object classes swap description AND colour together, so a "
    "colour identifies the appearance (e.g. 'ruby' potion is red), never the "
    "identity.",
]

TTY_COLORS = {
    "_doc": ("win/tty/termcap.c init_hilite() (Unix TERMINFO build): colours "
             "1-6 use setaf(c) plain; 9-14 are the same base colour plus bold "
             "(MD); white (15) is bold + setaf(7); gray (7) and no_color (8) "
             "emit NO colour escape (terminal default foreground); black (0) is "
             "bold + setaf(0) (dark gray) when use_darkgray is on (default), "
             "otherwise it is drawn exactly like blue (4)."),
    "sgr": {
        "0": "1;30 (or 34 when use_darkgray is off)",
        "1": "31", "2": "32", "3": "33", "4": "34", "5": "35", "6": "36",
        "7": "default fg", "8": "default fg",
        "9": "1;31", "10": "1;32", "11": "1;33", "12": "1;34", "13": "1;35",
        "14": "1;36", "15": "1;37",
    },
    "decode": ("color = base (SGR 30+base) + 8 if bold; bold+30 -> 0 (black); "
               "no fg escape -> 7 (gray, which also covers no_color 8)."),
}


# ---------------------------------------------------------------------------
# Optional cross-check against a real C compile
# ---------------------------------------------------------------------------

_DUMPER = r"""
#include "config.h"
#include "permonst.h"
#include "objclass.h"
#include <stdio.h>
extern struct permonst mons[];
extern struct objclass objects[];
extern struct objdescr obj_descr[];
static void s(const char *p) { if (!p) { printf("null"); return; }
  putchar('"'); for (; *p; p++) { if (*p=='"'||*p=='\\') putchar('\\'); putchar(*p);} putchar('"'); }
int main(void) {
  int i, j;
  printf("{\"mons\":[");
  for (i = 0; mons[i].mlet; i++) {
    struct permonst *m = &mons[i];
    if (i) putchar(',');
    printf("["); s(m->mname);
    printf(",%d,%d,%d,%d,%d,%d,%u,[", m->mlet, m->mlevel, m->mmove, m->ac, m->mr,
           m->maligntyp, m->geno);
    for (j = 0; j < NATTK; j++) printf("%s[%d,%d,%d,%d]", j ? "," : "",
           m->mattk[j].aatyp, m->mattk[j].adtyp, m->mattk[j].damn, m->mattk[j].damd);
    printf("],%u,%u,%u,%u,%u,%u,%lu,%lu,%u,%u,%u]", m->cwt, m->cnutrit, m->msound,
           m->msize, m->mresists, m->mconveys, m->mflags1, m->mflags2, m->mflags3,
           m->difficulty, m->mcolor);
  }
  printf("],\"objects\":[");
  for (i = 0; !i || objects[i].oc_class != ILLOBJ_CLASS; i++) {
    struct objclass *o = &objects[i];
    if (i) putchar(',');
    printf("["); s(obj_descr[i].oc_name); putchar(','); s(obj_descr[i].oc_descr);
    printf(",%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d]",
      o->oc_name_known, o->oc_merge, o->oc_uses_known, o->oc_pre_discovered,
      o->oc_magic, o->oc_charged, o->oc_unique, o->oc_nowish, o->oc_big,
      o->oc_tough, o->oc_dir, o->oc_material, o->oc_subtyp, o->oc_oprop,
      o->oc_class, o->oc_delay, o->oc_color, o->oc_prob, o->oc_weight,
      o->oc_cost, o->oc_wsdam, o->oc_wldam, o->oc_oc1, o->oc_oc2, o->oc_nutrition);
  }
  printf("]}\n");
  return 0;
}
"""


def cc_check(root: Path, mon_raws: list[dict], obj_raws: list, mail: bool) -> str:
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        return "cc-check skipped: no C compiler"
    if not mail:  # unixconf.h #defines MAIL unconditionally; -UMAIL can't undo it
        return "cc-check skipped: only supported for the default MAIL build"
    with tempfile.TemporaryDirectory() as td:
        dumper = Path(td) / "dump.c"
        dumper.write_text(_DUMPER)
        exe = Path(td) / "dump"
        cmd = [cc, "-w", "-std=gnu89", "-I", str(root / "include"),
               str(root / "src" / "monst.c"), str(root / "src" / "objects.c"),
               str(dumper), "-o", str(exe)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode:
            raise SystemExit(f"cc-check: compile failed:\n{proc.stderr[-2000:]}")
        data = json.loads(subprocess.run([str(exe)], check=True, capture_output=True,
                                         text=True, encoding="latin-1").stdout)
    for i, (c, p) in enumerate(zip(data["mons"], mon_raws, strict=True)):
        mine = [p["mname"], p["mlet"], p["mlevel"], p["mmove"], p["ac"], p["mr"],
                p["maligntyp"], p["geno"], [list(a) for a in p["mattk"]], p["cwt"],
                p["cnutrit"], p["msound"], p["msize"], p["mresists"], p["mconveys"],
                p["mflags1"], p["mflags2"], p["mflags3"], p["difficulty"], p["mcolor"]]
        if c != mine:
            raise SystemExit(f"cc-check: monster {i} differs:\n C  {c}\n py {mine}")
    for i, (c, (name, desc, r)) in enumerate(zip(data["objects"], obj_raws, strict=True)):
        mine = [name, desc] + [r[k] for k in OBJ_FIELDS[3:]]
        if c != mine:
            raise SystemExit(f"cc-check: object {i} differs:\n C  {c}\n py {mine}")
    return (f"cc-check OK: {len(data['mons'])} monsters and {len(data['objects'])} "
            f"objects identical to a {Path(cc).name} build")


# ---------------------------------------------------------------------------
# Validation + main
# ---------------------------------------------------------------------------


def validate(monsters: list[dict], objects: list[dict]) -> list[str]:
    notes = []
    bad = [(m["name"], m["difficulty"], m["difficulty_mstrength"])
           for m in monsters if m["difficulty"] != m["difficulty_mstrength"]]
    notes.append(f"mstrength() port vs monst.c difficulty: "
                 f"{len(monsters) - len(bad)}/{len(monsters)} agree"
                 + (f"; differ: {bad}" if bad else ""))
    sums: dict[str, int] = {}
    for o in objects:
        sums[o["class"]] = sums.get(o["class"], 0) + o["prob"]
    wrong = {c: s for c, s in sums.items() if s not in (0, 1000)}
    if wrong:
        raise SystemExit(f"object class probabilities do not sum to 1000: {wrong}")
    notes.append("object probabilities sum to 1000 in every generated class")
    # monst.c Rule #1: a class is contiguous among the randomly generatable
    # monsters, i.e. those before SPECIAL_PM (PM_LONG_WORM_TAIL)
    special = next(m["index"] for m in monsters if m["pm"] == "PM_LONG_WORM_TAIL")
    seen: set[str] = set()
    for m in monsters[:special]:
        if m["class"] in seen and monsters[m["index"] - 1]["class"] != m["class"]:
            raise SystemExit(f"class {m['class']} not contiguous at {m['name']}")
        seen.add(m["class"])
    return notes


def _compact(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False)


def write_json(path: Path, top: dict) -> None:
    """Top-level keys one per line; list items / dict entries one per line."""
    parts = []
    for k, v in top.items():
        if isinstance(v, list) and v:
            body = ",\n".join("  " + _compact(x) for x in v)
            parts.append(f" {_compact(k)}: [\n{body}\n ]")
        elif isinstance(v, dict) and v and k != "_meta":
            body = ",\n".join(f"  {_compact(kk)}: {_compact(vv)}" for kk, vv in v.items())
            parts.append(f" {_compact(k)}: {{\n{body}\n }}")
        else:
            parts.append(f" {_compact(k)}: {_compact(v)}")
    text = "{\n" + ",\n".join(parts) + "\n}\n"
    json.loads(text)  # sanity
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", type=Path, help="NetHack-3.6.7 source directory")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent.parent / "src" / "nh" / "data")
    ap.add_argument("--no-mail", action="store_true",
                    help="build without MAIL (drops mail daemon + scroll of mail)")
    ap.add_argument("--cc-check", action="store_true",
                    help="also compile monst.c/objects.c and compare every field")
    args = ap.parse_args(argv)
    root = args.source.expanduser().resolve()
    if (root / "NetHack-3.6.7").is_dir():
        root = root / "NetHack-3.6.7"
    if not (root / "src" / "monst.c").is_file():
        ap.error(f"{root} does not look like a NetHack source tree")

    defines = {"TEXTCOLOR": "1"}
    if not args.no_mail:
        defines["MAIL"] = "1"
    mon_headers = ["align.h", "monattk.h", "monflag.h", "permonst.h",
                   "monsym.h", "color.h"]
    obj_headers = ["objclass.h", "prop.h", "skills.h", "color.h"]
    draw_headers = ["align.h", "monattk.h", "monflag.h", "permonst.h", "monsym.h",
                    "color.h", "objclass.h", "rm.h", "trap.h"]

    draw_src = Source(root, "drawing.c", draw_headers, defines)
    drawing = build_drawing(draw_src)
    mon_src = Source(root, "monst.c", mon_headers, defines)
    monsters, mon_raws = build_monsters(mon_src, drawing["monsyms"])
    obj_src = Source(root, "objects.c", obj_headers, defines)
    objects, shuffle, obj_raws = build_objects(obj_src, drawing["oc_syms"])
    features = build_features(draw_src, drawing, objects)
    glyphs = build_glyph_index(monsters, objects, shuffle, features)

    version = (root / "include" / "patchlevel.h").read_text(encoding="latin-1")
    ver = ".".join(re.search(rf"#define {k}\s+(\d+)", version).group(1)
                   for k in ("VERSION_MAJOR", "VERSION_MINOR", "PATCHLEVEL"))
    meta = {"nethack_version": ver, "mail": not args.no_mail,
            "generator": "scripts/gen_nh_data.py"}

    notes = validate(monsters, objects)
    if args.cc_check:
        notes.append(cc_check(root, mon_raws, obj_raws, not args.no_mail))

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "monsters.json", {"_meta": {**meta, "count": len(monsters)},
                                       "monsters": monsters})
    write_json(out / "objects.json", {"_meta": {**meta, "count": len(objects)},
                                      "shuffle_groups": shuffle,
                                      "gem_color_variants": gem_variants(objects),
                                      "wand_of_nothing_direction":
                                          "per-game random: NODIR or IMMEDIATE",
                                      "objects": objects})
    write_json(out / "glyph_index.json", {"_meta": meta, **glyphs})
    write_json(out / "features.json", {"_meta": meta, **features})
    print(f"NetHack {ver}: {len(monsters)} monsters, {len(objects)} objects "
          f"-> {out}")
    for n in notes:
        print("  " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
