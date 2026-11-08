# Native build dependencies

Pinned so the build does not float:

- **CommonLibSSE** (libxse fork) commit `4506c635`, with its `lib/commonlib-shared` submodule at `29fbdb0e` (submodule at `extern/commonlibsse`, from https://github.com/libxse/commonlibsse). This fork covers game builds 1.5.97 through 1.7.104 and reads Address Library formats 1-2 (1.6.x) and 5 (1.7.x). The older CharmedBaryon CommonLibSSE-NG pin used by 3.0.0 stopped at 1.6.x and could not read the 1.7.104 library, which is what produced the `REL/ID.h(219)` popup. Licensed GPL-3.0-or-later with the Modding Exception and the GPL-3.0 Linking Exception; the release payload carries both texts under `00 Core/licenses/`.
- **xmake** 3.0 or newer drives the build; the `commonlibsse.plugin` rule generates the plugin resource and the SKSE version block.
- **spdlog** 1.16.0, fetched by xmake at configure time as declared by the fork. It is not pinned by hash: xmake resolves the version from its own package repository.

The version block also states the structure-layout contract. This plugin reads and writes engine fields
(`Actor::currentCombatTarget`, `TESNPC::combatStyle`, `TESActorBaseData` level data, `TESGlobal::value`,
`ProcessLists::highActorHandles`), all of which are at the same offset in the SE-era and current headers, but the
binary is compiled against the post-1.6.629 layout. It therefore sets `kVersionIndependent_StructsPost629` and
leaves `NoStructUse` clear, and it refuses to load on Skyrim SE 1.5.97 (pre-1.6.629). The `AddressLibraryV5` ex-bit declares support for the v5 (1.7.x) address-library format; it does not mean formats 1-2 stop working, and the reader keeps all three paths compiled in. The shipped SKSE version block is part of the product, not a build detail: it must declare Address Library independence **and** the v5 flag (`versionIndependenceEx` bit 1). Without the v5 flag SKSE's build-timestamp fallback lets the plugin load on 1.7.x and it then fails inside the address library reader. `tools/verify_version_block.py` checks the built DLL for that contract and CI fails when it is missing.

The plugin is built with `/Brepro`, a trimmed `__FILE__` prefix and the static C runtime (`set_runtimes("MT")`): no checkout path ends up in the binary and no redistributable is needed. The link is not bit-for-bit reproducible (the PDB signature differs per link), so a rebuilt DLL is compared by behaviour and by `tools/verify_version_block.py`, not by hash. The Windows SDK and MSVC version are part of the toolchain: release binaries are built with Visual Studio 2026. CI builds with the Visual Studio version on GitHub's `windows-latest` image, which can differ from the release toolchain, so its DLL is a build check, not the release binary.
