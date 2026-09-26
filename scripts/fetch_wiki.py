#!/usr/bin/env python3
"""Build an offline, grep-friendly NetHack knowledge base from NetHackWiki.

Outputs
  knowledge/wiki/<Page_Name>.txt  one plain-text file per wiki page (gitignored;
                                  regenerate with this script)
  knowledge/INDEX.md              grouped index, one line per file (committed)

Cache (gitignored, lets re-runs and --reconvert work without the network)
  .cache/nethackwiki/pages/<Page_Name>.json  raw wikitext + revision metadata
  .cache/nethackwiki/state.json              requested title -> page mapping
  .cache/nethackwiki/moves.json              page-move log since the snapshot

Version pinning
  NetHack 5.0.0 (the renamed 3.7.0) was released 2026-05-02 and NetHackWiki has
  been rewriting pages to describe 5.0.0 since then, and renaming some of them
  (Priest -> Cleric, gnome lord -> gnome leader, ...). The agent plays 3.6.x
  (NLE), so by default every page is taken at its last revision *before*
  --as-of (default 2026-05-02T00:00:00Z). Those revisions describe 3.6.x and
  mark 3.7.0 changes with {{upcoming}} notes, which are kept and rendered as
  "[NetHack 3.7.0 change, NOT in 3.6.x: ...]". Files are named after the page
  title at the snapshot date. --latest fetches current revisions instead.

Usage
  python3 scripts/fetch_wiki.py              # fetch what's missing, convert, write INDEX.md
  python3 scripts/fetch_wiki.py --force      # re-download and re-convert everything
  python3 scripts/fetch_wiki.py --reconvert  # rebuild .txt + INDEX.md from the cache (offline)
  python3 scripts/fetch_wiki.py --only "Floating eye" "Sokoban Level 1a"
  python3 scripts/fetch_wiki.py --list       # print the page plan and exit

Politeness: at most ~2 requests/second (--delay), a descriptive User-Agent, and
retries with exponential backoff on 429/5xx/network errors. Pages are fetched
through the MediaWiki API (https://nethackwiki.com/api.php), 50 per request;
index.php?action=raw sits behind a Cloudflare challenge for scripts.

Fetched text is CC BY-SA 3.0 (NetHackWiki contributors); see knowledge/README.md.
Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "knowledge" / "wiki"
INDEX_PATH = ROOT / "knowledge" / "INDEX.md"
CACHE_DIR = ROOT / ".cache" / "nethackwiki"

SITE = "https://nethackwiki.com"
API = SITE + "/api.php"
USER_AGENT = (
    "claude-plays-nethack-kb/1.0 (offline NetHack knowledge base builder for a "
    "game-playing AI agent; rate-limited to 2 req/s; Python-urllib)"
)
DEFAULT_AS_OF = "2026-05-02T00:00:00Z"  # NetHack 5.0.0 release date
BATCH = 50  # MediaWiki limit for titles= per query (non-bot)
LICENSE_LINE = ("CC BY-SA 3.0, NetHackWiki contributors; converted to plain text "
                "(see knowledge/README.md)")


# ----------------------------------------------------------------------------
# Page plan: what to fetch and how INDEX.md groups it.
#
# Curated pages are (title, gist[, wiki title]). Titles use the 3.6-era names;
# redirects and page moves are resolved automatically. A gist of "" means
# "auto-generate from the page's first sentence". The optional third element
# names the wiki page when the plain title is a disambiguation page.
# ----------------------------------------------------------------------------

STRATEGY = [
    ("General strategy (start here)", [
        ("Standard strategy", "Canonical game plan from turn 1 to ascension, with milestones"),
        ("Game stages", "Early/mid/late game goals and what to do at each stage"),
        ("Why do I keep dying?",
         "Beginner's guide to the most common deaths and how to avoid them"),
        ("Yet Another Stupid Death", "Catalogue of avoidable deaths (YASDs) and their lessons"),
        ("Things To Do If You're Going to Die Next Turn",
         "Emergency checklist: pray, quaff, zap, Elbereth, escape"),
        ("Player's misconceptions", "Popular myths about NetHack mechanics, corrected"),
        ("Role difficulty", "Which roles are easiest; Valkyrie is the easiest to win with"),
        ("Ascension kit", "The standard set of items/intrinsics you want before the endgame"),
        ("Ascension run", "Carrying the Amulet up the dungeon to the planes: plan and dangers"),
        ("Escape item", "Items that get you out of trouble instantly, and when to use them"),
        ("Healing", "Every way to restore hit points, ranked by situation"),
        ("Safe area", "Making safe spots to rest: Elbereth, scare monster, stairs, closets"),
        ("Movement tactics", "Positioning: fight in corridors/doorways, never get surrounded"),
        ("Hit and run", "Using speed to attack and retreat before monsters can respond"),
        ("Stash", "Where and how to store spare items safely between trips"),
        ("Digging for victory", "Descending fast by digging down; when it is and isn't wise"),
        ("Level teleport", "Level teleportation: sources, control, limits, and safe uses"),
        ("Protection racket", "Buying cheap AC from temple priests while at low experience level"),
        ("Nurse dancing", "Raising max HP by letting nurses 'heal' you while unarmed"),
        ("Exercise", "How training strength/dex/con/wis works and what abuses stats"),
        ("Trouble", "Problems prayer can fix (major/minor trouble) and their priority"),
        ("Portal detection methods",
         "Finding magic portals (Quest, Fort Ludios) by messages and tricks"),
        ("Cannibalism", "Eating your own race (dwarves, for a dwarf): -2..-5 Luck and aggravate monster"),
        ("Elbereth", "Engrave Elbereth to scare most monsters; which ignore it; 3.6 erasure rules"),
        ("Engraving", "Engraving mechanics: tools, durability, semi-permanent vs dust"),
    ]),
    ("Valkyrie and dwarf specifics", [
        ("Valkyrie", "Valkyrie role: starting kit, cold res + stealth, speed at XL7, strategy"),
        ("Dwarf (starting race)",
         "Dwarven race: infravision, peaceful Mines inhabitants, dwarvish gear"),
        ("Excalibur", "Dip a long sword into a fountain at XL5+ as a lawful to get Excalibur"),
        ("Mjollnir", "Thrown lightning war hammer artifact; Valkyries can catch it on return"),
        ("Valkyrie quest", "Valkyrie quest: Norn, Lord Surtur, fire giants, the Orb of Fate"),
    ]),
    ("Religion, luck and alignment", [
        ("Prayer", "When praying is safe (timeout, luck, alignment) and what gods fix"),
        ("Prayer timeout", "How prayer timeout works and how to estimate when you can pray"),
        ("Luck", "Luck mechanics: sources, penalties, timeout, and luckstones"),
        ("Alignment", "Lawful/neutral/chaotic alignment and what depends on it"),
        ("Alignment record", "Hidden alignment score: what raises/lowers it; needed for prayer"),
        ("Altar", "Altars: BUC-identify by dropping items, alignment, conversion"),
        ("Sacrifice", "Offering fresh corpses at altars for gifts, luck and conversion"),
        ("Crowning", "Becoming your god's champion: resistances, a skill slot, often an artifact weapon"),
        ("God", "The pantheons: each role's lawful/neutral/chaotic gods"),
        ("Anger", "Divine anger: causes, effects, and how to calm your god"),
        ("Sanctuary", "Hostile monsters won't enter a co-aligned temple you're in"),
        ("Aligned priest", "Temple priests: donate gold for AC protection; don't anger them"),
        ("Intrinsic protection", "AC bonus from priest donations and divine gifts"),
        ("Protection", "All sources of protection/AC, including buying it from priests"),
        ("Murder", "Killing peaceful @-humans/elves: alignment, luck and telepathy penalties"),
        ("Wide-angle disintegration beam",
         "Angry god's death ray: need reflection or disintegration resistance"),
        ("Altar farming", "Camping a co-aligned altar, sacrificing for artifact gifts"),
    ]),
    ("Identification, items and shops", [
        ("Identification", "Overview of every way to identify items"),
        ("Price identification", "Identify items from shop buy/sell prices; price tables"),
        ("Engrave identification",
         "Identify wands by engraving with them (E) and reading the message"),
        ("Curse-testing", "Learning BUC status: altars, pets stepping on items, other tricks"),
        ("Curse removal", "All ways to uncurse items (holy water, scroll, prayer)"),
        ("Randomized appearance", "Which item classes have per-game random appearances"),
        ("Wand strategy", "Which wands to keep, engrave-test, zap in emergencies"),
        ("Potion strategy", "What to do with unknown potions; dipping and quaff-testing"),
        ("Scroll strategy", "Read-testing unknown scrolls safely and in what order"),
        ("Ring strategy", "Testing unknown rings safely and which rings matter"),
        ("Alchemy", "Mixing potions by dipping; useful recipes and explosion risk"),
        ("Polypiling", "Polymorphing piles of junk items into better ones"),
        ("Charge", "Recharging wands/rings/tools and the explosion risk"),
        ("Shop", "Shop types, shopkeeper behavior, buying and selling"),
        ("Shopkeeper", "Shopkeeper stats, what angers them, and why not to fight one"),
        ("Stealing from shops", "Techniques to rob shops and the consequences"),
        ("Usage fee", "What shopkeepers charge for using unpaid items"),
        ("Container", "Boxes, chests and bags: looting, #force, and bag rules"),
        ("Bag of holding", "Weight-reducing bag; never put a wand of cancellation or BoH inside"),
        ("Unicorn horn", "Apply to cure confusion/stun/blindness/sickness; top-priority tool"),
        ("Digging", "Digging through walls and floors; where you can't dig"),
        ("Luckstone", "Gray stone that stops luck timing out; the Mines' End prize"),
        ("Unicorn", "Throw gems to co-aligned unicorns for luck; never kill co-aligned ones"),
    ]),
    ("Pets", [
        ("Pet", "Pet behavior, feeding, keeping it alive, and stealing via pets"),
        ("Domestic animal", "Dogs, cats, horses: taming by throwing food"),
        ("Taming", "Ways to tame monsters (food, scroll/spell of taming, magic harp)"),
        ("Treat", "Which foods pets eat and consider treats"),
        ("Leash", "Keeping pets next to you across levels"),
        ("Riding", "Riding a saddled steed: skill, benefits, risks"),
    ]),
    ("Food and corpses", [
        ("Comestible", "All food items: nutrition, weight, and eating time"),
        ("Corpse", "Which corpses are safe, dangerous, or give intrinsics; rotting"),
        ("Nutrition", "Hunger states, nutrition values, fainting and starvation"),
        ("Tin", "Tins: safe eating of dangerous corpses, opening methods"),
        ("Lichen", "F lichen: sticky but harmless; corpse never rots"),
        ("Lizard", "Lizard corpse never rots; cures stoning; eat to reduce confusion"),
    ]),
    ("Wishes, genocide and polymorph", [
        ("Wish", "What to wish for, exact wish syntax, and sources of wishes"),
        ("Wresting", "Getting one last zap out of an empty (x:0) wand"),
        ("Genocide", "Genocide mechanics and recommended targets (L, ;, mind flayers)"),
        ("Polymorph", "Polymorphing self/objects/monsters: risks and good forms"),
        ("Cancellation", "Effects of cancellation on monsters, items and you"),
    ]),
    ("Conduct", [
        ("Conduct", "Voluntary challenges tracked by the game (#conduct)"),
    ]),
    ("Roles, races and quests (for other random characters)", [
        ("Role", "Overview of the 13 roles"),
        ("Race", "Overview of the 5 player races"),
        ("Archeologist", "Fast, stealthy digger with pick-axe and tinning kit; weak early fighter"),
        ("Barbarian", "Strong melee role with poison resistance and a two-handed sword or axe"),
        ("Caveman", "Tough melee role with club and sling; slow start"),
        ("Healer", "Weak fighter: stethoscope, wand of sleep, healing spells, poison resistance"),
        ("Knight", "Lance and pony; strict code of conduct (no attacking fleeing monsters)"),
        ("Monk", "Martial arts, fast, many intrinsics; no body armor or weapons, vegetarian"),
        ("Priest", "Sees blessed/cursed status of all items; mace and clerical spells"),
        ("Ranger", "Bow with many arrows, multishot, cloak of displacement"),
        ("Rogue",
         "Throws daggers in volleys (multishot); starts with lock pick and potion of sickness"),
        ("Samurai", "Strong, fast lawful fighter with katana and bow (yumi)"),
        ("Tourist", "Hardest role: weak, lots of gold, expensive camera, magic mapping scrolls"),
        ("Wizard",
         "Spellcaster with force bolt, cloak of magic resistance, random wand; weak melee"),
        ("Human (starting race)", "Humans: no infravision; available to every role"),
        ("Elf (starting race)", "Elves: infravision, sleep resistance, elven gear; always chaotic"),
        ("Gnome (starting race)", "Gnomes: infravision, peaceful Gnomish Mines; always neutral"),
        ("Orc (starting race)",
         "Orcs: infravision, poison resistance, may eat most corpses; always chaotic"),
        ("Archeologist quest", ""),
        ("Barbarian quest", ""),
        ("Caveman quest", ""),
        ("Healer quest", ""),
        ("Knight quest", ""),
        ("Monk quest", ""),
        ("Priest quest", ""),
        ("Ranger quest", ""),
        ("Rogue quest", ""),
        ("Samurai quest", ""),
        ("Tourist quest", ""),
        ("Wizard quest", ""),
    ]),
]

DUNGEON = [
    ("Dungeon structure", [
        ("Mazes of Menace", "The main dungeon: overall layout and branch locations"),
        ("Dungeons of Doom", "The main dungeon branch from DL1 down to Medusa and the Castle"),
        ("Dungeon overview", "Ctrl-O / #overview: the in-game list of visited levels"),
        ("Branch", "All dungeon branches and where their entrances are"),
        ("Dungeon level", "How dungeon depth works; level difficulty and generation"),
        ("Special level", "List of all special (hand-designed) levels"),
        ("Staircase", "Up/down stairs and branch stairs"),
        ("Magic portal", "Portals to the Quest, Fort Ludios and the Planes"),
        ("Maze", "Maze filler levels below Medusa and in Gehennom"),
    ]),
    ("Early special levels and branches", [
        ("Gnomish Mines", "Mines branch (entrance DL2-4): gnomes/dwarves, peaceful for dwarves"),
        ("Minetown", "Mines town (3-4 levels in): temple, shops, altar; all variants"),
        ("Mines' End", "Bottom of the Mines: three variants, each hiding a luckstone"),
        ("Oracle (level)", "Oracle level (DL5-9): centaurs, fountains, consultations"),
        ("Oracle (monster)", "The Oracle: buy minor/major consultations; don't attack"),
        ("Big Room", "Optional huge open room (DL10-12): many monsters, no cover"),
        ("Rogue level", "Tribute level (DL15-18) drawn with old Rogue-style symbols"),
        ("Vault", "Closed 2x2 gold rooms; the guard, and how to get out"),
        ("Closet", "1-square niches; often hold stairs or trapdoors"),
    ]),
    ("Sokoban (maps + solutions)", [
        ("Sokoban", "Sokoban branch rules: no diagonal boulder pushes, luck penalties, prizes"),
        ("Sokoban Level 1a", "First Sokoban level, variant a: map and step-by-step solution"),
        ("Sokoban Level 1b", "First Sokoban level, variant b: map and step-by-step solution"),
        ("Sokoban Level 2a", "Second level, variant a: map and solution"),
        ("Sokoban Level 2b", "Second level, variant b: map and solution"),
        ("Sokoban Level 3a", "Third level, variant a: map and solution"),
        ("Sokoban Level 3b", "Third level, variant b: map and solution"),
        ("Sokoban Level 4a",
         "Top level, variant a: map + solution; zoo guards prize (bag of holding or amulet of reflection, 50/50)"),
        ("Sokoban Level 4b",
         "Top level, variant b: map + solution; zoo guards prize (bag of holding or amulet of reflection, 50/50)"),
    ]),
    ("The Quest", [
        ("Quest", "Quest rules: XL14 entry requirement, leader, nemesis, artifact"),
        ("Valkyrie quest", "Valkyrie quest levels (home/locate/goal), Norn and Lord Surtur"),
        ("Quest artifact", "Quest artifacts and their powers"),
        ("Lord Surtur", "Valkyrie quest nemesis: fire giant king; fire resistance essential"),
        ("Norn", "Valkyrie quest leader"),
        ("The Orb of Fate", "Valkyrie quest artifact: level teleport, half damage when carried"),
    ]),
    ("Mid-game levels", [
        ("Fort Ludios", "Optional portal branch: vault fortress full of soldiers and dragons"),
        ("Medusa's Island",
         "Medusa's level: need reflection or blindness and a way to cross water"),
        ("Castle", "Castle: drawbridge (passtune), wand of wishing, trapdoors to Gehennom"),
        ("Wand of wishing", "The Castle's wand of wishing; how to use and wrest it"),
        ("Drawbridge", "Opening/destroying the Castle drawbridge; passtune; force bolt/striking"),
        ("Passtune", "5-note tune that opens the drawbridge; learn it via Mastermind game"),
    ]),
    ("Gehennom", [
        ("Gehennom", "Gehennom overview: mazes, demon lairs, fire and no-prayer hazards"),
        ("Valley of the Dead", "First Gehennom level: undead, temple of Moloch, graveyards"),
        ("Juiblex's swamp",
         "Juiblex's lair (Gehennom 4-7): water everywhere, no-teleport; his engulf causes sickness"),
        ("Orcus-town", "Orcus Town: ruined Minetown full of undead, Orcus with wand of death"),
        ("Asmodeus' Lair",
         "Asmodeus' lair: no-teleport level; he casts cone of cold, so bring cold resistance"),
        ("Baalzebub's Lair",
         "Baalzebub's lair: no-teleport, fly-shaped maze around the demon lord's chamber"),
        ("Vlad's Tower", "Vlad's Tower branch: Vlad the Impaler holds the Candelabrum"),
        ("Wizard's Tower", "Wizard's Tower: the Wizard of Yendor holds the Book of the Dead"),
        ("Fake Wizard's Tower", "Decoy towers with portals; one leads to the real tower"),
        ("Vibrating square", "Target square for the invocation ritual at the bottom of Gehennom"),
        ("Invocation ritual",
         "Bell, Candelabrum (7 candles lit), Book: opening the Sanctum stairs"),
        ("Moloch's Sanctum", "Final Gehennom level: high priest of Moloch guards the Amulet"),
        ("Gehennom mapping", "Mapping Gehennom mazes efficiently to find the stairs"),
        ("Mysterious force", "Pushes you back down while climbing with the Amulet"),
    ]),
    ("Endgame", [
        ("End Game", "Overview of the Elemental Planes and the Astral Plane"),
        ("Elemental Planes", "The four elemental planes and how to find each exit portal"),
        ("Plane of Earth", "Dig through rock to the portal; earth elementals, xorns"),
        ("Plane of Air",
         "Open air with drifting clouds, air elementals and lightning; portal on the right side"),
        ("Plane of Fire", "Fire traps, lava and fire elementals; fire resistance is essential"),
        ("Plane of Water",
         "All water except moving air bubbles; the portal drifts inside a bubble"),
        ("Astral Plane", "Find the correct high altar among three and offer the Amulet"),
        ("Amulet of Yendor", "The goal item: fake vs real, and effects of carrying it"),
        ("Bell of Opening", "Invocation item from the Quest nemesis"),
        ("Candelabrum of Invocation", "Invocation item from Vlad; needs 7 candles attached"),
        ("Book of the Dead", "Invocation item from the Wizard of Yendor"),
        ("Ascension", "Winning the game: offering the Amulet on the right high altar"),
        ("Riders", "Death, Famine, Pestilence on the Astral Plane; revive after death"),
    ]),
    ("Special rooms", [
        ("Throne room", "Throne room full of monsters around a throne"),
        ("Beehive", "Killer bees and royal jelly"),
        ("Barracks", "Soldiers in a barracks room"),
        ("Zoo", "Room of sleeping monsters on gold"),
        ("Graveyard", "Undead, graves; digging up graves"),
        ("Leprechaun hall", "Leprechauns and gold"),
        ("Cockatrice nest", "Cockatrices and statues with items"),
        ("Anthole", "Room of ants"),
        ("Temple", "Temples and their priests; buying protection"),
    ]),
    ("Dungeon features", [
        ("Dungeon feature", "Overview of all dungeon features"),
        ("Fountain", "Quaffing/dipping effects, Excalibur, wishes, water moccasins"),
        ("Sink", "Kicking and dropping rings into sinks to identify them"),
        ("Throne", "Sitting on thrones: wishes, genocide, identification, risks"),
        ("Headstone", "Graves: engraving, digging up (with alignment penalty)"),
        ("Tree", "Trees: kick for fruit, chop down with an axe; they block movement"),
        ("Door", "Doors: opening, kicking, locks, shop doors, no diagonal moves"),
        ("Iron bars", "Iron bars: passing items/monsters through"),
        ("Moat", "Water in moats: drowning, crossing"),
        ("Lava", "Lava: instant death without fire resistance; sinking kills even with it"),
        ("Water", "All forms of water: potions, fountains, pools, moats, the Plane of Water"),
        ("Wet", "Water damage to items: rusting, diluting potions, blanking scrolls"),
        ("Ladder", "Ladders in Vlad's Tower and elsewhere"),
        ("Ice", "Ice: slipping, melting, digging holes"),
        ("Bones", "Bones files: ghost of a dead player and their cursed items"),
    ]),
    ("Traps", [
        ("Trap", "All trap types, how to detect and avoid them"),
        ("Anti-magic field", "Drains power (Pw); with magic resistance it drains HP instead"),
        ("Arrow trap", "Shoots arrows at you; can be disarmed to collect the arrows"),
        ("Dart trap", "Shoots darts that may be poisoned; poison resistance matters"),
        ("Beartrap", "Holds you in place for several turns; can be disarmed and reused"),
        ("Container trap", "Trapped boxes/chests: explosions, poison needles, gas clouds, shocks"),
        ("Falling rock trap", "Drops a rock on your head; a hard helmet reduces the damage"),
        ("Fire trap", "Burns you and your items and melts ice; fire resistance helps"),
        ("Hole", "Always-visible hole in the floor; you fall to the next level"),
        ("Land mine", "Explodes: damage, wounded legs, leaves a pit; can be disarmed"),
        ("Level teleporter", "Sends you to a random level; magic resistance blocks it"),
        ("Magic trap",
         "Random magical effects: summoned monsters, blinding flash, noises, rare boons"),
        ("Pit", "You fall in and spend turns climbing out; beware fighting from inside"),
        ("Spiked pit", "A pit with poisoned spikes"),
        ("Polymorph trap", "Polymorphs you (DL8+) unless you have magic resistance or unchanging"),
        ("Rolling boulder trap", "Launches a boulder that rolls across the trap square"),
        ("Rust trap", "Sprays water: rusts iron armor/weapons and wets items"),
        ("Sleeping gas trap", "Puts you to sleep unless you are sleep resistant"),
        ("Squeaky board", "Wakes nearby monsters; otherwise harmless"),
        ("Statue trap", "A statue that comes to life when you approach or search next to it"),
        ("Teleportation trap", "Teleports you within the level; magic resistance blocks it"),
        ("Trap door", "Drops you one or more levels down"),
        ("Web", "Entangles you; strong heroes tear free; home of giant spiders"),
    ]),
]

MECHANICS = [
    ("Character and attributes", [
        ("Hit points", "Max HP growth per level, natural regeneration, and dying at 0 HP"),
        ("Energy", "Power (Pw) for spellcasting: maximum, growth and regeneration"),
        ("Experience level", "Experience levels 1-30: XP thresholds, gaining and losing levels"),
        ("Experience points", "How experience points are earned from kills and other actions"),
        ("Attribute", "The six attributes (Str/Dex/Con/Int/Wis/Cha), limits and exercise"),
        ("Strength", "Strength: to-hit/damage bonuses, carrying capacity, 18/xx notation"),
        ("Dexterity", "Dexterity: to-hit bonus, multishot and spellcasting effects"),
        ("Constitution", "Constitution: HP gained per level and carrying capacity"),
        ("Intelligence", "Intelligence: spell failure for Int casters; brain-eating kills at 3"),
        ("Wisdom", "Wisdom: energy regeneration and spell failure for Wis casters"),
        ("Charisma", "Charisma: shop prices and a few other effects"),
        ("Armor class", "AC: how armor protects; negative AC also reduces damage taken"),
        ("Encumbrance", "Carrying capacity and Burdened..Overloaded penalties"),
        ("Weight", "Item weights and how they add to your load"),
        ("Speed", "Movement speed: intrinsic/extrinsic fast, very fast, monster speeds"),
        ("Skill", "Weapon and spell skills: training, per-role maximums, #enhance"),
        ("Enhance", "#enhance: advance a skill once it has enough training"),
        ("Twoweapon", "#twoweapon: fighting with two weapons, restrictions and skill"),
        ("Spellcasting", "Casting spells: failure rate formula, armor penalties, energy cost"),
        ("Spell", "What spells are; pointers to spellcasting and spellbooks"),
    ]),
    ("Combat and item mechanics", [
        ("To-hit", "To-hit formula: Luck, level, skill, encumbrance and target AC"),
        ("Damage", "How melee and missile damage is calculated, including bonuses"),
        ("D notation", "Dice notation (XdY) used for damage and random rolls"),
        ("Combat", "Melee combat basics and tactics"),
        ("Ranged attack", ""),
        ("Multishot", ""),
        ("Erosion", "Rust, corrosion, burning, rotting; erosion-proofing and repair"),
        ("Enchantment", "Weapon/armor enchantment (+N) and safe enchanting limits"),
        ("BUC", "Blessed/uncursed/cursed status and how to learn it"),
        ("Artifact", "All artifacts: alignment, sacrifice gifts, wishing, touching"),
        ("Artifact blast", "Touching cross-aligned artifacts hurts you; when it happens"),
        ("Bane", ""),
        ("Item", "Item classes and general object mechanics"),
        ("Discoveries", "The \\ discoveries list of item types you have identified"),
    ]),
    ("Properties and intrinsics", [
        ("Property", "Intrinsic vs extrinsic properties; full list and sources"),
        ("Resistance", "All resistances and how to obtain each"),
        ("Magic resistance",
         "MR: blocks death rays, polymorph, teleport traps, destroy armor and more"),
        ("Reflection", "Reflects rays and gazes (death, disintegration, Medusa); sources"),
        ("Free action", "Prevents most paralysis (floating eye, gelatinous cube, potions)"),
        ("Telepathy", "Sense monsters' minds while blind (intrinsic) or always (extrinsic)"),
        ("Stealth", "Move without waking sleeping monsters; sources"),
        ("See invisible", "See invisible monsters; sources"),
        ("Invisibility", "Being invisible: benefits, shopkeepers refuse service, sources"),
        ("Infravision", "See warm-blooded monsters in the dark (non-human races)"),
        ("Warning", "Shows numbers for nearby hostiles by threat level"),
        ("Displacement",
         "Displacement property: monsters see you where you are not",
         "Displacement (property)"),
        ("Clairvoyance", "Periodically maps the nearby area (donations, cornuthaum, Amulet)"),
        ("Enlightenment", "Reveals your hidden attributes and intrinsics"),
        ("Conflict", "Monsters fight each other (ring of conflict); angers peacefuls"),
        ("Sustain ability", ""),
        ("Slow digestion", "Greatly reduces food consumption (ring of slow digestion)"),
        ("Half spell damage", ""),
        ("Half physical damage", ""),
        ("Water walking", ""),
        ("Flying", "Flying: cross water, lava and pits while still reaching the floor"),
        ("Levitation", "Floating: can't pick up items or go downstairs; escaping it"),
        ("Breathless", "Magical breathing: can't drown, immune to gases"),
        ("Life saving", "Amulet of life saving: survive one death"),
        ("Protection from shape changers", ""),
        ("Monster detection", ""),
        ("Object detection", ""),
        ("Invulnerability", ""),
        ("Teleportation", "Teleporting within a level: sources, control, no-teleport levels"),
        ("Teleport control", ""),
        ("Teleportitis", ""),
        ("Polymorph control", ""),
        ("Polymorphitis", ""),
        ("Unchanging", ""),
        ("Regeneration",
         "Regeneration property: 1 HP per turn (ring of regeneration, trolls)",
         "Regeneration (property)"),
        ("Automatic searching", ""),
        ("Aggravate monster", ""),
        ("Jumping", "Jumping (knights, jumping boots/spell): range and uses"),
        ("Voracious hunger",
         "Hunger property: nutrition burns fast (ring of hunger, some corpses)"),
        ("Ring hunger", "Extra nutrition used by worn rings and amulets"),
        ("Fumbling", ""),
        ("Hit point regeneration", "How fast HP comes back naturally, by level and Con"),
        ("Energy regeneration",
         "How fast power (Pw) comes back, by role, Wis/Int, energy regeneration"),
    ]),
    ("Resistances", [
        ("Fire resistance", "Fire resistance: sources and what it protects against"),
        ("Cold resistance", "Cold resistance: sources and protection (Valkyries start with it)"),
        ("Shock resistance", "Shock resistance: sources and protection"),
        ("Sleep resistance", "Sleep resistance: sources and protection"),
        ("Disintegration resistance",
         "Disintegration resistance: black dragon scales; survive disintegration"),
        ("Poison resistance", "Poison resistance: essential; sources and what it prevents"),
        ("Acid resistance", ""),
        ("Stoning resistance", ""),
        ("Drain resistance", ""),
        ("Immunity to sickness", ""),
        ("Hallucination resistance", ""),
        ("Monster resistances", "Table of which monsters resist which damage types"),
    ]),
    ("Status effects, ailments and instadeaths", [
        ("Blindness", ""),
        ("Confusion", ""),
        ("Stun", ""),
        ("Hallucination", ""),
        ("Deafness", ""),
        ("Wounded legs", ""),
        ("Paralysis", ""),
        ("Sleep", ""),
        ("Glib", ""),
        ("Vomiting", ""),
        ("Stoning", "Turning to stone: cures (lizard, acidic corpse, stone to flesh, prayer)"),
        ("Sliming", "Turning into green slime: cure with fire, prayer or polymorph"),
        ("Strangulation", ""),
        ("Sickness", "Illness and food poisoning: deadly; cure with unicorn horn, prayer, potions"),
        ("Illness", ""),
        ("Food poisoning", ""),
        ("Lycanthropy", ""),
        ("Level drain", "Losing experience levels to drain attacks", "Drain life (monster attack)"),
        ("Poison", ""),
        ("Punishment", ""),
        ("Instant death", "Catalogue of instadeaths and how to prevent each"),
        ("Delayed instadeath",
         "Countdown deaths (stoning, sliming, illness, strangulation) and cures"),
        ("Drowning", "Drowning by eels or water; how to survive it"),
        ("Disintegration", ""),
        ("Touch of death", ""),
        ("Intelligence drain", ""),
        ("Starvation", ""),
    ]),
    ("Monster mechanics", [
        ("Monster", ""),
        ("Monster class", ""),
        ("Monster difficulty", ""),
        ("Monster level", ""),
        ("Monster creation", ""),
        ("Monster behavior", ""),
        ("Monster starting inventory", ""),
        ("Monsters (by speed)", ""),
        ("Monsters (by experience)", ""),
        ("Unique monster", ""),
        ("Player monster", ""),
        ("Quest guardian", ""),
        ("Demon lords and princes", ""),
        ("Covetous", ""),
        ("Shapeshifter", ""),
        ("Monster spell", ""),
        ("Passive attack", ""),
        ("Holding attack", ""),
        ("Engulfing", ""),
        ("Gaze attack", ""),
        ("Theft", ""),
        ("Werecreature", ""),
        ("Foocubus", ""),
        ("Hiding", ""),
        ("Bribe", ""),
    ]),
    ("Commands and interface", [
        ("Command", ""),
        ("Apply", ""),
        ("Far look", ""),
        ("Force", ""),
        ("Loot", ""),
        ("Untrap", ""),
        ("Chat", ""),
        ("Sit", ""),
        ("Rub", ""),
        ("Invoke", ""),
        ("Name", ""),
        ("Call", ""),
        ("Pay", ""),
        ("Throw", ""),
        ("Firing", ""),
        ("Quiver", ""),
        ("Wield", ""),
        ("Wear", ""),
        ("Put on", ""),
        ("Remove", ""),
        ("Take off", ""),
        ("Zap", ""),
        ("Read", ""),
        ("Quaff", ""),
        ("Eat", ""),
        ("Open", ""),
        ("Close", ""),
        ("Pick up", ""),
        ("Drop", ""),
        ("Rest", ""),
        ("Search", ""),
        ("Kick", "Kicking doors, objects and monsters; risks", "Kick (command)"),
        ("Travel", ""),
        ("Numeric prefix", ""),
        ("Swap weapons", ""),
        ("Dip", ""),
        ("Offer", ""),
        ("Turn undead", ""),
        ("Autopickup", ""),
        ("Options", ""),
        ("Autodig", ""),
        ("You hear", ""),
        ("Strange feeling", ""),
        ("Hallucinatory messages", ""),
    ]),
]

# Monster data from NetHack 3.6.7 src/monst.c (382 entries; the long worm tail
# pseudo-monster is omitted). Keys are the display symbols.
MONSTERS_BY_CLASS = {
    "a": ["giant ant", "killer bee", "soldier ant", "fire ant", "giant beetle", "queen bee"],
    "b": ["acid blob", "quivering blob", "gelatinous cube"],
    "c": ["chickatrice", "cockatrice", "pyrolisk"],
    "d": ["jackal", "fox", "coyote", "werejackal", "little dog", "dingo", "dog", "large dog",
          "wolf", "werewolf", "winter wolf cub", "warg", "winter wolf", "hell hound pup",
          "hell hound"],
    "e": ["gas spore", "floating eye", "freezing sphere", "flaming sphere", "shocking sphere"],
    "f": ["kitten", "housecat", "jaguar", "lynx", "panther", "large cat", "tiger"],
    "g": ["gremlin", "gargoyle", "winged gargoyle"],
    "h": ["hobbit", "dwarf", "bugbear", "dwarf lord", "dwarf king", "mind flayer",
          "master mind flayer"],
    "i": ["manes", "homunculus", "imp", "lemure", "quasit", "tengu"],
    "j": ["blue jelly", "spotted jelly", "ochre jelly"],
    "k": ["kobold", "large kobold", "kobold lord", "kobold shaman"],
    "l": ["leprechaun"],
    "m": ["small mimic", "large mimic", "giant mimic"],
    "n": ["wood nymph", "water nymph", "mountain nymph"],
    "o": ["goblin", "hobgoblin", "orc", "hill orc", "Mordor orc", "Uruk-hai", "orc shaman",
          "orc-captain"],
    "p": ["rock piercer", "iron piercer", "glass piercer"],
    "q": ["rothe", "mumak", "leocrotta", "wumpus", "titanothere", "baluchitherium", "mastodon"],
    "r": ["sewer rat", "giant rat", "rabid rat", "wererat", "rock mole", "woodchuck"],
    "s": ["cave spider", "centipede", "giant spider", "scorpion", "Scorpius"],
    "t": ["lurker above", "trapper"],
    "u": ["pony", "white unicorn", "gray unicorn", "black unicorn", "horse", "warhorse"],
    "v": ["fog cloud", "dust vortex", "ice vortex", "energy vortex", "steam vortex",
          "fire vortex"],
    "w": ["baby long worm", "baby purple worm", "long worm", "purple worm"],
    "x": ["grid bug", "xan"],
    "y": ["yellow light", "black light"],
    "z": ["zruty"],
    "A": ["couatl", "Aleax", "Angel", "ki-rin", "Archon"],
    "B": ["bat", "giant bat", "raven", "vampire bat"],
    "C": ["plains centaur", "forest centaur", "mountain centaur"],
    "D": ["baby gray dragon", "baby silver dragon", "baby red dragon", "baby white dragon",
          "baby orange dragon", "baby black dragon", "baby blue dragon", "baby green dragon",
          "baby yellow dragon", "gray dragon", "silver dragon", "red dragon", "white dragon",
          "orange dragon", "black dragon", "blue dragon", "green dragon", "yellow dragon",
          "Chromatic Dragon", "Ixoth"],
    "E": ["stalker", "air elemental", "fire elemental", "earth elemental", "water elemental"],
    "F": ["lichen", "brown mold", "yellow mold", "green mold", "red mold", "shrieker",
          "violet fungus"],
    "G": ["gnome", "gnome lord", "gnomish wizard", "gnome king"],
    "H": ["giant", "stone giant", "hill giant", "fire giant", "frost giant", "ettin",
          "storm giant", "titan", "minotaur", "Cyclops", "Lord Surtur"],
    "J": ["jabberwock"],
    "K": ["Keystone Kop", "Kop Sergeant", "Kop Lieutenant", "Kop Kaptain"],
    "L": ["lich", "demilich", "master lich", "arch-lich"],
    "M": ["kobold mummy", "gnome mummy", "orc mummy", "dwarf mummy", "elf mummy", "human mummy",
          "ettin mummy", "giant mummy"],
    "N": ["red naga hatchling", "black naga hatchling", "golden naga hatchling",
          "guardian naga hatchling", "red naga", "black naga", "golden naga", "guardian naga"],
    "O": ["ogre", "ogre lord", "ogre king"],
    "P": ["gray ooze", "brown pudding", "green slime", "black pudding"],
    "Q": ["quantum mechanic"],
    "R": ["rust monster", "disenchanter"],
    "S": ["garter snake", "snake", "water moccasin", "python", "pit viper", "cobra"],
    "T": ["troll", "ice troll", "rock troll", "water troll", "Olog-hai"],
    "U": ["umber hulk"],
    "V": ["vampire", "vampire lord", "Vlad the Impaler"],
    "W": ["barrow wight", "wraith", "Nazgul"],
    "X": ["xorn"],
    "Y": ["monkey", "ape", "owlbear", "yeti", "carnivorous ape", "sasquatch"],
    "Z": ["kobold zombie", "gnome zombie", "orc zombie", "dwarf zombie", "elf zombie",
          "human zombie", "ettin zombie", "ghoul", "giant zombie", "skeleton"],
    "'": ["straw golem", "paper golem", "rope golem", "gold golem", "leather golem", "wood golem",
          "flesh golem", "clay golem", "stone golem", "glass golem", "iron golem"],
    "@": ["human", "wererat", "werejackal", "werewolf", "elf", "Woodland-elf", "Green-elf",
          "Grey-elf", "elf-lord", "Elvenking", "doppelganger", "shopkeeper", "guard", "prisoner",
          "Oracle", "aligned priest", "high priest", "soldier", "sergeant", "nurse", "lieutenant",
          "captain", "watchman", "watch captain", "Medusa", "Wizard of Yendor", "Croesus",
          "archeologist", "barbarian", "caveman", "cavewoman", "healer", "knight", "monk",
          "priest", "priestess", "ranger", "rogue", "samurai", "tourist", "valkyrie", "wizard",
          "Lord Carnarvon", "Pelias", "Shaman Karnov", "Hippocrates", "King Arthur",
          "Grand Master", "Arch Priest", "Orion", "Master of Thieves", "Lord Sato", "Twoflower",
          "Norn", "Neferet the Green", "Thoth Amon", "Master Kaen", "Master Assassin",
          "Ashikaga Takauji", "Dark One", "student", "chieftain", "neanderthal", "attendant",
          "page", "abbot", "acolyte", "hunter", "thug", "ninja", "roshi", "guide", "warrior",
          "apprentice"],
    " ": ["ghost", "shade"],
    "&": ["water demon", "succubus", "horned devil", "incubus", "erinys", "barbed devil",
          "marilith", "vrock", "hezrou", "bone devil", "ice devil", "nalfeshnee", "pit fiend",
          "sandestin", "balrog", "Juiblex", "Yeenoghu", "Orcus", "Geryon", "Dispater",
          "Baalzebub", "Asmodeus", "Demogorgon", "Death", "Pestilence", "Famine", "mail daemon",
          "djinni", "Minion of Huhetotl", "Nalzok"],
    ";": ["jellyfish", "piranha", "shark", "giant eel", "electric eel", "kraken"],
    ":": ["newt", "gecko", "iguana", "baby crocodile", "lizard", "chameleon", "crocodile",
          "salamander"],
}

MONSTER_CLASS_NAMES = {
    "a": "ants and other insects", "b": "blobs", "c": "cockatrices", "d": "dogs and other canines",
    "e": "floating eyes and spheres", "f": "cats and other felines", "g": "gremlins and gargoyles",
    "h": "dwarves, hobbits, mind flayers (humanoids)", "i": "imps and minor demons", "j": "jellies",
    "k": "kobolds", "l": "leprechaun", "m": "mimics", "n": "nymphs", "o": "orcs", "p": "piercers",
    "q": "quadrupeds", "r": "rats and rodents", "s": "spiders and centipedes",
    "t": "trappers and lurkers above",
    "u": "horses and unicorns", "v": "vortices", "w": "worms", "x": "grid bugs and xan",
    "y": "lights", "z": "zruty", "A": "angelic beings", "B": "bats and birds", "C": "centaurs",
    "D": "dragons", "E": "elementals and stalkers", "F": "fungi and molds (lichens)", "G": "gnomes",
    "H": "giants and other giant humanoids", "J": "jabberwock", "K": "Keystone Kops", "L": "liches",
    "M": "mummies", "N": "nagas", "O": "ogres", "P": "puddings and oozes", "Q": "quantum mechanic",
    "R": "rust monster and disenchanter", "S": "snakes", "T": "trolls", "U": "umber hulk",
    "V": "vampires", "W": "wraiths and Nazgul", "X": "xorn", "Y": "apes and other apelike creatures",
    "Z": "zombies", "@": "humans and elves (incl. shopkeepers, priests, quest leaders)",
    " ": "ghosts and shades (shown as a blank space)", "'": "golems", "&": "demons (and djinni, mail daemon)",
    ";": "sea monsters (eels, sharks, jellyfish, kraken)", ":": "lizards, newts, crocodiles",
}

MONSTER_CLASS_PAGES = {
    "a": "Ant or other insect", "b": "Blob", "c": "Cockatrice (monster class)", "d": "Canine",
    "e": "Eye or sphere", "f": "Feline", "g": "Gremlin (monster class)", "h": "Humanoid (monster class)",
    "i": "Imp or minor demon", "j": "Jelly", "k": "Kobold (monster class)",
    "l": "Leprechaun (monster class)", "m": "Mimic", "n": "Nymph (monster class)",
    "o": "Orc (monster class)", "p": "Piercer", "q": "Quadruped", "r": "Rodent",
    "s": "Arachnid or centipede", "t": "Trapper or lurker above", "u": "Unicorn or horse",
    "v": "Vortex", "w": "Worm", "x": "Grid bug", "y": "Light (monster class)",
    "z": "Zruty (monster class)", "A": "Angelic being", "B": "Bat or bird",
    "C": "Centaur (monster class)", "D": "Dragon", "E": "Elemental", "F": "Fungus or mold",
    "G": "Gnome (monster class)", "H": "Giant humanoid", "J": "Jabberwock (monster class)",
    "K": "Keystone Kop (monster class)", "L": "Lich (monster class)", "M": "Mummy", "N": "Naga",
    "O": "Ogre (monster class)", "P": "Pudding or ooze", "Q": "Quantum mechanic (monster class)",
    "R": "Rust monster or disenchanter", "S": "Snake (monster class)", "T": "Troll (monster class)",
    "U": "Umber hulk (monster class)", "V": "Vampire (monster class)", "W": "Wraith (monster class)",
    "X": "Xorn (monster class)", "Y": "Apelike creature", "Z": "Zombie (monster class)",
    "@": "Human or elf", " ": "Ghost (monster class)", "'": "Golem", "&": "Demon (monster class)",
    ";": "Sea monster", ":": "Lizard (monster class)",
}

# Source names whose wiki page is not simply the capitalized name (disambiguation
# pages, role pages, renamed pages). These skip the "has a {{monster}} infobox" check.
_PLAYER_MONSTERS = ["archeologist", "barbarian", "caveman", "cavewoman", "healer", "knight",
                    "monk", "priest", "priestess", "ranger", "rogue", "samurai", "tourist",
                    "valkyrie", "wizard"]
MONSTER_TITLE_OVERRIDES = {
    "dwarf": ["Dwarf (monster)"], "gnome": ["Gnome (monster)"], "elf": ["Elf (monster)"],
    "human": ["Human (monster)"], "orc": ["Orc (monster)"], "giant": ["Giant (monster)"],
    "Oracle": ["Oracle (monster)"], "Death": ["Death (monster)"],
    "acolyte": ["Acolyte (quest guardian)", "Acolyte"],
    "caveman": ["Caveman (player monster)"], "cavewoman": ["Caveman (player monster)"],
    "priest": ["Priest (player monster)"], "priestess": ["Priest (player monster)"],
}
for _pm in _PLAYER_MONSTERS:
    MONSTER_TITLE_OVERRIDES.setdefault(_pm, [_pm.capitalize() + " (player monster)"])

# Object data from NetHack 3.6.7 src/objects.c: one "name[ = fixed appearance][ *]"
# per line; "*" marks per-game randomized appearances (unidentified name varies).
OBJECTS_SRC = {
    "Weapons": """
