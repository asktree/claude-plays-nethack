# NetHack knowledge base index

Plain-text copies of NetHackWiki pages for NetHack 3.6.x, one file per page in `wiki/`.
Search them with grep, e.g. `grep -ril 'cockatrice' knowledge/wiki` or
`grep -i -A3 'price' knowledge/wiki/Price_identification.txt`.

- Pages are a snapshot of the wiki as of 2026-05-02, before NetHack 5.0.0 (formerly 3.7.0)
  was released; `[NetHack 3.7.0 change, NOT in 3.6.x: ...]` notes describe later versions.
- Each file starts with a header (title, source URL, revision, version tag, license).
  Monster and object pages then list their infobox stats as `key: value` lines.
- `Also covers:` in a header lists other names that redirect to that page.
- Regenerate with `python3 scripts/fetch_wiki.py` (see knowledge/README.md).

Sections: Strategy | Dungeon and special levels | Monsters by class letter | Objects by class | Mechanics

## Strategy

### General strategy (start here)

- wiki/Standard_strategy.txt -- Canonical game plan from turn 1 to ascension, with milestones
- wiki/Game_stages.txt -- Early/mid/late game goals and what to do at each stage
- wiki/Why_do_I_keep_dying?.txt -- Beginner's guide to the most common deaths and how to avoid them
- wiki/Yet_Another_Stupid_Death.txt -- Catalogue of avoidable deaths (YASDs) and their lessons
- wiki/Things_To_Do_If_You're_Going_to_Die_Next_Turn.txt -- Emergency checklist: pray, quaff, zap, Elbereth, escape
- wiki/Player's_misconceptions.txt -- Popular myths about NetHack mechanics, corrected
- wiki/Role_difficulty.txt -- Which roles are easiest; Valkyrie is the easiest to win with
- wiki/Ascension_kit.txt -- The standard set of items/intrinsics you want before the endgame
- wiki/Ascension_run.txt -- Carrying the Amulet up the dungeon to the planes: plan and dangers
- wiki/Escape_item.txt -- Items that get you out of trouble instantly, and when to use them
- wiki/Healing.txt -- Every way to restore hit points, ranked by situation
- wiki/Safe_area.txt -- Making safe spots to rest: Elbereth, scare monster, stairs, closets
- wiki/Movement_tactics.txt -- Positioning: fight in corridors/doorways, never get surrounded
- wiki/Hit_and_run.txt -- Using speed to attack and retreat before monsters can respond
- wiki/Stash.txt -- Where and how to store spare items safely between trips
- wiki/Digging_for_victory.txt -- Descending fast by digging down; when it is and isn't wise
- wiki/Level_teleport.txt -- Level teleportation: sources, control, limits, and safe uses
- wiki/Protection_racket.txt -- Buying cheap AC from temple priests while at low experience level
- wiki/Nurse_dancing.txt -- Raising max HP by letting nurses 'heal' you while unarmed
- wiki/Exercise.txt -- How training strength/dex/con/wis works and what abuses stats
- wiki/Trouble.txt -- Problems prayer can fix (major/minor trouble) and their priority
- wiki/Portal_detection_methods.txt -- Finding magic portals (Quest, Fort Ludios) by messages and tricks
- wiki/Cannibalism.txt -- Eating your own race (dwarves, for a dwarf): -2..-5 Luck and aggravate monster
- wiki/Elbereth.txt -- Engrave Elbereth to scare most monsters; which ignore it; 3.6 erasure rules
- wiki/Engraving.txt -- Engraving mechanics: tools, durability, semi-permanent vs dust

### Valkyrie and dwarf specifics

- wiki/Valkyrie.txt -- Valkyrie role: starting kit, cold res + stealth, speed at XL7, strategy
- wiki/Dwarf_(starting_race).txt -- Dwarven race: infravision, peaceful Mines inhabitants, dwarvish gear
- wiki/Excalibur.txt -- Dip a long sword into a fountain at XL5+ as a lawful to get Excalibur
- wiki/Mjollnir.txt -- Thrown lightning war hammer artifact; Valkyries can catch it on return
- wiki/Valkyrie_quest.txt -- Valkyrie quest: Norn, Lord Surtur, fire giants, the Orb of Fate

### Religion, luck and alignment

- wiki/Prayer.txt -- When praying is safe (timeout, luck, alignment) and what gods fix
- wiki/Prayer_timeout.txt -- How prayer timeout works and how to estimate when you can pray
- wiki/Luck.txt -- Luck mechanics: sources, penalties, timeout, and luckstones
- wiki/Alignment.txt -- Lawful/neutral/chaotic alignment and what depends on it
- wiki/Alignment_record.txt -- Hidden alignment score: what raises/lowers it; needed for prayer
- wiki/Altar.txt -- Altars: BUC-identify by dropping items, alignment, conversion
- wiki/Sacrifice.txt -- Offering fresh corpses at altars for gifts, luck and conversion
- wiki/Crowning.txt -- Becoming your god's champion: resistances, a skill slot, often an artifact weapon
- wiki/God.txt -- The pantheons: each role's lawful/neutral/chaotic gods
- wiki/Anger.txt -- Divine anger: causes, effects, and how to calm your god
- wiki/Sanctuary.txt -- Hostile monsters won't enter a co-aligned temple you're in
- wiki/Aligned_priest.txt -- Temple priests: donate gold for AC protection; don't anger them
- wiki/Intrinsic_protection.txt -- AC bonus from priest donations and divine gifts
- wiki/Protection.txt -- All sources of protection/AC, including buying it from priests
- wiki/Murder.txt -- Killing peaceful @-humans/elves: alignment, luck and telepathy penalties
- wiki/Wide-angle_disintegration_beam.txt -- Angry god's death ray: need reflection or disintegration resistance
- wiki/Altar_farming.txt -- Camping a co-aligned altar, sacrificing for artifact gifts

### Identification, items and shops

- wiki/Identification.txt -- Overview of every way to identify items
- wiki/Price_identification.txt -- Identify items from shop buy/sell prices; price tables
- wiki/Wand.txt (section: Engrave-identification) -- Engrave identification: Identify wands by engraving with them (E) and reading the message
- wiki/Curse-testing.txt -- Learning BUC status: altars, pets stepping on items, other tricks
- wiki/Curse_removal.txt -- All ways to uncurse items (holy water, scroll, prayer)
- wiki/Randomized_appearance.txt -- Which item classes have per-game random appearances
- wiki/Wand_strategy.txt -- Which wands to keep, engrave-test, zap in emergencies
- wiki/Potion_strategy.txt -- What to do with unknown potions; dipping and quaff-testing
- wiki/Scroll_strategy.txt -- Read-testing unknown scrolls safely and in what order
- wiki/Ring_strategy.txt -- Testing unknown rings safely and which rings matter
- wiki/Alchemy.txt -- Mixing potions by dipping; useful recipes and explosion risk
- wiki/Polypiling.txt -- Polymorphing piles of junk items into better ones
- wiki/Charge.txt -- Recharging wands/rings/tools and the explosion risk
- wiki/Shop.txt -- Shop types, shopkeeper behavior, buying and selling
- wiki/Shopkeeper.txt -- Shopkeeper stats, what angers them, and why not to fight one
- wiki/Stealing_from_shops.txt -- Techniques to rob shops and the consequences
- wiki/Usage_fee.txt -- What shopkeepers charge for using unpaid items
- wiki/Container.txt -- Boxes, chests and bags: looting, #force, and bag rules
- wiki/Bag_of_holding.txt -- Weight-reducing bag; never put a wand of cancellation or BoH inside
- wiki/Unicorn_horn.txt -- Apply to cure confusion/stun/blindness/sickness; top-priority tool
- wiki/Digging.txt -- Digging through walls and floors; where you can't dig
- wiki/Luckstone.txt -- Gray stone that stops luck timing out; the Mines' End prize
- wiki/Unicorn.txt -- Throw gems to co-aligned unicorns for luck; never kill co-aligned ones

### Pets

- wiki/Pet.txt -- Pet behavior, feeding, keeping it alive, and stealing via pets
- wiki/Domestic_animal.txt -- Dogs, cats, horses: taming by throwing food
- wiki/Taming.txt -- Ways to tame monsters (food, scroll/spell of taming, magic harp)
- wiki/Treat.txt -- Which foods pets eat and consider treats
- wiki/Leash.txt -- Keeping pets next to you across levels
- wiki/Riding.txt -- Riding a saddled steed: skill, benefits, risks

### Food and corpses

- wiki/Comestible.txt -- All food items: nutrition, weight, and eating time
- wiki/Corpse.txt -- Which corpses are safe, dangerous, or give intrinsics; rotting
- wiki/Nutrition.txt -- Hunger states, nutrition values, fainting and starvation
- wiki/Tin.txt -- Tins: safe eating of dangerous corpses, opening methods
- wiki/Lichen.txt -- F lichen: sticky but harmless; corpse never rots
- wiki/Lizard.txt -- Lizard corpse never rots; cures stoning; eat to reduce confusion

### Wishes, genocide and polymorph

- wiki/Wish.txt -- What to wish for, exact wish syntax, and sources of wishes
- wiki/Wresting.txt -- Getting one last zap out of an empty (x:0) wand
- wiki/Genocide.txt -- Genocide mechanics and recommended targets (L, ;, mind flayers)
- wiki/Polymorph.txt -- Polymorphing self/objects/monsters: risks and good forms
- wiki/Cancellation.txt -- Effects of cancellation on monsters, items and you

### Conduct

