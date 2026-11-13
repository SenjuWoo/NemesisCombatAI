-- Static CRT: an SKSE plugin must not depend on the Visual C++ redistributable being installed.
set_runtimes("MT")

-- Keep the checkout path out of the binary (assert and log __FILE__ strings) and stamp the link with /Brepro.
-- The link is not bit-for-bit reproducible (the PDB signature differs per link), so this is privacy, not a hash pin.
add_cxflags('/d1trimfile:"' .. os.projectdir() .. '"', "/Brepro", { force = true })
add_ldflags("/Brepro", { force = true })

-- Builds the NPC combat-mind plugin and its host checks.
-- The library is CommonLibSSE (libxse fork): it knows runtimes 1.5.97 through 1.7.104 and reads Address
-- Library formats 1 and 2 (1.6.x) and 5 (1.7.x), which the older CommonLibSSE-NG pin cannot do.
includes("extern/commonlibsse")

set_project("NemesisCombatAI")
set_version("3.0.8")
set_license("MIT")
set_languages("c++23")
set_warnings("allextra")
set_arch("x64")

-- "xmake f -m release" must match a mode rule: without mode.release the build silently got no /O2 and no NDEBUG
-- (3.0.1-3.0.5 shipped unoptimised).
add_rules("mode.release", "mode.releasedbg")

-- The mod itself. The commonlibsse.plugin rule generates the SKSE version block from the options below.
-- address_library: engine IDs come from the Address Library, never from fixed exe offsets.
-- no_struct_use=false / layout_dependent=true: this plugin DOES read and write engine structures
-- (Actor::currentCombatTarget, TESNPC::combatStyle and its level data, TESGlobal::value,
-- ProcessLists::highActorHandles) and is compiled against the post-1.6.629 layout, so it must say so.
-- 1.5.97 carries the pre-1.6.629 layout and is refused at load in main.cpp instead of writing at wrong offsets.
target("NemesisCombatAI")
    add_rules("commonlibsse.plugin", {
        name = "NemesisCombatAI",
        author = "GennyWoo",
        description = "NPC combat mind: tiered morale, leader effects, caster style grading",
        license = "MIT",
        options = { address_library = true, no_struct_use = false, layout_dependent = true }
    })
    add_files("src/**.cpp")
    add_headerfiles("src/**.h")
    add_includedirs("src")
    add_defines("NOMINMAX", "WIN32_LEAN_AND_MEAN")

-- Policy checks run without Skyrim. The test file undefines NDEBUG itself so its assertions survive any mode.
target("policy_tests")
    set_kind("binary")
    add_files("tests/policy_tests.cpp")
    add_includedirs("src")

-- Same file with one assertion that is false on purpose. CI runs it and requires a failure, which proves the
-- assertions in policy_tests are really compiled in.
target("policy_selftest")
    set_kind("binary")
    add_files("tests/policy_tests.cpp")
    add_includedirs("src")
    add_defines("NCAI_SELFTEST_FAIL")
