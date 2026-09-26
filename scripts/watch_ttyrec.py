#!/usr/bin/env python3
"""Spectate a Hardfought game over HTTPS by replaying its public ttyrec.

While a game is being played, Hardfought publishes the growing recording at
  https://www.hardfought.org/userdata/<F>/<Name>/nethack/ttyrec/<stamp>.ttyrec
This fetches it (incrementally, with HTTP Range, caching what it has), feeds the
frames into a terminal emulator (pyte, 80x24) and prints the current screen.
No SSH needed, so it works from sandboxes that can only do HTTPS.

usage:
  scripts/watch_ttyrec.py ClaudeAscends            # newest ttyrec of that player
  scripts/watch_ttyrec.py --url <ttyrec url>
  scripts/watch_ttyrec.py ClaudeAscends --history 5 # also show the last 5 screens with changes
Be polite: run it when you need a look, not in a tight loop (the server is shared).
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parents[1] / "run" / "spectate"
UA = "claude-plays-nethack spectator (github.com/asktree/claude-plays-nethack)"


def http_get(url: str, start: int | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if start:
        req.add_header("Range", f"bytes={start}-")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 416:   # nothing new
            return b""
        raise


def newest_ttyrec(player: str) -> str:
    base = f"https://www.hardfought.org/userdata/{player[0]}/{player}/nethack/ttyrec/"
    html = http_get(base).decode(errors="replace")
    names = sorted(set(re.findall(r'href="([0-9][^"]+\.ttyrec(?:\.gz)?)"', html)))
    if not names:
        raise SystemExit(f"no ttyrecs listed at {base}")
    live = [n for n in names if n.endswith(".ttyrec")]
    return base + (live[-1] if live else names[-1])


def frames(data: bytes):
    i = 0
    while i + 12 <= len(data):
        sec, usec, ln = struct.unpack("<III", data[i:i + 12])
        if i + 12 + ln > len(data):
            break
        yield sec + usec / 1e6, data[i + 12:i + 12 + ln]
        i += 12 + ln


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("player", nargs="?")
    ap.add_argument("--url")
    ap.add_argument("--history", type=int, default=0, help="also print the last N distinct screens")
    a = ap.parse_args()
    import pyte  # pip install pyte
    url = a.url or newest_ttyrec(a.player)
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / url.rsplit("/", 1)[-1]
    have = local.read_bytes() if local.exists() else b""
    if url.endswith(".gz"):
        import gzip
        data = gzip.decompress(http_get(url))
    else:
        new = http_get(url, start=len(have) or None)
        data = have + new
        local.write_bytes(data)
    screen = pyte.Screen(80, 24)
    stream = pyte.ByteStream(screen)
    shots = []
    last_t = None
    for t, chunk in frames(data):
        stream.feed(chunk)
        last_t = t
        if a.history:
            shots.append("\n".join(screen.display))
    import datetime
    when = datetime.datetime.utcfromtimestamp(last_t).strftime("%Y-%m-%d %H:%M:%S UTC") if last_t else "?"
    print(f"{url}\n{len(data)} bytes, last frame {when}")
    if a.history:
        uniq = []
        for s in shots:
            if not uniq or uniq[-1] != s:
                uniq.append(s)
        for s in uniq[-a.history - 1:-1]:
            print("-" * 80)
            print("\n".join(r.rstrip() for r in s.split("\n")))
    print("=" * 80)
    for y, row in enumerate(screen.display):
        print(f"{y:>2}|{row.rstrip()}")


if __name__ == "__main__":
    main()