arrow
elven arrow = runed arrow
orcish arrow = crude arrow
silver arrow
ya = bamboo arrow
crossbow bolt
dart
shuriken = throwing star
boomerang
spear
elven spear = runed spear
orcish spear = crude spear
dwarvish spear = stout spear
silver spear
javelin = throwing spear
trident
dagger
elven dagger = runed dagger
orcish dagger = crude dagger
silver dagger
athame
scalpel
knife
stiletto
worm tooth
crysknife
axe
battle-axe = double-headed axe
short sword
elven short sword = runed short sword
orcish short sword = crude short sword
dwarvish short sword = broad short sword
scimitar = curved sword
silver saber
broadsword
elven broadsword = runed broadsword
long sword
two-handed sword
katana = samurai sword
tsurugi = long samurai sword
runesword = runed broadsword
partisan = vulgar polearm
ranseur = hilted polearm
spetum = forked polearm
glaive = single-edged polearm
lance
halberd = angled poleaxe
bardiche = long poleaxe
voulge = pole cleaver
dwarvish mattock = broad pick
fauchard = pole sickle
guisarme = pruning hook
bill-guisarme = hooked polearm
lucern hammer = pronged polearm
bec de corbin = beaked polearm
mace
morning star
war hammer
club
rubber hose
quarterstaff = staff
aklys = thonged club
flail
bullwhip
bow
elven bow = runed bow
orcish bow = crude bow
yumi = long bow
sling
crossbow
""",
    "Armor": """
