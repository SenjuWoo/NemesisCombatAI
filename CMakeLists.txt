# Build the native NPC policy and its host checks against pinned CommonLibSSE-NG.
cmake_minimum_required(VERSION 3.25)
project(NemesisCombatAI VERSION 3.0.0 LANGUAGES CXX)

# Keep all native dependencies on the same static release/debug CRT.
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set(ENABLE_SKYRIM_SE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_AE ON CACHE BOOL "" FORCE)
set(ENABLE_SKYRIM_VR OFF CACHE BOOL "" FORCE)
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(extern/commonlibsse-ng)
target_compile_options(CommonLibSSE PRIVATE /MP8)

# Keep the build machine's folder names out of the shipped DLL (__FILE__ strings in asserts and log locations).
file(TO_NATIVE_PATH "${CMAKE_CURRENT_SOURCE_DIR}" NCAI_TRIM)
target_compile_options(CommonLibSSE PRIVATE "/d1trimfile:${NCAI_TRIM}")

# Main owns SKSE metadata so runtime declarations stay next to admission checks.
add_library(NemesisCombatAI SHARED src/main.cpp)
target_link_libraries(NemesisCombatAI PRIVATE CommonLibSSE::CommonLibSSE)
target_include_directories(NemesisCombatAI PRIVATE src)
target_compile_definitions(NemesisCombatAI PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
target_compile_options(NemesisCombatAI PRIVATE /W4 /permissive- /Zc:__cplusplus /utf-8 /Brepro "/d1trimfile:${NCAI_TRIM}")
target_link_options(NemesisCombatAI PRIVATE /Brepro)
set_target_properties(NemesisCombatAI PROPERTIES PREFIX "")

# Policy checks run without Skyrim; assertions remain active in release builds.
enable_testing()
add_executable(policy_tests tests/policy_tests.cpp)
target_include_directories(policy_tests PRIVATE src)
target_compile_options(policy_tests PRIVATE /W4 /permissive- /utf-8 /UNDEBUG)
add_test(NAME policy_tests COMMAND policy_tests)
