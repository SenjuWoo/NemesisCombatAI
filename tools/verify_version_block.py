#!/usr/bin/env python3
"""Read the SKSE plugin version block out of a built DLL.

Why this exists: the reachable game versions and the Address Library flags live only in that struct. A build
that silently loses the AddressLibraryV5 bit loads on 1.7.x and then dies inside the address library reader
(REL/ID.h), which is exactly the 3.0.0 failure users reported. This checks the shipped bytes, not the source.
Usage: python tools/verify_version_block.py <dll> [--expect-version 3.0.1]
Exit code 0 = every expectation met; 1 = mismatch; 2 = could not read.
"""
import struct
import sys

ADDRESS_LIBRARY_POST_AE = 1 << 0   # versionIndependence: plugin resolves IDs through the address library
NO_STRUCT_USE = 1 << 0             # versionIndependenceEx: no engine struct layout is touched
ADDRESS_LIBRARY_V5 = 1 << 1        # versionIndependenceEx: reader understands the 1.7.x (format 5) library


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    base = pe + 24 + opt_size
    out = []
    for i in range(count):
        off = base + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, off + 8)
        out.append((name, va, vsize, rawptr, rawsize))
    return out


def rva_to_offset(secs, rva):
    for _name, va, vsize, rawptr, rawsize in secs:
        if va <= rva < va + max(vsize, rawsize):
            return rawptr + (rva - va)
    raise ValueError(f"RVA 0x{rva:x} is not inside any section")


def exports(data):
    """Return {name: rva} using the export directory (small, so a manual walk is enough)."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dirs = opt + (112 if magic == 0x20B else 96)
    exp_rva, exp_size = struct.unpack_from("<II", data, dirs)
    if not exp_rva:
        return {}
    secs = sections(data)
    e = rva_to_offset(secs, exp_rva)
    n_names = struct.unpack_from("<I", data, e + 24)[0]
    names_rva = struct.unpack_from("<I", data, e + 32)[0]
    ords_rva = struct.unpack_from("<I", data, e + 36)[0]
    funcs_rva = struct.unpack_from("<I", data, e + 28)[0]
    n_table = rva_to_offset(secs, names_rva)
    o_table = rva_to_offset(secs, ords_rva)
    f_table = rva_to_offset(secs, funcs_rva)
    out = {}
    for i in range(n_names):
        name_at = rva_to_offset(secs, struct.unpack_from("<I", data, n_table + 4 * i)[0])
        name = data[name_at:data.index(b"\0", name_at)].decode("ascii", "replace")
        ordinal = struct.unpack_from("<H", data, o_table + 2 * i)[0]
        out[name] = struct.unpack_from("<I", data, f_table + 4 * ordinal)[0]
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    expect = None
    if "--expect-version" in sys.argv:
        expect = sys.argv[sys.argv.index("--expect-version") + 1]

    data = open(path, "rb").read()
    exp = exports(data)
    if "SKSEPlugin_Version" not in exp:
        print("FAIL: no SKSEPlugin_Version export")
        return 1
    off = rva_to_offset(sections(data), exp["SKSEPlugin_Version"])

    (data_version, plugin_version) = struct.unpack_from("<II", data, off)
    name = data[off + 8:off + 8 + 256].split(b"\0")[0].decode("ascii", "replace")
    author = data[off + 264:off + 264 + 256].split(b"\0")[0].decode("ascii", "replace")
    ex, independence = struct.unpack_from("<II", data, off + 772)
    compatible = [struct.unpack_from("<I", data, off + 780 + 4 * i)[0] for i in range(16)]
    # VersionPackInfo in this fork: major<<24 | minor<<16 | patch<<4 | build
    major, minor, patch = (plugin_version >> 24) & 0xFF, (plugin_version >> 16) & 0xFF, (plugin_version >> 4) & 0xFFF
    reachable = [f"{(c >> 24) & 0xFF}.{(c >> 16) & 0xFF}.{(c >> 4) & 0xFFF}" for c in compatible if c]

    checks = [
        ("dataVersion == 1", data_version == 1),
        ("name", name == "NemesisCombatAI"),
        ("author", author == "GennyWoo"),
        ("address library independence set", bool(independence & ADDRESS_LIBRARY_POST_AE)),
        ("AddressLibraryV5 set (1.7.x library)", bool(ex & ADDRESS_LIBRARY_V5)),
        ("no struct use set", bool(ex & NO_STRUCT_USE)),
    ]
    if expect:
        checks.append((f"version {expect}", f"{major}.{minor}.{patch}" == expect))

    print(f"{path}\n  name={name} author={author} version={major}.{minor}.{patch}")
    print(f"  versionIndependence=0x{independence:08X} versionIndependenceEx=0x{ex:08X} compatible={reachable[:4]}")
    ok = True
    for label, passed in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {label}")
        ok &= passed
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