elven leather helm = leather hat
orcish helm = iron skull cap
dwarvish iron helm = hard hat
fedora
cornuthaum = conical hat
dunce cap = conical hat
dented pot
helmet *
helm of brilliance *
helm of opposite alignment *
helm of telepathy *
gray dragon scale mail
silver dragon scale mail
red dragon scale mail
white dragon scale mail
orange dragon scale mail
black dragon scale mail
blue dragon scale mail
green dragon scale mail
yellow dragon scale mail
gray dragon scales
silver dragon scales
red dragon scales
white dragon scales
orange dragon scales
black dragon scales
blue dragon scales
green dragon scales
yellow dragon scales
plate mail
crystal plate mail
bronze plate mail
splint mail
banded mail
dwarvish mithril-coat
elven mithril-coat
chain mail
orcish chain mail = crude chain mail
scale mail
studded leather armor
ring mail
orcish ring mail = crude ring mail
leather armor
leather jacket
Hawaiian shirt
T-shirt
mummy wrapping
elven cloak = faded pall
orcish cloak = coarse mantelet
dwarvish cloak = hooded cloak
oilskin cloak = slippery cloak
robe
alchemy smock = apron
leather cloak
cloak of protection *
cloak of invisibility *
cloak of magic resistance *
cloak of displacement *
small shield
elven shield = blue and green shield
Uruk-hai shield = white-handed shield
orcish shield = red-eyed shield
large shield
dwarvish roundshield = large round shield
shield of reflection = polished silver shield
leather gloves *
gauntlets of fumbling *
gauntlets of power *
gauntlets of dexterity *
low boots = walking shoes
iron shoes = hard shoes
high boots = jackboots
speed boots *
water walking boots *
jumping boots *
elven boots *
kicking boots *
fumble boots *
levitation boots *
""",
    "Rings": """
