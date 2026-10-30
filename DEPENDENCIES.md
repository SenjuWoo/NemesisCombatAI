# Native build dependencies

Pinned so the build does not float:

- **CommonLibSSE-NG** commit `b93280e832f263dbef44e44cbe2936622a02f91a` (submodule at `extern/commonlibsse-ng`, from https://github.com/CharmedBaryon/CommonLibSSE-NG). Its CMake project identifies itself as 3.6.0 while its manifest says 3.7.0; the commit is authoritative. Only SE and AE are compiled; VR and CommonLib's test dependencies are disabled.
- **vcpkg** baseline `817892b0ecbc6af994dd6df999c73faf795adbf2` (`vcpkg.json` `builtin-baseline`). Resolved packages for triplet `x64-windows-static`: rapidcsv 9.07, spdlog 1.17.0#1, fmt 12.2.0#1, vcpkg-cmake 2025-08-07, vcpkg-cmake-config 2026-07-21.

`build.ps1` refuses to build when either checkout differs from its pin. The vcpkg executable itself is not pinned by hash: any bootstrapped vcpkg at the baseline commit works.

The plugin is built with `/Brepro` and `/d1trimfile:<source root>`, so the same sources, toolchain and dependency pins give the same binary from any checkout location. The Windows SDK and MSVC version are part of the toolchain: release binaries are built with Visual Studio 2026 (generator `Visual Studio 18 2026`, the default). CI builds with the Visual Studio version on GitHub's `windows-latest` image, which can differ from the release toolchain, so its DLL is a build check, not the release binary.

`build.ps1` removes the `WindowsApps` directory from `PATH` only while its child tools run, because inaccessible executable aliases there break vcpkg helper discovery; it never edits your environment permanently.
