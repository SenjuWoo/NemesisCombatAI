# Nemesis Combat AI

Enemy nerve, morale and tactics for Skyrim Special Edition / Anniversary Edition: a native SKSE plugin plus a pack of tiered combat styles. Enemies get a mind rating from their level, combat skill, faction rank, leader title and faction doctrine, and the fight itself moves their nerve. Low-level enemies are cowardly and dumb, trained soldiers hold, veterans turn desperate instead of breaking, and elites stay composed. Movesets, attacks and animations are never touched: [For Honor In Skyrim BFCO](https://www.nexusmods.com/skyrimspecialedition/mods/185459) owns movesets.

The mod is distributed on [Nexus Mods](https://www.nexusmods.com/skyrimspecialedition/mods/185305) and as a FOMOD archive on the [releases page](../../releases). This repository is its source.

## What it does

- **Morale layer (native plugin, event-driven).** Reacts to combat starting, deaths and hits; no hooks, no Papyrus polling, no per-frame work. Only the engine's own Confidence value is moved, by a tracked amount that is taken off again when the fight ends, the actor dies or unloads, or the mod is switched off. Anything outstanding at save time is stored in the SKSE co-save and cleaned on load.
- **Tiered combat styles.** 31 styles in a light plugin for human melee, Draugr, archers, Forsworn, bosses and mages, applied through SkyPatcher. Mages are regraded once per session by the plugin from each caster's own level and skill.
- **For Honor wins.** An NPC that For Honor marks as a weapon master (its perk) is treated as Elite, and when Dynamic Grip is installed it is added to Dynamic Grip's own blacklist keyword so its For Honor moveset is not replaced.
- **Dynamic Grip support.** An optional setting lets only trained-or-better fighters, never casters, switch grips.
- **Auto-detecting installer.** The FOMOD looks for For Honor, Dynamic Grip, NPC Spell Variance, SkyTactics, SkyUI and MCM Helper by plugin name and ships only the matching settings.

## Requirements

SKSE64, Address Library for SKSE Plugins, Microsoft Visual C++ x64 runtime, SkyPatcher (styles), SkyUI and MCM Helper (menu). Dynamic Grip, For Honor In Skyrim BFCO and NPC Spell Variance are optional and detected automatically. Skyrim SE/AE only; VR is not supported.

## Settings

In game: Mod Configuration Menu, Nemesis Combat AI. Files: `Data/SKSE/Plugins/NemesisCombatAI.d/*.ini` with `CasterTiers=0|1`, `GripTiers=0|1` and `CasterStyle=Plugin.esp|HexFormID` to grade another mod's caster style. Later file names win.

## Repository layout

| Path | What |
|---|---|
| `src/` | Plugin source. `Policy.h` is the pure rating/morale policy, `main.cpp` the SKSE runtime, `StyleIds.h` is generated. |
| `tests/` | Host tests of the policy (no Skyrim needed). |
| `tools/` | `make_styles_esp.py` generates the styles plugin, its SkyPatcher INI and `StyleIds.h` from one table; `check_package.py` verifies them; `make_release_zip.py` builds the release archive. |
| `package/` | Everything that ships except the DLL: plugins, MCM config, scripts, INIs, FOMOD. |
| `extern/commonlibsse-ng` | CommonLibSSE-NG, pinned by submodule. |

## Building

Requirements: Visual Studio 2026 with the C++ x64 workload and Windows SDK (what CI and the release build use; pass `-Generator 'Visual Studio 17 2022'` for 2022, which is untested), CMake 3.25+, Git, Python 3.

```powershell
git clone --recurse-submodules https://github.com/SenjuWoo/NemesisCombatAI
# vcpkg at the pinned baseline (see DEPENDENCIES.md), bootstrapped:
git clone https://github.com/microsoft/vcpkg C:\vcpkg
git -C C:\vcpkg checkout 817892b0ecbc6af994dd6df999c73faf795adbf2
C:\vcpkg\bootstrap-vcpkg.bat -disableMetrics

cd NemesisCombatAI
./build.ps1 -VcpkgRoot C:\vcpkg   # builds, then runs the policy tests
python tools/check_package.py
python tools/make_release_zip.py build/Release/NemesisCombatAI.dll NemesisCombatAI.zip
```

The build never deploys anything to your game. Local builds trim the source folder out of embedded `__FILE__` strings, so a build from any checkout location contains no personal paths.

## Status

Built from source, host-tested and statically validated. A real play session on an earlier build confirmed that the plugin loads, finds its integrations, grades casters and applies morale without errors. Not yet confirmed in game: Dynamic Grip honoring the exclusion on For Honor masters in every situation, long sessions, very large battles and every mod combination. Host tests and a successful build do not prove runtime safety. There are no screenshots yet.

## Licence and credits

The source and package files are released under the [MIT licence](LICENSE). The plugin statically links CommonLibSSE-NG, spdlog, fmt and rapidcsv under their own licences; their notices ship in [`package/00 Core/THIRD-PARTY-NOTICES.txt`](package/00%20Core/THIRD-PARTY-NOTICES.txt). Dynamic Grip is by bosn; no files or assets of Dynamic Grip, For Honor or NPC Spell Variance are included.

The plugin source, installer and documentation were written with AI assistance and then built, tested and checked with tools and in game.