adornment *
gain strength *
gain constitution *
increase accuracy *
increase damage *
protection *
regeneration *
searching *
stealth *
sustain ability *
levitation *
hunger *
aggravate monster *
conflict *
warning *
poison resistance *
fire resistance *
cold resistance *
shock resistance *
free action *
slow digestion *
teleportation *
teleport control *
polymorph *
polymorph control *
invisibility *
see invisible *
protection from shape changers *
""",
    "Amulets": """
amulet of ESP *
amulet of life saving *
amulet of strangulation *
amulet of restful sleep *
amulet versus poison *
amulet of change *
amulet of unchanging *
amulet of reflection *
amulet of magical breathing *
cheap plastic imitation of the Amulet of Yendor = Amulet of Yendor
Amulet of Yendor
""",
    "Wands": """
light *
secret door detection *
enlightenment *
create monster *
wishing *
nothing *
striking *
make invisible *
slow monster *
speed monster *
undead turning *
polymorph *
cancellation *
teleportation *
opening *
locking *
probing *
digging *
magic missile *
fire *
cold *
sleep *
death *
lightning *
""",
    "Tools": """
large box
chest
ice box
sack = bag
oilskin sack = bag
bag of holding = bag
bag of tricks = bag
skeleton key = key
lock pick
credit card
tallow candle = candle
wax candle = candle
brass lantern
oil lamp = lamp
magic lamp = lamp
expensive camera
mirror = looking glass
crystal ball = glass orb
lenses
blindfold
towel
saddle
leash
stethoscope
tinning kit
tin opener
can of grease
figurine
magic marker
land mine
beartrap
tin whistle = whistle
magic whistle = whistle
wooden flute = flute
magic flute = flute
tooled horn = horn
frost horn = horn
fire horn = horn
horn of plenty = horn
wooden harp = harp
magic harp = harp
bell
bugle
leather drum = drum
drum of earthquake = drum
pick-axe
grappling hook = iron hook
unicorn horn
Candelabrum of Invocation = candelabrum
Bell of Opening = silver bell
""",
    "Potions": """
gain ability *
restore ability *
confusion *
blindness *
paralysis *
speed *
levitation *
hallucination *
invisibility *
see invisible *
healing *
extra healing *
gain level *
enlightenment *
monster detection *
object detection *
gain energy *
sleeping *
full healing *
polymorph *
booze *
sickness *
fruit juice *
acid *
oil *
water = clear
""",
    "Scrolls": """
enchant armor *
destroy armor *
confuse monster *
scare monster *
remove curse *
enchant weapon *
create monster *
taming *
genocide *
light *
teleportation *
gold detection *
food detection *
identify *
magic mapping *
amnesia *
fire *
earth *
punishment *
charging *
stinking cloud *
mail = stamped scroll
blank paper = unlabeled scroll
""",
    "Spellbooks": """
dig *
magic missile *
fireball *
cone of cold *
sleep *
finger of death *
light *
detect monsters *
healing *
knock *
force bolt *
confuse monster *
cure blindness *
drain life *
slow monster *
wizard lock *
create monster *
detect food *
cause fear *
clairvoyance *
cure sickness *
charm monster *
haste self *
detect unseen *
levitation *
extra healing *
restore ability *
invisibility *
detect treasure *
remove curse *
magic mapping *
identify *
turn undead *
polymorph *
teleport away *
create familiar *
cancellation *
protection *
jumping *
stone to flesh *
blank paper = plain
novel = paperback
Book of the Dead = papyrus
""",
    "Gems": """
dilithium crystal = white gem
diamond = white gem
ruby = red gem
jacinth = orange gem
sapphire = blue gem
black opal = black gem
emerald = green gem
turquoise = green gem
citrine = yellow gem
aquamarine = green gem
amber = yellowish brown gem
topaz = yellowish brown gem
jet = black gem
opal = white gem
chrysoberyl = yellow gem
garnet = red gem
amethyst = violet gem
jasper = red gem
fluorite = violet gem
obsidian = black gem
agate = orange gem
jade = green gem
worthless piece of white glass = white gem
worthless piece of blue glass = blue gem
worthless piece of red glass = red gem
worthless piece of yellowish brown glass = yellowish brown gem
worthless piece of orange glass = orange gem
worthless piece of yellow glass = yellow gem
worthless piece of black glass = black gem
worthless piece of green glass = green gem
worthless piece of violet glass = violet gem
luckstone = gray stone
loadstone = gray stone
touchstone = gray stone
flint = gray stone
rock
""",
    "Comestibles": """
tripe ration
corpse
egg
meatball
meat stick
huge chunk of meat
glob of gray ooze
glob of brown pudding
glob of green slime
glob of black pudding
kelp frond
eucalyptus leaf
apple
orange
pear
melon
banana
carrot
sprig of wolfsbane
clove of garlic
slime mold
lump of royal jelly
cream pie
candy bar
fortune cookie
pancake
lembas wafer
cram ration
food ration
K-ration
C-ration
tin
meat ring
""",
    "Coins": """
gold piece
""",
    "Other": """
