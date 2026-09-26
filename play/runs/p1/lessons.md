# p1 lessons (general, keep short)

- Never pick up blindly with a helper: check `here()` first (I grabbed a 350-wt locked large box). Kicking a box open shatters potions; #force with a blade risks the blade.
- Any object list must exclude shop stock (`for sale`) before choosing a corpse/loot target; a bad travel target cost 49 turns and made a fresh corpse too old.
- Corpse rule of thumb used: eat only kills < ~30 turns old, never dwarves/dogs/cats/were/cockatrice; lichen corpses never rot.
- Fight at doorway choke points: stand in the corridor square outside the door so packs (jackals, coyotes) come one at a time.
- The square just inside a shop door is the shopkeeper's home square: drops there get no offer; the shopkeeper blocks it for a turn or two — wait with `s`, then step out.
- Sell-offer price-ID: offer = base/2 (or base*3/8 for 25% of shopkeepers). Offer 10 => identify; offer 50 => 100zm ring.
- Trap doors can drop you a level before you found the downstairs: always know the `<` on arrival (search dead ends for hidden passages).
- Cropped-map column counting is error prone: use a coordinate-returning helper (`objects()`), not eyeballing.
- NEVER wield a weapon of unknown B/U/C status (picked-up orcish dagger welded itself to my hand at T:1267). If a throwaway weapon is needed, use the one already known uncursed (my +0 dagger) — or just don't.
- Prayer does NOT fix minor trouble (welded weapon, cursed items) when Luck is 0 off an altar (pray.c pleased(): action = rn1(Luck+2,1) → 1..2 fixes major only; minor needs action ≥ 3 → Luck ≥ 1). Only pray for major trouble (HP < 1/7, Weak, FoodPois, Stone, Slime, Strngl). Check the source before betting the prayer on a mechanic.