- wiki/Conduct.txt -- Voluntary challenges tracked by the game (#conduct)

### Roles, races and quests (for other random characters)

- wiki/Role.txt -- Overview of the 13 roles
- wiki/Race.txt -- Overview of the 5 player races
- wiki/Archeologist.txt -- Fast, stealthy digger with pick-axe and tinning kit; weak early fighter
- wiki/Barbarian.txt -- Strong melee role with poison resistance and a two-handed sword or axe
- wiki/Caveman.txt -- Tough melee role with club and sling; slow start
- wiki/Healer.txt -- Weak fighter: stethoscope, wand of sleep, healing spells, poison resistance
- wiki/Knight.txt -- Lance and pony; strict code of conduct (no attacking fleeing monsters)
- wiki/Monk.txt -- Martial arts, fast, many intrinsics; no body armor or weapons, vegetarian
- wiki/Priest.txt -- Sees blessed/cursed status of all items; mace and clerical spells
- wiki/Ranger.txt -- Bow with many arrows, multishot, cloak of displacement
- wiki/Rogue.txt -- Throws daggers in volleys (multishot); starts with lock pick and potion of sickness
- wiki/Samurai.txt -- Strong, fast lawful fighter with katana and bow (yumi)
- wiki/Tourist.txt -- Hardest role: weak, lots of gold, expensive camera, magic mapping scrolls
- wiki/Wizard.txt -- Spellcaster with force bolt, cloak of magic resistance, random wand; weak melee
- wiki/Human_(starting_race).txt -- Humans: no infravision; available to every role
- wiki/Elf_(starting_race).txt -- Elves: infravision, sleep resistance, elven gear; always chaotic
- wiki/Gnome_(starting_race).txt -- Gnomes: infravision, peaceful Gnomish Mines; always neutral
- wiki/Orc_(starting_race).txt -- Orcs: infravision, poison resistance, may eat most corpses; always chaotic
- wiki/Archeologist_quest.txt -- The Archeologist quest pits you against the Minion of Huhetotl for The Orb of Detection
- wiki/Barbarian_quest.txt -- The Barbarian quest pits you against Thoth Amon for The Heart of Ahriman
- wiki/Caveman_quest.txt -- The Caveman quest sees you fighting the Chromatic Dragon for The Sceptre of Might
- wiki/Healer_quest.txt -- The Healer quest pits a Healer hero against the Cyclops for the Bell of Opening ...
- wiki/Knight_quest.txt -- The Knight quest sees you fighting Ixoth for The Magic Mirror of Merlin
- wiki/Monk_quest.txt -- In the Monk quest, you fight Master Kaen for The Eyes of the Overworld
- wiki/Priest_quest.txt -- The Priest quest sees you fighting Nalzok for The Mitre of Holiness
- wiki/Ranger_quest.txt -- The Ranger quest sees you fighting Scorpius for The Longbow of Diana
- wiki/Rogue_quest.txt -- The Rogue quest sees you fighting the Master Assassin for The Master Key of Thievery
- wiki/Samurai_quest.txt -- The Samurai quest sees a Samurai hero fighting Ashikaga Takauji for the Bell of Opening ...
- wiki/Tourist_quest.txt -- The Tourist quest pits a Tourist hero against the Master of Thieves for the Bell ...
- wiki/Wizard_quest.txt -- The Wizard quest sees you fighting the Dark One for The Eye of the Aethiopica

## Dungeon and special levels

### Dungeon structure

- wiki/Mazes_of_Menace.txt -- The main dungeon: overall layout and branch locations
- wiki/Dungeons_of_Doom.txt -- The main dungeon branch from DL1 down to Medusa and the Castle
- wiki/Overview.txt -- Dungeon overview: Ctrl-O / #overview: the in-game list of visited levels
- wiki/Branch.txt -- All dungeon branches and where their entrances are
- wiki/Dungeon_level.txt -- How dungeon depth works; level difficulty and generation
- wiki/Special_level.txt -- List of all special (hand-designed) levels
- wiki/Staircase.txt -- Up/down stairs and branch stairs
- wiki/Magic_portal.txt -- Portals to the Quest, Fort Ludios and the Planes
- wiki/Maze.txt -- Maze filler levels below Medusa and in Gehennom

### Early special levels and branches

- wiki/Gnomish_Mines.txt -- Mines branch (entrance DL2-4): gnomes/dwarves, peaceful for dwarves
- wiki/Minetown.txt -- Mines town (3-4 levels in): temple, shops, altar; all variants
- wiki/Mines'_End.txt -- Bottom of the Mines: three variants, each hiding a luckstone
- wiki/Oracle_(level).txt -- Oracle level (DL5-9): centaurs, fountains, consultations
- wiki/Oracle_(monster).txt -- The Oracle: buy minor/major consultations; don't attack
- wiki/Big_Room.txt -- Optional huge open room (DL10-12): many monsters, no cover
- wiki/Rogue_level.txt -- Tribute level (DL15-18) drawn with old Rogue-style symbols
- wiki/Vault.txt -- Closed 2x2 gold rooms; the guard, and how to get out
- wiki/Closet.txt -- 1-square niches; often hold stairs or trapdoors

### Sokoban (maps + solutions)

- wiki/Sokoban.txt -- Sokoban branch rules: no diagonal boulder pushes, luck penalties, prizes
- wiki/Sokoban_Level_1a.txt -- First Sokoban level, variant a: map and step-by-step solution
- wiki/Sokoban_Level_1b.txt -- First Sokoban level, variant b: map and step-by-step solution
- wiki/Sokoban_Level_2a.txt -- Second level, variant a: map and solution
- wiki/Sokoban_Level_2b.txt -- Second level, variant b: map and solution
- wiki/Sokoban_Level_3a.txt -- Third level, variant a: map and solution
- wiki/Sokoban_Level_3b.txt -- Third level, variant b: map and solution
- wiki/Sokoban_Level_4a.txt -- Top level, variant a: map + solution; zoo guards prize (bag of holding or amulet of reflection, 50/50)
- wiki/Sokoban_Level_4b.txt -- Top level, variant b: map + solution; zoo guards prize (bag of holding or amulet of reflection, 50/50)

### The Quest

- wiki/Quest.txt -- Quest rules: XL14 entry requirement, leader, nemesis, artifact
- wiki/Valkyrie_quest.txt -- Valkyrie quest levels (home/locate/goal), Norn and Lord Surtur
- wiki/Quest_artifact.txt -- Quest artifacts and their powers
- wiki/Lord_Surtur.txt -- Valkyrie quest nemesis: fire giant king; fire resistance essential
- wiki/Norn.txt -- Valkyrie quest leader
- wiki/The_Orb_of_Fate.txt -- Valkyrie quest artifact: level teleport, half damage when carried

### Mid-game levels

- wiki/Fort_Ludios.txt -- Optional portal branch: vault fortress full of soldiers and dragons
- wiki/Medusa's_Island.txt -- Medusa's level: need reflection or blindness and a way to cross water
- wiki/Castle.txt -- Castle: drawbridge (passtune), wand of wishing, trapdoors to Gehennom
- wiki/Wand_of_wishing.txt -- The Castle's wand of wishing; how to use and wrest it
- wiki/Drawbridge.txt -- Opening/destroying the Castle drawbridge; passtune; force bolt/striking
- wiki/Passtune.txt -- 5-note tune that opens the drawbridge; learn it via Mastermind game

### Gehennom

- wiki/Gehennom.txt -- Gehennom overview: mazes, demon lairs, fire and no-prayer hazards
- wiki/Valley_of_the_Dead.txt -- First Gehennom level: undead, temple of Moloch, graveyards
- wiki/Juiblex's_swamp.txt -- Juiblex's lair (Gehennom 4-7): water everywhere, no-teleport; his engulf causes sickness
- wiki/Orcus-town.txt -- Orcus Town: ruined Minetown full of undead, Orcus with wand of death
- wiki/Asmodeus'_Lair.txt -- Asmodeus' lair: no-teleport level; he casts cone of cold, so bring cold resistance
- wiki/Baalzebub's_Lair.txt -- Baalzebub's lair: no-teleport, fly-shaped maze around the demon lord's chamber
- wiki/Vlad's_Tower.txt -- Vlad's Tower branch: Vlad the Impaler holds the Candelabrum
- wiki/Wizard's_Tower.txt -- Wizard's Tower: the Wizard of Yendor holds the Book of the Dead
- wiki/Fake_Wizard's_Tower.txt -- Decoy towers with portals; one leads to the real tower
- wiki/Vibrating_square.txt -- Target square for the invocation ritual at the bottom of Gehennom
- wiki/Invocation_ritual.txt -- Bell, Candelabrum (7 candles lit), Book: opening the Sanctum stairs
- wiki/Moloch's_Sanctum.txt -- Final Gehennom level: high priest of Moloch guards the Amulet
- wiki/Gehennom_mapping.txt -- Mapping Gehennom mazes efficiently to find the stairs
- wiki/Mysterious_force.txt -- Pushes you back down while climbing with the Amulet

### Endgame

- wiki/End_Game.txt -- Overview of the Elemental Planes and the Astral Plane
- wiki/Elemental_Planes.txt -- The four elemental planes and how to find each exit portal
- wiki/Plane_of_Earth.txt -- Dig through rock to the portal; earth elementals, xorns
- wiki/Plane_of_Air.txt -- Open air with drifting clouds, air elementals and lightning; portal on the right side
- wiki/Plane_of_Fire.txt -- Fire traps, lava and fire elementals; fire resistance is essential
- wiki/Plane_of_Water.txt -- All water except moving air bubbles; the portal drifts inside a bubble
- wiki/Astral_Plane.txt -- Find the correct high altar among three and offer the Amulet
- wiki/Amulet_of_Yendor.txt -- The goal item: fake vs real, and effects of carrying it
- wiki/Bell_of_Opening.txt -- Invocation item from the Quest nemesis
- wiki/Candelabrum_of_Invocation.txt -- Invocation item from Vlad; needs 7 candles attached
- wiki/Book_of_the_Dead.txt -- Invocation item from the Wizard of Yendor
- wiki/Ascension.txt -- Winning the game: offering the Amulet on the right high altar
- wiki/Riders.txt -- Death, Famine, Pestilence on the Astral Plane; revive after death

### Special rooms

- wiki/Throne_room.txt -- Throne room full of monsters around a throne
- wiki/Beehive.txt -- Killer bees and royal jelly
- wiki/Barracks.txt -- Soldiers in a barracks room
- wiki/Zoo.txt -- Room of sleeping monsters on gold
- wiki/Graveyard.txt -- Undead, graves; digging up graves
- wiki/Leprechaun_hall.txt -- Leprechauns and gold
- wiki/Cockatrice_nest.txt -- Cockatrices and statues with items
- wiki/Anthole.txt -- Room of ants
- wiki/Temple.txt -- Temples and their priests; buying protection

### Dungeon features

- wiki/Dungeon_feature.txt -- Overview of all dungeon features
- wiki/Fountain.txt -- Quaffing/dipping effects, Excalibur, wishes, water moccasins
- wiki/Sink.txt -- Kicking and dropping rings into sinks to identify them
- wiki/Throne.txt -- Sitting on thrones: wishes, genocide, identification, risks
- wiki/Headstone.txt -- Graves: engraving, digging up (with alignment penalty)
- wiki/Tree.txt -- Trees: kick for fruit, chop down with an axe; they block movement
- wiki/Door.txt -- Doors: opening, kicking, locks, shop doors, no diagonal moves
- wiki/Iron_bars.txt -- Iron bars: passing items/monsters through
- wiki/Moat.txt -- Water in moats: drowning, crossing
- wiki/Lava.txt -- Lava: instant death without fire resistance; sinking kills even with it
- wiki/Water.txt -- All forms of water: potions, fountains, pools, moats, the Plane of Water
- wiki/Wet.txt -- Water damage to items: rusting, diluting potions, blanking scrolls
- wiki/Ladder.txt -- Ladders in Vlad's Tower and elsewhere
- wiki/Ice.txt -- Ice: slipping, melting, digging holes
- wiki/Bones.txt -- Bones files: ghost of a dead player and their cursed items

### Traps

- wiki/Trap.txt -- All trap types, how to detect and avoid them
- wiki/Anti-magic_field.txt -- Drains power (Pw); with magic resistance it drains HP instead
- wiki/Arrow_and_dart_trap.txt -- Arrow trap: Shoots arrows at you; can be disarmed to collect the arrows
- wiki/Arrow_and_dart_trap.txt -- Dart trap: Shoots darts that may be poisoned; poison resistance matters
- wiki/Beartrap.txt -- Holds you in place for several turns; can be disarmed and reused
- wiki/Container_trap.txt -- Trapped boxes/chests: explosions, poison needles, gas clouds, shocks
- wiki/Falling_rock_trap.txt -- Drops a rock on your head; a hard helmet reduces the damage
- wiki/Fire_trap.txt -- Burns you and your items and melts ice; fire resistance helps
- wiki/Hole.txt -- Always-visible hole in the floor; you fall to the next level
- wiki/Land_mine.txt -- Explodes: damage, wounded legs, leaves a pit; can be disarmed
- wiki/Level_teleporter.txt -- Sends you to a random level; magic resistance blocks it
- wiki/Magic_trap.txt -- Random magical effects: summoned monsters, blinding flash, noises, rare boons
- wiki/Pit.txt -- You fall in and spend turns climbing out; beware fighting from inside
- wiki/Spiked_pit.txt -- A pit with poisoned spikes
- wiki/Polymorph_trap.txt -- Polymorphs you (DL8+) unless you have magic resistance or unchanging
- wiki/Rolling_boulder_trap.txt -- Launches a boulder that rolls across the trap square
- wiki/Rust_trap.txt -- Sprays water: rusts iron armor/weapons and wets items
- wiki/Sleeping_gas_trap.txt -- Puts you to sleep unless you are sleep resistant
- wiki/Squeaky_board.txt -- Wakes nearby monsters; otherwise harmless
- wiki/Statue_trap.txt -- A statue that comes to life when you approach or search next to it
- wiki/Teleportation_trap.txt -- Teleports you within the level; magic resistance blocks it
- wiki/Trap_door.txt -- Drops you one or more levels down
- wiki/Web.txt -- Entangles you; strong heroes tear free; home of giant spiders

## Monsters by class letter

Symbol letters as displayed on the map. Stats: level, speed, AC, magic
resistance, difficulty; attacks; what eating the corpse can convey.

### a -- ants and other insects

- wiki/Ant_or_other_insect.txt -- class overview
- wiki/Giant_ant.txt -- giant ant: lvl 2, spd 18, AC 3, MR 0, diff 4; attacks: Bite 1d4 physical
- wiki/Killer_bee.txt -- killer bee: lvl 1, spd 18, AC -1, MR 0, diff 5; attacks: Sting 1d3 poison (strength); eating conveys: Poison resistance (30%)
- wiki/Soldier_ant.txt -- soldier ant: lvl 3, spd 18, AC 3, MR 0, diff 6; attacks: Bite 2d4 physical, Sting 3d4 poison (strength); eating conveys: Poison resistance (20%)
- wiki/Fire_ant.txt -- fire ant: lvl 3, spd 18, AC 3, MR 10, diff 6; attacks: Bite 2d4 physical, bite 2d4 fire; eating conveys: fire resistance (20%)
- wiki/Giant_beetle.txt -- giant beetle: lvl 5, spd 6, AC 4, MR 0, diff 6; attacks: Bite 3d6 physical; eating conveys: Poison resistance (33%)
- wiki/Queen_bee.txt -- queen bee: lvl 9, spd 24, AC -4, MR 0, diff 12; attacks: sting 1d8 poison (strength); eating conveys: Poison resistance (60%)

### b -- blobs

- wiki/Blob.txt -- class overview
- wiki/Acid_blob.txt -- acid blob: lvl 1, spd 3, AC 8, MR 0, diff 2; attacks: Passive 1d8 acid; eating conveys: Cures stoning
- wiki/Quivering_blob.txt -- quivering blob: lvl 5, spd 1, AC 8, MR 0, diff 6; attacks: Touch 1d8; eating conveys: poison (33%)
- wiki/Gelatinous_cube.txt -- gelatinous cube: lvl 6, spd 6, AC 8, MR 0, diff 8; attacks: Touch 2d4 paralysis, passive 1d4 paralysis; eating conveys: fire resistance (10%), cold resistance (10%), shock resistance (10%), sleep resistance (10%)

### c -- cockatrices

- wiki/Cockatrice_(monster_class).txt -- class overview
- wiki/Chickatrice.txt -- chickatrice: lvl 4, spd 4, AC 8, MR 30, diff 7; attacks: Bite 1d2 physical, touch 0d0 stoning, passive 0d0 stoning; eating conveys: poison resistance (27%)
- wiki/Cockatrice.txt -- cockatrice: lvl 5, spd 6, AC 6, MR 30, diff 8; attacks: Bite 1d3 physical, touch 0d0 stoning, passive 0d0 stoning; eating conveys: poison resistance (33%)
- wiki/Pyrolisk.txt -- pyrolisk: lvl 6, spd 6, AC 6, MR 30, diff 8; attacks: Gaze 2d6 fire; eating conveys: Fire resistance (20%), poison resistance (20%)

### d -- dogs and other canines

- wiki/Canine.txt -- class overview
- wiki/Jackal.txt -- jackal: lvl 0, spd 12, AC 7, MR 0, diff 1; attacks: Bite 1d2 physical
- wiki/Fox.txt -- fox: lvl 0, spd 15, AC 7, MR 0, diff 1; attacks: Bite 1d3 physical
- wiki/Coyote.txt -- coyote: lvl 1, spd 12, AC 7, MR 0, diff 2; attacks: Bite 1d4 physical
- wiki/Werejackal.txt -- werejackal: lvl 2, spd 12, AC 10, MR 10, diff 3; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Little_dog.txt -- little dog: lvl 2, spd 18, AC 6, MR 0, diff 3; attacks: Bite 1d6 physical; eating conveys: grants aggravate monster
- wiki/Dingo.txt -- dingo: lvl 4, spd 16, AC 5, MR 0, diff 5; attacks: Bite 1d6 physical
- wiki/Dog.txt -- dog: lvl 4, spd 16, AC 5, MR 0, diff 5; attacks: Bite 1d6 physical; eating conveys: grants aggravate monster
- wiki/Large_dog.txt -- large dog: lvl 6, spd 15, AC 4, MR 0, diff 7; attacks: Bite 2d4 physical; eating conveys: grants aggravate monster
- wiki/Wolf.txt -- wolf: lvl 5, spd 12, AC 4, MR 0, diff 6; attacks: Bite 2d4 physical
- wiki/Werewolf.txt -- werewolf: lvl 5, spd 12, AC 10, MR 20, diff 6; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Winter_wolf_cub.txt -- winter wolf cub: lvl 5, spd 12, AC 4, MR 0, diff 7; attacks: Bite 1d8 physical, breath weapon 1d8 cold; eating conveys: cold resistance (33%)
- wiki/Warg.txt -- warg: lvl 7, spd 12, AC 4, MR 0, diff 8; attacks: Bite 2d6 physical
- wiki/Winter_wolf.txt -- winter wolf: lvl 7, spd 12, AC 4, MR 20, diff 9; attacks: Bite 2d6 physical, breath weapon 2d6 cold; eating conveys: cold resistance (47%)
- wiki/Hell_hound_pup.txt -- hell hound pup: lvl 7, spd 12, AC 4, MR 20, diff 9; attacks: Bite 2d6 physical, breath weapon 2d6 fire; eating conveys: fire resistance (47%)
- wiki/Hell_hound.txt -- hell hound: lvl 12, spd 14, AC 2, MR 20, diff 14; attacks: Bite 3d6 physical, breath weapon 3d6 fire; eating conveys: fire resistance (80%)

### e -- floating eyes and spheres

- wiki/Eye_or_sphere.txt -- class overview
- wiki/Gas_spore.txt -- gas spore: lvl 1, spd 3, AC 10, MR 0, diff 2; attacks: On-death explosion 4d6 physical
- wiki/Floating_eye.txt -- floating eye: lvl 2, spd 1, AC 9, MR 10, diff 3; attacks: Passive gaze 0d70 paralysis; eating conveys: Telepathy (100%)
- wiki/Freezing_sphere.txt -- freezing sphere: lvl 6, spd 13, AC 4, MR 0, diff 8; attacks: Explode 4d6 cold; eating conveys: cold resistance
- wiki/Flaming_sphere.txt -- flaming sphere: lvl 6, spd 13, AC 4, MR 0, diff 8; attacks: Explode 4d6 fire; eating conveys: fire resistance
- wiki/Shocking_sphere.txt -- shocking sphere: lvl 6, spd 13, AC 4, MR 0, diff 8; attacks: Explode 4d6 shock; eating conveys: shock resistance

### f -- cats and other felines

- wiki/Feline.txt -- class overview
- wiki/Kitten.txt -- kitten: lvl 2, spd 18, AC 6, MR 0, diff 3; attacks: Bite 1d6 physical; eating conveys: Intrinsic aggravate monster
- wiki/Housecat.txt -- housecat: lvl 4, spd 16, AC 5, MR 0, diff 5; attacks: Bite 1d6 physical; eating conveys: Intrinsic aggravate monster
- wiki/Jaguar.txt -- jaguar: lvl 4, spd 15, AC 6, MR 0, diff 6; attacks: Claw 1d4 physical, Claw 1d4 physical, Bite 1d8 physical
- wiki/Lynx.txt -- lynx: lvl 5, spd 15, AC 6, MR 0, diff 7; attacks: Claw 1d4 physical, Claw 1d4 physical, Bite 1d10 physical
- wiki/Panther.txt -- panther: lvl 5, spd 15, AC 6, MR 0, diff 7; attacks: Claw 1d4 physical, Claw 1d4 physical, Bite 1d10 physical
- wiki/Large_cat.txt -- large cat: lvl 6, spd 15, AC 4, MR 0, diff 7; attacks: Bite 2d4 physical; eating conveys: Intrinsic aggravate monster
- wiki/Tiger.txt -- tiger: lvl 6, spd 12, AC 6, MR 0, diff 8; attacks: Claw 2d4 physical, Claw 2d4 physical, Bite 1d10 physical

### g -- gremlins and gargoyles

- wiki/Gremlin_(monster_class).txt -- class overview
- wiki/Gremlin.txt -- gremlin: lvl 5, spd 12, AC 2, MR 25, diff 8; attacks: Claw 1d6 physical, claw 1d6 physical, bite 1d4 physical, claw 0d0 intrinsic theft; eating conveys: poison resistance (33%)
- wiki/Gargoyle.txt -- gargoyle: lvl 6, spd 10, AC -4, MR 0, diff 8; attacks: Claw 2d6 physical, claw 2d6 physical, bite 2d4 physical
- wiki/Winged_gargoyle.txt -- winged gargoyle: lvl 9, spd 15, AC −2, MR 0, diff 11; attacks: Claw 3d6 physical, claw 3d6 physical, bite 3d4 physical

### h -- dwarves, hobbits, mind flayers (humanoids)

- wiki/Humanoid_(monster_class).txt -- class overview
- wiki/Hobbit.txt -- hobbit: lvl 1, spd 9, AC 10, MR 0, diff 2; attacks: Weapon 1d6 physical
- wiki/Dwarf_(monster).txt -- dwarf: lvl 2, spd 6, AC 10, MR 10, diff 4; attacks: Weapon 1d8 physical
- wiki/Bugbear.txt -- bugbear: lvl 3, spd 9, AC 5, MR 0, diff 5; attacks: Weapon 2d4 physical
- wiki/Dwarf_lord.txt -- dwarf lord: lvl 4, spd 6, AC 10, MR 10, diff 6; attacks: Weapon 2d4 physical, weapon 2d4 physical
- wiki/Dwarf_king.txt -- dwarf king: lvl 6, spd 6, AC 10, MR 20, diff 8; attacks: Weapon 2d6 physical, weapon 2d6 physical
- wiki/Mind_flayer.txt -- mind flayer: lvl 9, spd 12, AC 5, MR 90, diff 13; attacks: Weapon 1d4 physical, Tentacle 2d1 int drain, Tentacle 2d1 int drain, Tentacle 2d1 int drain; eating conveys: telepathy (50%) or +1 intelligence (50%)
- wiki/Master_mind_flayer.txt -- master mind flayer: lvl 13, spd 12, AC 0, MR 90, diff 19; attacks: Weapon 1d8, Tentacle 2d1 int drain, Tentacle 2d1 int drain, Tentacle 2d1 int drain, Tentacle 2d1 int drain, Tentacle 2d1 int drain; eating conveys: Telepathy (5...

### i -- imps and minor demons

- wiki/Imp_or_minor_demon.txt -- class overview
- wiki/Manes.txt -- manes: lvl 1, spd 3, AC 7, MR 0, diff 3; attacks: Claw 1d3, claw 1d3, bite 1d4
- wiki/Homunculus.txt -- homunculus: lvl 2, spd 12, AC 6, MR 10, diff 3; attacks: Bite 1d3 sleep; eating conveys: poison (6%), sleep (6%)
- wiki/Imp.txt -- imp: lvl 3, spd 12, AC 2, MR 20, diff 4; attacks: Claw 1d4 physical
- wiki/Lemure.txt -- lemure: lvl 3, spd 3, AC 7, MR 0, diff 5; attacks: Claw 1d3 physical; eating conveys: Sleep resistance
- wiki/Quasit.txt -- quasit: lvl 3, spd 15, AC 2, MR 20, diff 7; attacks: Claw 1d2 poisonous (dexterity), claw 1d2 poisonous (dexterity), bite 1d4 physical; eating conveys: Poison (20%)
- wiki/Tengu.txt -- tengu: lvl 6, spd 13, AC 5, MR 30, diff 7; attacks: Bite 1d7 physical; eating conveys: Poison resistance (13%), teleport control (17%), causes teleportitis (20%)

### j -- jellies

- wiki/Jelly.txt -- class overview
- wiki/Blue_jelly.txt -- blue jelly: lvl 4, spd 0, AC 8, MR 10, diff 5; attacks: Passive 0d6 cold; eating conveys: Cold (13%), poison (13%)
- wiki/Spotted_jelly.txt -- spotted jelly: lvl 5, spd 0, AC 8, MR 10, diff 6; attacks: Passive 0d6 acid
- wiki/Ochre_jelly.txt -- ochre jelly: lvl 6, spd 3, AC 8, MR 20, diff 8; attacks: Engulf 3d6 acid, passive 3d6 acid

### k -- kobolds

- wiki/Kobold_(monster_class).txt -- class overview
- wiki/Kobold.txt -- kobold: lvl 0, spd 6, AC 10, MR 0, diff 1; attacks: Weapon 1d4
- wiki/Large_kobold.txt -- large kobold: lvl 1, spd 6, AC 10, MR 0, diff 2; attacks: Weapon 1d6
- wiki/Kobold_lord.txt -- kobold lord: lvl 2, spd 6, AC 10, MR 0, diff 3; attacks: Weapon 2d4
- wiki/Kobold_shaman.txt -- kobold shaman: lvl 2, spd 6, AC 6, MR 10, diff 4; attacks: Spell-casting 0d0 mage

### l -- leprechaun

- wiki/Leprechaun_(monster_class).txt -- class overview
- wiki/Leprechaun.txt -- leprechaun: lvl 5, spd 15, AC 8, MR 20, diff 4; attacks: Claw 1d2 steal gold; eating conveys: Causes teleportitis (50%)

### m -- mimics

- wiki/Mimic.txt -- class overview
- wiki/Small_mimic.txt -- small mimic: lvl 7, spd 3, AC 7, MR 0, diff 8; attacks: Claw 3d4 physical
- wiki/Large_mimic.txt -- large mimic: lvl 8, spd 3, AC 7, MR 10, diff 9; attacks: Claw 3d4 sticky
- wiki/Giant_mimic.txt -- giant mimic: lvl 9, spd 3, AC 7, MR 20, diff 11; attacks: Claw 3d4 sticky, claw 3d6 sticky

### n -- nymphs

- wiki/Nymph_(monster_class).txt -- class overview
- wiki/Wood_nymph.txt -- wood nymph: lvl 3, spd 12, AC 9, MR 20, diff 5; attacks: Claw 0d0 item theft, Claw 0d0 seduction theft; eating conveys: Causes teleportitis (30%)
- wiki/Water_nymph.txt -- water nymph: lvl 3, spd 12, AC 9, MR 20, diff 5; attacks: Claw 0d0 item theft, claw 0d0 seduction theft; eating conveys: Causes teleportitis (30%)
- wiki/Mountain_nymph.txt -- mountain nymph: lvl 3, spd 12, AC 9, MR 20, diff 5; attacks: Claw 0d0 item theft, Claw 0d0 seduction theft; eating conveys: Causes teleportitis (30%)

### o -- orcs

- wiki/Orc_(monster_class).txt -- class overview
- wiki/Goblin.txt -- goblin: lvl 0, spd 9, AC 10, MR 0, diff 1; attacks: Weapon 1d4
- wiki/Hobgoblin.txt -- hobgoblin: lvl 1, spd 9, AC 10, MR 0, diff 3; attacks: Weapon 1d6
- wiki/Orc_(monster).txt -- orc: lvl 1, spd 9, AC 10, MR 0, diff 3; attacks: Weapon 1d8
- wiki/Hill_orc.txt -- hill orc: lvl 2, spd 9, AC 10, MR 0, diff 4; attacks: Weapon 1d6
- wiki/Mordor_orc.txt -- Mordor orc: lvl 3, spd 5, AC 10, MR 0, diff 5; attacks: Weapon 1d6
- wiki/Uruk-hai.txt -- Uruk-hai: lvl 3, spd 7, AC 10, MR 0, diff 5; attacks: Weapon 1d8
- wiki/Orc_shaman.txt -- orc shaman: lvl 3, spd 9, AC 5, MR 10, diff 5; attacks: Spell-casting 0d0 mage
- wiki/Orc-captain.txt -- orc-captain: lvl 5, spd 5, AC 10, MR 0, diff 7; attacks: Weapon 2d4 physical, weapon 2d4 physical

### p -- piercers

- wiki/Piercer.txt -- class overview
- wiki/Piercer.txt -- rock piercer: lvl 3, spd 1, AC 3, MR 0, diff 4; attacks: Bite 2d6
- wiki/Piercer.txt -- iron piercer: lvl 3, spd 1, AC 3, MR 0, diff 4; attacks: Bite 2d6
- wiki/Piercer.txt -- glass piercer: lvl 3, spd 1, AC 3, MR 0, diff 4; attacks: Bite 2d6

### q -- quadrupeds

- wiki/Quadruped.txt -- class overview
- wiki/Rothe.txt -- rothe: lvl 2, spd 9, AC 7, MR 0, diff 4; attacks: Claw 1d3 physical, Bite 1d3 physical, Bite 1d8 physical
- wiki/Mumak.txt -- mumak: lvl 5, spd 9, AC 0, MR 0, diff 7; attacks: Butt 4d12 physical, Bite 2d6 physical
- wiki/Leocrotta.txt -- leocrotta: lvl 6, spd 18, AC 4, MR 10, diff 8; attacks: Claw 2d6 physical, Bite 2d6 physical, Claw 2d6 physical
- wiki/Wumpus.txt -- wumpus: lvl 8, spd 3, AC 2, MR 10, diff 9; attacks: Bite 3d6 physical
- wiki/Titanothere.txt -- titanothere: lvl 12, spd 12, AC 6, MR 0, diff 13; attacks: Claw 2d8 physical
- wiki/Baluchitherium.txt -- baluchitherium: lvl 14, spd 12, AC 5, MR 0, diff 15; attacks: Claw 5d4 physical, Claw 5d4 physical
- wiki/Mastodon.txt -- mastodon: lvl 20, spd 12, AC 5, MR 0, diff 22; attacks: Butt 4d8 physical, Butt 4d8 physical

### r -- rats and rodents

- wiki/Rodent.txt -- class overview
- wiki/Sewer_rat.txt -- sewer rat: lvl 0, spd 12, AC 7, MR 0, diff 1; attacks: Bite 1d3
- wiki/Giant_rat.txt -- giant rat: lvl 1, spd 10, AC 7, MR 0, diff 2; attacks: Bite 1d3
- wiki/Rabid_rat.txt -- rabid rat: lvl 2, spd 12, AC 6, MR 0, diff 4; attacks: Bite 2d4 poisonous (constitution)
- wiki/Wererat.txt -- wererat: lvl 2, spd 12, AC 10, MR 10, diff 3; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Rock_mole.txt -- rock mole: lvl 3, spd 3, AC 0, MR 20, diff 4; attacks: Bite 1d6
- wiki/Woodchuck.txt -- woodchuck: lvl 3, spd 3, AC 0, MR 20, diff 4; attacks: Bite 1d6

### s -- spiders and centipedes

- wiki/Arachnid_or_centipede.txt -- class overview
- wiki/Cave_spider.txt -- cave spider: lvl 1, spd 12, AC 3, MR 0, diff 3; attacks: Bite 1d2 physical; eating conveys: Poison resistance (7%)
- wiki/Centipede.txt -- centipede: lvl 2, spd 4, AC 3, MR 0, diff 4; attacks: Bite 1d3 poisonous (drains strength); eating conveys: poison resistance (13%)
- wiki/Giant_spider.txt -- giant spider: lvl 5, spd 15, AC 4, MR 0, diff 7; attacks: Bite 2d4 poison (strength); eating conveys: poison resistance (33%)
- wiki/Scorpion.txt -- scorpion: lvl 5, spd 15, AC 3, MR 0, diff 8; attacks: Claw 1d2 physical, Claw 1d2 physical, sting 1d4 poison (strength); eating conveys: poison resistance (50%)
- wiki/Scorpius.txt -- Scorpius: lvl 15, spd 12, AC 10, MR 0, diff 17; attacks: Claw 2d6, claw quest-artifact-stealing 2d6, sting sickness 1d4; eating conveys: Poison (100%)

### t -- trappers and lurkers above

- wiki/Trapper_or_lurker_above.txt -- class overview
- wiki/Lurker_above.txt -- lurker above: lvl 10, spd 3, AC 3, MR 0, diff 12; attacks: Engulfing digestion 1d8
- wiki/Trapper.txt -- trapper: lvl 12, spd 3, AC 3, MR 0, diff 14; attacks: Engulfing digestion 1d10

### u -- horses and unicorns

- wiki/Unicorn_or_horse.txt -- class overview
- wiki/Pony.txt -- pony: lvl 3, spd 16, AC 6, MR 0, diff 4; attacks: Kick 1d6, Bite 1d2
- wiki/Unicorn.txt -- white unicorn: lvl 4, spd 24, AC 2, MR 70, diff 6; attacks: Headbutt 1d12; Kick 1d6; eating conveys: Poison (27%)
- wiki/Unicorn.txt -- gray unicorn: lvl 4, spd 24, AC 2, MR 70, diff 6; attacks: Headbutt 1d12; Kick 1d6; eating conveys: Poison (27%)
- wiki/Unicorn.txt -- black unicorn: lvl 4, spd 24, AC 2, MR 70, diff 6; attacks: Headbutt 1d12; Kick 1d6; eating conveys: Poison (27%)
- wiki/Horse.txt -- horse: lvl 5, spd 20, AC 5, MR 0, diff 7; attacks: Kick 1d8 physical, bite 1d3 physical
- wiki/Warhorse.txt -- warhorse: lvl 7, spd 24, AC 4, MR 0, diff 9; attacks: Kick 1d10, Bite 1d4

### v -- vortices

- wiki/Vortex.txt -- class overview
- wiki/Fog_cloud.txt -- fog cloud: lvl 3, spd 1, AC 0, MR 0, diff 4; attacks: Engulf 1d6 moisture
- wiki/Dust_vortex.txt -- dust vortex: lvl 4, spd 20, AC 2, MR 30, diff 6; attacks: Engulf 2d8 blind
- wiki/Ice_vortex.txt -- ice vortex: lvl 5, spd 20, AC 2, MR 30, diff 7; attacks: Engulf 1d6 cold
- wiki/Energy_vortex.txt -- energy vortex: lvl 6, spd 20, AC 2, MR 30, diff 9; attacks: Engulf 1d6 shock, Engulf 2d6 drain energy, Passive 0d4 shock
- wiki/Steam_vortex.txt -- steam vortex: lvl 7, spd 22, AC 2, MR 30, diff 9; attacks: Engulf 1d8 fire
- wiki/Fire_vortex.txt -- fire vortex: lvl 8, spd 22, AC 2, MR 30, diff 10; attacks: Engulf 1d10 fire, passive 0d4 fire

### w -- worms

- wiki/Worm.txt -- class overview
- wiki/Baby_long_worm.txt -- baby long worm: lvl 5, spd 3, AC 5, MR 0, diff 6; attacks: Bite 1d4 physical
- wiki/Baby_purple_worm.txt -- baby purple worm: lvl 8, spd 3, AC 5, MR 0, diff 9; attacks: Bite 1d6
- wiki/Long_worm.txt -- long worm: lvl 9, spd 3, AC 5, MR 10, diff 10; attacks: Bite 2d4 physical
- wiki/Purple_worm.txt -- purple worm: lvl 15, spd 9, AC 6, MR 20, diff 17; attacks: Bite 2d8 physical, engulf 1d10 digest

### x -- grid bugs and xan

- wiki/Grid_bug.txt -- class overview
- wiki/Grid_bug.txt -- grid bug: lvl 0, spd 12, AC 9, MR 0, diff 1; attacks: Bite d1 shock
- wiki/Xan.txt -- xan: lvl 7, spd 18, AC −4, MR 0, diff 9; attacks: Sting 1d4 wounded legs; eating conveys: poison resistance (47%)

### y -- lights

- wiki/Light_(monster_class).txt -- class overview
- wiki/Yellow_light.txt -- yellow light: lvl 3, spd 15, AC 0, MR 0, diff 5; attacks: Explode 10d20 blind
- wiki/Black_light.txt -- black light: lvl 5, spd 15, AC 0, MR 0, diff 7; attacks: Explode 10d12 hallucination

### z -- zruty

- wiki/Zruty_(monster_class).txt -- class overview
- wiki/Zruty.txt -- zruty: lvl 9, spd 8, AC 3, MR 0, diff 11; attacks: Claw 3d4, Claw 3d4, Bite 3d6

### A -- angelic beings

- wiki/Angelic_being.txt -- class overview
- wiki/Couatl.txt -- couatl: lvl 8, spd 10, AC 5, MR 30, diff 11; attacks: Bite 2d4 poison, Bite 1d3 physical, Bearhug 2d4 drowning
- wiki/Aleax.txt -- Aleax: lvl 10, spd 8, AC 0, MR 30, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical, kick 1d4 physical
- wiki/Angel.txt -- Angel: lvl 14, spd 10, AC -4, MR 55, diff 19; attacks: Weapon 1d6 physical, Weapon 1d6 physical, Claw 1d4 physical, Cast 2d6 magic missile (0d6 in melee range)
- wiki/Ki-rin.txt -- ki-rin: lvl 16, spd 18, AC −5, MR 90, diff 21; attacks: Kick 2d4, kick 2d4, butt 3d6, spell-casting 2d6 mage
- wiki/Archon.txt -- Archon: lvl 19, spd 16, AC −6, MR 80, diff 26; attacks: Weapon 2d4 physical, Weapon 2d4 physical, Gaze 2d6 blind/stun, Claw 1d8 physical, Spell-casting 0d0 mage

### B -- bats and birds

- wiki/Bat_or_bird.txt -- class overview
- wiki/Bat.txt -- bat: lvl 0, spd 22, AC 8, MR 0, diff 2; attacks: Bite 1d4
- wiki/Giant_bat.txt -- giant bat: lvl 2, spd 22, AC 7, MR 0, diff 3; attacks: Bite 1d6 physical; eating conveys: stuns the hero
- wiki/Raven.txt -- raven: lvl 4, spd 20, AC 6, MR 0, diff 6; attacks: Bite 1d6 physical, claw 1d6 blinding
- wiki/Vampire_bat.txt -- vampire bat: lvl 5, spd 20, AC 6, MR 0, diff 7; attacks: Bite 1d6 physical, bite 0d0 poison (strength)

### C -- centaurs

- wiki/Centaur_(monster_class).txt -- class overview
- wiki/Plains_centaur.txt -- plains centaur: lvl 4, spd 18, AC 4, MR 0, diff 6; attacks: Weapon 1d6 physical, Kick 1d6 physical
- wiki/Forest_centaur.txt -- forest centaur: lvl 5, spd 18, AC 3, MR 10, diff 8; attacks: Weapon 1d8 physical, Kick 1d6 physical
- wiki/Mountain_centaur.txt -- mountain centaur: lvl 6, spd 20, AC 2, MR 10, diff 9; attacks: Weapon 1d10 physical, Kick 1d6 physical, Kick 1d6 physical

### D -- dragons

- wiki/Dragon.txt -- class overview
- wiki/Baby_gray_dragon.txt -- baby gray dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6
- wiki/Baby_silver_dragon.txt -- baby silver dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6 physical
- wiki/Baby_red_dragon.txt -- baby red dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6 physical
- wiki/Baby_white_dragon.txt -- baby white dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6 physical
- wiki/Baby_orange_dragon.txt -- baby orange dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6
- wiki/Baby_black_dragon.txt -- baby black dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6
- wiki/Baby_blue_dragon.txt -- baby blue dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6
- wiki/Baby_green_dragon.txt -- baby green dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6
- wiki/Baby_yellow_dragon.txt -- baby yellow dragon: lvl 12, spd 9, AC 2, MR 10, diff 13; attacks: Bite 2d6; eating conveys: Cures stoning
- wiki/Gray_dragon.txt -- gray dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 magic missile, bite 3d8, claw 1d4, claw 1d4
- wiki/Silver_dragon.txt -- silver dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 cold, bite 3d8 physical, claw 1d4 physical, claw 1d4 physical
- wiki/Red_dragon.txt -- red dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 6d6 fire, bite 3d8 physical, claw 1d4 physical, claw 1d4 physical; eating conveys: Fire resistance (100%)
- wiki/White_dragon.txt -- white dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 cold, bite 3d8 physical, claw 1d4 physical, claw 1d4 physical; eating conveys: Cold resistance (100%)
- wiki/Orange_dragon.txt -- orange dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d25 sleep, bite 3d8, claw 1d4, claw 1d4; eating conveys: Sleep resistance (100%)
- wiki/Black_dragon.txt -- black dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 1d255 disintegration, bite 3d8, claw 1d4, claw 1d4; eating conveys: Disintegration resistance (100%)
- wiki/Blue_dragon.txt -- blue dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 lightning, bite 3d8, claw 1d4, claw 1d4; eating conveys: shock resistance (100%)
- wiki/Green_dragon.txt -- green dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 poison, bite 3d8 physical, claw 1d4 physical, claw 1d4 physical; eating conveys: Poison resistance (100%)
- wiki/Yellow_dragon.txt -- yellow dragon: lvl 15, spd 9, AC -1, MR 20, diff 20; attacks: Breath 4d6 acidic, bite 3d8, claw 1d4, claw 1d4; eating conveys: Cures stoning
- wiki/Chromatic_Dragon.txt -- Chromatic Dragon: lvl 16, spd 12, AC 0, MR 30, diff 23; attacks: Breath 6d8 random, spell-casting 0d0 mage, claw 2d8 quest-artifact-stealing, bite 4d8 physical, bite 4d8 physical, sting 1d6 physical; eating conveys: Fire resist...
- wiki/Ixoth.txt -- Ixoth: lvl 15, spd 12, AC -1, MR 20, diff 22; attacks: Breath 8d6 fire, bite 4d8 physical, spell-casting 0d0 mage, claw 2d4 physical, claw 2d4 quest-artifact-stealing; eating conveys: Fire (100%)

### E -- elementals and stalkers

- wiki/Elemental.txt -- class overview
- wiki/Stalker.txt -- stalker: lvl 8, spd 12, AC 3, MR 0, diff 9; attacks: Claw 4d4 physical; eating conveys: Invisibility, see invisible (only if invisible when corpse is eaten); causes stunning
- wiki/Air_elemental.txt -- air elemental: lvl 8, spd 36, AC 2, MR 30, diff 10; attacks: Engulf 1d10 physical
- wiki/Fire_elemental.txt -- fire elemental: lvl 8, spd 12, AC 2, MR 30, diff 10; attacks: Claw 3d6 fire, passive 0d4 fire
- wiki/Earth_elemental.txt -- earth elemental: lvl 8, spd 6, AC 2, MR 30, diff 10; attacks: Claw 4d6
- wiki/Water_elemental.txt -- water elemental: lvl 8, spd 6, AC 2, MR 30, diff 10; attacks: Claw 5d6 physical

### F -- fungi and molds (lichens)

- wiki/Fungus_or_mold.txt -- class overview
- wiki/Lichen.txt -- lichen: lvl 0, spd 1, AC 9, MR 0, diff 1; attacks: Touch 0d0 sticky
- wiki/Brown_mold.txt -- brown mold: lvl 1, spd 0, AC 9, MR 0, diff 2; attacks: Passive 0d6 cold; eating conveys: Cold resistance (3%), poison resistance (3%)
- wiki/Yellow_mold.txt -- yellow mold: lvl 1, spd 0, AC 9, MR 0, diff 2; attacks: Passive 0d4 stun; eating conveys: Poison resistance (7%), causes hallucination
- wiki/Green_mold.txt -- green mold: lvl 1, spd 0, AC 9, MR 0, diff 2; attacks: Passive 0d4 acid; eating conveys: Cures stoning
- wiki/Red_mold.txt -- red mold: lvl 1, spd 0, AC 9, MR 0, diff 2; attacks: Passive 0d4 fire; eating conveys: Fire resistance (3%), poison resistance (3%)
- wiki/Shrieker.txt -- shrieker: lvl 3, spd 1, AC 7, MR 0, diff 2; attacks: None; eating conveys: Poison (20%)
- wiki/Violet_fungus.txt -- violet fungus: lvl 3, spd 1, AC 7, MR 0, diff 5; attacks: Touch 1d4 sticky; eating conveys: Poison (20%)

### G -- gnomes

- wiki/Gnome_(monster_class).txt -- class overview
- wiki/Gnome_(monster).txt -- gnome: lvl 1, spd 6, AC 10, MR 4, diff 3; attacks: Weapon 1d6
- wiki/Gnome_lord.txt -- gnome lord: lvl 3, spd 8, AC 10, MR 4, diff 4; attacks: Weapon 1d8 physical
- wiki/Gnomish_wizard.txt -- gnomish wizard: lvl 3, spd 10, AC 4, MR 10, diff 5; attacks: Spell-casting
- wiki/Gnome_king.txt -- gnome king: lvl 5, spd 10, AC 10, MR 20, diff 6; attacks: Weapon 2d6 physical

### H -- giants and other giant humanoids

- wiki/Giant_humanoid.txt -- class overview
- wiki/Giant_(monster).txt -- giant: lvl 6, spd 6, AC 0, MR 0, diff 8; attacks: Weapon 2d10; eating conveys: Increase strength (50%)
- wiki/Stone_giant.txt -- stone giant: lvl 6, spd 6, AC 0, MR 0, diff 8; attacks: Weapon 2d10; eating conveys: Increase Strength (50%)
- wiki/Hill_giant.txt -- hill giant: lvl 8, spd 10, AC 6, MR 0, diff 10; attacks: Weapon 2d8; eating conveys: Increase strength (50%)
- wiki/Fire_giant.txt -- fire giant: lvl 9, spd 12, AC 4, MR 5, diff 11; attacks: Weapon 2d10; eating conveys: Fire (30%), Increase strength (50%)
- wiki/Frost_giant.txt -- frost giant: lvl 10, spd 12, AC 3, MR 10, diff 13; attacks: Weapon 2d12; eating conveys: Cold (33%), Increase strength (50%)
- wiki/Ettin.txt -- ettin: lvl 10, spd 12, AC 3, MR 0, diff 13; attacks: Weapon 2d8 physical, weapon 3d6 physical
- wiki/Storm_giant.txt -- storm giant: lvl 16, spd 12, AC 3, MR 10, diff 19; attacks: Weapon 2d12; eating conveys: shock (50%), Increase strength (50%)
- wiki/Titan.txt -- titan: lvl 16, spd 18, AC −3, MR 70, diff 20; attacks: Weapon 2d8 physical, Spell-casting 0d0 mage
- wiki/Minotaur.txt -- minotaur: lvl 15, spd 15, AC 6, MR 0, diff 17; attacks: Claw 3d10, claw 3d10, butt 2d8
- wiki/Cyclops.txt -- Cyclops: lvl 18, spd 12, AC 0, MR 0, diff 23; attacks: Weapon 4d8, weapon 4d8, claw quest artifact-stealing 2d6
- wiki/Lord_Surtur.txt -- Lord Surtur: lvl 15, spd 12, AC 2, MR 50, diff 19; attacks: Weapon 2d10, weapon 2d10, claw quest-artifact-stealing 2d6; eating conveys: Fire (50%)

### J -- jabberwock

- wiki/Jabberwock_(monster_class).txt -- class overview
- wiki/Jabberwock.txt -- jabberwock: lvl 15, spd 12, AC -2, MR 50, diff 18; attacks: Bite 2d10 physical, bite 2d10 physical, claw 2d10 physical, claw 2d10 physical

### K -- Keystone Kops

- wiki/Keystone_Kop_(monster_class).txt -- class overview
- wiki/Keystone_Kop.txt -- Keystone Kop: lvl 1, spd 6, AC 10, MR 10, diff 3; attacks: Weapon 1d4
- wiki/Kop_Sergeant.txt -- Kop Sergeant: lvl 2, spd 8, AC 10, MR 10, diff 4; attacks: Weapon 1d6
- wiki/Kop_Lieutenant.txt -- Kop Lieutenant: lvl 3, spd 10, AC 10, MR 20, diff 5; attacks: Weapon 1d8
- wiki/Kop_Kaptain.txt -- Kop Kaptain: lvl 4, spd 12, AC 10, MR 20, diff 6; attacks: Weapon 2d6

### L -- liches

- wiki/Lich_(monster_class).txt -- class overview
- wiki/Lich.txt -- lich: lvl 11, spd 6, AC 0, MR 30, diff 14; attacks: Touch 1d10 cold, Spell-casting 0d0 mage; eating conveys: cold resistance
- wiki/Demilich.txt -- demilich: lvl 14, spd 9, AC -2, MR 60, diff 18; attacks: Touch 3d4 cold, Spell-casting 0d0 mage; eating conveys: Cold
- wiki/Master_lich.txt -- master lich: lvl 17, spd 9, AC -4, MR 90, diff 21; attacks: Touch 3d6 cold, spell-casting; eating conveys: Cold
- wiki/Arch-lich.txt -- arch-lich: lvl 25, spd 9, AC -6, MR 90, diff 29; attacks: Touch 5d6 cold, Spell-casting 0d0 mage; eating conveys: Fire, Cold

### M -- mummies

- wiki/Mummy.txt -- class overview
- wiki/Kobold_mummy.txt -- kobold mummy: lvl 3, spd 8, AC 6, MR 20, diff 4; attacks: Claw 1d4
- wiki/Gnome_mummy.txt -- gnome mummy: lvl 4, spd 10, AC 6, MR 20, diff 5; attacks: Claw 1d6
- wiki/Orc_mummy.txt -- orc mummy: lvl 5, spd 10, AC 5, MR 20, diff 6; attacks: Claw 1d6
- wiki/Dwarf_mummy.txt -- dwarf mummy: lvl 5, spd 10, AC 5, MR 20, diff 6; attacks: Claw 1d6
- wiki/Elf_mummy.txt -- elf mummy: lvl 6, spd 12, AC 4, MR 30, diff 7; attacks: Claw 2d4; eating conveys: Sleep (67%)
- wiki/Human_mummy.txt -- human mummy: lvl 6, spd 12, AC 4, MR 30, diff 7; attacks: Claw 2d4 physical, claw 2d4 physical
- wiki/Ettin_mummy.txt -- ettin mummy: lvl 7, spd 12, AC 4, MR 30, diff 8; attacks: Claw 2d6, Claw 2d6
- wiki/Giant_mummy.txt -- giant mummy: lvl 8, spd 14, AC 3, MR 30, diff 10; attacks: Claw 3d4 physical, claw 3d4 physical; eating conveys: Strength

### N -- nagas

- wiki/Naga.txt -- class overview
- wiki/Red_naga_hatchling.txt -- red naga hatchling: lvl 3, spd 10, AC 6, MR 0, diff 4; attacks: Bite 1d4; eating conveys: Fire (10%), Poison (10%)
- wiki/Black_naga_hatchling.txt -- black naga hatchling: lvl 3, spd 10, AC 6, MR 0, diff 4; attacks: Bite 1d4; eating conveys: Poison (20%)
- wiki/Golden_naga_hatchling.txt -- golden naga hatchling: lvl 3, spd 10, AC 6, MR 0, diff 4; attacks: Bite 1d4; eating conveys: Poison (20%)
- wiki/Guardian_naga_hatchling.txt -- guardian naga hatchling: lvl 3, spd 10, AC 6, MR 0, diff 4; attacks: Bite 1d4; eating conveys: Poison (20%)
- wiki/Red_naga.txt -- red naga: lvl 6, spd 12, AC 4, MR 0, diff 8; attacks: Bite 2d4 physical, Breath 2d6 fire; eating conveys: fire resistance (20%), poison resistance (20%)
- wiki/Black_naga.txt -- black naga: lvl 8, spd 14, AC 2, MR 10, diff 10; attacks: Bite 2d6, Spit 0d0 acid venom; eating conveys: Poison (53%)
- wiki/Golden_naga.txt -- golden naga: lvl 10, spd 14, AC 2, MR 70, diff 13; attacks: Bite 2d6 physical, Spell-casting 4d6 mage; eating conveys: Poison (66%)
- wiki/Guardian_naga.txt -- guardian naga: lvl 12, spd 16, AC 0, MR 50, diff 16; attacks: Bite 1d6 paralysis, Spit 1d6 blinding venom, Hug 2d4; eating conveys: Poison (80%)

### O -- ogres

- wiki/Ogre_(monster_class).txt -- class overview
- wiki/Ogre.txt -- ogre: lvl 5, spd 10, AC 5, MR 0, diff 7; attacks: Weapon 2d5 physical
- wiki/Ogre_lord.txt -- ogre lord: lvl 7, spd 12, AC 3, MR 30, diff 9; attacks: Weapon 2d6 physical
- wiki/Ogre_king.txt -- ogre king: lvl 9, spd 14, AC 4, MR 60, diff 11; attacks: Weapon 3d5 physical

### P -- puddings and oozes

- wiki/Pudding_or_ooze.txt -- class overview
- wiki/Gray_ooze.txt -- gray ooze: lvl 3, spd 1, AC 8, MR 0, diff 4; attacks: Bite 2d8 rusting; eating conveys: fire resistance (7%), cold resistance (7%), poison resistance (7%)
- wiki/Brown_pudding.txt -- brown pudding: lvl 5, spd 3, AC 8, MR 0, diff 6; attacks: Bite 0d0 decay; eating conveys: cold resistance (11%), shock resistance (11%), poison resistance (11%)
- wiki/Green_slime.txt -- green slime: lvl 6, spd 6, AC 6, MR 0, diff 8; attacks: Touch 1d4 sliming, Passive 0d0 sliming; eating conveys: causes sliming
- wiki/Black_pudding.txt -- black pudding: lvl 10, spd 6, AC 6, MR 0, diff 12; attacks: Bite 3d8 corrosion, Passive 0d0 corrosion; eating conveys: cold resistance (22%), shock resistance (22%), poison resistance (22%)

### Q -- quantum mechanic

- wiki/Quantum_mechanic_(monster_class).txt -- class overview
- wiki/Quantum_mechanic.txt -- quantum mechanic: lvl 7, spd 12, AC 3, MR 10, diff 9; attacks: Claw 1d4 teleportation; eating conveys: toggles speed

### R -- rust monster and disenchanter

- wiki/Rust_monster_or_disenchanter.txt -- class overview
- wiki/Rust_monster.txt -- rust monster: lvl 5, spd 18, AC 2, MR 0, diff 8; attacks: 0d0 touch rust, 0d0 touch rust, 0d0 passive rust
- wiki/Disenchanter.txt -- disenchanter: lvl 12, spd 12, AC −10, MR 0, diff 14; attacks: Claw 4d4 disenchant, passive 0d0 disenchant

### S -- snakes

- wiki/Snake_(monster_class).txt -- class overview
- wiki/Garter_snake.txt -- garter snake: lvl 1, spd 8, AC 8, MR 0, diff 3; attacks: Bite 1d2
- wiki/Snake.txt -- snake: lvl 4, spd 15, AC 3, MR 0, diff 6; attacks: Bite 1d6 poison; eating conveys: poison resistance (26%)
- wiki/Water_moccasin.txt -- water moccasin: lvl 4, spd 15, AC 3, MR 0, diff 7; attacks: Bite 1d6 poison; eating conveys: Poison resistance (26%)
- wiki/Python.txt -- python: lvl 6, spd 3, AC 5, MR 0, diff 8; attacks: Bite 1d4 physical, Touch 0d0 physical, Hug 1d4 drowning, Hug 2d4 physical
- wiki/Pit_viper.txt -- pit viper: lvl 6, spd 15, AC 2, MR 0, diff 9; attacks: Bite 1d4 poison, Bite 1d4 poison; eating conveys: poison (40%)
- wiki/Cobra.txt -- cobra: lvl 6, spd 18, AC 2, MR 0, diff 10; attacks: Bite 2d4 poison, Spit 0d0 blinding venom; eating conveys: poison (40%)

### T -- trolls

- wiki/Troll_(monster_class).txt -- class overview
- wiki/Troll.txt -- troll: lvl 7, spd 12, AC 4, MR 0, diff 9; attacks: Weapon 4d2, claw 4d2, bite 2d6
- wiki/Ice_troll.txt -- ice troll: lvl 9, spd 10, AC 2, MR 20, diff 12; attacks: Weapon 2d6, claw 2d6 cold, bite 2d6; eating conveys: Cold (60%)
- wiki/Rock_troll.txt -- rock troll: lvl 9, spd 12, AC 0, MR 0, diff 12; attacks: Weapon 3d6, claw 2d8, bite 2d6
- wiki/Water_troll.txt -- water troll: lvl 11, spd 14, AC 4, MR 40, diff 13; attacks: Weapon 2d8, claw 2d8, bite 2d6
- wiki/Olog-hai.txt -- Olog-hai: lvl 13, spd 12, AC −4, MR 0, diff 16; attacks: Weapon 3d6, claw 2d8, bite 2d6

### U -- umber hulk

- wiki/Umber_hulk_(monster_class).txt -- class overview
- wiki/Umber_hulk.txt -- umber hulk: lvl 9, spd 6, AC 2, MR 25, diff 12; attacks: Claw 3d4, Claw 3d4, Bite 2d5, Gaze confusion

### V -- vampires

- wiki/Vampire_(monster_class).txt -- class overview
- wiki/Vampire.txt -- vampire: lvl 10, spd 12, AC 1, MR 25, diff 12; attacks: Claw 1d6 physical, bite 1d6 drain life
- wiki/Vampire_lord.txt -- vampire lord: lvl 12, spd 14, AC 0, MR 50, diff 14; attacks: Claw 1d8, bite 1d8 drain life
- wiki/Vlad_the_Impaler.txt -- Vlad the Impaler: lvl 28, spd 26, AC -6, MR 80, diff 32; attacks: Weapon 2d10 physical, bite 1d12 drain life

### W -- wraiths and Nazgul

- wiki/Wraith_(monster_class).txt -- class overview
- wiki/Barrow_wight.txt -- barrow wight: lvl 3, spd 12, AC 5, MR 5, diff 7; attacks: Weapon 0d0 drain life, spell-casting 0d0 mage, claw 1d4 physical
- wiki/Wraith.txt -- wraith: lvl 6, spd 12, AC 4, MR 15, diff 8; attacks: Touch 1d6 drain life; eating conveys: gain level
- wiki/Nazgul.txt -- Nazgul: lvl 13, spd 12, AC 0, MR 25, diff 17; attacks: Weapon 1d4 drain life, breath 2d25 sleep

### X -- xorn

- wiki/Xorn_(monster_class).txt -- class overview
- wiki/Xorn.txt -- xorn: lvl 8, spd 9, AC −2, MR 20, diff 11; attacks: Claw 1d3 physical, claw 1d3 physical, claw 1d3 physical, bite 4d6 physical

### Y -- apes and other apelike creatures

- wiki/Apelike_creature.txt -- class overview
- wiki/Monkey.txt -- monkey: lvl 2, spd 12, AC 6, MR 0, diff 4; attacks: Claw 0d0 item theft, bite 1d3 physical
- wiki/Ape.txt -- ape: lvl 4, spd 12, AC 6, MR 0, diff 6; attacks: Claw 1d3, Claw 1d3, Bite 1d6
- wiki/Owlbear.txt -- owlbear: lvl 5, spd 12, AC 5, MR 0, diff 7; attacks: Claw 1d6, Claw 1d6, Hug 2d8
- wiki/Yeti.txt -- yeti: lvl 5, spd 15, AC 6, MR 0, diff 7; attacks: Claw 1d6 physical, claw 1d6 physical, bite 1d4 physical; eating conveys: cold resistance (33%)
- wiki/Carnivorous_ape.txt -- carnivorous ape: lvl 6, spd 12, AC 6, MR 0, diff 8; attacks: Claw 1d4, Claw 1d4, Bearhug 1d8
- wiki/Sasquatch.txt -- sasquatch: lvl 7, spd 15, AC 6, MR 0, diff 9; attacks: Claw 1d6, Claw 1d6, Kick 1d8

### Z -- zombies

- wiki/Zombie_(monster_class).txt -- class overview
- wiki/Kobold_zombie.txt -- kobold zombie: lvl 0, spd 6, AC 10, MR 0, diff 1; attacks: Claw 1d4
- wiki/Gnome_zombie.txt -- gnome zombie: lvl 1, spd 6, AC 10, MR 0, diff 2; attacks: Claw 1d5
- wiki/Orc_zombie.txt -- orc zombie: lvl 2, spd 6, AC 9, MR 0, diff 3; attacks: Claw 1d6
- wiki/Dwarf_zombie.txt -- dwarf zombie: lvl 2, spd 6, AC 9, MR 0, diff 3; attacks: Claw 1d6
- wiki/Elf_zombie.txt -- elf zombie: lvl 3, spd 6, AC 9, MR 0, diff 4; attacks: Claw 1d7; eating conveys: Sleep (67%)
- wiki/Human_zombie.txt -- human zombie: lvl 4, spd 6, AC 8, MR 0, diff 5; attacks: Claw 1d8
- wiki/Ettin_zombie.txt -- ettin zombie: lvl 6, spd 8, AC 6, MR 0, diff 7; attacks: Claw 1d10, claw 1d10
- wiki/Ghoul.txt -- ghoul: lvl 3, spd 6, AC 10, MR 0, diff 5; attacks: Claw 1d2 paralysis, Claw 1d3 physical
- wiki/Giant_zombie.txt -- giant zombie: lvl 8, spd 8, AC 6, MR 0, diff 9; attacks: Claw 2d8, claw 2d8; eating conveys: Increase strength (50%)
- wiki/Skeleton.txt -- skeleton: lvl 12, spd 8, AC 4, MR 0, diff 14; attacks: Weapon 2d6 physical, Touch 1d6 slowing

### ' -- golems

- wiki/Golem.txt -- class overview
- wiki/Straw_golem.txt -- straw golem: lvl 3, spd 12, AC 10, MR 0, diff 4; attacks: Claw 1d2 physical, Claw 1d2 physical
- wiki/Paper_golem.txt -- paper golem: lvl 3, spd 12, AC 10, MR 0, diff 4; attacks: Claw 1d3 physical
- wiki/Rope_golem.txt -- rope golem: lvl 4, spd 9, AC 8, MR 0, diff 6; attacks: Claw 1d4 physical, Claw 1d4 physical, Holding 6d1 grab
- wiki/Gold_golem.txt -- gold golem: lvl 5, spd 9, AC 6, MR 0, diff 6; attacks: Claw 2d3 physical, claw 2d3 physical
- wiki/Leather_golem.txt -- leather golem: lvl 6, spd 6, AC 6, MR 0, diff 7; attacks: Claw 1d6, Claw 1d6
- wiki/Wood_golem.txt -- wood golem: lvl 7, spd 3, AC 4, MR 0, diff 8; attacks: Claw 3d4
- wiki/Flesh_golem.txt -- flesh golem: lvl 9, spd 8, AC 9, MR 30, diff 10; attacks: Claw 2d8 physical, Claw 2d8 physical; eating conveys: fire resistance (12%), cold resistance (12%), shock resistance (12%), sleep resistance (12%), poison resistance (12%)
- wiki/Clay_golem.txt -- clay golem: lvl 11, spd 7, AC 7, MR 40, diff 12; attacks: Claw 3d10
- wiki/Stone_golem.txt -- stone golem: lvl 14, spd 6, AC 5, MR 50, diff 15; attacks: Claw 3d8
- wiki/Glass_golem.txt -- glass golem: lvl 16, spd 6, AC 1, MR 50, diff 18; attacks: Claw 2d8 physical, claw 2d8 physical
- wiki/Iron_golem.txt -- iron golem: lvl 18, spd 6, AC 3, MR 60, diff 22; attacks: Weapon 4d10 physical, breath 4d6 poison (strength)

### @ -- humans and elves (incl. shopkeepers, priests, quest leaders)

- wiki/Human_or_elf.txt -- class overview
- wiki/Human_(monster).txt -- human: lvl 0, spd 12, AC 10, MR 0, diff 2; attacks: Weapon 1d6
- wiki/Wererat.txt -- wererat: lvl 2, spd 12, AC 10, MR 10, diff 3; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Werejackal.txt -- werejackal: lvl 2, spd 12, AC 10, MR 10, diff 3; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Werewolf.txt -- werewolf: lvl 5, spd 12, AC 10, MR 20, diff 6; attacks: Weapon 2d4 physical; eating conveys: causes lycanthropy
- wiki/Elf_(monster).txt -- elf: lvl 10, spd 12, AC 10, MR 2, diff 12; attacks: Weapon 1d8 physical; eating conveys: Sleep resistance (67%)
- wiki/Woodland-elf.txt -- Woodland-elf: lvl 4, spd 12, AC 10, MR 10, diff 6; attacks: Weapon 2d4 physical; eating conveys: sleep resistance (26%)
- wiki/Green-elf.txt -- Green-elf: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 2d4; eating conveys: Sleep (33%)
- wiki/Grey-elf.txt -- Grey-elf: lvl 6, spd 12, AC 10, MR 10, diff 8; attacks: Weapon 2d4; eating conveys: Sleep (40%)
- wiki/Elf-lord.txt -- elf-lord: lvl 8, spd 12, AC 10, MR 20, diff 11; attacks: Weapon 2d4, weapon 2d4; eating conveys: Sleep (53%)
- wiki/Elvenking.txt -- Elvenking: lvl 9, spd 12, AC 10, MR 25, diff 11; attacks: Weapon 2d4 physical, weapon 2d4 physical; eating conveys: sleep resistance (60%)
- wiki/Doppelganger.txt -- doppelganger: lvl 9, spd 12, AC 5, MR 20, diff 11; attacks: Weapon 1d12; eating conveys: Causes polymorph
- wiki/Shopkeeper.txt -- shopkeeper: lvl 12, spd 18, AC 0, MR 50, diff 15; attacks: Weapon 4d4 physical, Weapon 4d4 physical
- wiki/Guard.txt -- guard: lvl 12, spd 12, AC 10, MR 40, diff 14; attacks: Weapon 4d10 physical
- wiki/Prisoner.txt -- prisoner: lvl 12, spd 12, AC 10, MR 0, diff 14; attacks: Weapon 1d6 physical
- wiki/Oracle_(monster).txt -- Oracle: lvl 12, spd 0, AC 0, MR 50, diff 13; attacks: Passive 0d4 magic missile
- wiki/Aligned_priest.txt -- aligned priest: lvl 12, spd 12, AC 10, MR 50, diff 15; attacks: Weapon 4d10 physical, kick 1d4 physical, spell-casting 0d0 (clerical)
- wiki/High_priest.txt -- high priest: lvl 25, spd 15, AC 7, MR 70, diff 30; attacks: Weapon 4d10, Kick 2d8, 2d8 spell-casting clerical, 2d8 spell-casting clerical
- wiki/Soldier.txt -- soldier: lvl 6, spd 10, AC 10, MR 0, diff 8; attacks: Weapon 1d8 physical
- wiki/Sergeant_(monster).txt -- sergeant: lvl 8, spd 10, AC 10, MR 5, diff 10; attacks: Weapon 2d6 physical
- wiki/Nurse.txt -- nurse: lvl 11, spd 6, AC 0, MR 0, diff 13; attacks: Claw 2d6 heal; eating conveys: Poison (73%)
- wiki/Lieutenant.txt -- lieutenant: lvl 10, spd 10, AC 10, MR 15, diff 12; attacks: Weapon 3d4 physical, weapon 3d4 physical
- wiki/Captain.txt -- captain: lvl 12, spd 10, AC 10, MR 15, diff 14; attacks: Weapon 4d4 physical, weapon 4d4 physical
- wiki/Watchman.txt -- watchman: lvl 6, spd 10, AC 10, MR 0, diff 8; attacks: Weapon 1d8
- wiki/Watchman.txt -- watch captain: lvl 6, spd 10, AC 10, MR 0, diff 8; attacks: Weapon 1d8
- wiki/Medusa.txt -- Medusa: lvl 20, spd 12, AC 2, MR 50, diff 25; attacks: Weapon 2d4 physical, Claw 1d8 physical, Gaze 0d0 stoning, Bite 1d6 poison; eating conveys: Poison resistance (100%), turns eater to stone
- wiki/Wizard_of_Yendor.txt -- Wizard of Yendor: lvl 30, spd 12, AC -8, MR 100, diff 34; attacks: Claw 2d12 amulet-stealing, spell-casting 0d0 mage; eating conveys: Fire resistance (25%), poison resistance (25%), teleport control (25%), causes teleportitis (...
- wiki/Croesus.txt -- Croesus: lvl 20, spd 15, AC 0, MR 40, diff 22; attacks: Weapon 4d10
- wiki/Archeologist_(player_monster).txt -- archeologist: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Barbarian_(player_monster).txt -- barbarian: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Caveman_(player_monster).txt -- caveman: lvl 10, spd 12, AC 10, MR 0, diff 12; attacks: Weapon 2d4 physical
- wiki/Caveman_(player_monster).txt -- cavewoman: lvl 10, spd 12, AC 10, MR 0, diff 12; attacks: Weapon 2d4 physical
- wiki/Healer_(player_monster).txt -- healer: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical
- wiki/Knight_(player_monster).txt -- knight: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Monk_(player_monster).txt -- monk: lvl 10, spd 12, AC 10, MR 2, diff 11; attacks: Claw 1d8 physical, kick 1d8 physical
- wiki/Priest_(player_monster).txt -- priest: lvl 10, spd 12, AC 10, MR 2, diff 12; attacks: Weapon 1d6 physical
- wiki/Priest_(player_monster).txt -- priestess: lvl 10, spd 12, AC 10, MR 2, diff 12; attacks: Weapon 1d6 physical
- wiki/Ranger_(player_monster).txt -- ranger: lvl 10, spd 12, AC 10, MR 2, diff 12; attacks: Weapon 1d4 physical
- wiki/Rogue_(player_monster).txt -- rogue: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Samurai_(player_monster).txt -- samurai: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d8 physical, weapon 1d8 physical
- wiki/Tourist_(player_monster).txt -- tourist: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Valkyrie_(player_monster).txt -- valkyrie: lvl 10, spd 12, AC 10, MR 1, diff 12; attacks: Weapon 1d8 physical, weapon 1d8 physical
- wiki/Wizard_(player_monster).txt -- wizard: lvl 10, spd 12, AC 10, MR 3, diff 12; attacks: Weapon 1d6 physical
- wiki/Lord_Carnarvon.txt -- Lord Carnarvon: lvl 20, spd 12, AC 0, MR 30, diff 22; attacks: Weapon 1d6 physical
- wiki/Pelias.txt -- Pelias: lvl 20, spd 12, AC 0, MR 30, diff 22; attacks: Weapon 1d6
- wiki/Shaman_Karnov.txt -- Shaman Karnov: lvl 20, spd 12, AC 0, MR 30, diff 22; attacks: Weapon 2d4
- wiki/Hippocrates.txt -- Hippocrates: lvl 20, spd 12, AC 0, MR 40, diff 22; attacks: Weapon 1d6
- wiki/King_Arthur.txt -- King Arthur: lvl 20, spd 12, AC 0, MR 40, diff 23; attacks: Weapon 1d6, weapon 1d6
- wiki/Grand_Master.txt -- Grand Master: lvl 25, spd 12, AC 0, MR 70, diff 30; attacks: Claw 4d10, kick 2d8, spell-casting (clerical) 2d8, spell-casting (clerical) 2d8
- wiki/Arch_Priest.txt -- Arch Priest: lvl 25, spd 12, AC 7, MR 70, diff 30; attacks: Weapon 4d10 physical, kick 2d8 physical, spellcasting 2d8 clerical, spellcasting 2d8 clerical
- wiki/Orion.txt -- Orion: lvl 20, spd 12, AC 0, MR 30, diff 22; attacks: Weapon 1d6
- wiki/Master_of_Thieves.txt -- Master of Thieves: lvl 20, spd 12, AC 0, MR 30, diff 24; attacks: Weapon 2d6 physical, weapon 2d6 physical, claw 2d4 quest-artifact-stealing
- wiki/Lord_Sato.txt -- Lord Sato: lvl 20, spd 12, AC 0, MR 30, diff 23; attacks: Weapon 1d8 physical, weapon 1d6 physical
- wiki/Twoflower.txt -- Twoflower: lvl 20, spd 12, AC 10, MR 20, diff 22; attacks: Weapon 1d6, weapon 1d6
- wiki/Norn.txt -- Norn: lvl 20, spd 12, AC 0, MR 80, diff 23; attacks: Weapon 1d8, weapon 1d6
- wiki/Neferet_the_Green.txt -- Neferet the Green: lvl 20, spd 12, AC 0, MR 60, diff 23; attacks: Weapon 1d6 physical, spell-casting 2d8 mage
- wiki/Thoth_Amon.txt -- Thoth Amon: lvl 16, spd 12, AC 0, MR 10, diff 22; attacks: Weapon 1d6 physical, spell-casting 0d0 mage, spell-casting 0d0 mage, claw 1d4 quest-artifact-stealing
- wiki/Master_Kaen.txt -- Master Kaen: lvl 25, spd 12, AC −10, MR 10, diff 31; attacks: Claw 16d2 physical, claw 16d2 physical, Spell-casting 0d0 clerical, claw 1d4 Amulet theft; eating conveys: Poison resistance (100%)
- wiki/Master_Assassin.txt -- Master Assassin: lvl 15, spd 12, AC 0, MR 30, diff 20; attacks: Weapon 2d6 poison (strength), weapon 2d8 physical, claw 2d6 Amulet theft
- wiki/Ashikaga_Takauji.txt -- Ashikaga Takauji: lvl 15, spd 12, AC 0, MR 40, diff 19; attacks: Weapon 2d6 physical, Weapon 2d6 physical, claw 2d6 quest-artifact-stealing
- wiki/Dark_One.txt -- Dark One: lvl 15, spd 12, AC 0, MR 80, diff 20; attacks: Weapon 1d6 physical, Weapon 1d6 physical, claw 1d4 artifact theft, spell-casting 0d0 mage
- wiki/Student.txt -- student: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d6 physical
- wiki/Chieftain.txt -- chieftain: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d6 physical
- wiki/Neanderthal.txt -- neanderthal: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 2d4 physical
- wiki/Attendant.txt -- attendant: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d6
- wiki/Page.txt -- page: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d6 physical, Weapon 1d6 physical
- wiki/Abbot.txt -- abbot: lvl 5, spd 12, AC 10, MR 20, diff 8; attacks: Claw 8d2 physical, Kick 3d2 stun, Spell-casting 0d0 clerical
- wiki/Acolyte.txt -- acolyte: lvl 5, spd 12, AC 10, MR 20, diff 8; attacks: Weapon 1d6 physical, Spell-casting 0d0 clerical
- wiki/Hunter.txt -- hunter: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d4 physical
- wiki/Thug.txt -- thug: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d6 physical, weapon 1d6 physical
- wiki/Ninja.txt -- ninja: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d8 physical, weapon 1d8 physical
- wiki/Roshi.txt -- roshi: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d8 physical, weapon 1d8
- wiki/Guide.txt -- guide: lvl 5, spd 12, AC 10, MR 20, diff 8; attacks: Weapon 1d6 physical, Spellcasting 0d0 mage
- wiki/Warrior.txt -- warrior: lvl 5, spd 12, AC 10, MR 10, diff 7; attacks: Weapon 1d8 physical, weapon 1d8 physical
- wiki/Apprentice.txt -- apprentice: lvl 5, spd 12, AC 10, MR 30, diff 8; attacks: Weapon 1d6 physical, Spellcasting 0d0 mage

### (blank space) -- ghosts and shades (shown as a blank space)

- wiki/Ghost_(monster_class).txt -- class overview
- wiki/Ghost.txt -- ghost: lvl 10, spd 3, AC -5, MR 50, diff 12; attacks: touch 1d1 physical
- wiki/Shade.txt -- shade: lvl 12, spd 10, AC 10, MR 0, diff 14; attacks: Touch 2d6 paralyse, Touch 1d6 slowing

### & -- demons (and djinni, mail daemon)

- wiki/Demon_(monster_class).txt -- class overview
- wiki/Water_demon.txt -- water demon: lvl 8, spd 12, AC −4, MR 30, diff 11; attacks: Weapon 1d3, claw 1d3, bite 1d3
- wiki/Foocubus.txt -- succubus: lvl 6, spd 12, AC 0, MR 70, diff 8; attacks: bite 0d0 seduction, claw 1d3 physical, claw 1d3 physical, bite 2d6 drain life
- wiki/Horned_devil.txt -- horned devil: lvl 6, spd 9, AC -5, MR 50, diff 9; attacks: Weapon 1d4, claw 1d4, bite 2d3, sting 1d3
- wiki/Foocubus.txt -- incubus: lvl 6, spd 12, AC 0, MR 70, diff 8; attacks: bite 0d0 seduction, claw 1d3 physical, claw 1d3 physical, bite 2d6 drain life
- wiki/Erinys.txt -- erinys: lvl 7, spd 12, AC 2, MR 30, diff 10; attacks: Weapon poisonous 2d4
- wiki/Barbed_devil.txt -- barbed devil: lvl 8, spd 12, AC 0, MR 35, diff 10; attacks: Claw 2d4, claw 2d4, sting 3d4
- wiki/Marilith.txt -- marilith: lvl 7, spd 12, AC -6, MR 80, diff 11; attacks: Weapon 2d4, Weapon 2d4, Claw 2d4, Claw 2d4, Claw 2d4, Claw 2d4
- wiki/Vrock.txt -- vrock: lvl 8, spd 12, AC 0, MR 50, diff 11; attacks: Claw 1d4 physical, claw 1d4 physical, claw 1d8 physical, claw 1d8 physical, bite 1d6 physical
- wiki/Hezrou.txt -- hezrou: lvl 9, spd 6, AC −2, MR 55, diff 12; attacks: Claw 1d3, claw 1d3, bite 4d4
- wiki/Bone_devil.txt -- bone devil: lvl 9, spd 15, AC -1, MR 40, diff 13; attacks: Weapon 3d4, sting poisonous 2d4
- wiki/Ice_devil.txt -- ice devil: lvl 11, spd 6, AC -4, MR 55, diff 14; attacks: Claw 1d4, claw 1d4, bite 2d4, sting cold 3d4
- wiki/Nalfeshnee.txt -- nalfeshnee: lvl 11, spd 9, AC -1, MR 65, diff 15; attacks: Claw 1d4, claw 1d4, bite 2d4, spell-casting 0d0 mage
- wiki/Pit_fiend.txt -- pit fiend: lvl 13, spd 6, AC -3, MR 65, diff 16; attacks: Weapon 4d2, weapon 4d2, grabbing 2d4
- wiki/Sandestin.txt -- sandestin: lvl 13, spd 12, AC 4, MR 60, diff 15; attacks: Weapon 2d6, weapon 2d6
- wiki/Balrog.txt -- balrog: lvl 16, spd 5, AC -2, MR 75, diff 20; attacks: Weapon 8d4, Weapon 4d6
- wiki/Juiblex.txt -- Juiblex: lvl 22, spd 3, AC -7, MR 65, diff 26; attacks: Engulf 4d10 disease, Spit 3d6 acid
- wiki/Yeenoghu.txt -- Yeenoghu: lvl 25, spd 18, AC −5, MR 80, diff 31; attacks: Weapon 3d6 physical, weapon 2d8 confusion, claw 1d6 paralyze, spellcasting 2d6 magic missile
- wiki/Orcus.txt -- Orcus: lvl 30, spd 9, AC -6, MR 85, diff 36; attacks: Weapon 3d6 physical, claw 3d4 physical, claw 3d4 physical, spell-casting 8d6 mage, sting 2d4 poisonous
- wiki/Geryon.txt -- Geryon: lvl 33, spd 3, AC -3, MR 75, diff 36; attacks: Claw 3d6, claw 3d6, sting poisonous 2d4
- wiki/Dispater.txt -- Dispater: lvl 36, spd 15, AC −2, MR 80, diff 40; attacks: Weapon 4d6 physical, spell-casting 0d0 mage
- wiki/Baalzebub.txt -- Baalzebub: lvl 41, spd 9, AC -5, MR 85, diff 45; attacks: Bite poisonous 2d6, gaze stunning 2d6
- wiki/Asmodeus.txt -- Asmodeus: lvl 49, spd 12, AC −7, MR 90, diff 53; attacks: Claw 4d4 physical, monster spell 6d6 cone of cold
- wiki/Demogorgon.txt -- Demogorgon: lvl 50 (106), spd 15, AC -8, MR 95, diff 57; attacks: spell-casting 8d6 mage, Sting 1d4 drain life, Claw 1d6 disease, Claw 1d6 disease (stun if first disease attack successful)
- wiki/Death_(monster).txt -- Death: lvl 30, spd 12, AC −5, MR 100, diff 34; attacks: Touch 8d8 deadly, touch 8d8 deadly; eating conveys: teleport control (but attempting to eat Death is an instadeath)
- wiki/Pestilence.txt -- Pestilence: lvl 30, spd 12, AC −5, MR 100, diff 34; attacks: Touch 8d8 disease, Touch 8d8 disease; eating conveys: teleport control (but attempting to eat Pestilence is an instadeath)
- wiki/Famine.txt -- Famine: lvl 30, spd 12, AC −5, MR 100, diff 34; attacks: Touch 8d8 hungering, Touch 8d8 hungering; eating conveys: teleport control (but attempting to eat Famine is an instadeath)
- wiki/Mail_daemon.txt -- mail daemon: lvl 25, spd 24, AC 10, MR 127, diff 26; attacks: None
- wiki/Djinni.txt -- djinni: lvl 7, spd 12, AC 4, MR 30, diff 8; attacks: Weapon 2d8 physical
- wiki/Minion_of_Huhetotl.txt -- Minion of Huhetotl: lvl 16, spd 12, AC -2, MR 75, diff 23; attacks: Weapon 8d4, Weapon 4d6, Spell-casting, Claw 2d6 quest artifact-stealing
- wiki/Nalzok.txt -- Nalzok: lvl 16, spd 12, AC −2, MR 85, diff 23; attacks: Weapon 8d4 physical, weapon 4d6 physical, spell-casting 0d0 mage, claw 2d6 quest-artifact-stealing

### ; -- sea monsters (eels, sharks, jellyfish, kraken)

- wiki/Sea_monster.txt -- class overview
- wiki/Jellyfish.txt -- jellyfish: lvl 3, spd 3, AC 6, MR 0, diff 5; attacks: Sting 3d3 poison (strength); eating conveys: poison resistance (20%)
- wiki/Piranha.txt -- piranha: lvl 5, spd 12, AC 4, MR 0, diff 6; attacks: Bite 2d6
- wiki/Shark.txt -- shark: lvl 7, spd 12, AC 2, MR 0, diff 9; attacks: Bite 5d6 physical
- wiki/Giant_eel.txt -- giant eel: lvl 5, spd 9, AC -1, MR 0, diff 7; attacks: Bite 3d6 physical, Touch 0d0 drowning
- wiki/Electric_eel.txt -- electric eel: lvl 7, spd 10, AC −3, MR 0, diff 10; attacks: Bite 4d6 shock, touch 0d0 drowning; eating conveys: Shock (47%)
- wiki/Kraken.txt -- kraken: lvl 20, spd 3, AC 6, MR 0, diff 22; attacks: Claw 2d4, Claw 2d4, Hug 2d6 drowning, bite 5d4

### : -- lizards, newts, crocodiles

- wiki/Lizard_(monster_class).txt -- class overview
- wiki/Newt.txt -- newt: lvl 0, spd 6, AC 8, MR 0, diff 1; attacks: Bite 1d2
- wiki/Gecko.txt -- gecko: lvl 1, spd 6, AC 8, MR 0, diff 2; attacks: Bite 1d3
- wiki/Iguana.txt -- iguana: lvl 2, spd 6, AC 7, MR 0, diff 3; attacks: Bite 1d4
- wiki/Baby_crocodile.txt -- baby crocodile: lvl 3, spd 6, AC 7, MR 0, diff 4; attacks: Bite 1d4
- wiki/Lizard.txt -- lizard: lvl 5, spd 6, AC 6, MR 10, diff 6; attacks: Bite 1d6; eating conveys: Cures stoning
- wiki/Chameleon.txt -- chameleon: lvl 6, spd 5, AC 6, MR 10, diff 7; attacks: Bite 4d2 physical; eating conveys: Causes polymorph
- wiki/Crocodile.txt -- crocodile: lvl 6, spd 9, AC 5, MR 0, diff 7; attacks: Bite 4d2, Claw 1d12
- wiki/Salamander.txt -- salamander: lvl 8, spd 12, AC -1, MR 0, diff 12; attacks: Weapon 2d8 physical, Touch 1d6 fire, bearhug 2d6 physical, bearhug 3d6 fire; eating conveys: Fire resistance (53%)

## Objects by class

Object stats: base cost ($), weight, AC, damage (small/large), nutrition;
'unidentified' is the fixed unidentified name (random appearance = varies per game).

### Weapons ) 

- wiki/Weapon.txt -- overview: Weapon
- wiki/Polearm.txt -- overview: Polearm
- wiki/Projectile.txt -- overview: Projectile
- wiki/Ranged_weapon.txt -- overview: Ranged weapon
- wiki/Poisoned_weapon.txt -- overview: Poisoned weapon
- wiki/Weapon-tool.txt -- overview: Weapon-tool
- wiki/Martial_arts.txt -- overview: Martial arts
- wiki/Arrow.txt -- arrow; $2, wt 1, dmg 1d6/1d6
- wiki/Elven_arrow.txt -- elven arrow (unidentified: runed arrow); $2, wt 1, dmg 1d7/1d6
- wiki/Orcish_arrow.txt -- orcish arrow (unidentified: crude arrow); $2, wt 1, dmg 1d5/1d6
- wiki/Silver_arrow.txt -- silver arrow; $5, wt 1, dmg 1d6+/1d6+
- wiki/Ya.txt -- ya (unidentified: bamboo arrow); $4, wt 1, dmg 1d7/1d7
- wiki/Crossbow_bolt.txt -- crossbow bolt; $2, wt 1, dmg 1d4+1/1d6+1
- wiki/Dart.txt -- dart; $2, wt 1, dmg 1d3/1d2
- wiki/Shuriken.txt -- shuriken (unidentified: throwing star); $5, wt 1, dmg 1d8/1d6
- wiki/Boomerang.txt -- boomerang; $20, wt 5, dmg 1d9/1d9
- wiki/Spear.txt -- spear; $3, wt 30, dmg 1d6/1d8
- wiki/Elven_spear.txt -- elven spear (unidentified: runed spear); $3, wt 30, dmg 1d7/1d8
- wiki/Orcish_spear.txt -- orcish spear (unidentified: crude spear); $3, wt 30, dmg 1d5/1d8
- wiki/Dwarvish_spear.txt -- dwarvish spear (unidentified: stout spear); $3, wt 35, dmg 1d8/1d8
- wiki/Silver_spear.txt -- silver spear; $40, wt 36, dmg 1d6/1d8
- wiki/Javelin.txt -- javelin (unidentified: throwing spear); $3, wt 20, dmg 1d6/1d6
- wiki/Trident.txt -- trident; $5, wt 25, dmg 1d6+1/3d4
- wiki/Dagger.txt -- dagger; $4, wt 10, dmg 1d4/1d3
- wiki/Elven_dagger.txt -- elven dagger (unidentified: runed dagger); $4, wt 10, dmg 1d5/1d3
- wiki/Orcish_dagger.txt -- orcish dagger (unidentified: crude dagger); $4, wt 10, dmg 1d3/1d3
- wiki/Silver_dagger.txt -- silver dagger; $40, wt 12, dmg 1d4+/1d3+
- wiki/Athame.txt -- athame; $4, wt 10, dmg 1d4/1d3
- wiki/Scalpel.txt -- scalpel; $6, wt 5, dmg 1d3/1d3
- wiki/Knife.txt -- knife; $4, wt 5, dmg 1d3/1d2
- wiki/Stiletto.txt -- stiletto; $4, wt 5, dmg 1d3/1d2
- wiki/Worm_tooth.txt -- worm tooth; $2, wt 20, dmg 1d2/1d2
- wiki/Crysknife.txt -- crysknife; $100, wt 20, dmg 1d10/1d10
- wiki/Axe.txt -- axe; $8, wt 60, dmg 1d6/1d4
- wiki/Battle-axe.txt -- battle-axe (unidentified: double-headed axe); $40, wt 120, dmg 1d8+1d4/1d6+2d4
- wiki/Short_sword.txt -- short sword; $10, wt 30, dmg 1d6/1d8
- wiki/Elven_short_sword.txt -- elven short sword (unidentified: runed short sword); $10, wt 30, dmg 1d8/1d8
- wiki/Orcish_short_sword.txt -- orcish short sword (unidentified: crude short sword); $10, wt 30, dmg 1d5/1d8
- wiki/Dwarvish_short_sword.txt -- dwarvish short sword (unidentified: broad short sword); $10, wt 30, dmg 1d7/1d8
- wiki/Scimitar.txt -- scimitar (unidentified: curved sword); $15, wt 40, dmg 1d8/1d8
- wiki/Silver_saber.txt -- silver saber; $75, wt 40, dmg 1d8+/1d8+
- wiki/Broadsword.txt -- broadsword; $10, wt 70, dmg 2d4/1d6+1
- wiki/Elven_broadsword.txt -- elven broadsword (unidentified: runed broadsword); $10, wt 70, dmg 1d6+1d4/1d6+1
- wiki/Long_sword.txt -- long sword; $15, wt 40, dmg 1d8/1d12
- wiki/Two-handed_sword.txt -- two-handed sword; $50, wt 150, dmg 1d12/3d6
- wiki/Katana.txt -- katana (unidentified: samurai sword); $80, wt 40, dmg 1d10/1d12
- wiki/Tsurugi.txt -- tsurugi (unidentified: long samurai sword); $500, wt 60, dmg 1d16/1d8+2d6
- wiki/Runesword.txt -- runesword (unidentified: runed broadsword); $300, wt 40, dmg 2d4/1d6+1
- wiki/Partisan.txt -- partisan (unidentified: vulgar polearm); $10, wt 80, dmg d6/d6+1
- wiki/Ranseur.txt -- ranseur (unidentified: hilted polearm); $6, wt 50, dmg 2d4/2d4
- wiki/Spetum.txt -- spetum (unidentified: forked polearm); $5, wt 50, dmg d6+1/2d6
- wiki/Glaive.txt -- glaive (unidentified: single-edged polearm); $6, wt 75, dmg d6/d10
- wiki/Lance.txt -- lance; $10, wt 180, dmg 1d6/1d8
- wiki/Halberd.txt -- halberd (unidentified: angled poleaxe); $10, wt 150, dmg d10/2d6
- wiki/Bardiche.txt -- bardiche (unidentified: long poleaxe); $7, wt 120, dmg 2d4/3d4
- wiki/Voulge.txt -- voulge (unidentified: pole cleaver); $5, wt 125, dmg 2d4/2d4
- wiki/Dwarvish_mattock.txt -- dwarvish mattock (unidentified: broad pick); $50, wt 120, dmg 1d12/1d8+2d6
- wiki/Fauchard.txt -- fauchard (unidentified: pole sickle); $5, wt 60, dmg d6/d8
- wiki/Guisarme.txt -- guisarme (unidentified: pruning hook); $5, wt 80, dmg 2d4/d8
- wiki/Bill-guisarme.txt -- bill-guisarme (unidentified: hooked polearm); $7, wt 120, dmg 2d4/d10
- wiki/Lucern_hammer.txt -- lucern hammer (unidentified: pronged polearm); $7, wt 150, dmg 2d4/d6
- wiki/Bec_de_corbin.txt -- bec de corbin (unidentified: beaked polearm); $8, wt 100, dmg d8/d6
- wiki/Mace.txt -- mace; $5, wt 30, dmg 1d6+1/1d6
- wiki/Morning_star.txt -- morning star; $10, wt 120, dmg 2d4/1d6+1
- wiki/War_hammer.txt -- war hammer; $5, wt 50, dmg 1d4+1/1d4
- wiki/Club.txt -- club; $3, wt 30, dmg 1d6/1d3
- wiki/Rubber_hose.txt -- rubber hose; $3, wt 20, dmg 1d4/1d3
- wiki/Quarterstaff.txt -- quarterstaff (unidentified: staff); $5, wt 40, dmg 1d6/1d6
- wiki/Aklys.txt -- aklys (unidentified: thonged club); $4, wt 15, dmg 1d6/1d3
- wiki/Flail.txt -- flail; $4, wt 15, dmg 1d6+1/2d4
- wiki/Bullwhip.txt -- bullwhip; $4, wt 20, dmg 1d2/1
- wiki/Bow.txt -- bow; $60, wt 30, dmg 1d2/1d2
- wiki/Elven_bow.txt -- elven bow (unidentified: runed bow); $60, wt 30, dmg 1d2/1d2
- wiki/Orcish_bow.txt -- orcish bow (unidentified: crude bow); $60, wt 30, dmg 1d2/1d2
- wiki/Yumi.txt -- yumi (unidentified: long bow); $60, wt 30, dmg 1d2/1d2
- wiki/Sling.txt -- sling; $20, wt 3, dmg d2/d2
- wiki/Crossbow.txt -- crossbow; $40, wt 50, dmg 1d2/1d2

### Armor [

- wiki/Armor.txt -- overview: Armor
- wiki/Body_armor.txt -- overview: Body armor
- wiki/Cloak.txt -- overview: Cloak
- wiki/Helm.txt -- overview: Helm
- wiki/Gloves.txt -- overview: Gloves
- wiki/Boots.txt -- overview: Boots
- wiki/Shield.txt -- overview: Shield
- wiki/Shirt.txt -- overview: Shirt
- wiki/Dragon_scale_mail.txt -- overview: Dragon scale mail
- wiki/Dragon_scales.txt -- overview: Dragon scales
- wiki/GDSM_versus_SDSM.txt -- overview: GDSM versus SDSM
- wiki/Elven_leather_helm.txt -- elven leather helm (unidentified: leather hat); $8, wt 3, AC 1
- wiki/Orcish_helm.txt -- orcish helm (unidentified: iron skull cap); $10, wt 30, AC 1
- wiki/Dwarvish_iron_helm.txt -- dwarvish iron helm (unidentified: hard hat); $20, wt 40, AC 2
- wiki/Fedora.txt -- fedora; $1, wt 3, AC 0
- wiki/Cornuthaum.txt -- cornuthaum (unidentified: conical hat); $80, wt 4, AC 0; MC1; clairvoyance (Wizards only); +1 charisma (Wizards only); blocks clairvoyance (non-Wizards); −1 charisma (non-Wizards)
- wiki/Dunce_cap.txt -- dunce cap (unidentified: conical hat); $1, wt 4, AC 0; autocurses; intelligence = 6; wisdom = 6; shop markup
- wiki/Dented_pot.txt -- dented pot; $8, wt 10, AC 1
- wiki/Helmet.txt -- helmet (random appearance); $10, wt 30, AC 1
- wiki/Helm_of_brilliance.txt -- helm of brilliance (random appearance); $50, wt 50, AC 1; intelligence bonus; wisdom bonus; doesn't hinder; spellcasting
- wiki/Helm_of_opposite_alignment.txt -- helm of opposite alignment (random appearance); $50, wt 50, AC 1; autocurses; opposite alignment
- wiki/Helm_of_telepathy.txt -- helm of telepathy (random appearance); $50, wt 50, AC 1; telepathy
- wiki/Gray_dragon_scale_mail.txt -- gray dragon scale mail; $1200, wt 40, AC 9; magic resistance
- wiki/Silver_dragon_scale_mail.txt -- silver dragon scale mail; $1200, wt 40, AC 9; reflection
- wiki/Red_dragon_scale_mail.txt -- red dragon scale mail; $900, wt 40, AC 9; fire resistance
- wiki/White_dragon_scale_mail.txt -- white dragon scale mail; $900, wt 40, AC 9; cold resistance
- wiki/Orange_dragon_scale_mail.txt -- orange dragon scale mail; $900, wt 40, AC 9; sleep resistance
- wiki/Black_dragon_scale_mail.txt -- black dragon scale mail; $1200, wt 40, AC 9; disintegration resistance
- wiki/Blue_dragon_scale_mail.txt -- blue dragon scale mail; $900, wt 40, AC 9; shock resistance
- wiki/Green_dragon_scale_mail.txt -- green dragon scale mail; $900, wt 40, AC 9; poison resistance
- wiki/Yellow_dragon_scale_mail.txt -- yellow dragon scale mail; $900, wt 40, AC 9; acid resistance
- wiki/Gray_dragon_scales.txt -- gray dragon scales; $700, wt 40, AC 3; magic resistance
- wiki/Silver_dragon_scales.txt -- silver dragon scales; $700, wt 40, AC 3; reflection
- wiki/Red_dragon_scales.txt -- red dragon scales; $500, wt 40, AC 3; fire resistance
- wiki/White_dragon_scales.txt -- white dragon scales; $500, wt 40, AC 3; cold resistance
- wiki/Orange_dragon_scales.txt -- orange dragon scales; $500, wt 40, AC 3; sleep resistance
- wiki/Black_dragon_scales.txt -- black dragon scales; $700, wt 40, AC 3; disintegration resistance
- wiki/Blue_dragon_scales.txt -- blue dragon scales; $500, wt 40, AC 3; shock resistance
- wiki/Green_dragon_scales.txt -- green dragon scales; $500, wt 40, AC 3; poison resistance
- wiki/Yellow_dragon_scales.txt -- yellow dragon scales; $500, wt 40, AC 3; acid resistance
- wiki/Plate_mail.txt -- plate mail; $600, wt 450, AC 7; MC2
- wiki/Crystal_plate_mail.txt -- crystal plate mail; $820, wt 450, AC 7; MC2
- wiki/Bronze_plate_mail.txt -- bronze plate mail; $400, wt 450, AC 6; MC1
- wiki/Splint_mail.txt -- splint mail; $80, wt 400, AC 6; MC1
- wiki/Banded_mail.txt -- banded mail; $90, wt 350, AC 6; MC1
- wiki/Dwarvish_mithril-coat.txt -- dwarvish mithril-coat; $240, wt 150, AC 6; MC2
- wiki/Elven_mithril-coat.txt -- elven mithril-coat; $240, wt 150, AC 5; MC2
- wiki/Chain_mail.txt -- chain mail; $75, wt 300, AC 5; MC1
- wiki/Orcish_chain_mail.txt -- orcish chain mail (unidentified: crude chain mail); $75, wt 300, AC 4; MC1
- wiki/Scale_mail.txt -- scale mail; $45, wt 250, AC 4; MC1
- wiki/Studded_leather_armor.txt -- studded leather armor; $15, wt 200, AC 3; MC1
- wiki/Ring_mail.txt -- ring mail; $100, wt 250, AC 3; MC1
- wiki/Orcish_ring_mail.txt -- orcish ring mail (unidentified: crude ring mail); $80, wt 250, AC 2; MC1
- wiki/Leather_armor.txt -- leather armor; $5, wt 150, AC 2; MC1
- wiki/Leather_jacket.txt -- leather jacket; $10, wt 30, AC 1
- wiki/Hawaiian_shirt.txt -- Hawaiian shirt; $3, wt 5, AC 0; shop markup
- wiki/T-shirt.txt -- T-shirt; $2, wt 5, AC 0; readable; shop markup
- wiki/Mummy_wrapping.txt -- mummy wrapping; $2, wt 3, AC 0; MC1; negates invisibility
- wiki/Elven_cloak.txt -- elven cloak (unidentified: faded pall); $60, wt 10, AC 1; MC1; stealth
- wiki/Orcish_cloak.txt -- orcish cloak (unidentified: coarse mantelet); $40, wt 10, AC 0; MC1
- wiki/Dwarvish_cloak.txt -- dwarvish cloak (unidentified: hooded cloak); $50, wt 10, AC 0; MC1
- wiki/Oilskin_cloak.txt -- oilskin cloak (unidentified: slippery cloak); $50, wt 10, AC 1; MC2; slippery
- wiki/Robe.txt -- robe; $50, wt 15, AC 2; MC2; enhanced; spellcasting
- wiki/Alchemy_smock.txt -- alchemy smock (unidentified: apron); $50, wt 10, AC 1; MC1; acid resistance; poison resistance
- wiki/Leather_cloak.txt -- leather cloak; $40, wt 15, AC 1; MC1
- wiki/Cloak_of_protection.txt -- cloak of protection (random appearance); $50, wt 10, AC 3; MC3
- wiki/Cloak_of_invisibility.txt -- cloak of invisibility (random appearance); $60, wt 10, AC 1; MC1; invisibility
- wiki/Cloak_of_magic_resistance.txt -- cloak of magic resistance (random appearance); $60, wt 10, AC 1; MC1; magic resistance
- wiki/Cloak_of_displacement.txt -- cloak of displacement (random appearance); $50, wt 10, AC 1; MC1; displacement
- wiki/Small_shield.txt -- small shield; $3, wt 30, AC 1
- wiki/Elven_shield.txt -- elven shield (unidentified: blue and green shield); $7, wt 40, AC 2
- wiki/Uruk-hai_shield.txt -- Uruk-hai shield (unidentified: white-handed shield); $7, wt 50, AC 1
- wiki/Orcish_shield.txt -- orcish shield (unidentified: red-eyed shield); $7, wt 50, AC 1
- wiki/Large_shield.txt -- large shield; $10, wt 100, AC 2
- wiki/Dwarvish_roundshield.txt -- dwarvish roundshield (unidentified: large round shield); $10, wt 100, AC 2
- wiki/Shield_of_reflection.txt -- shield of reflection (unidentified: polished silver shield); $50, wt 50, AC 2; reflection
- wiki/Leather_gloves.txt -- leather gloves (random appearance); $8, wt 10, AC 1
- wiki/Gauntlets_of_fumbling.txt -- gauntlets of fumbling (random appearance); $50, wt 10, AC 1; fumbling
- wiki/Gauntlets_of_power.txt -- gauntlets of power (random appearance); $50, wt 30, AC 1; sets wearer's strength to 25
- wiki/Gauntlets_of_dexterity.txt -- gauntlets of dexterity (random appearance); $50, wt 10, AC 1; dexterity bonus
- wiki/Low_boots.txt -- low boots (unidentified: walking shoes); $8, wt 10, AC 1
- wiki/Iron_shoes.txt -- iron shoes (unidentified: hard shoes); $16, wt 50, AC 2
- wiki/High_boots.txt -- high boots (unidentified: jackboots); $12, wt 20, AC 2
- wiki/Speed_boots.txt -- speed boots (random appearance); $50, wt 20, AC 1; speed
- wiki/Water_walking_boots.txt -- water walking boots (random appearance); $50, wt 20, AC 1; water walking
- wiki/Jumping_boots.txt -- jumping boots (random appearance); $50, wt 20, AC 1; jumping
- wiki/Elven_boots.txt -- elven boots (random appearance); $8, wt 15, AC 1; stealth
- wiki/Kicking_boots.txt -- kicking boots (random appearance); $8, wt 50, AC 1; enhanced kicking
- wiki/Fumble_boots.txt -- fumble boots (random appearance); $30, wt 20, AC 1; fumbling
- wiki/Levitation_boots.txt -- levitation boots (random appearance); $30, wt 15, AC 1; levitation

### Rings =

- wiki/Ring.txt -- overview: Ring
- wiki/Ring_of_adornment.txt -- ring of adornment (random appearance); $100
- wiki/Ring_of_gain_strength.txt -- ring of gain strength (random appearance); $150
- wiki/Ring_of_gain_constitution.txt -- ring of gain constitution (random appearance); $150
- wiki/Ring_of_increase_accuracy.txt -- ring of increase accuracy (random appearance); $150
- wiki/Ring_of_increase_damage.txt -- ring of increase damage (random appearance); $150
- wiki/Ring_of_protection.txt -- ring of protection (random appearance); $100
- wiki/Ring_of_regeneration.txt -- ring of regeneration (random appearance); $200
- wiki/Ring_of_searching.txt -- ring of searching (random appearance); $200
- wiki/Ring_of_stealth.txt -- ring of stealth (random appearance); $100
- wiki/Ring_of_sustain_ability.txt -- ring of sustain ability (random appearance); $100
- wiki/Ring_of_levitation.txt -- ring of levitation (random appearance); $200
- wiki/Ring_of_hunger.txt -- ring of hunger (random appearance); $100
- wiki/Ring_of_aggravate_monster.txt -- ring of aggravate monster (random appearance); $150
- wiki/Ring_of_conflict.txt -- ring of conflict (random appearance); $300
- wiki/Ring_of_warning.txt -- ring of warning (random appearance); $100
- wiki/Ring_of_poison_resistance.txt -- ring of poison resistance (random appearance); $150
- wiki/Ring_of_fire_resistance.txt -- ring of fire resistance (random appearance); $200
- wiki/Ring_of_cold_resistance.txt -- ring of cold resistance (random appearance); $150
- wiki/Ring_of_shock_resistance.txt -- ring of shock resistance (random appearance); $150
- wiki/Ring_of_free_action.txt -- ring of free action (random appearance); $200
- wiki/Ring_of_slow_digestion.txt -- ring of slow digestion (random appearance); $200
- wiki/Ring_of_teleportation.txt -- ring of teleportation (random appearance); $200
- wiki/Ring_of_teleport_control.txt -- ring of teleport control (random appearance); $300
- wiki/Ring_of_polymorph.txt -- ring of polymorph (random appearance); $300
- wiki/Ring_of_polymorph_control.txt -- ring of polymorph control (random appearance); $300
- wiki/Ring_of_invisibility.txt -- ring of invisibility (random appearance); $150
- wiki/Ring_of_see_invisible.txt -- ring of see invisible (random appearance); $150
- wiki/Ring_of_protection_from_shape_changers.txt -- ring of protection from shape changers (random appearance); $100

### Amulets "

- wiki/Amulet.txt -- overview: Amulet
- wiki/Amulet_of_ESP.txt -- amulet of ESP (random appearance)
- wiki/Amulet_of_life_saving.txt -- amulet of life saving (random appearance)
- wiki/Amulet_of_strangulation.txt -- amulet of strangulation (random appearance)
- wiki/Amulet_of_restful_sleep.txt -- amulet of restful sleep (random appearance)
- wiki/Amulet_versus_poison.txt -- amulet versus poison (random appearance)
- wiki/Amulet_of_change.txt -- amulet of change (random appearance)
- wiki/Amulet_of_unchanging.txt -- amulet of unchanging (random appearance)
- wiki/Amulet_of_reflection.txt -- amulet of reflection (random appearance)
- wiki/Amulet_of_magical_breathing.txt -- amulet of magical breathing (random appearance)
- wiki/Cheap_plastic_imitation_of_the_Amulet_of_Yendor.txt -- cheap plastic imitation of the Amulet of Yendor (unidentified: Amulet of Yendor); $0
- wiki/Amulet_of_Yendor.txt -- Amulet of Yendor; $30000

### Wands /

- wiki/Wand.txt -- overview: Wand
- wiki/Attack_wand.txt -- overview: Attack wand
- wiki/Beam.txt -- overview: Beam
- wiki/Wand_of_light.txt -- wand of light (random appearance); $100, non-directional
- wiki/Wand_of_secret_door_detection.txt -- wand of secret door detection (random appearance); $150, non-directional
- wiki/Wand_of_enlightenment.txt -- wand of enlightenment (random appearance); $150, non-directional
- wiki/Wand_of_create_monster.txt -- wand of create monster (random appearance); $200, non-directional
- wiki/Wand_of_wishing.txt -- wand of wishing (random appearance); $500, non-directional
- wiki/Wand_of_nothing.txt -- wand of nothing (random appearance); $100, random
- wiki/Wand_of_striking.txt -- wand of striking (random appearance); $150, beam
- wiki/Wand_of_make_invisible.txt -- wand of make invisible (random appearance); $150, beam
- wiki/Wand_of_slow_monster.txt -- wand of slow monster (random appearance); $150, beam
- wiki/Wand_of_speed_monster.txt -- wand of speed monster (random appearance); $150, beam
- wiki/Wand_of_undead_turning.txt -- wand of undead turning (random appearance); $150, beam
- wiki/Wand_of_polymorph.txt -- wand of polymorph (random appearance); $200, beam
- wiki/Wand_of_cancellation.txt -- wand of cancellation (random appearance); $200, beam
- wiki/Wand_of_teleportation.txt -- wand of teleportation (random appearance); $200, beam
- wiki/Wand_of_opening.txt -- wand of opening (random appearance); $150, beam
- wiki/Wand_of_locking.txt -- wand of locking (random appearance); $150, beam
- wiki/Wand_of_probing.txt -- wand of probing (random appearance); $150, beam
- wiki/Wand_of_digging.txt -- wand of digging (random appearance); $150, ray
- wiki/Wand_of_magic_missile.txt -- wand of magic missile (random appearance); $150, ray
- wiki/Wand_of_fire.txt -- wand of fire (random appearance); $175, ray
- wiki/Wand_of_cold.txt -- wand of cold (random appearance); $175, ray
- wiki/Wand_of_sleep.txt -- wand of sleep (random appearance); $175, ray
- wiki/Wand_of_death.txt -- wand of death (random appearance); $500, ray
- wiki/Wand_of_lightning.txt -- wand of lightning (random appearance); $175, ray

### Tools (

- wiki/Tool.txt -- overview: Tool
- wiki/Light_source.txt -- overview: Light source
- wiki/Musical_instrument.txt -- overview: Musical instrument
- wiki/Unlocking_tool.txt -- overview: Unlocking tool
- wiki/Whistle.txt -- overview: Whistle
- wiki/Large_box.txt -- large box; $8, wt 350
- wiki/Chest.txt -- chest; $16, wt 600
- wiki/Ice_box.txt -- ice box; $42, wt 900
- wiki/Sack.txt -- sack (unidentified: bag); $2, wt 15
- wiki/Oilskin_sack.txt -- oilskin sack (unidentified: bag); $100, wt 15
- wiki/Bag_of_holding.txt -- bag of holding (unidentified: bag); $100, wt 15
- wiki/Bag_of_tricks.txt -- bag of tricks (unidentified: bag); $100, wt 15
- wiki/Skeleton_key.txt -- skeleton key (unidentified: key); $10, wt 3
- wiki/Lock_pick.txt -- lock pick; $20, wt 4
- wiki/Credit_card.txt -- credit card; $10, wt 1
- wiki/Light_source.txt (section: Candles) -- tallow candle (unidentified: candle)
- wiki/Light_source.txt (section: Candles) -- wax candle (unidentified: candle)
- wiki/Brass_lantern.txt -- brass lantern; $20, wt 30
- wiki/Oil_lamp.txt -- oil lamp (unidentified: lamp); $10, wt 20
- wiki/Magic_lamp.txt -- magic lamp (unidentified: lamp); $50, wt 20
- wiki/Expensive_camera.txt -- expensive camera; $200, wt 12
- wiki/Mirror.txt -- mirror (unidentified: looking glass); $10, wt 13
- wiki/Crystal_ball.txt -- crystal ball (unidentified: glass orb); $60, wt 150
- wiki/Pair_of_lenses.txt -- lenses; $80, wt 3
- wiki/Blindfold.txt -- blindfold; $20, wt 2
- wiki/Towel.txt -- towel; $50, wt 2
- wiki/Saddle.txt -- saddle; $150, wt 200
- wiki/Leash.txt -- leash; $20, wt 12
- wiki/Stethoscope.txt -- stethoscope; $75, wt 4
- wiki/Tinning_kit.txt -- tinning kit; $30, wt 100
- wiki/Tin_opener.txt -- tin opener; $30, wt 4
- wiki/Can_of_grease.txt -- can of grease; $20, wt 20
- wiki/Figurine.txt -- figurine; $80, wt 50
- wiki/Magic_marker.txt -- magic marker; $50, wt 2
- wiki/Land_mine.txt -- land mine
- wiki/Beartrap.txt -- beartrap; $60, wt 200
- wiki/Tin_whistle.txt -- tin whistle (unidentified: whistle); $10, wt 3
- wiki/Magic_whistle.txt -- magic whistle (unidentified: whistle); $10, wt 3
- wiki/Wooden_flute.txt -- wooden flute (unidentified: flute); $12, wt 5
- wiki/Magic_flute.txt -- magic flute (unidentified: flute); $36, wt 5
- wiki/Tooled_horn.txt -- tooled horn (unidentified: horn); $15, wt 18
- wiki/Frost_horn.txt -- frost horn (unidentified: horn); $50, wt 18
- wiki/Fire_horn.txt -- fire horn (unidentified: horn); $50, wt 18
- wiki/Horn_of_plenty.txt -- horn of plenty (unidentified: horn); $50, wt 18
- wiki/Wooden_harp.txt -- wooden harp (unidentified: harp); $50, wt 30
- wiki/Magic_harp.txt -- magic harp (unidentified: harp); $50, wt 30
- wiki/Bell.txt -- bell; $50, wt 30
- wiki/Bugle.txt -- bugle; $15, wt 10
- wiki/Leather_drum.txt -- leather drum (unidentified: drum); $25, wt 25
- wiki/Drum_of_earthquake.txt -- drum of earthquake (unidentified: drum); $25, wt 25
- wiki/Pick-axe.txt -- pick-axe; $50, wt 100, dmg 1d6/1d3
- wiki/Grappling_hook.txt -- grappling hook (unidentified: iron hook); $50, wt 30, dmg 1d2/1d6
- wiki/Unicorn_horn.txt -- unicorn horn; $100, wt 20, dmg 1d12/1d12
- wiki/Candelabrum_of_Invocation.txt -- Candelabrum of Invocation (unidentified: candelabrum); $5000, wt 10
- wiki/Bell_of_Opening.txt -- Bell of Opening (unidentified: silver bell); $5000, wt 10

### Potions !

- wiki/Potion.txt -- overview: Potion
- wiki/Potion_quaffing_effects.txt -- overview: Potion quaffing effects
- wiki/Vapors.txt -- overview: Vapors
- wiki/Potion_of_holy_water.txt -- overview: Potion of holy water
- wiki/Potion_of_unholy_water.txt -- overview: Potion of unholy water
- wiki/Potion_of_gain_ability.txt -- potion of gain ability (random appearance); $300
- wiki/Potion_of_restore_ability.txt -- potion of restore ability (random appearance); $100
- wiki/Potion_of_confusion.txt -- potion of confusion (random appearance); $100
- wiki/Potion_of_blindness.txt -- potion of blindness (random appearance); $150
- wiki/Potion_of_paralysis.txt -- potion of paralysis (random appearance); $300
- wiki/Potion_of_speed.txt -- potion of speed (random appearance); $200
- wiki/Potion_of_levitation.txt -- potion of levitation (random appearance); $200
- wiki/Potion_of_hallucination.txt -- potion of hallucination (random appearance); $100
- wiki/Potion_of_invisibility.txt -- potion of invisibility (random appearance); $150
- wiki/Potion_of_see_invisible.txt -- potion of see invisible (random appearance); $50
- wiki/Potion_of_healing.txt -- potion of healing (random appearance); $100
- wiki/Potion_of_extra_healing.txt -- potion of extra healing (random appearance); $100
- wiki/Potion_of_gain_level.txt -- potion of gain level (random appearance); $300
- wiki/Potion_of_enlightenment.txt -- potion of enlightenment (random appearance); $200
- wiki/Potion_of_monster_detection.txt -- potion of monster detection (random appearance); $150
- wiki/Potion_of_object_detection.txt -- potion of object detection (random appearance); $150
- wiki/Potion_of_gain_energy.txt -- potion of gain energy (random appearance); $150
- wiki/Potion_of_sleeping.txt -- potion of sleeping (random appearance); $100
- wiki/Potion_of_full_healing.txt -- potion of full healing (random appearance); $200
- wiki/Potion_of_polymorph.txt -- potion of polymorph (random appearance); $200
- wiki/Potion_of_booze.txt -- potion of booze (random appearance); $50
- wiki/Potion_of_sickness.txt -- potion of sickness (random appearance); $50
- wiki/Potion_of_fruit_juice.txt -- potion of fruit juice (random appearance); $50
- wiki/Potion_of_acid.txt -- potion of acid (random appearance); $250
- wiki/Potion_of_oil.txt -- potion of oil (random appearance); $250
- wiki/Potion_of_water.txt -- potion of water (unidentified: clear); $100

### Scrolls ?

- wiki/Scroll.txt -- overview: Scroll
- wiki/Scroll_of_enchant_armor.txt -- scroll of enchant armor (random appearance); $80
- wiki/Scroll_of_destroy_armor.txt -- scroll of destroy armor (random appearance); $100
- wiki/Scroll_of_confuse_monster.txt -- scroll of confuse monster (random appearance); $100
- wiki/Scroll_of_scare_monster.txt -- scroll of scare monster (random appearance); $100
- wiki/Scroll_of_remove_curse.txt -- scroll of remove curse (random appearance); $80
- wiki/Scroll_of_enchant_weapon.txt -- scroll of enchant weapon (random appearance); $60
- wiki/Scroll_of_create_monster.txt -- scroll of create monster (random appearance); $200
- wiki/Scroll_of_taming.txt -- scroll of taming (random appearance); $200
- wiki/Scroll_of_genocide.txt -- scroll of genocide (random appearance); $300
- wiki/Scroll_of_light.txt -- scroll of light (random appearance); $50
- wiki/Scroll_of_teleportation.txt -- scroll of teleportation (random appearance); $100
- wiki/Scroll_of_gold_detection.txt -- scroll of gold detection (random appearance); $100
- wiki/Scroll_of_food_detection.txt -- scroll of food detection (random appearance); $100
- wiki/Scroll_of_identify.txt -- scroll of identify (random appearance); $20
- wiki/Scroll_of_magic_mapping.txt -- scroll of magic mapping (random appearance); $100
- wiki/Scroll_of_amnesia.txt -- scroll of amnesia (random appearance); $200
- wiki/Scroll_of_fire.txt -- scroll of fire (random appearance); $100
- wiki/Scroll_of_earth.txt -- scroll of earth (random appearance); $200
- wiki/Scroll_of_punishment.txt -- scroll of punishment (random appearance); $300
- wiki/Scroll_of_charging.txt -- scroll of charging (random appearance); $300
- wiki/Scroll_of_stinking_cloud.txt -- scroll of stinking cloud (random appearance); $300
- wiki/Scroll_of_mail.txt -- scroll of mail (unidentified: stamped scroll); $0
- wiki/Scroll_of_blank_paper.txt -- scroll of blank paper (unidentified: unlabeled scroll); $60

### Spellbooks +

- wiki/Spellbook.txt -- overview: Spellbook
- wiki/Spellbook_of_dig.txt -- spellbook of dig (random appearance); spell level 5, matter
- wiki/Spellbook_of_magic_missile.txt -- spellbook of magic missile (random appearance); spell level 2, attack
- wiki/Spellbook_of_fireball.txt -- spellbook of fireball (random appearance); spell level 4, attack
- wiki/Spellbook_of_cone_of_cold.txt -- spellbook of cone of cold (random appearance); spell level 4, attack
- wiki/Spellbook_of_sleep.txt -- spellbook of sleep (random appearance); spell level 1, enchantment
- wiki/Spellbook_of_finger_of_death.txt -- spellbook of finger of death (random appearance); spell level 7, attack
- wiki/Spellbook_of_light.txt -- spellbook of light (random appearance); spell level 1, divination
- wiki/Spellbook_of_detect_monsters.txt -- spellbook of detect monsters (random appearance); spell level 1, divination
- wiki/Spellbook_of_healing.txt -- spellbook of healing (random appearance); spell level 1, healing
- wiki/Spellbook_of_knock.txt -- spellbook of knock (random appearance); spell level 1, matter
- wiki/Spellbook_of_force_bolt.txt -- spellbook of force bolt (random appearance); spell level 1, attack
- wiki/Spellbook_of_confuse_monster.txt -- spellbook of confuse monster (random appearance); spell level 2, enchantment
- wiki/Spellbook_of_cure_blindness.txt -- spellbook of cure blindness (random appearance); spell level 2, healing
- wiki/Spellbook_of_drain_life.txt -- spellbook of drain life (random appearance); spell level 2, attack
- wiki/Spellbook_of_slow_monster.txt -- spellbook of slow monster (random appearance); spell level 2, enchantment
- wiki/Spellbook_of_wizard_lock.txt -- spellbook of wizard lock (random appearance); spell level 2, matter
- wiki/Spellbook_of_create_monster.txt -- spellbook of create monster (random appearance); spell level 2, clerical
- wiki/Spellbook_of_detect_food.txt -- spellbook of detect food (random appearance); spell level 2, divination
- wiki/Spellbook_of_cause_fear.txt -- spellbook of cause fear (random appearance); spell level 3, enchantment
- wiki/Spellbook_of_clairvoyance.txt -- spellbook of clairvoyance (random appearance); spell level 3, divination
- wiki/Spellbook_of_cure_sickness.txt -- spellbook of cure sickness (random appearance); spell level 3, healing
- wiki/Spellbook_of_charm_monster.txt -- spellbook of charm monster (random appearance); spell level 3, enchantment
- wiki/Spellbook_of_haste_self.txt -- spellbook of haste self (random appearance); spell level 3, escape
- wiki/Spellbook_of_detect_unseen.txt -- spellbook of detect unseen (random appearance); spell level 3, divination
- wiki/Spellbook_of_levitation.txt -- spellbook of levitation (random appearance); spell level 4, escape
- wiki/Spellbook_of_extra_healing.txt -- spellbook of extra healing (random appearance); spell level 3, healing
- wiki/Spellbook_of_restore_ability.txt -- spellbook of restore ability (random appearance); spell level 4, healing
- wiki/Spellbook_of_invisibility.txt -- spellbook of invisibility (random appearance); spell level 4, escape
- wiki/Spellbook_of_detect_treasure.txt -- spellbook of detect treasure (random appearance); spell level 4, divination
- wiki/Spellbook_of_remove_curse.txt -- spellbook of remove curse (random appearance); spell level 3, clerical
- wiki/Spellbook_of_magic_mapping.txt -- spellbook of magic mapping (random appearance); spell level 5, divination
- wiki/Spellbook_of_identify.txt -- spellbook of identify (random appearance); spell level 3, divination
- wiki/Spellbook_of_turn_undead.txt -- spellbook of turn undead (random appearance); spell level 6, clerical
- wiki/Spellbook_of_polymorph.txt -- spellbook of polymorph (random appearance); spell level 6, matter
- wiki/Spellbook_of_teleport_away.txt -- spellbook of teleport away (random appearance); spell level 6, escape
- wiki/Spellbook_of_create_familiar.txt -- spellbook of create familiar (random appearance); spell level 6, clerical
- wiki/Spellbook_of_cancellation.txt -- spellbook of cancellation (random appearance); spell level 7, matter
- wiki/Spellbook_of_protection.txt -- spellbook of protection (random appearance); spell level 1, clerical
- wiki/Spellbook_of_jumping.txt -- spellbook of jumping (random appearance); spell level 1, escape
- wiki/Spellbook_of_stone_to_flesh.txt -- spellbook of stone to flesh (random appearance); spell level 3, healing
- wiki/Spellbook_of_blank_paper.txt -- spellbook of blank paper (unidentified: plain); $0, wt 50
- wiki/Novel.txt -- novel (unidentified: paperback); $20, wt 1
- wiki/Book_of_the_Dead.txt -- Book of the Dead (unidentified: papyrus); $10000, wt 20

### Gems and stones *

- wiki/Gem.txt -- overview: Gem
- wiki/Gray_stone.txt -- overview: Gray stone
- wiki/Dilithium_crystal.txt -- dilithium crystal (unidentified: white gem); $4500, wt 1
- wiki/Gem.txt -- diamond (unidentified: white gem)
- wiki/Gem.txt -- ruby (unidentified: red gem)
- wiki/Gem.txt -- jacinth (unidentified: orange gem)
- wiki/Gem.txt -- sapphire (unidentified: blue gem)
- wiki/Gem.txt -- black opal (unidentified: black gem)
- wiki/Gem.txt -- emerald (unidentified: green gem)
- wiki/Gem.txt -- turquoise (unidentified: green gem)
- wiki/Gem.txt -- citrine (unidentified: yellow gem)
- wiki/Gem.txt -- aquamarine (unidentified: green gem)
- wiki/Gem.txt -- amber (unidentified: yellowish brown gem)
- wiki/Gem.txt -- topaz (unidentified: yellowish brown gem)
- wiki/Gem.txt -- jet (unidentified: black gem)
- wiki/Gem.txt -- opal (unidentified: white gem)
- wiki/Gem.txt -- chrysoberyl (unidentified: yellow gem)
- wiki/Gem.txt -- garnet (unidentified: red gem)
- wiki/Amethyst_stone.txt -- amethyst (unidentified: violet gem); $600, wt 1
- wiki/Gem.txt -- jasper (unidentified: red gem)
- wiki/Gem.txt -- fluorite (unidentified: violet gem)
- wiki/Gem.txt -- obsidian (unidentified: black gem)
- wiki/Gem.txt -- agate (unidentified: orange gem)
- wiki/Gem.txt -- jade (unidentified: green gem)
- wiki/Gem.txt -- worthless piece of white glass (unidentified: white gem)
- wiki/Gem.txt -- worthless piece of blue glass (unidentified: blue gem)
- wiki/Gem.txt -- worthless piece of red glass (unidentified: red gem)
- wiki/Gem.txt -- worthless piece of yellowish brown glass (unidentified: yellowish brown gem)
- wiki/Gem.txt -- worthless piece of orange glass (unidentified: orange gem)
- wiki/Gem.txt -- worthless piece of yellow glass (unidentified: yellow gem)
- wiki/Gem.txt -- worthless piece of black glass (unidentified: black gem)
- wiki/Gem.txt -- worthless piece of green glass (unidentified: green gem)
- wiki/Gem.txt -- worthless piece of violet glass (unidentified: violet gem)
- wiki/Luckstone.txt -- luckstone (unidentified: gray stone); $60, wt 10, dmg 1d3/1d3
- wiki/Loadstone.txt -- loadstone (unidentified: gray stone); $1, wt 500, dmg 1d3/1d3
- wiki/Touchstone.txt -- touchstone (unidentified: gray stone); $45, wt 10, dmg 1d3/1d3
- wiki/Flint_stone.txt -- flint (unidentified: gray stone); $1, wt 10, dmg 1d6/1d6
- wiki/Rock.txt -- rock; $0, wt 10, dmg 1d3/1d3

### Comestibles (food) %

- wiki/Comestible.txt -- overview: Comestible
- wiki/Glob.txt -- overview: Glob
- wiki/Tripe_ration.txt -- tripe ration; $15, wt 10, nutr 200
- wiki/Corpse.txt -- corpse; $5
- wiki/Egg.txt -- egg; $9, wt 1, nutr 80
- wiki/Meatball.txt -- meatball; $5, wt 1, nutr 5
- wiki/Meat_stick.txt -- meat stick; $5, wt 1, nutr 5
- wiki/Huge_chunk_of_meat.txt -- huge chunk of meat; $105, wt 400, nutr 2000
- wiki/Glob.txt -- glob of gray ooze
- wiki/Glob.txt -- glob of brown pudding
- wiki/Glob.txt (section: Globs of green slime) -- glob of green slime
- wiki/Glob.txt -- glob of black pudding
- wiki/Kelp_frond.txt -- kelp frond; $6, wt 1, nutr 30
- wiki/Eucalyptus_leaf.txt -- eucalyptus leaf; $6, wt 1, nutr 30
- wiki/Apple.txt -- apple; $7, wt 2, nutr 50
- wiki/Orange.txt -- orange; $9, wt 2, nutr 80
- wiki/Pear.txt -- pear; $7, wt 2, nutr 50
- wiki/Melon.txt -- melon; $10, wt 5, nutr 100
- wiki/Banana.txt -- banana; $9, wt 2, nutr 80
- wiki/Carrot.txt -- carrot; $7, wt 2, nutr 50
- wiki/Sprig_of_wolfsbane.txt -- sprig of wolfsbane; $7, wt 1, nutr 40
- wiki/Clove_of_garlic.txt -- clove of garlic; $7, wt 1, nutr 40
- wiki/Slime_mold.txt -- slime mold; $17, wt 5, nutr 250
- wiki/Lump_of_royal_jelly.txt -- lump of royal jelly; $15, wt 2, nutr 200
- wiki/Cream_pie.txt -- cream pie; $10, wt 10, nutr 100
- wiki/Candy_bar.txt -- candy bar; $10, wt 2, nutr 100
- wiki/Fortune_cookie.txt -- fortune cookie; $7, wt 1, nutr 40
- wiki/Pancake.txt -- pancake; $15, wt 2, nutr 200
- wiki/Lembas_wafer.txt -- lembas wafer; $45, wt 5, nutr 800
- wiki/Cram_ration.txt -- cram ration; $35, wt 15, nutr 600
- wiki/Food_ration.txt -- food ration; $45, wt 20, nutr 800
- wiki/K-ration.txt -- K-ration; $25, wt 10, nutr 400
- wiki/C-ration.txt -- C-ration; $20, wt 10, nutr 300
- wiki/Tin.txt -- tin; $5, wt 10
- wiki/Meat_ring.txt -- meat ring; $5, wt 1, nutr 5

### Coins $

- wiki/Zorkmid.txt -- gold piece; $1, wt 0.01

### Boulders, statues, iron balls, chains, venom ` 0 _

- wiki/Boulder.txt -- boulder; $0, wt 6000
- wiki/Statue.txt -- statue; $0, wt varies
- wiki/Heavy_iron_ball.txt -- heavy iron ball; $10, wt 480
- wiki/Iron_chain.txt -- iron chain; $0, wt 120
- wiki/Venom.txt -- blinding venom (unidentified: splash of venom); $0, wt 1
- wiki/Venom.txt -- acid venom (unidentified: splash of venom)

### Artifacts

- wiki/Artifact.txt -- overview: Artifact
- wiki/Quest_artifact.txt -- overview: Quest artifact
- wiki/Unique_item.txt -- overview: Unique item
- wiki/Excalibur.txt -- Excalibur; $4000, wt 40, dmg 1d8 +1d10/1d12 +1d10; drain resistance; automatic searching; improved searching (special)
- wiki/Stormbringer.txt -- Stormbringer; $8000, wt 40, dmg 2d4 +1d2 +1d8/1d6+1 +1d2 +1d8; bloodthirsty; drain resistance
- wiki/Mjollnir.txt -- Mjollnir; $4000, wt 50, dmg 1d4+1 +1d24/1d4 +1d24; throwable; lightning strikes on hit
- wiki/Cleaver.txt -- Cleaver; $1500, wt 120, dmg 1d8+1d4 +1d6/1d6+2d4 +1d6
- wiki/Grimtooth.txt -- Grimtooth; $300, wt 10, dmg 1d3 +1d6/1d3 +1d6; detect elves
- wiki/Orcrist.txt -- Orcrist; $2000, wt 70, dmg 1d6+1d4 ×2/1d6+1 ×2; detect orcs
- wiki/Sting.txt -- Sting; $800, wt 10, dmg 1d5 x2/1d3 x2; detect orcs
- wiki/Magicbane.txt -- Magicbane; $3500, wt 10, dmg 1d4 +1d4 +/1d3 +1d4 +; magic resistance; absorbs and negates 95% of curses; special attacks
- wiki/Frost_Brand.txt -- Frost Brand; $3000, wt 40, dmg 1d8 ×2/1d12 ×2; cold resistance
- wiki/Fire_Brand.txt -- Fire Brand; $3000, wt 40, dmg 1d8 ×2/1d12 ×2; fire resistance
- wiki/Dragonbane.txt -- Dragonbane; $500, wt 70, dmg 2d4 x2/1d6+1 x2; reflection
- wiki/Demonbane.txt -- Demonbane; $2500, wt 40, dmg 1d8 x2/1d12 x2; prevents demon gating
- wiki/Werebane.txt -- Werebane; $1500, wt 40, dmg 1d8 x2 +/1d8 x2 +; prevents; lycanthropy
- wiki/Grayswandir.txt -- Grayswandir; $8000, wt 40, dmg 1d8 ×2 +/1d8 ×2 +; hallucination resistance
- wiki/Giantslayer.txt -- Giantslayer; $200, wt 40, dmg 1d8 ×2/1d12 ×2
- wiki/Ogresmasher.txt -- Ogresmasher; $200, wt 50, dmg 1d4+1 x2/1d4 x2; sets constitution to 25
- wiki/Trollsbane.txt -- Trollsbane; $200, wt 120, dmg 2d4 ×2/1d6+1 ×2
- wiki/Vorpal_Blade.txt -- Vorpal Blade; $4000, wt 40, dmg 1d8 +1/1d12 +1; beheading
- wiki/Snickersnee.txt -- Snickersnee; $1200, wt 40, dmg 1d10 +1d8/1d12 +1d8
- wiki/Sunsword.txt -- Sunsword; $1500, wt 40, dmg 1d8 x2/1d12 x2; light source; blocks light-based blindness
- wiki/The_Orb_of_Detection.txt -- The Orb of Detection; $2500, wt 150; telepathy; magic resistance; half spell damage
- wiki/The_Heart_of_Ahriman.txt -- The Heart of Ahriman; $2500, wt 10; stealth
- wiki/The_Sceptre_of_Might.txt -- The Sceptre of Might; $2500, wt 30, dmg 1d6+1 ×2/1d6 ×2; magic resistance
- wiki/The_Staff_of_Aesculapius.txt -- The Staff of Aesculapius; $5000, wt 40, dmg 1d6 ×2 +1d8/1d6 ×2 +1d8; hungerless regeneration; drain resistance
- wiki/The_Magic_Mirror_of_Merlin.txt -- The Magic Mirror of Merlin; $1500, wt 13; telepathy; magic resistance (special)
- wiki/The_Eyes_of_the_Overworld.txt -- The Eyes of the Overworld; $2500, wt 3
- wiki/The_Mitre_of_Holiness.txt -- The Mitre of Holiness; $2000, wt 40; fire resistance
- wiki/The_Longbow_of_Diana.txt -- The Longbow of Diana; $4000, wt 30, dmg 1d2/1d2; reflection
- wiki/The_Master_Key_of_Thievery.txt -- The Master Key of Thievery; $3500, wt 3; warning; teleport control; half physical damage
- wiki/The_Tsurugi_of_Muramasa.txt -- The Tsurugi of Muramasa; $4500, wt 60, dmg 1d16 +1d8/1d8+2d6 +1d8; bisection; protection
- wiki/The_Platinum_Yendorian_Express_Card.txt -- The Platinum Yendorian Express Card; $7000, wt 1; telepathy; magic resistance; half spell damage
- wiki/The_Orb_of_Fate.txt -- The Orb of Fate; $3500, wt 150; warning; half spell damage; half physical damage; acts as luckstone
- wiki/The_Eye_of_the_Aethiopica.txt -- The Eye of the Aethiopica; $4000, wt 20; faster energy regeneration; half spell damage

## Mechanics

### Character and attributes

- wiki/Hit_points.txt -- Max HP growth per level, natural regeneration, and dying at 0 HP
- wiki/Energy.txt -- Power (Pw) for spellcasting: maximum, growth and regeneration
- wiki/Experience_level.txt -- Experience levels 1-30: XP thresholds, gaining and losing levels
- wiki/Experience_points.txt -- How experience points are earned from kills and other actions
- wiki/Attribute.txt -- The six attributes (Str/Dex/Con/Int/Wis/Cha), limits and exercise
- wiki/Strength.txt -- Strength: to-hit/damage bonuses, carrying capacity, 18/xx notation
- wiki/Dexterity.txt -- Dexterity: to-hit bonus, multishot and spellcasting effects
- wiki/Constitution.txt -- Constitution: HP gained per level and carrying capacity
- wiki/Intelligence.txt -- Intelligence: spell failure for Int casters; brain-eating kills at 3
- wiki/Wisdom.txt -- Wisdom: energy regeneration and spell failure for Wis casters
- wiki/Charisma.txt -- Charisma: shop prices and a few other effects
- wiki/Armor_class.txt -- AC: how armor protects; negative AC also reduces damage taken
- wiki/Encumbrance.txt -- Carrying capacity and Burdened..Overloaded penalties
- wiki/Weight.txt -- Item weights and how they add to your load
- wiki/Speed.txt -- Movement speed: intrinsic/extrinsic fast, very fast, monster speeds
- wiki/Skill.txt -- Weapon and spell skills: training, per-role maximums, #enhance
- wiki/Enhance.txt -- #enhance: advance a skill once it has enough training
- wiki/Twoweapon.txt -- #twoweapon: fighting with two weapons, restrictions and skill
- wiki/Spellcasting.txt -- Casting spells: failure rate formula, armor penalties, energy cost
- wiki/Spell.txt -- What spells are; pointers to spellcasting and spellbooks

### Combat and item mechanics

- wiki/To-hit.txt -- To-hit formula: Luck, level, skill, encumbrance and target AC
- wiki/Damage.txt -- How melee and missile damage is calculated, including bonuses
- wiki/D_notation.txt -- Dice notation (XdY) used for damage and random rolls
- wiki/Combat.txt -- Melee combat basics and tactics
- wiki/Ranged_attack.txt -- In NetHack, a ranged attack is one that can hit a target more than one ...
- wiki/Multishot.txt -- In NetHack, the hero and monsters are capable of multishot when throwing or firing certain ...
- wiki/Erosion.txt -- Rust, corrosion, burning, rotting; erosion-proofing and repair
- wiki/Enchantment.txt -- Weapon/armor enchantment (+N) and safe enchanting limits
- wiki/BUC.txt -- Blessed/uncursed/cursed status and how to learn it
- wiki/Artifact.txt -- All artifacts: alignment, sacrifice gifts, wishing, touching
- wiki/Artifact_blast.txt -- Touching cross-aligned artifacts hurts you; when it happens
- wiki/Bane.txt -- A Bane is a semi-informal name used to refer to a group of artifact weapons ...
- wiki/Item.txt -- Item classes and general object mechanics
- wiki/Discoveries.txt -- The \ discoveries list of item types you have identified

### Properties and intrinsics

- wiki/Property.txt -- Intrinsic vs extrinsic properties; full list and sources
- wiki/Resistance.txt -- All resistances and how to obtain each
- wiki/Magic_resistance.txt -- MR: blocks death rays, polymorph, teleport traps, destroy armor and more
- wiki/Reflection.txt -- Reflects rays and gazes (death, disintegration, Medusa); sources
- wiki/Free_action.txt -- Prevents most paralysis (floating eye, gelatinous cube, potions)
- wiki/Telepathy.txt -- Sense monsters' minds while blind (intrinsic) or always (extrinsic)
- wiki/Stealth.txt -- Move without waking sleeping monsters; sources
- wiki/See_invisible.txt -- See invisible monsters; sources
- wiki/Invisibility.txt -- Being invisible: benefits, shopkeepers refuse service, sources
- wiki/Infravision.txt -- See warm-blooded monsters in the dark (non-human races)
- wiki/Warning.txt -- Shows numbers for nearby hostiles by threat level
- wiki/Displacement.txt -- Displacement property: monsters see you where you are not
- wiki/Clairvoyance.txt -- Periodically maps the nearby area (donations, cornuthaum, Amulet)
- wiki/Enlightenment.txt -- Reveals your hidden attributes and intrinsics
- wiki/Conflict.txt -- Monsters fight each other (ring of conflict); angers peacefuls
- wiki/Sustain_ability.txt -- Sustain ability is a property that appears in NetHack and prevents most changes to the ...
- wiki/Slow_digestion.txt -- Greatly reduces food consumption (ring of slow digestion)
- wiki/Half_spell_damage.txt -- Half spell damage is an extrinsic property that occurs in NetHack, and reduces damage taken ...
- wiki/Half_physical_damage.txt -- Half physical damage is an extrinsic property in NetHack which halves many types of physical ...
- wiki/Water_walking.txt -- Water walking is a property in NetHack that allows you to walk over deep water ...
- wiki/Flying.txt -- Flying: cross water, lava and pits while still reaching the floor
- wiki/Levitation.txt -- Floating: can't pick up items or go downstairs; escaping it
- wiki/Breathless.txt -- Magical breathing: can't drown, immune to gases
- wiki/Life_saving.txt -- Amulet of life saving: survive one death
- wiki/Protection_from_shape_changers.txt -- Protection from shape changers is a property in NetHack that prevents shape changer monsters from ...
- wiki/Monster_detection.txt -- Monster detection is a property in NetHack that allows a hero to see all monsters ...
- wiki/Object_detection.txt -- Object detection is an item effect in NetHack that allows a hero to see all ...
- wiki/Invulnerability.txt -- Invulnerability is a condition temporarily granted to the character while they make a successful prayer ...
- wiki/Teleportation.txt -- Teleporting within a level: sources, control, no-teleport levels
- wiki/Teleport_control.txt -- Teleport control is a property that occurs in NetHack, and allows the hero or a ...
- wiki/Teleportitis.txt -- Teleportitis is a property that causes the player to teleport occasionally
- wiki/Polymorph_control.txt -- Polymorph control is a property in NetHack that allows the hero to maintain control over ...
- wiki/Polymorphitis.txt -- The intrinsic property polymorphitis gives a 1% chance per turn of polymorphing into a random ...
- wiki/Unchanging.txt -- Unchanging is a property in NetHack that prevents the hero from being polymorphed or otherwise ...
- wiki/Regeneration_(property).txt -- Regeneration: Regeneration property: 1 HP per turn (ring of regeneration, trolls)
- wiki/Automatic_searching.txt -- Automatic searching is a useful property that causes you to automatically search every square around ...
- wiki/Aggravate_monster.txt -- Aggravate monster is a property in NetHack that makes it easier for monsters to notice ...
- wiki/Jumping.txt -- Jumping (knights, jumping boots/spell): range and uses
- wiki/Voracious_hunger.txt -- Hunger property: nutrition burns fast (ring of hunger, some corpses)
- wiki/Ring.txt (section: Ring hunger) -- Ring hunger: Extra nutrition used by worn rings and amulets
- wiki/Fumbling.txt -- Fumbling is a property acquired extrinsically by wearing gauntlets of fumbling or fumble boots
- wiki/Hit_points.txt (section: Hit point recovery) -- Hit point regeneration: How fast HP comes back naturally, by level and Con
- wiki/Energy.txt (section: Energy regeneration) -- Energy regeneration: How fast power (Pw) comes back, by role, Wis/Int, energy regeneration

### Resistances

- wiki/Fire_resistance.txt -- Fire resistance: sources and what it protects against
- wiki/Cold_resistance.txt -- Cold resistance: sources and protection (Valkyries start with it)
- wiki/Shock_resistance.txt -- Shock resistance: sources and protection
- wiki/Sleep_resistance.txt -- Sleep resistance: sources and protection
- wiki/Disintegration_resistance.txt -- Disintegration resistance: black dragon scales; survive disintegration
- wiki/Poison_resistance.txt -- Poison resistance: essential; sources and what it prevents
- wiki/Acid_resistance.txt -- Acid resistance is a form of resistance property that appears in NetHack
- wiki/Stoning_resistance.txt -- Stoning resistance is a resistance property that appears in NetHack, and protects against the effects ...
- wiki/Drain_resistance.txt -- Drain resistance, or level drain resistance, is a property in NetHack that nullifies attacks and ...
- wiki/Immunity_to_sickness.txt -- Immunity to sickness (also known as sickness resistance) is a property that appears in NetHack, ...
- wiki/Hallucination_resistance.txt -- Hallucination resistance is a rare resistance property that occurs in NetHack, and protects against the ...
- wiki/Monster_resistances.txt -- Table of which monsters resist which damage types

### Status effects, ailments and instadeaths

- wiki/Blindness.txt -- Blindness is a property that appears in NetHack, and blocks the ability of a hero ...
- wiki/Confusion.txt -- Confusion, or the state of being confused, is a property that affects you
- wiki/Stun.txt -- A player or monster that is stunned has lost control over its movements
- wiki/Hallucination.txt -- Hallucination is a status-impairing property that appears in NetHack, and shows up on the status ...
- wiki/Deafness.txt -- Deafness is a status property effect that occurs in NetHack
- wiki/Wounded_legs.txt -- Wounded legs is a temporary intrinsic property that occurs in NetHack and impairs the ability ...
- wiki/Paralysis.txt -- Paralysis is a magically-induced inability to move
- wiki/Sleep.txt -- Sleep is a status condition that occurs in NetHack, and can affect both the hero ...
- wiki/Glib.txt -- Glib is a property in NetHack that occurs as a result of a hero using ...
- wiki/Vomiting.txt -- Vomiting or nausea is a status affliction caused by eating
- wiki/Stoning.txt -- Turning to stone: cures (lizard, acidic corpse, stone to flesh, prayer)
- wiki/Sliming.txt -- Turning into green slime: cure with fire, prayer or polymorph
- wiki/Strangulation.txt -- Strangulation is a property in NetHack that induces a delayed instadeath by choking
- wiki/Sickness.txt -- Illness and food poisoning: deadly; cure with unicorn horn, prayer, potions
- wiki/Sickness.txt (section: Illness) -- Illness: Sickness is a property in NetHack that can induce a delayed instadeath after a set ...
- wiki/Sickness.txt (section: Food poisoning) -- Food poisoning: Sickness is a property in NetHack that can induce a delayed instadeath after a set ...
- wiki/Lycanthropy.txt -- Lycanthropy is an intrinsic property that appears in NetHack and is heavily associated with werecreatures
- wiki/Drain_life_(monster_attack).txt -- Level drain: Losing experience levels to drain attacks
- wiki/Poison.txt -- Poison is a damage type that appears in NetHack, and can occur from various hazards, ...
- wiki/Punishment.txt -- Punishment is a state that occurs in NetHack where a hero has a heavy iron ...
- wiki/Instant_death.txt -- Catalogue of instadeaths and how to prevent each
- wiki/Delayed_instadeath.txt -- Countdown deaths (stoning, sliming, illness, strangulation) and cures
- wiki/Drowning.txt -- Drowning by eels or water; how to survive it
- wiki/Disintegration.txt -- Disintegration is an extremely rare form of damage type that occurs in NetHack
- wiki/Touch_of_death.txt -- The touch of death is a monster spell in NetHack that is cast by some ...
- wiki/Intelligence_drain.txt -- Intelligence drain, also known as drain intelligence, is a damage type that appears very rarely ...
- wiki/Nutrition.txt (section: Hunger status) -- Starvation: In NetHack, nutrition is a stat that is essential for keeping the hero alive

### Monster mechanics

- wiki/Monster.txt -- In NetHack, a monster is any creature that you may encounter while exploring the Mazes ...
- wiki/Monster_class.txt -- All monsters belong to a monster class, based on the default ASCII monster symbol that ...
- wiki/Monster_difficulty.txt -- In NetHack, a monster's difficulty is a number from 1 to 57 which represents the ...
- wiki/Monster_level.txt -- Monster level is the experience level of a monster
- wiki/Monster_creation.txt -- Monster creation is the process by which NetHack determines when, where and how a particular ...
- wiki/Peaceful.txt -- Monster behavior: In NetHack, monsters that are peaceful do not attack you, and will simply wander around ...
- wiki/Monster_starting_inventory.txt -- In NetHack, certain types of monsters may be created with objects in their starting inventory ...
- wiki/Monsters_(by_speed).txt -- This is a list of monsters in NetHack sorted by speed, then by monster difficulty ...
- wiki/Monsters_(by_experience).txt -- This is a list of monsters in NetHack sorted by base experience value, then by ...
- wiki/Unique_monster.txt -- In NetHack, there are various unique monsters that are usually only generated once, which is ...
- wiki/Player_monster.txt -- A player monster is any type of monster in NetHack that represents one of the ...
- wiki/Quest_guardian.txt -- Quest guardians are peaceful humans generated on the Home level of the Quest in NetHack
- wiki/Demon_lords_and_princes.txt -- In NetHack, several unique, named demon lords and princes sit above the ranks of the ...
- wiki/Covetous.txt -- In NetHack, a covetous monster is a monster that desires one or more unique items ...
- wiki/Shapeshifter.txt -- In NetHack, a shapeshifter or shape changer is a monster that can change form either ...
- wiki/Monster_spell.txt -- In NetHack, a monster spell is a category of spell that only spell-casting monsters can ...
- wiki/Passive_attack.txt -- In NetHack, some monsters possess a passive attack - it is used automatically in retaliation ...
- wiki/Holding_attack.txt -- A holding attack prevents the player from moving away from a monster
- wiki/Engulfing.txt -- An engulfing attack is one which involves you being caught inside a monster, whether by ...
- wiki/Gaze_attack.txt -- A gaze attack is a form of offense that some monsters in NetHack have, which ...
- wiki/Theft.txt -- On NetHackWiki, theft can refer to any of the following:
- wiki/Werecreature.txt -- A werecreature or lycanthrope is a type of monster that appears in NetHack, and can ...
- wiki/Foocubus.txt -- In NetHack, the term foocubus (plural foocubi, derived from foo) refers to either one or ...
- wiki/Hiding.txt -- In NetHack, some monsters have the ability to hide
- wiki/Bribe.txt -- Certain monsters in Nethack can be bribed

### Commands and interface

- wiki/Commands.txt -- Command: In NetHack, a command is an action you want the game to perform
- wiki/Apply.txt -- Apply, `a`, is a command in NetHack that lets the player use an item
- wiki/Far_look.txt -- The far look command is a feature in NetHack, used by pressing the semicolon key ...
- wiki/Force.txt -- In NetHack, the hero can force open locked containers using a weapon
- wiki/Loot.txt -- Loot is also the general name by which the stuff that you have found is ...
- wiki/Untrap.txt -- The #untrap extended command will attempt to disable an adjacent trap if it can be ...
- wiki/Chat.txt -- Using this command will normally prompt the player to select a cardinal direction, and if ...
- wiki/Sit.txt -- Sitting is a form of extended command that appears in NetHack, and is performed by ...
- wiki/Rub.txt
- wiki/Invoke.txt -- The #invoke extended command allows you to activate certain objects
- wiki/Name.txt -- Naming items in NetHack can be very helpful for keeping track of items
- wiki/Call.txt -- In NetHack, you can call (or name) a monster by pressing `C`
- wiki/Pay.txt -- Pay is a command that appears in NetHack
- wiki/Throw.txt -- You can throw just about any object you can carry in your inventory
- wiki/Firing.txt -- Firing is the act of shooting (`f`) ammunition from a quiver (`Q`) using a launcher
- wiki/Quiver.txt -- Your quiver is a location in your knapsack where you store your projectiles
- wiki/Wield.txt -- Press `w` to wield a weapon
- wiki/Wear.txt -- Wear, `W`, is a command used to wear pieces of armor and shields
- wiki/Put_on.txt -- The put on command is, by default, mapped to `P`
- wiki/Remove.txt -- The remove command is, by default, mapped to capital R: `R`
- wiki/Take_off.txt -- Take off, `T`, is a command used to take off worn armor and shields
- wiki/Zap.txt -- To zap a wand, press `z`. Some wands, like the wand of light or the ...
- wiki/Read.txt -- By pressing `r` you can read something
- wiki/Quaff.txt -- Quaffing, done by hitting `q`, means drinking
- wiki/Eat.txt -- Eating is a command that appears in NetHack, and is performed using the `e` key
- wiki/Open.txt -- Press `o` to open a door
- wiki/Close.txt -- Close, `c`, is a command that is used to close an open door
- wiki/Pick_up.txt -- You can pick up items from the dungeon floor using the `,` key
- wiki/Drop.txt -- To drop something is to remove it from your inventory and place it on the ...
- wiki/Rest.txt -- Resting, or waiting, is a type of command available to the hero in NetHack, and ...
- wiki/Search.txt -- The search command is a feature in NetHack that searches the 8 squares surrounding you ...
- wiki/Kick.txt -- Kicking doors, objects and monsters; risks
- wiki/Travel.txt -- Travel is a feature in some NetHack ports that allows one to move quickly along ...
- wiki/Numeric_prefix.txt -- Many commands in NetHack can be preceded by a numeric prefix, which modifies the action ...
- wiki/Swap_weapons.txt -- Press `x` to swap wielded primary weapon and secondary weapon
- wiki/Dip.txt -- The player will be prompted, first, for an object to be dipped, then an object ...
- wiki/Sacrifice.txt -- Offer: In NetHack, sacrifice is an action performed at an altar that can reduce the hero's ...
- wiki/Turn_undead.txt -- The #turn (turn undead) extended command is a command in NetHack
- wiki/Autopickup.txt -- Autopickup is an option, on by default, that specifies that your character automatically picks up ...
- wiki/Options.txt -- Like most other games, NetHack has options that affect the look and feel of the ...
- wiki/Options.txt (section: autodig) -- Autodig: Like most other games, NetHack has options that affect the look and feel of the ...
- wiki/You_hear.txt -- This is a list of messages in NetHack that begin with "You hear"
- wiki/You_have_a_strange_feeling_for_a_moment_then_it_passes.txt -- Strange feeling: You have a strange feeling for a moment, then it passes
- wiki/Hallucinatory_messages.txt -- In NetHack, you may encounter some unexpected messages while hallucinating