boulder
statue
heavy iron ball
iron chain
blinding venom = splash of venom
acid venom = splash of venom
""",
}

OBJECT_TITLE_PREFIX = {"Rings": "Ring of ", "Potions": "Potion of ", "Scrolls": "Scroll of ",
                       "Spellbooks": "Spellbook of ", "Wands": "Wand of "}
OBJECT_TITLE_OVERRIDES = {
    "flint": ["Flint stone", "Flint"],
    "gold piece": ["Gold piece", "Zorkmid"],
    "lenses": ["Pair of lenses", "Lenses"],
    "blinding venom": ["Blinding venom", "Venom"],
    "acid venom": ["Acid venom", "Venom"],
    "cheap plastic imitation of the Amulet of Yendor": [
        "Cheap plastic imitation of the Amulet of Yendor", "Amulet of Yendor"],
    "novel": ["Novel"],
    "obsidian": ["Obsidian stone", "Gem"],
    "Book of the Dead": ["Book of the Dead"],
    "blank paper@Scrolls": ["Scroll of blank paper"],
    "blank paper@Spellbooks": ["Spellbook of blank paper"],
}

# Class overview pages, listed first in each object section of INDEX.md.
OBJECT_OVERVIEW = {
    "Weapons": ["Weapon", "Polearm", "Projectile", "Ranged weapon", "Poisoned weapon",
                "Weapon-tool", "Martial arts"],
    "Armor": ["Armor", "Body armor", "Cloak", "Helm", "Gloves", "Boots", "Shield", "Shirt",
              "Dragon scale mail", "Dragon scales", "GDSM versus SDSM"],
    "Rings": ["Ring"],
    "Amulets": ["Amulet"],
    "Wands": ["Wand", "Attack wand", "Beam"],
    "Tools": ["Tool", "Light source", "Musical instrument", "Unlocking tool", "Whistle"],
    "Potions": ["Potion", "Potion quaffing effects", "Vapors", "Potion of holy water",
                "Potion of unholy water"],
    "Scrolls": ["Scroll"],
    "Spellbooks": ["Spellbook"],
    "Gems": ["Gem", "Gray stone"],
    "Comestibles": ["Comestible", "Glob"],
    "Coins": [],
    "Other": [],
    "Artifacts": ["Artifact", "Quest artifact", "Unique item"],
}
OBJECT_SECTION_NAMES = {
    "Weapons": "Weapons ) ", "Armor": "Armor [", "Rings": "Rings =", "Amulets": "Amulets \"",
    "Wands": "Wands /", "Tools": "Tools (", "Potions": "Potions !", "Scrolls": "Scrolls ?",
    "Spellbooks": "Spellbooks +", "Gems": "Gems and stones *", "Comestibles": "Comestibles (food) %",
    "Coins": "Coins $", "Other": "Boulders, statues, iron balls, chains, venom ` 0 _",
    "Artifacts": "Artifacts",
}

# From NetHack 3.6.7 include/artilist.h (the obsolete Palantir is excluded).
ARTIFACTS = [
    "Excalibur", "Stormbringer", "Mjollnir", "Cleaver", "Grimtooth", "Orcrist", "Sting",
    "Magicbane", "Frost Brand", "Fire Brand", "Dragonbane", "Demonbane", "Werebane",
    "Grayswandir", "Giantslayer", "Ogresmasher", "Trollsbane", "Vorpal Blade", "Snickersnee",
    "Sunsword", "The Orb of Detection", "The Heart of Ahriman", "The Sceptre of Might",
    "The Staff of Aesculapius", "The Magic Mirror of Merlin", "The Eyes of the Overworld",
    "The Mitre of Holiness", "The Longbow of Diana", "The Master Key of Thievery",
    "The Tsurugi of Muramasa", "The Platinum Yendorian Express Card", "The Orb of Fate",
    "The Eye of the Aethiopica",
]


# ----------------------------------------------------------------------------
# Plan construction
# ----------------------------------------------------------------------------

@dataclass
class Req:
    key: str                  # unique id within the plan
    candidates: list          # wiki titles to try, in order
    group: str                # strategy | dungeon | mechanics | monsters | objects
    section: str              # INDEX subsection
    label: str                # display name
    gist: str = ""
    need_infobox: str = ""    # candidate must contain {{<this> ...}} (monster pages)
    meta: dict = field(default_factory=dict)


def ucfirst(s: str) -> str:
    return s[:1].upper() + s[1:]


def parse_object_line(line: str):
    randomized = line.endswith(" *")
    if randomized:
        line = line[:-2]
    name, _, appearance = line.partition(" = ")
    return name.strip(), appearance.strip(), randomized


def build_plan() -> list:
    reqs: list = []
    seen: set = set()

    def add(req: Req):
        if req.key in seen:
            return
        seen.add(req.key)
        reqs.append(req)

    for group, sections in (("strategy", STRATEGY), ("dungeon", DUNGEON), ("mechanics", MECHANICS)):
        for section, items in sections:
            for title, gist, *wiki in items:
                add(Req(key=f"{group}:{title}", candidates=wiki or [title], group=group,
                        section=section, label=title, gist=gist))

    for letter, names in MONSTERS_BY_CLASS.items():
        for name in names:
            if name in MONSTER_TITLE_OVERRIDES:
                cands, need = MONSTER_TITLE_OVERRIDES[name], ""
            else:
                cands, need = [ucfirst(name), ucfirst(name) + " (monster)"], "monster"
            add(Req(key=f"monster:{letter}:{name}", candidates=cands, group="monsters",
                    section=letter, label=name, need_infobox=need, meta={"symbol": letter}))
        if letter in MONSTER_CLASS_PAGES:
            add(Req(key=f"monsterclass:{letter}", candidates=[MONSTER_CLASS_PAGES[letter]],
                    group="monsters", section=letter, label="class overview",
                    meta={"class_page": True}))

    for cls, titles in OBJECT_OVERVIEW.items():
        for t in titles:
            add(Req(key=f"objclass:{cls}:{t}", candidates=[t], group="objects", section=cls,
                    label=t, meta={"overview": True}))
    for cls, block in OBJECTS_SRC.items():
        for line in block.strip().splitlines():
            name, appearance, randomized = parse_object_line(line)
            if name.startswith("worthless piece of"):
                OBJECT_TITLE_OVERRIDES.setdefault(name, ["Gem"])  # redirects to Gem at the snapshot
            cands = (OBJECT_TITLE_OVERRIDES.get(f"{name}@{cls}") or OBJECT_TITLE_OVERRIDES.get(name)
                     or [OBJECT_TITLE_PREFIX.get(cls, "") + (name if cls in OBJECT_TITLE_PREFIX
                                                            else ucfirst(name))])
            full = (OBJECT_TITLE_PREFIX[cls].lower() + name if cls in OBJECT_TITLE_PREFIX
                    and name not in ("novel", "Book of the Dead") else name)
            add(Req(key=f"object:{cls}:{name}", candidates=cands, group="objects", section=cls,
                    label=full, meta={"appearance": appearance, "random": randomized}))
    for art in ARTIFACTS:
        add(Req(key=f"object:Artifacts:{art}", candidates=[art], group="objects",
                section="Artifacts", label=art))
    return reqs


# ----------------------------------------------------------------------------
# HTTP / MediaWiki API
# ----------------------------------------------------------------------------

class TransientError(Exception):
    pass


class Http:
    """Rate-limited JSON GETs against the MediaWiki API with retry/backoff."""

    RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}

    def __init__(self, delay: float = 0.5, retries: int = 6, verbose: bool = False):
        self.delay, self.retries, self.verbose = delay, retries, verbose
        self.last = 0.0
        self.count = 0

    def get(self, params: dict) -> dict:
        params = dict(params, format="json", formatversion="2")
        url = API + "?" + urllib.parse.urlencode(params)
        backoff = 2.0
        for attempt in range(1, self.retries + 1):
            wait = self.last + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            self.count += 1
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                           "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = resp.read()
                    ctype = resp.headers.get("Content-Type", "")
                if "json" not in ctype:
                    raise TransientError(f"non-JSON response ({ctype}); Cloudflare challenge?")
                data = json.loads(body.decode("utf-8"))
                err = data.get("error")
                if err:
                    if err.get("code") in ("maxlag", "ratelimited", "readonly"):
                        raise TransientError(err.get("code"))
                    raise RuntimeError(f"API error: {err}")
                return data
            except urllib.error.HTTPError as e:
                if e.code not in self.RETRY_STATUS:
                    raise
                ra = e.headers.get("Retry-After") if e.headers else None
                pause = float(ra) if ra and ra.isdigit() else backoff
                why = f"HTTP {e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, TransientError,
                    json.JSONDecodeError) as e:
                pause, why = backoff, f"{type(e).__name__}: {e}"
            if attempt == self.retries:
                raise RuntimeError(f"giving up after {attempt} attempts ({why}): {url[:200]}")
            log(f"  transient failure ({why}); retry {attempt}/{self.retries - 1} in {pause:.0f}s")
            time.sleep(pause)
            backoff = min(backoff * 2, 120)
        raise AssertionError("unreachable")


def query_latest(http: Http, titles: list, namespace: int = 0) -> dict:
    """Latest revision (with content) of up to 50 titles, following redirects.

    Returns {requested title: info}, info being {"missing": True} or
    {"current", "fragment", "revid", "timestamp", "content"}; "incomplete": True
    means the API truncated the batch and the title must be retried alone."""
    data = http.get(dict(action="query", redirects="1", prop="revisions",
                         rvprop="ids|timestamp|content", rvslots="main", titles="|".join(titles)))
    q = data.get("query", {})
    norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
    redir = {r["from"]: (r["to"], r.get("tofragment", "")) for r in q.get("redirects", [])}
    pages = {p["title"]: p for p in q.get("pages", [])}
    out = {}
    for t in titles:
        name, frag, hops = norm.get(t, t), "", 0
        while name in redir and hops < 5:
            name, frag = redir[name]
            hops += 1
        p = pages.get(name)
        if p is None or p.get("missing") or p.get("invalid") or p.get("ns", 0) != namespace:
            out[t] = {"missing": True}
            continue
        revs = p.get("revisions")
        if not revs:
            out[t] = {"current": name, "fragment": frag, "incomplete": True}
            continue
        r = revs[0]
        out[t] = {"current": name, "fragment": frag, "revid": r["revid"],
                  "timestamp": r["timestamp"], "content": r["slots"]["main"].get("content", "")}
    return out


def query_as_of(http: Http, title: str, as_of: str, follow: bool = True):
    """Last revision of `title` at or before `as_of` (None if the page is newer).
    With follow=False a redirect page's own history is used instead of its target's."""
    params = dict(action="query", prop="revisions", titles=title, rvlimit="1", rvdir="older",
                  rvstart=as_of, rvprop="ids|timestamp|content", rvslots="main")
    if follow:
        params["redirects"] = "1"
    data = http.get(params)
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    revs = pages[0].get("revisions") or []
    if not revs:
        return None
    r = revs[0]
    return {"revid": r["revid"], "timestamp": r["timestamp"],
            "content": r["slots"]["main"].get("content", "")}


def fetch_moves(http: Http, since: str) -> list:
    """Main-namespace page moves newer than `since`, newest first."""
    moves, cont = [], {}
    while True:
        d = http.get(dict(action="query", list="logevents", letype="move", lelimit="500",
                          leend=since, leprop="title|details|timestamp", **cont))
        for ev in d.get("query", {}).get("logevents", []):
            tgt = (ev.get("params") or {}).get("target_title")
            if ev.get("ns") == 0 and tgt:
                moves.append({"from": ev["title"], "to": tgt, "timestamp": ev["timestamp"]})
        if "continue" in d:
            cont = {"lecontinue": d["continue"]["lecontinue"]}
        else:
            return moves


def title_at_snapshot(current: str, moves: list) -> str:
    name = current
    for mv in moves:  # newest first: undo each rename in turn
        if mv["to"] == name:
            name = mv["from"]
    return name


REDIRECT_RE = re.compile(r"^\s*#REDIRECT\s*:?\s*\[\[([^\]|#]+)(?:#([^\]|]*))?", re.I)


# ----------------------------------------------------------------------------
# Cache / state
# ----------------------------------------------------------------------------

def stem_for(title: str) -> str:
    """File stem = the title's wiki URL form (spaces -> '_'), e.g. Mines'_End,
    Dwarf_(monster); only '/' (not allowed in file names) becomes '-'."""
    s = re.sub(r"[\x00-\x1f]", "", title.replace(" ", "_").replace("/", "-"))
    return s.strip("_") or "page"


class State:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir
        self.pages_dir = cache_dir / "pages"
        self.path = cache_dir / "state.json"
        self.data = {"mode": None, "as_of": None, "resolve": {}, "pages": {}}
        if self.path.exists():
            self.data = json.loads(self.path.read_text())

    @property
    def resolve(self) -> dict:
        return self.data["resolve"]

    @property
    def pages(self) -> dict:  # current title -> {"stem", "title"}
        return self.data["pages"]

    def save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1, sort_keys=True))
        tmp.replace(self.path)

    def page_file(self, stem: str) -> Path:
        return self.pages_dir / f"{stem}.json"

    def load_page(self, stem: str):
        p = self.page_file(stem)
        return json.loads(p.read_text()) if p.exists() else None

    def store_page(self, rec: dict):
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.page_file(rec["stem"]).write_text(json.dumps(rec, indent=1, ensure_ascii=False))


def assign_output_stems(state: State, currents: list) -> dict:
    """File stem for each referenced page: its title at the snapshot, made
    shell-safe. On a (case-insensitive) clash the page that existed at the
    snapshot and kept its title wins; the others get _2, _3, ..."""
    recs = {c: state.load_page(state.pages[c]["stem"]) for c in currents}

    def rank(c):
        r = recs[c]
        return (bool(r.get("post_snapshot")), r["current_title"] != r["title"], c)
    out, taken = {}, set()
    for c in sorted(recs, key=rank):
        stem = base = stem_for(recs[c]["title"])
        k = 2
        while stem.lower() in taken:
            stem, k = f"{base}_{k}", k + 1
        taken.add(stem.lower())
        out[c] = stem
    return out


def log(msg: str):
    print(msg, file=sys.stderr, flush=True)


INFOBOX_CHECK = {"monster": re.compile(r"\{\{\s*[Mm]onster\s*[|\n]")}


def resolve_requests(http: Http, reqs: list, state: State) -> dict:
    """Map each request to a current wiki title. Returns {title: latest-info}
    for every title looked up, so the fetch step can reuse fetched content."""
    latest: dict = {}
    pending = {r.key: list(r.candidates) for r in reqs}
    by_key = {r.key: r for r in reqs}
    while pending:
        need = sorted({c[0] for c in pending.values() if c and c[0] not in latest})
        for i in range(0, len(need), BATCH):
            chunk = need[i:i + BATCH]
            log(f"  resolving titles {i + 1}-{i + len(chunk)} of {len(need)}")
            res = query_latest(http, chunk)
            for t, info in res.items():
                if info.get("incomplete"):
                    info = query_latest(http, [t])[t]
                latest[t] = info
        for key in list(pending):
            cands = pending[key]
            while cands and cands[0] in latest:
                info, req = latest[cands[0]], by_key[key]
                ok = not info.get("missing")
                if ok and req.need_infobox:
                    ok = bool(INFOBOX_CHECK[req.need_infobox].search(info.get("content", "")))
                if ok:
                    state.resolve[key] = {"title": cands[0], "current": info["current"],
                                          "fragment": info.get("fragment", ""),
                                          "requested": req.candidates}
                    del pending[key]
                    break
                cands.pop(0)
            else:
                if not cands:
                    state.resolve[key] = {"missing": True, "requested": by_key[key].candidates}
                    del pending[key]
    return latest


def fetch_pages(http: Http, currents: list, latest_by_title: dict, state: State, *,
                as_of, moves: list, force: bool) -> list:
    """Download the snapshot revision of each current title into the cache.
    Returns the list of stems written."""
    latest_by_current = {}
    for info in latest_by_title.values():
        if not info.get("missing") and "revid" in info:
            latest_by_current.setdefault(info["current"], info)
    used_stems = {v["stem"].lower(): cur for cur, v in state.pages.items()}
    written = []
    for n, current in enumerate(currents, 1):
        entry = state.pages.get(current)
        if entry and not force and state.page_file(entry["stem"]).exists():
            continue
        info = latest_by_current.get(current)
        if info is None:
            info = query_latest(http, [current])[current]
            if info.get("missing"):
                log(f"  ! vanished: {current}")
                continue
        rec = {"current_title": current, "latest_revid": info["revid"],
               "latest_timestamp": info["timestamp"], "as_of": as_of, "post_snapshot": False,
               "redirected_at_snapshot": []}
        title = current
        if as_of is None or info["timestamp"] <= as_of:
            rev = {k: info[k] for k in ("revid", "timestamp", "content")}
        else:
            rev = query_as_of(http, current, as_of)
            if rev is None:  # page created after the snapshot date
                rev = {k: info[k] for k in ("revid", "timestamp", "content")}
                rec["post_snapshot"] = True
            else:
                title = title_at_snapshot(current, moves)
                hops = 0
                m = REDIRECT_RE.match(rev["content"])
                while m and hops < 3:  # it was only a redirect back then: follow it
                    target = m.group(1).strip()
                    rec["redirected_at_snapshot"].append(target)
                    older = query_as_of(http, target, as_of)
                    if older is None:
                        break
                    rev, title, hops = older, target, hops + 1
                    m = REDIRECT_RE.match(rev["content"])
        stem = stem_for(title)
        if used_stems.get(stem.lower(), current) != current:
            k = 2
            while f"{stem}_{k}".lower() in used_stems:
                k += 1
            stem = f"{stem}_{k}"
        used_stems[stem.lower()] = current
        rec.update(title=title, stem=stem, revid=rev["revid"], timestamp=rev["timestamp"],
                   content=rev["content"])
        state.store_page(rec)
        state.pages[current] = {"stem": stem, "title": title}
        written.append(stem)
        if n % 25 == 0:
            state.save()
            log(f"  fetched {n}/{len(currents)} pages ({http.count} requests so far)")
    state.save()
    return written


def repair_post_snapshot(http: Http, state: State, reqs: list, moves: list, as_of: str) -> dict:
    """Requests that landed on a page created after the snapshot (typically a new
    disambiguation page left behind by a rename) are re-pointed at what the
    title meant at the snapshot: the page it was moved to, or the page it then
    redirected to. Returns {current title: latest-info} still to be fetched."""
    todo: dict = {}
    for r in reqs:
        res = state.resolve.get(r.key) or {}
        page = state.pages.get(res.get("current", ""))
        rec = state.load_page(page["stem"]) if page else None
        if not rec or not rec.get("post_snapshot"):
            continue
        cur, target, frag = res["current"], None, ""
        moved = [m for m in moves if m["from"] == cur]
        if moved:
            target = moved[-1]["to"]  # moves are newest first: take the first move away
        else:
            old = query_as_of(http, res.get("title", cur), as_of, follow=False)
            m = REDIRECT_RE.match(old["content"]) if old else None
            if m:
                target, frag = m.group(1).strip(), (m.group(2) or "").strip()
        if not target:
            continue
        info = query_latest(http, [target])[target]
        if info.get("missing") or info.get("current") == cur:
            continue
        log(f"  {r.label}: '{cur}' is newer than the snapshot; using '{info['current']}'")
        state.resolve[r.key] = {"title": target, "current": info["current"],
                                "fragment": frag or info.get("fragment", ""),
                                "requested": r.candidates, "repaired_from": cur}
        todo[info["current"]] = info
    return todo


# Templates whose content is transcluded into pages (generated skill tables).
TRANSCLUDE_RE = re.compile(r"^[\w' -]+ skill table$")
TEMPLATE_NAME_RE = re.compile(r"\{\{\s*([^{}|<>\[\]\n#:]+?)\s*[|}]")


def template_cache_file(name: str) -> Path:
    return CACHE_DIR / "templates" / f"{stem_for(name)}.json"


def fetch_templates(http: Http, state: State, stems: list, *, as_of, force: bool) -> int:
    """Download (as of the snapshot) the transcluded templates the pages use."""
    names = set()
    for stem in stems:
        rec = state.load_page(stem)
        for m in TEMPLATE_NAME_RE.finditer(rec["content"] if rec else ""):
            n = norm_name(m.group(1))
            if TRANSCLUDE_RE.match(n):
                names.add(n)
    count = 0
    for n in sorted(names):
        path = template_cache_file(n)
        if path.exists() and not force:
            continue
        title = "Template:" + ucfirst(n)
        rev = query_as_of(http, title, as_of) if as_of else None
        if rev is None:
            info = query_latest(http, [title], namespace=10)[title]
            if info.get("missing"):
                log(f"  ! template missing: {title}")
                continue
            rev = {k: info[k] for k in ("revid", "timestamp", "content")}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(rev, name=n, title=title), indent=1, ensure_ascii=False))
        count += 1
    return count


def load_templates() -> dict:
    out = {}
    for p in sorted((CACHE_DIR / "templates").glob("*.json")):
        rec = json.loads(p.read_text())
        out[rec["name"]] = rec["content"]
    return out


TEMPLATE_SOURCES: dict = {}  # filled by main() from the cache


def transclude(src: str, pos: list, named: dict) -> str:
    """Minimal MediaWiki transclusion: <noinclude>/<onlyinclude> and {{{params}}}."""
    src = re.sub(r"<noinclude>.*?(</noinclude>|\Z)", "", src, flags=re.S | re.I)
    m = re.search(r"<onlyinclude>(.*?)</onlyinclude>", src, flags=re.S | re.I)
    if m:
        src = m.group(1)
    src = re.sub(r"</?includeonly>", "", src, flags=re.I)
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)
    args = {str(i + 1): v for i, v in enumerate(pos)}
    args.update(named)

    def param(mm):
        name, _, default = mm.group(1).partition("|")
        return args.get(name.strip(), default)
    for _ in range(5):
        new = re.sub(r"\{\{\{([^{}]*)\}\}\}", param, src)
        if new == src:
            break
        src = new
    return "\n" + src.strip("\n") + "\n"


# ----------------------------------------------------------------------------
# Wikitext -> plain text
# ----------------------------------------------------------------------------

MONSTER_SYMBOLS = {n.lower(): sym for sym, names in MONSTERS_BY_CLASS.items() for n in names}

# Monster flags from Template:Attributes (flag -> phrase).
ATTRIBUTE_TEXT = {
    "fly": "can fly", "swim": "can swim", "amorphous": "can flow under doors",
    "wallwalk": "can phase through walls", "cling": "can cling to the ceiling",
    "tunnel": "can tunnel through walls", "needpick": "needs a pick-axe to tunnel",
    "conceal": "hides under items", "hide": "blends in with its surroundings",
    "amphibious": "can survive underwater", "breathless": "does not need to breathe",
    "notake": "cannot pick up items", "noeyes": "has no eyes", "nohands": "has no hands",
    "nolimbs": "has no limbs", "nohead": "has no head", "mindless": "is mindless",
    "humanoid": "is humanoid", "animal": "is an animal", "slithy": "is serpent-like",
    "unsolid": "has no solid form", "thick": "has a thick hide", "oviparous": "lays eggs",
    "regen": "regenerates HP quickly", "seeinvis": "sees invisible", "tport": "teleports",
    "tportcntrl": "has teleport control", "acid": "is acidic to eat",
    "veg1": "is vegan food", "veg2": "is vegetarian food", "pois": "is poisonous to eat",
    "carnivore": "carnivorous", "herbivore": "herbivorous", "omnivore": "omnivorous",
    "metallivore": "eats metal", "nopoly": "not a valid polymorph form", "undead": "is undead",
    "were": "lycanthrope (changes between human and animal form)", "human": "is human",
    "elf": "is an elf", "dwarf": "is a dwarf", "gnome": "is a gnome", "orc": "is an orc",
    "demon": "is a demon", "merc": "is a mercenary (Yendorian army)", "lord": "is a lord of its kind",
    "prince": "is a prince of its kind", "giant": "is a giant", "male": "always male",
    "female": "always female", "neuter": "neuter", "hostile": "always generated hostile",
    "peaceful": "always generated peaceful", "domestic": "can be tamed by feeding",
    "wander": "wanders", "stalk": "follows you to other levels", "nasty": "is extra nasty",
    "strong": "is strong", "rockthrow": "throws boulders", "greedy": "likes gold",
    "jewels": "likes gems", "collect": "picks up weapons and food", "magic": "picks up magic items",
    "wantsamul": "wants the Amulet of Yendor", "wantsbell": "wants the Bell of Opening",
    "wantsbook": "wants the Book of the Dead", "wantscand": "wants the Candelabrum",
    "wantsarti": "wants your quest artifact",
    "wantsall": "wants the Amulet, Bell, Book, Candelabrum and quest artifact",
    "covetous": "covetous (wants the Amulet and invocation items)",
    "waitsforu": "waits for you to come into view", "close": "lets you close unless attacked",
    "infravision": "has infravision", "infravisible": "visible with infravision",
    "nohell": "not generated in Gehennom", "hell": "only generated in Gehennom",
    "sgroup": "appears in small groups", "lgroup": "appears in large groups",
    "nocorpse": "never leaves a corpse", "death": "resists death magic",
    "drain": "resists level drain", "plusone": "needs a +1 weapon to hit",
    "plustwo": "needs a +2 weapon to hit", "plusthree": "needs a +3 weapon to hit",
    "plusfour": "needs a +4 weapon to hit", "light": "emits light", "notame": "cannot be tamed",
    "vampire": "is a vampire", "does_too_eat": "",
}

INFOBOXES = {
    "monster": "Monster", "weapon": "Weapon", "armor": "Armor", "armour": "Armor",
    "ring": "Ring", "amulet": "Amulet", "wand": "Wand", "potion": "Potion", "scroll": "Scroll",
    "spellbook": "Spellbook", "tool": "Tool", "comestible": "Comestible", "item": "Item",
    "artifact weapon": "Artifact", "artifact": "Artifact", "gem": "Gem", "food": "Comestible",
    "level": "Level", "trap": "Trap",
}
INFOBOX_SKIP = {"tile", "color", "colour", "top", "reference", "image", "sortkey", "languages"}
LEVEL_KEYS = {"branch": "Branch", "from": "From level", "to": "To level",
              "probability": "Probability", "variants": "Variants", "bones": "Bones",
              "mapping": "Mappable", "teleport": "Teleportable", "digfloor": "Diggable floor",
              "digwalls": "Diggable walls"}
INFOBOX_KEYS = {
    "nutr": "Nutrition", "nutrition": "Nutrition", "ac": "AC", "mr": "MR", "align": "Alignment",
    "resistances conveyed": "Resistances conveyed", "smalldmg": "Damage vs small",
    "largedmg": "Damage vs large", "tohit": "To-hit bonus", "skillraw": "Skill",
    "maxcharges": "Max charges", "muse": "Monster use", "abundance": "Probability",
    "whenwielded": "When wielded", "whencarried": "When carried", "wheninvoked": "When invoked",
    "bonusversus": "Bonus damage versus", "base": "Base item", "noenchant": "Cannot be enchanted",
    "ink": "Ink to write", "turns": "Turns to eat/read", "equiv": "Equivalent",
    "exp": "Experience", "experience": "Experience", "glyph": "Symbol", "symbol": "Symbol",
}

COLOR_TEMPLATES = {
    "black", "red", "green", "brown", "blue", "magenta", "cyan", "gray", "grey", "lightgray",
    "light gray", "lightgrey", "orange", "bright green", "brightgreen", "yellow", "bright blue",
    "brightblue", "bright magenta", "brightmagenta", "bright cyan", "brightcyan", "white",
    "darkgray", "dark gray", "darkgrey", "no color", "nocolor", "purple", "metal color",
}
COLOR_RE = re.compile(r"(bright|light|dark)?\s*(red|green|blue|magenta|cyan|gray|grey|yellow|"
                      r"orange|brown|white|black|purple)")
PASSTHROUGH = {"nowrap", "nobr", "nowraplinks", "hover", "abbr", "tooltip", "explain", "anchor2",
               "alignment", "smallcaps", "float right", "float left",
               "small", "big", "center", "highlight", "hilite", "color", "colour", "font",
               "strike", "s", "u", "underline", "shy", "spoiler", "hidden", "mono"}
DROP = {
    "languages", "items", "refsrc", "reffunc", "refdat", "refsrc2", "ref", "reflist", "todo",
    "stub", "merge", "mergeto", "mergefrom", "merge to", "merge from", "cleanup", "delete",
    "wikify", "citation needed", "cn", "fact", "verify", "dod", "ngpl", "rodney", "basedon",
    "cc-by-sa-3.0", "community", "clear", "clr", "-", "prettytable", "toc", "tocright",
    "toc right", "nethack versions", "monsters", "monsters/expanded", "featured", "fa",
    "otheruses", "otheruses4", "for", "about", "redirect", "distinguish", "anchor", "wikipedia",
    "wikia", "boots top", "cloak top", "helm top", "shield top", "gloves top", "shirt top",
    "body armor top", "noprint", "sourcecode", "src", "srclink", "spoiler warning", "dead link",
    "disambig", "disambiguation", "versions", "stub-monster", "monster-stub", "unfinished",
    "needs update", "outdated", "construction", "under construction", "archived", "sfx",
    "variant", "variants", "tile", "icon", "version icon", "move", "rename", "split",
    "encyclopedia",  # in-game encyclopedia quotes: flavor text only
    "encyclopedia-redirect", "keyboard commands", "features", "religion", "gods",
    "redirects-here", "for2", "note", "randomvariable", "slashem-7e7", "variant-343",
    "noversion", "dcorbett", "bilious", "alternate tilesets", "va", "patch",
    # ASCII radius diagrams built with #expr; the surrounding prose covers them
    "lightradius", "darkradius", "jumpradius", "circleradius9", "circleradiussquared6",
    "drawbridgeradius", "earthquakearea", "cloudsize",
}


def norm_name(name: str) -> str:
    n = re.sub(r"\s+", " ", name.replace("_", " ")).strip()
    if n.lower().startswith("template:"):
        n = n[9:].strip()
    return n.lower()


def split_top(s: str, sep: str = "|") -> list:
    """Split on `sep` outside [[...]] links."""
    parts, buf, depth, i, n = [], [], 0, 0, len(s)
    while i < n:
        if s.startswith("[[", i):
            depth += 1; buf.append("[["); i += 2; continue
        if s.startswith("]]", i) and depth:
            depth -= 1; buf.append("]]"); i += 2; continue
        if depth == 0 and s.startswith(sep, i):
            parts.append("".join(buf)); buf = []; i += len(sep); continue
        buf.append(s[i]); i += 1
    parts.append("".join(buf))
    return parts


def split_template(inner: str):
    parts = split_top(inner)
    name, pos, named = parts[0], [], {}
    for a in parts[1:]:
        m = re.match(r"^\s*([^=\[\]<>\n]+?)\s*=(.*)$", a, re.S)
        if m:
            named[m.group(1).strip()] = m.group(2).strip()
        else:
            pos.append(a.strip())
    return name, pos, named


TOK_OPEN, TOK_CLOSE = "\ue000", "\ue001"
TOK_RE = re.compile("\ue000(\\d+)\ue001")
TOK_LINE_RE = re.compile("^\\s*\ue000\\d+\ue001\\s*$")
PIPE, EQ, HEAD, BR = "\ue002", "\ue003", "\ue004", "\ue005"  # {{!}}, {{=}}, heading, <br> in cells
TPL_RE = re.compile(r"\{\{(?!\{)((?:(?!\{\{|\}\}).)*?)\}\}", re.S)
LINK_RE = re.compile(r"\[\[((?:(?!\[\[|\]\]).)*?)\]\]", re.S)
EXTLINK_RE = re.compile(r"\[((?:https?:|ftp:)?//[^\s\]]+)(?:\s+([^\]]*))?\]")
HEADING_RE = re.compile(r"^(={1,6})\s*(.+?)\s*(={1,6})\s*$")
LIST_RE = re.compile(r"^([*#:;]+)\s*(.*)$")
TABLE_START_RE = re.compile(r"^\s*:*\s*\{\|")
TABLE_END_RE = re.compile(r"^\s*\|\}")
INLINE_TAGS_RE = re.compile(
    r"</?(span|div|small|big|center|font|u|s|strike|del|ins|abbr|b|i|em|strong|cite|p|"
    r"blockquote|q|dfn|mark|wbr|table|tr|td|th|caption|tbody|thead|hr|onlyinclude|"
    r"includeonly|noinclude|section|poem)\b[^>]*>", re.I)
ATTR_RE = re.compile(r"^\s*(?:[\w-]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s|]+)\s*)+$")


class Converter:
    """Convert one page of wikitext to readable plain text."""

    def __init__(self, title: str):
        self.title = title
        self.blocks: list = []
        self.infoboxes: list = []      # [(kind, [(key, value), ...])]
        self.version_tags: list = []
        self.unknown: Counter = Counter()

    # -- placeholder tokens (verbatim blocks, rendered tables, infoboxes) --
    def token(self, text: str, block: bool = False) -> str:
        self.blocks.append(text)
        t = f"{TOK_OPEN}{len(self.blocks) - 1}{TOK_CLOSE}"
        return f"\n{t}\n" if block else t

    def restore(self, s: str) -> str:
        for _ in range(20):
            new = TOK_RE.sub(lambda m: self.blocks[int(m.group(1))], s)
            if new == s:
                break
            s = new
        return s

    # -- pipeline --
    def convert(self, src: str) -> str:
        s = src.replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r"<!--.*?(?:-->|\Z)", "", s, flags=re.S)
        s = re.sub(r"<noinclude>.*?</noinclude>", "", s, flags=re.S | re.I)
        s = re.sub(r"<includeonly>.*?</includeonly>", "", s, flags=re.S | re.I)
        s = self.protect(s)
        s = re.sub(r"<ref\b[^>]*/\s*>", "", s, flags=re.I)
        s = re.sub(r"<ref\b[^>]*>.*?</ref\s*>", "", s, flags=re.S | re.I)
        s = re.sub(r"<references\b[^>]*/\s*>|<references\b[^>]*>.*?</references\s*>", "", s,
                   flags=re.S | re.I)
        s = re.sub(r"<(gallery|imagemap|timeline|templatedata)\b[^>]*>.*?</\1\s*>", "", s,
                   flags=re.S | re.I)
        s = self.expand_templates(s)
        s = s.replace(PIPE, "|").replace(EQ, "=")
        s = self.tables(s)
        s = self.block_lines(s)
        s = prune_empty_sections(s)
        s = self.restore(s)
        return tidy(s)

    def protect(self, s: str) -> str:
        s = re.sub(r"<nowiki>(.*?)</nowiki>", lambda m: self.token(html.unescape(m.group(1))),
                   s, flags=re.S | re.I)
        s = re.sub(r"<nowiki\s*/>", "", s, flags=re.I)
        s = re.sub(r"<pre\b[^>]*>(.*?)</pre\s*>",
                   lambda m: self.token(pre_text(m.group(1)), True), s, flags=re.S | re.I)
        s = re.sub(r"<(syntaxhighlight|source)\b[^>]*>(.*?)</\1\s*>",
                   lambda m: self.token(pre_text(m.group(2)), True), s, flags=re.S | re.I)
        s = re.sub(r"<replacecharsblock\b[^>]*>(.*?)</replacecharsblock\s*>",
                   lambda m: self.token(replacechars(m.group(1)), True), s, flags=re.S | re.I)
        s = re.sub(r"<replacechars\b[^>]*>(.*?)</replacechars\s*>",
                   lambda m: self.token(replacechars(m.group(1))), s, flags=re.S | re.I)
        s = re.sub(r"<math\b[^>]*>(.*?)</math\s*>", lambda m: self.token(m.group(1).strip()),
                   s, flags=re.S | re.I)
        return s

    # -- templates --
    def expand_templates(self, s: str) -> str:
        for _ in range(60):
            new = TPL_RE.sub(lambda m: self.template(m.group(1)), s)
            if new == s:
                break
            s = new
        return s

    def template(self, inner: str) -> str:
        name, pos, named = split_template(inner)
        raw = name.strip()
        n = norm_name(name)
        if n.startswith("#"):
            return self.parser_function(raw, pos, named)
        if ":" in n:
            fn, _, arg = raw.partition(":")
            f = fn.strip().lower()
            if f in ("lc", "uc", "lcfirst", "ucfirst"):
                a = arg.strip()
                return {"lc": a.lower(), "uc": a.upper(), "lcfirst": a[:1].lower() + a[1:],
                        "ucfirst": ucfirst(a)}[f]
            if f in ("displaytitle", "defaultsort", "fullurl", "localurl", "urlencode",
                     "anchorencode", "ns", "int", "padleft", "padright", "formatnum"):
                return arg.strip() if f in ("formatnum", "anchorencode") else ""
        if n in ("pagename", "fullpagename", "basepagename", "subpagename"):
            return self.title
        if n == "sitename":
            return "NetHackWiki"
        if n == "!":
            return PIPE
        if n in ("=", "equals"):
            return EQ
        handler = TEMPLATE_HANDLERS.get(n)
        if handler:
            return handler(self, pos, named)
        if n in INFOBOXES:
            return self.infobox(n, pos, named)
        m = re.fullmatch(r"nethack-(\d)(\d)(\d)", n)
        if m:
            tag = f"NetHack {m.group(1)}.{m.group(2)}.{m.group(3)}"
            if tag not in self.version_tags:
                self.version_tags.append(tag)
            return ""
        if n in COLOR_TEMPLATES or n in PASSTHROUGH or COLOR_RE.fullmatch(n):
            return pos[0] if pos else ""
        if n in DROP or n.startswith(("nethack-", "infobox", "navbox")):
            return ""
        if n in TEMPLATE_SOURCES:
            return transclude(TEMPLATE_SOURCES[n], pos, named)
        if n == "of" or n.endswith(" of"):  # {{of|wand|x|y}}, {{? of|x}}: show the specifiers
            items = [p for p in (pos[1:] if n == "of" else pos) if p]
            if len(items) > 1:
                conj = " or " if named.get("or") else " and " if named.get("and") else ", "
                return ", ".join(items[:-1]) + conj + items[-1]
            return items[0] if items else ""
        self.unknown[n] += 1
        return ""

    def parser_function(self, raw: str, pos: list, named: dict) -> str:
        fn, _, first = raw[1:].partition(":")
        fn = fn.strip().lower()
        args = [first.strip()] + pos
        if fn == "if":
            return (args[1] if len(args) > 1 else "") if args[0] else (args[2] if len(args) > 2 else "")
        if fn == "ifeq":
            same = len(args) > 1 and args[0] == args[1]
            return (args[2] if len(args) > 2 else "") if same else (args[3] if len(args) > 3 else "")
        if fn == "switch":
            return named.get(args[0], named.get("#default", ""))
        return ""

    def infobox(self, kind: str, pos: list, named: dict) -> str:
        rows = []
        if kind == "monster":
            name = self.value(named.get("name", "")) or self.title
            sym = MONSTER_SYMBOLS.get(name.lower()) or MONSTER_SYMBOLS.get(self.title.lower())
            rows.append(("Name", name))
            if sym is not None:
                rows.append(("Symbol", "(blank space)" if sym == " " else sym))
        if kind == "level" and pos and pos[0]:
            rows.append(("Level", self.value(pos[0])))
        keymap = LEVEL_KEYS if kind == "level" else INFOBOX_KEYS
        for k, v in named.items():
            kl = k.strip().lower()
            if kl in INFOBOX_SKIP or (kind == "monster" and kl == "name"):
                continue
            v = self.value(v)
            if not v:
                continue
            key = keymap.get(kl, ucfirst(k.strip()))
            if key == "Symbol" and " " not in v:
                v = re.sub(r"(.)\1+", r"\1", v)  # DDDDD -> D
            rows.append((key, v))
        self.infoboxes.append((kind, rows))
        body = "\n".join(f"{k}: {v}" for k, v in rows)
        return self.token(f"[{INFOBOXES[kind]} infobox]\n{body}\n[end infobox]", block=True)

    def value(self, v: str) -> str:
        """Render an infobox value on a single line."""
        v = re.sub(r"^\s*[*#:]+\s*", "", v)
        v = re.sub(r"\n\s*[*#:]+\s*", "; ", v)
        v = re.sub(r"</li>\s*<li\b[^>]*>", "; ", v, flags=re.I)
        v = re.sub(r"<\s*/?\s*br\s*/?\s*>", "; ", v, flags=re.I)
        v = re.sub(r"\s*\n\s*", "; ", v.strip())
        v = re.sub(r"</?(ul|ol|li)\b[^>]*>", "", v, flags=re.I)
        v = self.restore(self.inline(v))
        v = re.sub(r";\s*\(", " (", re.sub(r"\s+", " ", v))
        return v.strip(" ;")

    # -- tables --
    def tables(self, s: str) -> str:
        lines = s.split("\n")
        out, i = [], 0
        while i < len(lines):
            if TABLE_START_RE.match(lines[i]):
                j = table_end(lines, i)
                out.append(self.token(self.render_table(lines[i:j]), block=True))
                i = j
            else:
                out.append(lines[i])
                i += 1
        return "\n".join(out)

    def render_table(self, lines: list) -> str:
        caption, rows = "", []
        cur = None
        body = lines[1:-1] if len(lines) > 1 and TABLE_END_RE.match(lines[-1]) else lines[1:]

        def add_cells(text: str, header: bool):
            nonlocal cur
            if cur is None:
                cur = []
                rows.append(cur)
            seps = ("!!", "||") if header else ("||",)
            pieces = [text]
            for sep in seps:
                pieces = [p for piece in pieces for p in split_top(piece, sep)]
            for p in pieces:
                attrs, content = "", p
                parts = split_top(p, "|")
                if len(parts) > 1 and ATTR_RE.match(parts[0] or "x=y"):
                    attrs, content = parts[0], "|".join(parts[1:])
                cur.append({"h": header, "text": content, "cs": span_attr(attrs, "colspan"),
                            "rs": span_attr(attrs, "rowspan")})

        k = 0
        while k < len(body):
            line = body[k]
            st = line.strip()
            if TABLE_START_RE.match(line):
                j = table_end(body, k)
                nested = self.token(self.render_table(body[k:j]), block=True)
                if cur:
                    cur[-1]["text"] += "\n" + nested
                else:
                    add_cells(nested, False)
                k = j
                continue
            if st.startswith("|+"):
                parts = split_top(st[2:], "|")
                caption = ("|".join(parts[1:]) if len(parts) > 1 and ATTR_RE.match(parts[0])
                           else st[2:])
            elif st.startswith("|-"):
                cur = None
            elif st.startswith("!"):
                add_cells(st[1:], True)
            elif st.startswith("|") and not st.startswith("|}"):
                add_cells(st[1:], False)
            elif cur:
                cur[-1]["text"] += "\n" + line
            k += 1
        rows = [r for r in rows if r]
        if not rows:
            return ""
        block_mode = False
        for r in rows:
            for c in r:
                cell = re.sub(r"<\s*/?\s*br\s*/?\s*>", BR, c["text"].strip("\n"), flags=re.I)
                txt = self.restore(self.block_lines(cell))
                c["out"] = txt.strip("\n")
                lines_ = [ln for ln in c["out"].split("\n") if ln.strip()]
                if len(lines_) > 1 and any(ln.startswith(" ") for ln in lines_):
                    block_mode = True
                if len(lines_) > 1 and any(ln.startswith(("|", "+")) and ln.rstrip().endswith(("|", "+"))
                                           for ln in lines_):
                    block_mode = True  # nested table
        cap = self.restore(self.inline(caption)).strip().lstrip("|").strip()
        if block_mode:
            out = [f"Table: {cap}"] if cap else []
            for r in rows:
                heads = [c["out"] for c in r if c["h"] and "\n" not in c["out"]]
                for c in r:
                    if c["h"] and "\n" not in c["out"]:
                        continue
                    label = (heads[0] + ": ") if heads and len(heads) == 1 else ""
                    out.append(label + re.sub(r"\s*" + BR + r"\s*", "\n", c["out"]))
                    out.append("")
            return "\n".join(out).rstrip()
        # grid with colspan/rowspan expansion
        grid, carry = [], {}
        for r in rows:
            line, col = [], 0
            cells = list(r)
            while cells or col in carry:
                if col in carry:
                    left, txt, h = carry[col]
                    line.append((txt, h))
                    if left <= 1:
                        del carry[col]
                    else:
                        carry[col] = (left - 1, txt, h)
                    col += 1
                    continue
                c = cells.pop(0)
                txt = re.sub(r"\s*" + BR + r"\s*", "; ", one_line(c["out"])).strip("; ")
                for x in range(max(1, min(c["cs"], 20))):
                    line.append((txt if x == 0 else "", c["h"]))
                    if c["rs"] > 1:
                        carry[col] = (c["rs"] - 1, txt if x == 0 else "", c["h"])
                    col += 1
            grid.append(line)
        width = max(len(r) for r in grid)
        for r in grid:
            r.extend([("", False)] * (width - len(r)))
        cellw = [max(len(r[i][0]) for r in grid) for i in range(width)]
        pad = max(cellw) <= 50 and sum(cellw) + 3 * width <= 180
        out = [f"Table: {cap}"] if cap else []
        for n_, r in enumerate(grid):
            cells = [t.replace("|", "\\|") for t, _ in r]
            if pad:
                cells = [t.ljust(cellw[i]) for i, t in enumerate(cells)]
            out.append(("| " + " | ".join(cells) + " |").rstrip())
            if n_ == 0 and all(h for _, h in r) and len(grid) > 1:
                out.append("|" + "|".join("-" * ((cellw[i] if pad else 3) + 2) for i in range(width)) + "|")
        return "\n".join(out)

    # -- line-level structure: headings, lists, preformatted lines --
    def block_lines(self, s: str) -> str:
        out, counters = [], []
        para = False  # last output line is a paragraph line that may continue
        for raw in s.split("\n"):
            if TOK_LINE_RE.match(raw):
                out.append(raw.strip())
                counters, para = [], False
                continue
            m = HEADING_RE.match(raw)
            if m and not raw.startswith(" "):
                level = min(len(m.group(1)), len(m.group(3)))
                text = self.inline(m.group(2)).strip()
                out += ["", HEAD + "#" * level + " " + text, ""]
                counters, para = [], False
                continue
            if re.match(r"^-{4,}\s*$", raw) or not raw.strip():
                out.append("")
                counters, para = [], False
                continue
            m = LIST_RE.match(raw)
            if m and not raw.startswith(" "):
                prefix, text = m.group(1), m.group(2)
                depth, kind = len(prefix), prefix[-1]
                para = False
                if kind == "#":
                    counters = (counters + [0] * depth)[:depth]
                    counters[depth - 1] += 1
                    out.append("   " * (depth - 1) + f"{counters[-1]}. " + self.inline(text).strip())
                    continue
                if not prefix.startswith("#"):
                    counters = []
                if kind == "*":
                    out.append("  " * (depth - 1) + "- " + self.inline(text).strip())
                elif kind == ":":
                    out.append("    " * depth + self.inline(text).strip())
                else:  # ; term : definition
                    term, sep, defi = colon_split(text)
                    line = "  " * (depth - 1) + self.inline(term).strip()
                    if sep:
                        line += ": " + self.inline(defi).strip()
                    out.append(line)
                continue
            counters = []
            if raw.startswith(" "):
                # preformatted line: the leading space is markup; keep the rest verbatim
                out.append(self.inline(raw[1:].rstrip()))
                para = False
                continue
            text = self.inline(raw).strip()
            if para and out and out[-1] and not TOK_LINE_RE.match(raw):
                out[-1] += " " + text  # MediaWiki joins consecutive paragraph lines
            else:
                out.append(text)
            para = bool(text) and not TOK_RE.fullmatch(text)
        return "\n".join(out)

    # -- inline markup --
    def inline(self, s: str) -> str:
        for _ in range(10):
            new = LINK_RE.sub(self._link, s)
            if new == s:
                break
            s = new
        s = EXTLINK_RE.sub(lambda m: (m.group(2) or m.group(1)).strip(), s)
        s = re.sub(r"''([^'\n]+?)'''s\b", r"\1's", s)
        s = re.sub(r"'{5}", "", s)
        s = s.replace("''''", "'")
        s = re.sub(r"'''|''", "", s)
        s = re.sub(r"<\s*/?\s*br\s*/?\s*>", "\n", s, flags=re.I)
        s = re.sub(r"<li\b[^>]*>", "\n- ", s, flags=re.I)
        s = re.sub(r"</li>|</?(ul|ol|dl|dd|dt)\b[^>]*>", "", s, flags=re.I)
        s = re.sub(r"<sup\b[^>]*>(.*?)</sup>",
                   lambda m: "^" + m.group(1) if len(m.group(1)) <= 4 else m.group(1),
                   s, flags=re.I | re.S)
        s = re.sub(r"</?sub\b[^>]*>", "", s, flags=re.I)
        s = re.sub(r"<(kbd|code|tt|samp|var|key)\b[^>]*>(.*?)</\1>",
                   lambda m: (f"`{m.group(2)}`" if 0 < len(m.group(2)) <= 40
                              and "\n" not in m.group(2) else m.group(2)),
                   s, flags=re.I | re.S)
        s = INLINE_TAGS_RE.sub("", s)
        s = re.sub(r"__(NO)?(TOC|EDITSECTION|FORCETOC|NEWSECTIONLINK|INDEX|NOINDEX)__", "", s)
        s = html.unescape(s).replace("\xa0", " ").replace("⁄", "/")
        return s

    def _link(self, m) -> str:
        inner = m.group(1)
        target, sep, text = inner.partition("|")
        t = target.strip()
        low = t.lower()
        if re.match(r"(file|image|media|category)\s*:", low):
            return ""
        if re.match(r"[a-z]{2}(-[a-z]{2,4})?\s*:", low) and not low.startswith(("wp:",)):
            return ""  # interlanguage link
        if sep:
            shown = text.strip()
            if len(shown) == 1 and not t.startswith(":"):
                # a bare map glyph such as [[Gnome lord|G]]: keep what it stands for
                name = re.sub(r"\s*\(.*?\)\s*$", "", t.split("#")[0].replace("_", " ")).strip()
                return f"{shown} ({name})" if name and name.lower() != shown.lower() else shown
            if shown:
                return text
            return re.sub(r"\s*\(.*\)$", "", t.lstrip(":").split(":")[-1])  # pipe trick
        t = t.lstrip(":")
        for prefix in ("wikipedia:", "wp:", "w:", "source:"):
            if t.lower().startswith(prefix):
                t = t[len(prefix):]
        return t


def pre_text(body: str) -> str:
    return html.unescape(body).replace("\xa0", " ").strip("\n")


def replacechars(body: str) -> str:
    """<replacecharsblock>: optional 'X=replacement' mapping lines, a blank line,
    then a verbatim map. Keep only the map."""
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    i = 0
    while i < len(lines) and lines[i].strip() and "=" in lines[i]:
        i += 1
    if 0 < i < len(lines) and not lines[i].strip():
        lines = lines[i + 1:]
    return pre_text("\n".join(lines))


def span_attr(attrs: str, name: str) -> int:
    m = re.search(name + r"\s*=\s*[\"']?(\d+)", attrs, re.I)
    return int(m.group(1)) if m else 1


def table_end(lines: list, start: int) -> int:
    depth, k = 0, start
    while k < len(lines):
        if TABLE_START_RE.match(lines[k]):
            depth += 1
        elif TABLE_END_RE.match(lines[k]):
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return len(lines)


def colon_split(text: str):
    depth, i = 0, 0
    while i < len(text):
        if text.startswith("[[", i):
            depth += 1; i += 2; continue
        if text.startswith("]]", i):
            depth = max(0, depth - 1); i += 2; continue
        if text[i] == ":" and depth == 0 and not text.startswith("://", i):
            return text[:i], ":", text[i + 1:]
        i += 1
    return text, "", ""


def one_line(s: str) -> str:
    parts = [p.strip() for p in s.split("\n") if p.strip()]
    out = ""
    for p in parts:
        if not out:
            out = p
        elif p.startswith(("- ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            out += "; " + p.lstrip("- ")
        else:
            out += " " + p
    return re.sub(r"[ \t]+", " ", out)


def prune_empty_sections(s: str) -> str:
    """Drop headings whose section ended up empty (References, Encyclopedia entry...).
    Headings carry the HEAD sentinel so map lines starting with '#' are never touched."""
    def level(ln: str) -> int:
        return len(ln) - len(ln[1:].lstrip("#")) - 1 if ln.startswith(HEAD) else 0
    while True:
        lines, keep = s.split("\n"), []
        for i, ln in enumerate(lines):
            lv = level(ln)
            if lv:
                nxt = next((x for x in lines[i + 1:] if x.strip()), None)
                if nxt is None or 0 < level(nxt) <= lv:
                    continue
            keep.append(ln)
        if len(keep) == len(lines):
            return s
        s = "\n".join(keep)


def tidy(s: str) -> str:
    s = "\n".join(ln.rstrip() for ln in s.replace(HEAD, "").split("\n"))
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip("\n") + "\n"


# -- template handlers -------------------------------------------------------

def _t_frac(c, pos, named):
    p = [x for x in pos if x != ""]
    if len(p) >= 3:
        return f"{p[0]} {p[1]}/{p[2]}"
    if len(p) == 2:
        return f"{p[0]}/{p[1]}"
    if len(p) == 1:
        return f"1/{p[0]}"
    return "/"


def _t_upcoming(c, pos, named):
    ver = (pos[0] if pos else named.get("1", "")).strip() or "a future version"
    if re.match(r"^\d", ver):
        ver = "NetHack " + ver
    text = (pos[1] if len(pos) > 1 else named.get("2", "")).strip()
    tag = f"{ver} change, NOT in 3.6.x"
    if "\n" not in text.strip():
        return f"\n\n[{tag}: {text.strip()}]\n\n"
    return f"\n\n[{tag}:]\n\n{text.strip()}\n\n[end of {ver} change]\n\n"


def _t_message(c, pos, named):
    msg = c.value(pos[0] if pos else named.get("1", ""))
    expl = c.value(pos[1] if len(pos) > 1 else named.get("2", ""))
    return c.token(f"\"{msg}\"" + (f" -- {expl}" if expl else ""))


def _t_monsym(c, pos, named):
    name = (pos[0] if pos else "").replace("_", " ").strip()
    sym = MONSTER_SYMBOLS.get(name.lower())
    if sym is None:
        return ""  # not a 3.6 monster (variant or deferred)
    return "' '" if sym == " " else sym


def _t_monsymlink(c, pos, named):
    return (pos[0] if pos else "").strip()


def _t_monclass(c, pos, named):
    return (pos[0] if pos else "").strip()


def _t_attributes(c, pos, named):
    flags = [k for k, v in named.items() if v.strip() and v.strip() != "0"]
    text = "; ".join(ATTRIBUTE_TEXT.get(f, f) for f in flags if ATTRIBUTE_TEXT.get(f, f))
    subject = (pos[0] if pos else "").strip()
    return f"({subject}: {text})" if " also" in subject else text


def _t_sa(c, pos, named):
    return (pos[1] if len(pos) > 1 and pos[1] else (pos[0] if pos else ""))


def _t_main(c, pos, named):
    items = [named.get(f"l{i + 1}", p) for i, p in enumerate(pos) if p]
    return "\n\n(Main article: " + ", ".join(items) + ")\n\n" if items else ""


def _t_seealso(c, pos, named):
    items = [named.get(f"l{i + 1}", p) for i, p in enumerate(pos) if p]
    return "\n\n(See also: " + ", ".join(items) + ")\n\n" if items else ""


def _t_kbd(c, pos, named):
    keys = [k.strip() for k in pos if k.strip()]
    if not keys:
        return ""
    mod = keys[0].lower()
    if len(keys) == 2 and len(keys[1]) == 1 and mod == "shift":
        return f"`{keys[1].upper()}`"                  # {{kbd|shift|z}} -> Z
    if len(keys) == 2 and len(keys[1]) == 1 and mod in ("ctrl", "control", "^"):
        return f"`^{keys[1].upper()}`"                 # {{kbd|ctrl|x}} -> ^X
    if len(keys) == 2 and len(keys[1]) == 1 and mod in ("alt", "meta", "m"):
        return f"`M-{keys[1]}`"
    return "`" + "+".join(keys) + "`"


def _t_commit(c, pos, named):
    h = (pos[0] if pos else "").strip()
    return (pos[1] if len(pos) > 1 and pos[1] else f"commit {h[:8]}") if h else "a commit"


def _t_tl(c, pos, named):
    return "{{" + (pos[0] if pos else "") + "}}"


def _t_first(c, pos, named):
    return pos[0] if pos else ""


def _t_last(c, pos, named):
    return pos[-1] if pos else ""


def _t_random_appearance(c, pos, named):
    return "random appearance"


def _t_wp(c, pos, named):
    return pos[1] if len(pos) > 1 else (pos[0] if pos else "")


def _t_davg(c, pos, named):
    n, x = (pos + ["", ""])[:2]
    return f"{n}d{x}" if x else f"d{n}"


def _t_rn1(c, pos, named):
    try:
        x, y = int(pos[0]), int(pos[1])
        return f"{y}-{x + y - 1}"
    except (ValueError, IndexError):
        return "rn1(" + ",".join(pos) + ")"


def _t_questmon(c, pos, named):
    mon, role, kind = (pos + ["", "", ""])[:3]
    return f"{mon} is a monster (the quest {kind} of the {ucfirst(role)} quest)" if role else mon


def _t_caption(c, pos, named):
    return "\n\n" + "\n".join(p for p in pos if p) + "\n\n"


def _t_guidebook(c, pos, named):
    text = re.sub(r"\s+", " ", pos[0] if pos else named.get("1", "")).strip()
    return f"\n\nGuidebook: \"{text}\"\n\n" if text else ""


TEMPLATE_HANDLERS = {
    "frac": _t_frac, "sfrac": _t_frac, "upcoming": _t_upcoming, "message": _t_message,
    "msg": _t_message, "monsym": _t_monsym, "monsymlink": _t_monsymlink,
    "monclasslink": _t_monclass, "monclass": _t_monclass, "mcsl": _t_monclass,
    "monclasssym": _t_monclass, "attributes": _t_attributes, "sa": _t_sa, "main": _t_main,
    "see also": _t_seealso, "seealso": _t_seealso, "kbd": _t_kbd, "key": _t_kbd,
    "keypress": _t_kbd, "button": _t_kbd, "tt": _t_kbd, "code": _t_kbd, "commit": _t_commit,
    "tl": _t_tl, "random appearance": _t_random_appearance, "w": _t_wp, "wp": _t_wp,
    "sic": lambda c, p, n: (p[0] if p else "") + " [sic]", "guidebook": _t_guidebook,
    "right-align": _t_first, "yes": lambda c, p, n: p[0] if p else "yes",
    "davg": _t_davg, "rn1": _t_rn1, "questmon": _t_questmon, "caption": _t_caption,
    "msl": _t_monsymlink, "function": _t_last, "diagonal split header": lambda c, p, n: " / ".join(p),
    "footnote": lambda c, p, n: f" (note: {p[0]})" if p else "",
    "no": lambda c, p, n: p[0] if p else "no", "partial": _t_first,
}


# ----------------------------------------------------------------------------
# Output: page files and INDEX.md
# ----------------------------------------------------------------------------

def page_url(title: str) -> str:
    return f"{SITE}/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe="/:'(),!*")


def render_page(rec: dict, aliases: list):
    conv = Converter(rec["title"])
    body = conv.convert(rec["content"])
    h = [f"Title: {rec['title']}"]
    if rec["current_title"] != rec["title"]:
        h.append(f"Current wiki title: {rec['current_title']} (renamed after the snapshot)")
    h.append(f"Source: {page_url(rec['title'])}")
    rev = f"Revision: {rec['revid']} of {rec['timestamp'][:10]}"
    if rec.get("as_of"):
        newer = "unchanged since" if rec["latest_revid"] == rec["revid"] else \
            f"page has been edited since, latest {rec['latest_timestamp'][:10]}"
        rev += (f" (snapshot as of {rec['as_of'][:10]}, i.e. before NetHack 5.0.0; {newer})")
    h.append(rev)
    h.append(f"Permalink: {SITE}/index.php?oldid={rec['revid']}")
    if rec.get("post_snapshot"):
        h.append("WARNING: page created after the snapshot date; it may describe NetHack 5.0.0, not 3.6.x")
    if rec.get("redirected_at_snapshot"):
        h.append(f"Note: at the snapshot date this title redirected to {rec['title']}")
    if conv.version_tags:
        h.append("Wiki version tag: page states it reflects " + ", ".join(conv.version_tags))
    if aliases:
        h.append("Also covers: " + "; ".join(aliases))
    h.append(f"License: {LICENSE_LINE}")
    text = "\n".join(h) + "\n" + "=" * 78 + "\n\n" + body
    return text, conv


def first_sentence(text: str, max_words: int = 15) -> str:
    """First sentence of a rendered page's body (skipping header and infobox)."""
    body = text.split("=" * 78, 1)[-1]
    body = re.sub(r"^\[\w[\w ]* infobox\]\n.*?^\[end infobox\]$", "", body, flags=re.S | re.M)
    for line in body.split("\n"):
        s = line.strip()
        if (not s or s.startswith(("#", "[", "|", "(Main", "(See", "Table:", "- ", "Guidebook:", '"'))
                or TOK_RE.search(s)):
            continue
        s = re.split(r"(?<=[a-z0-9\)\]'\"])\.\s", s + " ")[0].strip().rstrip(".")
        words = s.split()
        if len(words) < 3:
            continue
        return " ".join(words[:max_words]) + (" ..." if len(words) > max_words else "")
    return ""


