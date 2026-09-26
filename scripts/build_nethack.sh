#!/usr/bin/env bash
#
# build_nethack.sh -- build and install a local, vanilla NetHack 3.6.7
# (tty + curses window ports, tty by default) for developing and testing the
# terminal harness.  Real games are played on a public server; this build
# only has to behave like vanilla 3.6.7 tty.  See scripts/README-nethack-local.md.
#
# Idempotent: the source tarball is cached (and checksum-verified), and a
# stamp in the prefix records the inputs of the last successful install
# (tarball, patches, this script, prefix, compiler).  If none changed the
# script only makes sure the pristine source copy exists and exits.
# Rebuilding never wipes the variable data in HACKDIR (record, logfile,
# xlogfile, save/, dumplog/, bones), unlike `make install`, which rm -rf's it.
#
# Environment knobs:
#   NH_PREFIX           install prefix               [$HOME/.local/nethack-3.6.7]
#   NH_BUILD_DIR        tarball cache + build tree   [$HOME/.cache/nethack-build]
#   NH_PRISTINE_SRC     unpatched source tree kept for rule lookups
#                                                    [$HOME/src/nethack-3.6.7]
#                       (set to "" to skip it)
#   NH_SKIP_PATCHES     space-separated patch file names to leave out,
#                       e.g. NH_SKIP_PATCHES=seed.patch
#   NH_SHIPPED_LEXYACC  1 = use the pre-generated lexer/parser sources from
#                       sys/share even if lex/yacc are installed (automatic
#                       when either tool is missing)
#   NH_FORCE            1 = rebuild and reinstall even if the stamp matches
#
# Result:
#   $NH_PREFIX/bin/nethack          launcher (vanilla sys/unix/nethack.sh)
#   $NH_PREFIX/lib/nethackdir/      HACKDIR: nethack binary, recover, nhdat,
#                                   sysconf, record, logfile, xlogfile, perm,
#                                   save/, dumplog/, lock and bones files

set -euo pipefail

NH_VERSION=3.6.7
TARBALL_URL=https://www.nethack.org/download/3.6.7/nethack-367-src.tgz
TARBALL_SHA256=98cf67df6debf9668a61745aa84c09bcab362e5d33f5b944ec5155d44d2aacb2
TARBALL_TOPDIR=NetHack-3.6.7

SCRIPT_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
PATCH_DIR=$(dirname "$SCRIPT_PATH")/patches

NH_PREFIX=${NH_PREFIX:-$HOME/.local/nethack-$NH_VERSION}
NH_BUILD_DIR=${NH_BUILD_DIR:-$HOME/.cache/nethack-build}
NH_PRISTINE_SRC=${NH_PRISTINE_SRC-$HOME/src/nethack-$NH_VERSION}
NH_SKIP_PATCHES=${NH_SKIP_PATCHES:-}
NH_SHIPPED_LEXYACC=${NH_SHIPPED_LEXYACC:-0}
NH_FORCE=${NH_FORCE:-0}
NH_PREFIX=${NH_PREFIX%/}
NH_BUILD_DIR=${NH_BUILD_DIR%/}

HACKDIR=$NH_PREFIX/lib/nethackdir
TARBALL=$NH_BUILD_DIR/$(basename "$TARBALL_URL")
SRC=$NH_BUILD_DIR/$TARBALL_TOPDIR
LOG=$NH_BUILD_DIR/build.log
STAMP=$NH_PREFIX/.build-stamp

log() { printf '[build_nethack] %s\n' "$*"; }
die() { printf '[build_nethack] ERROR: %s\n' "$*" >&2; exit 1; }

# Run a build step with its output going to $LOG; show the tail on failure.
run() {
    printf '\n$ %s\n' "$*" >>"$LOG"
    if ! "$@" >>"$LOG" 2>&1; then
        tail -n 40 "$LOG" >&2
        die "step failed: $* (full log: $LOG)"
    fi
}

sha256() { sha256sum "$1" | cut -d' ' -f1; }

# --- sanity checks ----------------------------------------------------------

