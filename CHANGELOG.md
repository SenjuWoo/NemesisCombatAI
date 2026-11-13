# Changelog

## 3.0.7

Crash hardening on top of 3.0.6.

- A C++ exception inside any plugin callback (startup, data loaded, save, load, revert, queued work) is written to the log as `<where>: <message>` instead of leaving the callback and closing the game.
- The log file is optional. A Documents path with characters outside the system code page, or a folder the game may not write to, used to throw during plugin load; the plugin now runs without a file log.
- The plugin refuses to load, with one log line, when SKSE does not hand over its serialization, messaging or task interface.
- A null actor name can no longer reach the log formatter.
- No gameplay, record, FormID, settings or co-save change from 3.0.6.

## 3.0.6 (beta)

Audit release. Static gates pass; this binary has not been run in game yet.

- **For Honor masters keep their Dynamic Grip exclusion when `GripTiers` is off.** Since 3.0.3 the first evaluation of any fighter released every keyword this plugin owned, masters included, whenever the grip option was not installed. The decision is now one tested rule: a master is always blocked, everyone else only while the option is on.
- **Boss bonus works with the tiered styles.** Bosses were recognised only by the two vanilla boss styles, which SkyPatcher has already swapped for the Nemesis boss pool in a Full tactics install. The plugin now also recognises its own boss styles (ids generated from the same table as the plugin).
- **Fear and rally effects are left alone.** The authored Confidence is read from the permanent value, so a temporary effect is no longer mistaken for the authored value and partly cancelled by the morale shift.
- **Optimised binary.** `xmake f -m release` matched no mode rule, so 3.0.1-3.0.5 were compiled without optimisation and with assertions. The build now applies the release mode (DLL about half the size).
- A shift stored in a save is taken back before the first evaluation after loading, not after it.
- Settings files: a UTF-8 byte-order mark is accepted, unknown keys and values that are not 0/1/true/false are reported in the log, and `Debug=1` logs every verdict and release. The first releases of a session are now logged like the first verdicts.
- Documentation: uninstall instructions now say what is true (load a save made out of combat, or let the plugin clean it once, before removing the mod); the co-save is described as version 2; the Morale only installer option names the faction style pools it keeps.
- Build and CI: host tests keep their assertions in every build mode and CI proves they can fail; the package check compares version strings across the build file, installer and docs; xmake is pinned in CI.

## 3.0.5 (beta)

Beta: every static gate and the 1.6.1170 load/init/save-load path pass; live Confidence readback is still outstanding.

- Dynamic Grip ownership moved into one ledger. `ReleaseAll()` now clears the bookkeeping even when this plugin never added a keyword - a base that only holds a For Honor master no longer leaves a stale exclusion behind on a world change or when the option is switched off.
- Caster grading uses an explicit `GradeState` (`graded` flag + world generation) instead of overloading generation 0 as "never graded". The first world of a process always grades, a failed or skipped pass stays retryable, and `Reset()` is called whenever styles are restored.
- Documentation now separates runtime-confirmed support (AE 1.6.1170) from declared support (1.6.629-1.6.1179, 1.7.99, 1.7.104) in both README and INSTALL.
- Tests cover the state transitions: first world grading, repeat pass, failed pass retry, save A -> B -> A, ledger release with owned/foreign keywords, and repeated cleanup.

## 3.0.4

- `OnRevert` now gives back both in-memory edits before the world changes: owned Dynamic Grip keywords are removed and edited caster styles are restored, so the next save starts from the authored data instead of inheriting the previous world's edits.
- Fixed the generation guard: a fresh process (world generation 0) no longer looks like "already graded in world 0", so the first grading pass always runs; a failed or disabled pass stays retryable.
- Release packager refuses a DLL whose SKSE version block does not match `--expect-version`.
- INSTALL testing section corrected (3.0.2 text replaced with the actual 3.0.3/3.0.4 evidence).
- No gameplay, record, FormID or co-save layout change beyond 3.0.3.

## 3.0.3

- **Fixed the Confidence modifier.** In this CommonLibSSE fork `RestoreActorValue()` converts the amount to `|delta|` and posts it on the damage channel, so 3.0.1/3.0.2 applied morale bonuses as penalties and left temporary damage instead of a base change. Shifts now use `ModActorValue(kPermanent)`, which keeps both the sign and the authored value.
- Co-save record version is now 2. Version 1 records (3.0.0-3.0.2) describe a different channel and amount, so they are dropped with one warning instead of being replayed with a guess. New saves store signed permanent deltas.
- Every release path now hands the shift back: combat end, death, unload, `OnRevert` (which also releases any actor still resident before clearing state), and switching the feature off.
- Dynamic Grip: keywords this plugin added are released when the grip option is off, and ownership is reconciled on save load, so a keyword another mod removed is no longer claimed.
- Caster grading keeps each base's authored combat style and can restore it, and retries per world instead of a permanent one-shot flag.
- Docs: release-zip command corrected (it takes the built DLL), 3.0.3 identifiers everywhere, update note for saves made with 3.0.0-3.0.2.

## 3.0.2

- Corrected the SKSE version-independence declaration. The plugin reads and writes engine structures (`Actor::currentCombatTarget`, `TESNPC::combatStyle` and its level data, `TESGlobal::value`, `ProcessLists::highActorHandles`), so it now declares the post-1.6.629 layout instead of claiming `NoStructUse`. Same code paths, same behaviour; the loader sees an accurate declaration.
- Skyrim SE 1.5.97 is refused at load (one log line) instead of running against the pre-1.6.629 structure layout. Supported builds are AE 1.6.629 through 1.7.104.
- Not a behaviour change: records, FormIDs, settings, MCM ids and the `NMSI` v1 co-save are untouched. 3.0.1 stays available for rollback.

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