def infobox_dict(conv) -> dict:
    return {k.lower(): v for _, rows in conv.infoboxes[:1] for k, v in rows}


def monster_gist(label: str, ib: dict) -> str:
    bits = []
    for key, short in (("level", "lvl"), ("speed", "spd"), ("ac", "AC"), ("mr", "MR"),
                       ("difficulty", "diff")):
        if ib.get(key):
            bits.append(f"{short} {ib[key]}")
    out = label + (": " + ", ".join(bits) if bits else "")
    if ib.get("attacks"):
        out += f"; attacks: {ib['attacks']}"
    conveyed = ib.get("resistances conveyed", "")
    if conveyed and conveyed.lower() not in ("none", "nothing"):
        out += f"; eating conveys: {conveyed}"
    return shorten(out, 230)


def object_gist(label: str, ib: dict, meta: dict) -> str:
    out = label
    if meta.get("random"):
        out += " (random appearance)"
    elif meta.get("appearance"):
        out += f" (unidentified: {meta['appearance']})"
    bits = []
    clean = lambda v: re.sub(r"\s*\(.*?\)", "", v or "").strip()
    for key, fmt in (("cost", "${}"), ("weight", "wt {}"), ("ac", "AC {}")):
        if clean(ib.get(key)):
            bits.append(fmt.format(clean(ib.get(key))))
    sm, lg = clean(ib.get("damage vs small")), clean(ib.get("damage vs large"))
    if sm or lg:
        bits.append(f"dmg {sm or '?'}/{lg or '?'}")
    for key, fmt in (("nutrition", "nutr {}"), ("level", "spell level {}"), ("type", "{}")):
        if clean(ib.get(key)):
            bits.append(fmt.format(clean(ib.get(key))))
    if bits:
        out += "; " + ", ".join(bits)
    special = ib.get("special") or ib.get("when wielded") or ib.get("when carried")
    if special:
        out += f"; {special}"
    return shorten(out, 200)