# NH_PREFIX is baked into the binary (-DHACKDIR="..."), the Makefiles and a
# sed expression, so keep it to boring characters.
for var in NH_PREFIX NH_BUILD_DIR; do
    val=${!var}
    [[ $val == /* ]] || die "$var must be an absolute path (got '$val')"
    [[ $val =~ ^[A-Za-z0-9._/+-]+$ ]] \
        || die "$var may only contain letters, digits and ._/+- (got '$val')"
done

for tool in make tar gzip patch sed awk sha256sum install "${CC:-cc}"; do
    command -v "$tool" >/dev/null 2>&1 || die "required tool not found: $tool"
done

PATCHES=()
for p in "$PATCH_DIR"/*.patch; do
    [[ -e $p ]] || continue
    if [[ " $NH_SKIP_PATCHES " == *" $(basename "$p") "* ]]; then
        log "skipping $(basename "$p") (NH_SKIP_PATCHES)"
        continue
    fi
    PATCHES+=("$p")
done

# lev_comp/dgn_comp need yacc+lex; without them use the pre-generated
# sources the devteam ships in sys/share.
YACC_CMD= LEX_CMD=
if [[ $NH_SHIPPED_LEXYACC != 1 ]]; then
    if command -v yacc >/dev/null 2>&1; then YACC_CMD=yacc
    elif command -v bison >/dev/null 2>&1; then YACC_CMD="bison -y"
    elif command -v byacc >/dev/null 2>&1; then YACC_CMD=byacc
    fi
    if command -v lex >/dev/null 2>&1; then LEX_CMD=lex
    elif command -v flex >/dev/null 2>&1; then LEX_CMD=flex
    fi
fi
if [[ -n $YACC_CMD && -n $LEX_CMD ]]; then
    LEXYACC_MODE="YACC=$YACC_CMD LEX=$LEX_CMD"
else
    LEXYACC_MODE=shipped
fi

fingerprint() {
    {
        echo "nethack $NH_VERSION $TARBALL_SHA256"
        echo "prefix $NH_PREFIX"
        echo "lexyacc $LEXYACC_MODE"
        echo "cc $("${CC:-cc}" --version 2>/dev/null | head -n1)"
        echo "script $(sha256 "$SCRIPT_PATH")"
        for p in ${PATCHES[@]+"${PATCHES[@]}"}; do
            echo "patch $(basename "$p") $(sha256 "$p")"
        done
    } | sha256sum | cut -d' ' -f1
}

fetch_tarball() {
    mkdir -p "$NH_BUILD_DIR"
    if [[ -f $TARBALL && $(sha256 "$TARBALL") == "$TARBALL_SHA256" ]]; then
        return 0
    fi
    log "downloading $TARBALL_URL"
    rm -f "$TARBALL.part"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --retry 3 -o "$TARBALL.part" "$TARBALL_URL"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$TARBALL.part" "$TARBALL_URL"
    else
        die "need curl or wget to download $TARBALL_URL"
    fi
    local got
    got=$(sha256 "$TARBALL.part")
    if [[ $got != "$TARBALL_SHA256" ]]; then
        rm -f "$TARBALL.part"
        die "checksum mismatch for $TARBALL_URL: got $got, want $TARBALL_SHA256"
    fi
    mv "$TARBALL.part" "$TARBALL"
}

# Unmodified 3.6.7 tree for rule lookups.  Never patched, never overwritten.
ensure_pristine_src() {
    [[ -n $NH_PRISTINE_SRC ]] || return 0
    if [[ -e $NH_PRISTINE_SRC ]]; then
        grep -q '^#define PATCHLEVEL 7' "$NH_PRISTINE_SRC/include/patchlevel.h" 2>/dev/null \
            || log "WARNING: $NH_PRISTINE_SRC exists but is not a NetHack 3.6.7 tree; left alone"
        return 0
    fi
    fetch_tarball
    log "unpacking pristine source to $NH_PRISTINE_SRC"
    local parent tmp
    parent=$(dirname "$NH_PRISTINE_SRC")
    mkdir -p "$parent"
    tmp=$(mktemp -d "$parent/.nethack-src.XXXXXX")
    tar -xzf "$TARBALL" -C "$tmp"
    mv "$tmp/$TARBALL_TOPDIR" "$NH_PRISTINE_SRC"
    rmdir "$tmp"
}

# --- up to date? ----------------------------------------------------------

mkdir -p "$NH_BUILD_DIR"
if command -v flock >/dev/null 2>&1; then
    exec 9>"$NH_BUILD_DIR/.lock"
    flock 9   # serialize concurrent runs sharing a build dir
fi

FP=$(fingerprint)
if [[ $NH_FORCE != 1 && -f $STAMP && $(head -n1 "$STAMP") == "$FP" \
      && -x $HACKDIR/nethack && -x $NH_PREFIX/bin/nethack \
      && -f $HACKDIR/nhdat && -f $HACKDIR/sysconf \
      && -d $HACKDIR/save && -d $HACKDIR/dumplog ]]; then
    # (nethack silently skips the dumplog if dumplog/ is missing)
    ensure_pristine_src
    log "up to date: $NH_PREFIX (NH_FORCE=1 to rebuild)"
    exit 0
fi

# Check for ncurses up front: a missing -dev package otherwise shows up
# as a link error deep in the build.
ncurses_probe=$(mktemp -d)
printf '#include <curses.h>\nint main(void) { return initscr() == 0; }\n' \
    >"$ncurses_probe/probe.c"
if ! "${CC:-cc}" "$ncurses_probe/probe.c" -o "$ncurses_probe/probe" \
        -lncurses -ltinfo >/dev/null 2>&1; then
    rm -rf "$ncurses_probe"
    die "ncurses headers/libraries not found (Debian/Ubuntu: apt-get install libncurses-dev)"
fi
rm -rf "$ncurses_probe"

# --- fetch, unpack, patch ---------------------------------------------------

fetch_tarball
ensure_pristine_src

: >"$LOG"
log "unpacking fresh build tree in $SRC (log: $LOG)"
rm -rf "$SRC"
tar -xzf "$TARBALL" -C "$NH_BUILD_DIR"

for p in ${PATCHES[@]+"${PATCHES[@]}"}; do
    log "applying $(basename "$p")"
    run patch -d "$SRC" -p1 --batch --no-backup-if-mismatch -i "$p"
done

# --- configure --------------------------------------------------------------

# Stock Linux hints (already tty + curses, DLB, SYSCF, DUMPLOG, TIMED_DELAY),
# with the install locations moved under $NH_PREFIX.
HINTS=sys/unix/hints/linux-local
sed -e "s|^PREFIX=.*|PREFIX=$NH_PREFIX|" \
    -e 's|^HACKDIR=.*|HACKDIR=$(PREFIX)/lib/$(GAME)dir|' \
    -e 's|^SHELLDIR *=.*|SHELLDIR = $(PREFIX)/bin|' \
    "$SRC/sys/unix/hints/linux" >"$SRC/$HINTS"
for want in "PREFIX=$NH_PREFIX" 'HACKDIR=$(PREFIX)/lib/$(GAME)dir' \
            'SHELLDIR = $(PREFIX)/bin' 'CFLAGS+=-DCURSES_GRAPHICS'; do
    grep -qxF "$want" "$SRC/$HINTS" || die "hints/linux changed shape; could not set: $want"
done
run sh -c "cd '$SRC' && sh sys/unix/setup.sh $HINTS"

MAKE_ARGS=(
    # nroff/tbl/col are often missing; the Guidebook isn't installed anyway,
    # so use the preformatted copy (Makefile.doc's documented fallback).
    "GUIDECMD=cat Guidebook.txt"
)
if [[ $LEXYACC_MODE == shipped ]]; then
    log "lex/yacc: using pre-generated sources from sys/share"
    cp "$SRC"/sys/share/{lev,dgn}_{yacc,lex}.c "$SRC/util/"
    cp "$SRC"/sys/share/{lev,dgn}_comp.h "$SRC/include/"
    # newer than lev_comp.y/.l etc. so make never tries to regenerate them
    touch "$SRC"/util/{lev,dgn}_yacc.c
    touch "$SRC"/include/{lev,dgn}_comp.h "$SRC"/util/{lev,dgn}_lex.c
else
    log "lex/yacc: $LEXYACC_MODE"
    MAKE_ARGS+=("YACC=$YACC_CMD" "LEX=$LEX_CMD")
fi

# --- build ------------------------------------------------------------------

log "building (serial make; takes a minute or two)"
run make -C "$SRC" "${MAKE_ARGS[@]}" all

# --- install ----------------------------------------------------------------

# Same files and modes as `make install` (hints: GAMEPERM 0755,
# VARDIRPERM 0755, VARFILEPERM 0600) minus its `rm -rf $(HACKDIR)`.
# Games may be running from this prefix while it is rebuilt, so every file
# is copied next to its destination and renamed over it: a game starting
# mid-install never sees a missing or half-written file, and running games
# keep the binary/nhdat inodes they already have open.
put() {  # put MODE SRC DEST
    install -m "$1" "$2" "$3.new.$$"
    mv -f "$3.new.$$" "$3"
}
log "installing into $NH_PREFIX"
install -d -m 0755 "$NH_PREFIX/bin" "$HACKDIR" "$HACKDIR/save" "$HACKDIR/dumplog"
put 0755 "$SRC/src/nethack" "$HACKDIR/nethack"
put 0755 "$SRC/util/recover" "$HACKDIR/recover"
for f in nhdat license symbols; do
    put 0644 "$SRC/dat/$f" "$HACKDIR/$f"
done
for f in perm record logfile xlogfile; do
    [[ -e $HACKDIR/$f ]] || : >"$HACKDIR/$f"
    chmod 0600 "$HACKDIR/$f"
done

# Launcher: the substitution Makefile.top's `dofiles` target makes.
sed -e "s;/usr/games/lib/nethackdir;$HACKDIR;" \
    "$SRC/sys/unix/nethack.sh" >"$NH_BUILD_DIR/nethack.launcher"
put 0755 "$NH_BUILD_DIR/nethack.launcher" "$NH_PREFIX/bin/nethack"

# sysconf: vanilla sys/unix/sysconf with three changes.
#  WIZARDS=*     anyone may use -D (wizard mode) to set up test scenarios.
#  MAXPLAYERS=0  lock files are <uid><playername>, so any number of games
#                with different names can run at once, while a second game
#                under the same name gets "There is already a game in
#                progress under your name."  (1..25 would switch to shared
#                alock..ylock letter locks with no per-name check.)
#  DUMPLOGFILE   one dump per finished game, named by end time (%D) because
#                games run with NETHACK_SEED all share one frozen start time
#                (%d).  Relative to the playground the game chdir()s into:
#                $HACKDIR/dumplog normally, $NETHACKDIR/dumplog for a private
#                playground (where two games may share a name, e.g. "wizard").
{
    echo "# Generated by claude-plays-nethack scripts/build_nethack.sh from the"
    echo "# vanilla sys/unix/sysconf; rewritten on every (re)build, so edit the"
    echo "# script rather than this file.  Changed: WIZARDS, MAXPLAYERS, DUMPLOGFILE."
    echo "#"
    sed -e 's|^WIZARDS=.*|WIZARDS=*|' \
        -e 's|^MAXPLAYERS=.*|MAXPLAYERS=0|' \
        -e 's|^#DUMPLOGFILE=.*|DUMPLOGFILE=dumplog/%n.%D.txt|' \
        "$SRC/sys/unix/sysconf"
} >"$NH_BUILD_DIR/sysconf"
for want in 'WIZARDS=*' 'MAXPLAYERS=0' 'DUMPLOGFILE=dumplog/%n.%D.txt'; do
    grep -qxF "$want" "$NH_BUILD_DIR/sysconf" || die "sysconf changed shape; could not set: $want"
done
put 0600 "$NH_BUILD_DIR/sysconf" "$HACKDIR/sysconf"

# --- smoke test + stamp -----------------------------------------------------

version=$("$NH_PREFIX/bin/nethack" --version 2>&1 | head -n1)
[[ $version == *"Version $NH_VERSION"* ]] || die "installed binary reports: $version"

applied=()
for p in ${PATCHES[@]+"${PATCHES[@]}"}; do applied+=("$(basename "$p")"); done
{
    echo "$FP"
    echo "# $version"
    echo "# built $(date -u '+%Y-%m-%dT%H:%M:%SZ') by $SCRIPT_PATH"
    echo "# patches: ${applied[*]:-none}"
    echo "# lex/yacc: $LEXYACC_MODE"
} >"$STAMP"

log "done: $version"
log "  launcher: $NH_PREFIX/bin/nethack"
log "  HACKDIR:  $HACKDIR"
log "  patches:  ${applied[*]:-none}"
