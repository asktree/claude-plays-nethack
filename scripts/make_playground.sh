#!/usr/bin/env bash
# make_playground.sh NAME -- clone the local NetHack install into ~/.local/nethack-NAME: the same binary and data
# files, its own lock/save/bones/score files. Wizard-mode games all lock and save as "wizard", so only one can run
# per playground; a second parallel wizard-mode QA game starts with
#   bin/nh start-local qaN --wizard --nethack ~/.local/nethack-NAME/bin/nethack
set -euo pipefail
name=${1:?usage: make_playground.sh NAME}
src=${NH_PREFIX:-$HOME/.local/nethack-3.6.7}
dst=$HOME/.local/nethack-$name
[ -e "$dst" ] && { echo "$dst exists"; exit 0; }
mkdir -p "$dst/bin" "$dst/lib/nethackdir/save" "$dst/lib/nethackdir/dumplog"
for f in "$src"/lib/nethackdir/*; do
    case "$(basename "$f")" in
        [0-9]*|save|dumplog|bones*|perm|record|logfile|xlogfile|livelog|paniclog) ;;
        *) cp -a "$f" "$dst/lib/nethackdir/" ;;
    esac
done
touch "$dst"/lib/nethackdir/{perm,record,logfile,xlogfile,paniclog}
sed "s#$src/lib/nethackdir#$dst/lib/nethackdir#g" "$src/bin/nethack" > "$dst/bin/nethack"
chmod 755 "$dst/bin/nethack"
echo "playground $dst ready: --nethack $dst/bin/nethack"
