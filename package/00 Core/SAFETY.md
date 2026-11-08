# What this mod touches, and what it never does

**Never:** starts combat, forces animations, adds factions, disables AI, hooks game functions, runs per-frame work, edits attacks, perks, packages, OAR/BFCO/For Honor files, parry rules or animation variables.

**Per-actor, at runtime (native plugin):**
- Shifts the engine's own **Confidence** value by a tracked amount while an enemy is in combat, and takes exactly that amount off again when combat ends, the actor dies or unloads, or the MCM master toggle goes off. The result is clamped to the engine's 0..4 scale.
- An amount still outstanding at save time is stored in the SKSE co-save (record `NMSI` v1, the 2.x layout), so a save made mid-fight is cleaned on load; old 2.x records restore the same way.
- Skipped by default: followers and teammates, essential actors, named uniques, anyone not hostile to the player, children, and **animals** (wolves, bears and the like keep their own nerve).
- If For Honor is installed, any NPC it marks as a weapon master (its perk, ForHonorBFCO.esp `0xD7B`) is treated as Elite. If Dynamic Grip is also installed, that NPC's base is given Dynamic Grip's own blacklist keyword (DynamicGrip.esp `0x815`, editor ID `DynamicGrip_BlacklistKwd`) so Dynamic Grip leaves its For Honor moveset alone. Only people are touched, never the player, and only keywords this plugin added are ever removed. The keyword is held in memory for the session; nothing about it is written to your save.

**Once per session, at the first load (native plugin, optional):** the combat style of human-like casters on the vanilla mage styles (csHumanMagic, csWE31Mage, csWERangedConjurer, csSoldierMagic, csWarlock, csForswornMagic, csVampireMagic, csDraugrMagic) is switched to one of eight Nemesis caster styles chosen from the caster's own level and skill. Followers, named uniques (while Skip Uniques is on), template NPCs and non-people are left alone. This is the same base-record change SkyPatcher makes.

**At load time (SkyPatcher):** `NemesisCombatAI_Styles.esp.ini` swaps combat styles only for NPCs on the vanilla human melee, Draugr, archer, Forsworn and boss styles, using 23 Nemesis styles. `ZZZ_NemesisCombatAI.ini` keeps the 2.x faction style pools; it loads after the tier file, so with Full tactics the human-melee faction lines in it no longer find their targets (the tier file already restyled them) and the caster lines are superseded by the level grading. Neither file changes Aggression or Confidence.

**To undo everything:** disable the mod. Combat styles and keywords are not saved in your game. Any Confidence still applied at the moment you save and quit is removed the next time that save is loaded.

Built and tool-checked. Gameplay was played on 3.0.0; the 3.0.1 DLL was load-tested on Skyrim 1.6.1170 (3.0.2 changes only the version declaration and adds a Skyrim SE 1.5.97 refusal) and has not been played, nor run on 1.7.x yet. Long-session, large-battle and mod-interaction testing is still open: report problems with `NemesisCombatAI.log` from `Documents\My Games\Skyrim Special Edition\SKSE`.
