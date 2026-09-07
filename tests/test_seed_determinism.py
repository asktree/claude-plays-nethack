"""Two games at the same seeds must agree on everything, including state
NetHack derives from the wall clock rather than the RNGs. ubirthday drives
shopkeeper names, anthole species and glass-gem prices; the NLE fork seeds
it from time_seed when fix_moon_phase is on (a real run diverged at its
first shop: "Adjama's" vs "Wonotobo's general store")."""

from __future__ import annotations

import glob
import os
import re

import gymnasium as gym
from nle import nethack


def _birthdate(seed: int, fix_moon_phase: bool) -> str:
    env = gym.make(
        "NetHack-v0", character="val-hum-fem-law", actions=nethack.ACTIONS,
        fix_moon_phase=fix_moon_phase, allow_all_modes=True,
    )
    try:
        env.unwrapped.seed(seed, seed, reseed=False)
        env.reset()
        vardir = env.unwrapped.nethack._vardir
        acts = list(nethack.ACTIONS)
        # #quit, confirm, then pump the end-of-game screens until NLE says done.
        for key in [nethack.Command.QUIT, ord("y")] + [nethack.MiscAction.MORE] * 30:
            _, _, term, trunc, _ = env.step(acts.index(key))
            if term or trunc:
                break
        for path in glob.glob(vardir + "/**/xlogfile", recursive=True):
            m = re.search(r"birthdate=(\d{8})", open(path, errors="replace").read())
            if m:
                return m.group(1)
        raise AssertionError(f"no birthdate in xlogfile under {vardir}")
    finally:
        env.close()


def test_birthdate_is_seed_determined():
    assert _birthdate(7, True) == _birthdate(7, True)
    assert _birthdate(7, True) != _birthdate(8, True)


def test_birthdate_is_wall_clock_without_fix_moon_phase():
    import datetime
    assert _birthdate(7, False) == datetime.date.today().strftime("%Y%m%d")