def shorten(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 3].rstrip() + "..."


def build_index(plan: list, state: State, rendered: dict, out_stem: dict) -> str:
    L = ["# NetHack knowledge base index", "",
         "Plain-text copies of NetHackWiki pages for NetHack 3.6.x, one file per page in `wiki/`.",
         "Search them with grep, e.g. `grep -ril 'cockatrice' knowledge/wiki` or",
         "`grep -i -A3 'price' knowledge/wiki/Price_identification.txt`.",
         "",
         "- Pages are a snapshot of the wiki as of 2026-05-02, before NetHack 5.0.0 (formerly 3.7.0)",
         "  was released; `[NetHack 3.7.0 change, NOT in 3.6.x: ...]` notes describe later versions.",
         "- Each file starts with a header (title, source URL, revision, version tag, license).",
         "  Monster and object pages then list their infobox stats as `key: value` lines.",
         "- `Also covers:` in a header lists other names that redirect to that page.",
         "- Regenerate with `python3 scripts/fetch_wiki.py` (see knowledge/README.md).",
         ""]
    by_group: dict = {}
    for r in plan:
        by_group.setdefault(r.group, []).append(r)

    def target(r: Req):
        res = state.resolve.get(r.key) or {}
        if res.get("missing") or "current" not in res:
            return None, ""
        return out_stem.get(res["current"]), res.get("fragment", "")

    def line_for(r: Req, gist: str) -> str:
        stem, frag = target(r)
        if not stem:
            return ""
        where = f"wiki/{stem}.txt" + (f" (section: {frag})" if frag else "")
        return f"- {where} -- {gist}" if gist else f"- {where}"

    def auto_gist(r: Req) -> str:
        stem, _ = target(r)
        conv_body = rendered.get(stem, ("", None))[0] if stem else ""
        g = first_sentence(conv_body)
        return g

    toc = [("strategy", "Strategy"), ("dungeon", "Dungeon and special levels"),
           ("monsters", "Monsters by class letter"), ("objects", "Objects by class"),
           ("mechanics", "Mechanics")]
    L.append("Sections: " + " | ".join(t for _, t in toc))
    L.append("")
    for group, heading in toc:
        reqs = by_group.get(group, [])
        L += [f"## {heading}", ""]
        if group in ("strategy", "dungeon", "mechanics"):
            sections: dict = {}
            for r in reqs:
                sections.setdefault(r.section, []).append(r)
            for sec, items in sections.items():
                L += [f"### {sec}", ""]
                for r in items:
                    stem, frag = target(r)
                    if not stem:
                        continue
                    gist = r.gist or auto_gist(r)
                    # name the entry when the file is really about something else
                    if frag or stem_for(r.label).lower() != stem.lower():
                        gist = f"{r.label}: {gist}" if gist else r.label
                    L.append(line_for(r, gist))
                L.append("")
        elif group == "monsters":
            L += ["Symbol letters as displayed on the map. Stats: level, speed, AC, magic",
                  "resistance, difficulty; attacks; what eating the corpse can convey.", ""]
            for letter in MONSTERS_BY_CLASS:
                shown = "(blank space)" if letter == " " else letter
                L += [f"### {shown} -- {MONSTER_CLASS_NAMES.get(letter, '')}", ""]
                members = [x for x in reqs if x.section == letter]
                for r in sorted(members, key=lambda x: not x.meta.get("class_page")):
                    stem, frag = target(r)
                    if not stem:
                        continue
                    conv = rendered.get(stem, ("", None))[1]
                    if r.meta.get("class_page"):
                        L.append(f"- wiki/{stem}.txt -- class overview")
                        continue
                    ib = infobox_dict(conv) if conv else {}
                    L.append(f"- wiki/{stem}.txt -- " + monster_gist(r.label, ib))
                L.append("")
        else:
            L += ["Object stats: base cost ($), weight, AC, damage (small/large), nutrition;",
                  "'unidentified' is the fixed unidentified name (random appearance = varies per game).", ""]
            for cls, title in OBJECT_SECTION_NAMES.items():
                L += [f"### {title}", ""]
                seen_stems: set = set()
                for r in [x for x in reqs if x.section == cls]:
                    stem, frag = target(r)
                    if not stem:
                        continue
                    conv = rendered.get(stem, ("", None))[1]
                    if r.meta.get("overview"):
                        L.append(f"- wiki/{stem}.txt -- overview: {r.label}")
                        seen_stems.add(stem)
                        continue
                    ib = infobox_dict(conv) if conv else {}
                    if stem in seen_stems or frag:
                        extra = f" (section: {frag})" if frag else ""
                        L.append(f"- wiki/{stem}.txt{extra} -- {object_gist(r.label, {}, r.meta)}")
                    else:
                        L.append(f"- wiki/{stem}.txt -- {object_gist(r.label, ib, r.meta)}")
                    seen_stems.add(stem)
                L.append("")
    return "\n".join(L).rstrip() + "\n"


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-download everything (ignore cache)")
    ap.add_argument("--reconvert", action="store_true",
                    help="only rebuild .txt files and INDEX.md from the cache (no network)")
    ap.add_argument("--only", nargs="+", metavar="TITLE",
                    help="limit to these plan entries (matched by title/label, case-insensitive); "
                         "unknown titles are fetched as extra pages")
    ap.add_argument("--latest", action="store_true", help="use current revisions, not the snapshot")
    ap.add_argument("--as-of", default=DEFAULT_AS_OF, help=f"snapshot timestamp (default {DEFAULT_AS_OF})")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests (default 0.5)")
    ap.add_argument("--list", action="store_true", help="print the page plan and exit")
    ap.add_argument("--no-index", action="store_true", help="don't rewrite INDEX.md")
    ap.add_argument("--prune", action="store_true", help="delete .txt files not in the plan")
    ap.add_argument("--templates-report", action="store_true",
                    help="print unrendered template names (converter maintenance)")
    args = ap.parse_args(argv)

    plan = build_plan()
    full_plan = plan
    if args.only:
        wanted = {t.lower() for t in args.only}
        plan = [r for r in plan if r.label.lower() in wanted
                or any(c.lower() in wanted for c in r.candidates)]
        known = {r.label.lower() for r in plan} | {c.lower() for r in plan for c in r.candidates}
        for t in args.only:
            if t.lower() not in known:
                plan.append(Req(key=f"extra:{t}", candidates=[t], group="extra",
                                section="Extra pages", label=t))
    if args.list:
        for r in plan:
            print(f"{r.group:10s} {r.section[:28]:28s} {r.label:40s} -> {' | '.join(r.candidates)}")
        print(f"{len(plan)} requests", file=sys.stderr)
        return 0

    as_of = None if args.latest else args.as_of
    state = State(CACHE_DIR)
    force = args.force
    if not args.reconvert and state.data.get("pages") and state.data.get("as_of", "unset") != as_of:
        log(f"cache was built with as_of={state.data.get('as_of')}; refetching with as_of={as_of}")
        force = True
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def cached(r: Req) -> bool:
        res = state.resolve.get(r.key)
        if not res or res.get("requested") != r.candidates:
            return False  # never resolved, or the plan changed its candidate titles
        if res.get("missing"):
            return True
        page = state.pages.get(res["current"])
        return bool(page) and state.page_file(page["stem"]).exists()

    need = plan if force else [r for r in plan if not cached(r)]
    fetched: list = []
    http = Http(delay=args.delay)
    if need and not args.reconvert:
        moves = []
        if as_of:
            mpath = CACHE_DIR / "moves.json"
            if mpath.exists() and not force:
                moves = json.loads(mpath.read_text())["moves"]
            else:
                log("fetching page-move log since the snapshot date")
                moves = fetch_moves(http, as_of)
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                mpath.write_text(json.dumps({"as_of": as_of, "moves": moves}, indent=1))
        log(f"resolving {len(need)} requested titles")
        latest = resolve_requests(http, need, state)
        currents = sorted({state.resolve[r.key]["current"] for r in need
                           if not state.resolve[r.key].get("missing")})
        log(f"downloading {len(currents)} pages (snapshot {as_of or 'latest'})")
        state.data["as_of"], state.data["mode"] = as_of, ("latest" if as_of is None else "snapshot")
        fetched = fetch_pages(http, currents, latest, state, as_of=as_of, moves=moves, force=force)
        if as_of:
            fixes = repair_post_snapshot(http, state, plan, moves, as_of)
            if fixes:
                fetched += fetch_pages(http, sorted(fixes), fixes, state, as_of=as_of,
                                       moves=moves, force=force)
        log(f"{len(fetched)} pages downloaded with {http.count} API requests")
        state.save()

    every = full_plan + [r for r in plan if r.group == "extra"]
    referenced = sorted({res["current"] for r in every
                         for res in [state.resolve.get(r.key) or {}]
                         if res.get("current") in state.pages
                         and state.page_file(state.pages[res["current"]]["stem"]).exists()})
    out_stem = assign_output_stems(state, referenced)

    # Aliases: other requested names that land on the same page.
    aliases: dict = {}
    for r in every:
        res = state.resolve.get(r.key) or {}
        page = state.pages.get(res.get("current", ""))
        if not page or res["current"] not in out_stem:
            continue
        name = r.label if not r.meta.get("class_page") else None
        if name and name.lower() != page["title"].lower() and not r.meta.get("overview"):
            frag = res.get("fragment")
            lst = aliases.setdefault(res["current"], [])
            entry = name + (f" (section {frag})" if frag else "")
            if entry.lower() not in (a.lower() for a in lst):
                lst.append(entry)

    # Convert every cached page referenced by the plan.
    if not args.reconvert:
        n_tpl = fetch_templates(http, state, [state.pages[c]["stem"] for c in referenced],
                                as_of=as_of, force=force)
        if n_tpl:
            log(f"{n_tpl} transcluded templates (skill tables) downloaded")
    TEMPLATE_SOURCES.update(load_templates())
    rendered: dict = {}
    unknown = Counter()
    written = 0
    for cur in referenced:
        rec = state.load_page(state.pages[cur]["stem"])
        stem = out_stem[cur]
        text, conv = render_page(rec, aliases.get(cur, []))
        rendered[stem] = (text, conv)
        unknown.update(conv.unknown)
        out = OUT_DIR / f"{stem}.txt"
        if not out.exists() or out.read_text() != text:
            out.write_text(text)
            written += 1
    log(f"{written} .txt files written/updated in {OUT_DIR.relative_to(ROOT)} "
        f"({len(referenced)} pages total)")

    if args.prune:
        keep = {f"{s}.txt" for s in out_stem.values()}
        for f in OUT_DIR.glob("*.txt"):
            if f.name not in keep:
                f.unlink()
                log(f"  pruned {f.name}")
    if not args.no_index and not args.only:
        INDEX_PATH.write_text(build_index(full_plan, state, rendered, out_stem))
        log(f"wrote {INDEX_PATH.relative_to(ROOT)}")

    missing = [r for r in plan if (state.resolve.get(r.key) or {}).get("missing")]
    for r in missing:
        log(f"  MISSING on wiki: {r.label} (tried: {', '.join(r.candidates)})")
    if args.templates_report:
        for name, n in unknown.most_common():
            print(f"{n:6d}  {name}")
    groups = Counter(r.group for r in plan if not (state.resolve.get(r.key) or {}).get("missing"))
    log("requests resolved per group: " + ", ".join(f"{g}={n}" for g, n in sorted(groups.items())))
    size = sum(f.stat().st_size for f in OUT_DIR.glob("*.txt"))
    log(f"knowledge/wiki: {len(list(OUT_DIR.glob('*.txt')))} files, {size / 1e6:.1f} MB; "
        f"{len(missing)} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
