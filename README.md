<p align="center">
  <img src="assets/mark.svg" width="72" height="72" alt="Nemesis Combat AI">
</p>

<div align="center">

# Nemesis Combat AI

<p>
  <a href="https://github.com/SenjuWoo/NemesisCombatAI/actions/workflows/ci.yml"><img src="https://github.com/SenjuWoo/NemesisCombatAI/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-8C3A32?labelColor=0d1117" alt="MIT License"></a>
  <a href="https://github.com/SenjuWoo/NemesisCombatAI/releases/latest"><img src="https://img.shields.io/github/v/release/SenjuWoo/NemesisCombatAI?label=release&color=8C3A32&labelColor=0d1117" alt="latest release"></a>
</p>

</div>

Enemy nerve, morale and tactics for Skyrim Special Edition / Anniversary Edition: a native SKSE plugin plus a pack of tiered combat styles. Enemies get a mind rating from their level, combat skill, faction rank, leader title and faction doctrine, and the fight itself moves their nerve. Low-level enemies are cowardly and dumb, trained soldiers hold, veterans turn desperate instead of breaking, and elites stay composed. Movesets, attacks and animations are never touched: [For Honor In Skyrim BFCO](https://www.nexusmods.com/skyrimspecialedition/mods/185459) owns movesets.

The mod is distributed on [Nexus Mods](https://www.nexusmods.com/skyrimspecialedition/mods/185305) and as a FOMOD archive on the [releases page](../../releases). This repository is its source.

## What it does

- **Morale layer (native plugin, event-driven).** Reacts to combat starting, deaths and hits; no hooks, no Papyrus polling, no per-frame work. Only the engine's own Confidence value is moved, by a tracked amount that is taken off again when the fight ends, the actor dies or unloads, or the mod is switched off. Anything outstanding at save time is stored in the SKSE co-save and cleaned on load.
- **Tiered combat styles.** 31 styles in a light plugin for human melee, Draugr, archers, Forsworn, bosses and mages, applied through SkyPatcher. Mages are regraded once per session by the plugin from each caster's own level and skill.
- **For Honor wins.** An NPC that For Honor marks as a weapon master (its perk) is treated as Elite, and when Dynamic Grip is installed it is added to Dynamic Grip's own blacklist keyword so its For Honor moveset is not replaced.
- **Dynamic Grip support.** An optional setting lets only trained-or-better fighters, never casters, switch grips.
- **Auto-detecting installer.** The FOMOD looks for For Honor, Dynamic Grip, NPC Spell Variance, SkyTactics, SkyUI and MCM Helper by plugin name and ships only the matching settings.

## Requirements

SKSE64 and the Address Library for SKSE Plugins, both matching your game build. One DLL serves Skyrim AE 1.6.629 or newer (1.6.x, 1.7.99, 1.7.104); 1.7.99/1.7.104 need Address Library All-in-One v13 or newer, 1.6.x uses v11. Skyrim SE 1.5.97 uses the older structure layout and the plugin refuses to load on it. The plugin links the C runtime statically, so the Visual C++ redistributable is not required. SkyPatcher is needed for the tiered styles, SkyUI and MCM Helper for the menu. Dynamic Grip, For Honor In Skyrim BFCO and NPC Spell Variance are optional and detected automatically. Skyrim SE/AE only; VR is not supported.

## Settings

In game: Mod Configuration Menu, Nemesis Combat AI. Files: `Data/SKSE/Plugins/NemesisCombatAI.d/*.ini` with `CasterTiers=0|1`, `GripTiers=0|1` and `CasterStyle=Plugin.esp|HexFormID` to grade another mod's caster style. Later file names win.

## Repository layout

| Path | What |
|---|---|
| `src/` | Plugin source. `Policy.h` is the pure rating/morale policy, `main.cpp` the SKSE runtime, `StyleIds.h` is generated. |
| `tests/` | Host tests of the policy (no Skyrim needed). |
| `tools/` | `make_styles_esp.py` generates the styles plugin, its SkyPatcher INI and `StyleIds.h` from one table; `check_package.py` verifies them; `make_release_zip.py` builds the release archive; `verify_version_block.py` reads the SKSE version block out of a built DLL (the Address Library contract). |
| `package/` | Everything that ships except the DLL: plugins, MCM config, scripts, INIs, FOMOD, licences. |
| `extern/commonlibsse` | CommonLibSSE (libxse fork), pinned by submodule; it covers game builds 1.5.97 through 1.7.104 and reads Address Library formats 1-2 and 5. This plugin refuses 1.5.97 because it is compiled against the post-1.6.629 structure layout. |

## Building

Requirements: Visual Studio 2026 with the C++ x64 workload and Windows SDK, xmake 3.0+, Git, Python 3.

```powershell
git clone --recurse-submodules https://github.com/SenjuWoo/NemesisCombatAI
cd NemesisCombatAI
xmake f -p windows -a x64 -m release -y
xmake b -y                                    # plugin and host policy tests
./build/windows/x64/release/policy_tests.exe
python tools/verify_version_block.py build/windows/x64/release/NemesisCombatAI.dll --expect-version 3.0.3
python tools/check_package.py
python tools/make_release_zip.py build/windows/x64/release/NemesisCombatAI.dll ../NemesisCombatAI-3.0.3.zip
```

The plugin is linked with the static C runtime, so it does not need the Visual C++ redistributable. The build never deploys anything to your game.

## Status

3.0.2 is a compatibility rebuild of 3.0.0 (3.0.1 corrected the Address Library v5 declaration, 3.0.2 corrected the structure-layout declaration and refuses Skyrim SE 1.5.97). Verified on Skyrim AE **1.6.1170.0 with SKSE 2.2.8**: the plugin loads (`skse64.log`: `plugin NemesisCombatAI.dll (00000001 NemesisCombatAI 03000020) loaded correctly`) and initialises (`NemesisCombatAI.log`: config read from both INI files, For Honor and Dynamic Grip integrations found, `ready: combat, death and hit sinks registered`, tiered styles plugin active). **Not yet run on 1.7.99/1.7.104**, the builds the original fix is for - 1.7.x reports with `skse64.log` and `NemesisCombatAI.log` are wanted. Gameplay was played on 3.0.0 on 1.6.1170 and no gameplay code changed since; combat, MCM and save/load have not been replayed on 3.0.2. Host tests and a successful load do not prove runtime safety. There are no screenshots yet.

## Licence and credits

The source and package files are released under the [MIT licence](LICENSE). The plugin statically links CommonLibSSE (libxse fork, GPL-3.0-or-later with the Modding Exception and the GPL-3.0 Linking Exception), spdlog and fmt under their own licences; their notices and the licence texts ship in [`package/00 Core/THIRD-PARTY-NOTICES.txt`](package/00%20Core/THIRD-PARTY-NOTICES.txt) and `package/00 Core/licenses/`. Dynamic Grip is by bosn; no files or assets of Dynamic Grip, For Honor or NPC Spell Variance are included.

The plugin source, installer and documentation were written with AI assistance and then built, tested and checked with tools and in game.
