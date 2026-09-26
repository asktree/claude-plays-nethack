"""nh — a terminal harness for playing real NetHack (local or on a public server).

The game runs inside a tmux pane (so the connection survives harness
restarts and humans can watch with `tmux attach -r`). A per-game daemon
(`nh.daemon`) owns the pane, parses the screen, and hosts a persistent
Python kernel. The `nh` CLI (`nh.cli`) is a thin client over a unix socket.
"""

__version__ = "0.1.0"
