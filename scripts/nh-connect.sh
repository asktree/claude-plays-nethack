#!/usr/bin/env bash
# Open an interactive ssh session to a public NetHack server's dgamelaunch
# lobby. Run inside the harness's tmux pane by `bin/nh start-remote`.
#
#   scripts/nh-connect.sh hardfought    # Hardfought US (us.hardfought.org)
#
# Host keys are pinned in play/ssh/known_hosts (strict checking). Needs a
# machine with direct outbound SSH (e.g. your own computer).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER="${1:-hardfought}"

case "$SERVER" in
  hardfought|hdf-us) HOST=us.hardfought.org; LOGIN=nethack ;;
  *) echo "unknown server: $SERVER" >&2; exit 2 ;;
esac

OPTS=(-tt
      -o StrictHostKeyChecking=yes
      -o "UserKnownHostsFile=$ROOT/play/ssh/known_hosts"
      -o ServerAliveInterval=30
      -o ServerAliveCountMax=6
      -o PubkeyAuthentication=no
      -o PreferredAuthentications=keyboard-interactive,password,none)
exec ssh "${OPTS[@]}" "$LOGIN@$HOST"
