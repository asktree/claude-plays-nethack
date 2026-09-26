"""Filesystem layout for per-game runtime state (all under run/, gitignored)."""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = Path(os.environ.get("NH_RUN_DIR", str(REPO_ROOT / "run")))
CURRENT_FILE = RUN_DIR / "CURRENT"


def game_dir(name: str) -> Path:
    if not name or "/" in name or name.startswith("."):
        raise ValueError(f"bad game name {name!r}")
    return RUN_DIR / name


def load_meta(name: str) -> dict:
    p = game_dir(name) / "meta.json"
    if not p.exists():
        raise FileNotFoundError(f"no game {name!r} (missing {p}). Start one with `nh start-local`.")
    return json.loads(p.read_text())


def save_meta(name: str, meta: dict) -> None:
    d = game_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(meta, indent=2))


def current_game(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("NH_GAME")
    if env:
        return env
    if CURRENT_FILE.exists():
        name = CURRENT_FILE.read_text().strip()
        if name:
            return name
    raise SystemExit("no current game: pass --game NAME, set NH_GAME, or run `nh use NAME`")


def set_current(name: str) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_FILE.write_text(name + "\n")
