# Configure, build and test the native plugin and its host policy tests. Never deploys anything to Skyrim.
#   ./build.ps1 -VcpkgRoot C:\vcpkg                       (or set VCPKG_ROOT)
#   ./build.ps1 -VcpkgRoot C:\vcpkg -Generator 'Visual Studio 17 2022'
# The vcpkg checkout must be at the pinned baseline and bootstrapped (vcpkg.exe present).
[CmdletBinding()]
param(
    [ValidateSet('Release', 'Debug')][string]$Configuration = 'Release',
    [string]$VcpkgRoot = $env:VCPKG_ROOT,
    [string]$Generator = 'Visual Studio 18 2026'
)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$buildRoot = Join-Path $sourceRoot 'build'
$pinnedCommonLib = 'b93280e832f263dbef44e44cbe2936622a02f91a'
$pinnedVcpkg = '817892b0ecbc6af994dd6df999c73faf795adbf2'

if (-not $VcpkgRoot) { throw 'Pass -VcpkgRoot or set VCPKG_ROOT to a vcpkg checkout at the pinned baseline.' }
if (-not (Test-Path -LiteralPath (Join-Path $VcpkgRoot 'vcpkg.exe'))) { throw "No vcpkg.exe in '$VcpkgRoot'; run its bootstrap-vcpkg.bat first." }

# Refuse silently changed dependency checkouts before invoking their build logic.
$commonLibRevision = & git -C (Join-Path $sourceRoot 'extern/commonlibsse-ng') rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $commonLibRevision -ne $pinnedCommonLib) { throw "CommonLibSSE-NG checkout differs from the pinned revision $pinnedCommonLib (run: git submodule update --init)." }
$vcpkgRevision = & git -C $VcpkgRoot rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $vcpkgRevision -ne $pinnedVcpkg) { throw "vcpkg checkout differs from the pinned baseline $pinnedVcpkg." }

# WindowsApps aliases can be inaccessible to build tools; keep this workaround process-local.
$previousPath = $env:Path
$previousMetrics = $env:VCPKG_DISABLE_METRICS
try {
    $env:Path = ($env:Path -split ';' | Where-Object { $_ -and $_ -notlike '*\Microsoft\WindowsApps*' }) -join ';'
    $env:VCPKG_DISABLE_METRICS = '1'
    & cmake -S $sourceRoot -B $buildRoot -G $Generator -A x64 "-DCMAKE_TOOLCHAIN_FILE=$VcpkgRoot/scripts/buildsystems/vcpkg.cmake" '-DVCPKG_TARGET_TRIPLET=x64-windows-static' '-DVCPKG_HOST_TRIPLET=x64-windows-static'
    if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }
    & cmake --build $buildRoot --config $Configuration --parallel 8
    if ($LASTEXITCODE -ne 0) { throw 'Native build failed.' }
    & ctest --test-dir $buildRoot -C $Configuration --output-on-failure
    if ($LASTEXITCODE -ne 0) { throw 'Policy tests failed.' }
    Write-Host "Built: $buildRoot/$Configuration/NemesisCombatAI.dll"
} finally {
    $env:Path = $previousPath
    $env:VCPKG_DISABLE_METRICS = $previousMetrics
}
