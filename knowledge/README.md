# NetHack knowledge base

Offline plain-text copies of NetHackWiki pages, for the player agent to `grep`
during play. The target game is NetHack 3.6.x: NLE runs 3.6.6, and the wiki mostly
documents 3.6.7.

## Layout

| path | what | in git? |
|---|---|---|
| `INDEX.md` | Grouped index with one line per file: strategy, dungeon and special levels, monsters by class letter (with stats), objects by class (with cost, weight and unidentified appearance), mechanics | yes |
| `README.md` | This file | yes |
| `wiki/<Page_Name>.txt` | One converted wiki page per file | no, regenerate it |
| `../scripts/fetch_wiki.py` | Fetcher and converter | yes |
| `../.cache/nethackwiki/` | Raw wikitext and revision metadata used for re-runs | no |

File names are the page title in the wiki's URL form: spaces become `_`, and a
`/`, if any, becomes `-`. So the file for a title is `title.replace(" ", "_") +
".txt"`, for example `Mines'_End.txt`, `Dwarf_(monster).txt` or
`Why_do_I_keep_dying?.txt`. Some names contain `'`, `(` or `?`, so quote the
path in shell commands, e.g. `cat "knowledge/wiki/Mines'_End.txt"`.

For renamed pages the title is the one the page had at the snapshot date; see
the version caveat below.

## File format

Each file starts with a header:

```
Title: Floating eye
Source: https://nethackwiki.com/wiki/Floating_eye
Revision: 200274 of 2026-03-09 (snapshot as of 2026-05-02, i.e. before NetHack 5.0.0; ...)
Permalink: https://nethackwiki.com/index.php?oldid=200274
Wiki version tag: page states it reflects NetHack 3.6.7
Also covers: <other names that redirect here, e.g. gem names on Gem.txt>
License: CC BY-SA 3.0, NetHackWiki contributors; converted to plain text (see knowledge/README.md)
==============================================================================
```

A few rules for the body that follows:

- **Infoboxes:** monster, object and special-level pages open with their infobox as
  `key: value` lines between `[Monster infobox]` and `[end infobox]`. Monster
  infoboxes list difficulty, level, speed, AC, MR, attacks, resistances,
  resistances conveyed, weight and nutrition. Object infoboxes list cost, weight,
  damage and AC. Level infoboxes say whether the level is diggable, teleportable
  and mappable.
- **Structure:** headings are `##` and `###`, bullets are `- `, and tables are
  `| a | b |` pipe tables.
- **Maps:** level maps, Sokoban maps and solutions, and other `<pre>` blocks are
  kept verbatim.
- **Messages:** game messages appear as `"message text" -- explanation`, so you
  can grep for a message you just saw.
- **Dropped content:** references, images, navigation boxes and flavour quotes
  from the in-game encyclopedia are removed.

## Version caveat: the snapshot is from before NetHack 5.0.0

NetHack 5.0.0, the renamed 3.7.0, was released on 2026-05-02. Since then
NetHackWiki has been rewriting pages to describe 5.0.0, and has renamed some of
them: Priest became Cleric, gnome lord became gnome leader, and dwarf king
became dwarf ruler. Here is how the knowledge base handles that:

- **Snapshot revision.** Every page is taken at its last revision **before
  2026-05-02**. Those revisions describe 3.6.x and flag 3.7 changes explicitly.
- **3.7 notes are kept.** They appear as
  `[NetHack 3.7.0 change, NOT in 3.6.x: ...]` notes, which do **not** apply to
  our game.
- **Older-version notes are kept.** Notes such as "In NetHack 3.4.3 ..." or
  "Before 3.6.0 ..." are left intact. When a page says two versions behave
  differently, the 3.6.x behaviour is the one that applies.
- **Version tag.** The `Wiki version tag` header line records which version the
  page says it was last checked against. A page tagged 3.4.3 may be stale for
  3.6.
- **Snapshot-era names.** Files are named after the page title at the snapshot
  date, so they use 3.6 names (`Priest.txt`, `Gnome_lord.txt`). A header line
  notes the current wiki title.

## Regenerating

```
python3 scripts/fetch_wiki.py              # fetch anything missing, convert, rewrite INDEX.md
python3 scripts/fetch_wiki.py --reconvert  # offline: rebuild wiki/*.txt and INDEX.md from the cache
python3 scripts/fetch_wiki.py --force      # re-download everything
python3 scripts/fetch_wiki.py --only "Floating eye" "Some other page"   # add or refresh pages
python3 scripts/fetch_wiki.py --list       # show the page plan
python3 scripts/fetch_wiki.py --latest     # current wiki text (5.0.0-oriented) instead of the snapshot
```

The script needs only the standard library (Python 3.9 or later). It uses the
MediaWiki API at `https://nethackwiki.com/api.php` and batches 50 pages per
request. It makes at most about 2 requests per second, sends a descriptive
User-Agent, and retries with backoff. `index.php?action=raw` is behind a
Cloudflare challenge for scripts, which is why the script doesn't use it.

The page list lives in the script:

- **Monsters and objects** are the canonical NetHack 3.6.7 lists from `monst.c`,
  `objects.c` and `artilist.h`.
- **Strategy, dungeon and mechanics** pages are curated lists, and INDEX.md gists
  are written next to them.

Add a title there to include it permanently.

## License and attribution

The text in `wiki/` comes from **NetHackWiki** (https://nethackwiki.com) and was
written by the NetHackWiki contributors. Each file's `Source:` and `Permalink:`
lines point to the exact page revision used, and the page history lists its
authors.

- **License:** according to
  [NetHackWiki:Copyrights](https://nethackwiki.com/wiki/NetHackWiki:Copyrights),
  contributions are licensed under the **Creative Commons
  Attribution-ShareAlike 3.0 Unported** license (CC BY-SA 3.0,
  https://creativecommons.org/licenses/by-sa/3.0/). The wiki was originally
  under the GNU Free Documentation License 1.2 or later. It was relicensed to
  CC BY-SA 3.0 on 2009-06-19 under section 11 of GFDL 1.3. The site footer
  shows no license line; the copyright page above is the authoritative
  statement.
- **Other material on the wiki:**
  - Some pages include the Hugo/O'Donnell spoilers, which use a BSD-style
    license.
  - Some pages include Rodney contributions, released under the GFDL.
  - Quotations of NetHack source code and game messages are covered by the
    NetHack General Public License, and the wiki's copyright page notes that
    this license is not CC BY-SA-compatible.
- **Changes we made:** the wikitext was converted to plain text. Templates were
  rendered or removed, and references, images and navigation were dropped.
  Converted pages are derivative works under CC BY-SA 3.0. The page dumps stay
  out of git because they are large and can be regenerated. If you redistribute
  them, keep this attribution and the same license.
