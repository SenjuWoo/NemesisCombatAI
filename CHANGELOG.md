# Changelog

## 3.0.1

- Addresses the startup failure `REL/ID.h(219): failed to open address library file` that 3.0.0 caused on Skyrim 1.7.104 (reported by several users right after release). Verification on 1.7.104 is still pending: the fix is build-validated (version block and format-5 reader present in the binary) and the DLL is load-tested on 1.6.1170.
- Cause: 3.0.0 was built on a CommonLibSSE pin that only knows game builds up to 1.6.x and only reads Address Library formats 1-2, and its version block did not set the `AddressLibraryV5` flag SKSE uses for 1.7.x. SKSE's build-timestamp fallback let the plugin load, and its own address library reader then failed.
- The plugin now builds on CommonLibSSE (libxse fork): game builds 1.5.97 through 1.7.104 with one DLL, Address Library format 5 (v13) included. The version block declares Address Library independence and the v5 contract, and `tools/verify_version_block.py` checks the built binary in CI.
- The C runtime is linked statically, so the Visual C++ redistributable is no longer a requirement.
- No gameplay change: same records, FormIDs, settings, MCM ids and `NMSI` v1 co-save.

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
