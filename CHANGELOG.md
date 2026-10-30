# Changelog

## 3.0.0

- Rebuilt as a lightweight native SKSE plugin: event-driven, no Papyrus scanning, no per-frame work.
- Enemies get a mind rating (rabble, trained, veteran, elite) from level, combat skill, faction rank, titles and doctrine. Allies, leaders, casualties, outnumbering, health, much stronger targets and archers move their nerve; veterans and elites go into a last stand instead of fleeing.
- New: 31 tiered combat styles in a light plugin for human melee, Draugr, archers, Forsworn, bosses and mages. Replaces SkyTactics.
- New: mages are graded by their own level, including modded enemies that reuse the vanilla mage styles. Other mods' caster styles can be added with a `CasterStyle` line.
- New: For Honor wins. NPCs that For Honor picks as weapon masters are treated as elites and kept out of Dynamic Grip.
- New: Dynamic Grip support. Only trained-or-better fighters, never casters, switch grips.
- New: auto-detecting installer (For Honor, Dynamic Grip, NPC Spell Variance, SkyTactics, SkyUI, MCM Helper).
- Animals, followers, teammates, essential NPCs and named uniques are skipped by default. "Skip Friendly" now means only enemies of the player.
- Removed: the For Honor Hero Gate overlay (For Honor chooses its own masters), aggression edits, stat surge and the equipment threat cap.
- Settings saved in the menu carry over.

Earlier versions (1.x and 2.x) were distributed on Nexus Mods only; their source was not preserved.
