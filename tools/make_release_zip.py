"""Builds the FOMOD release archive: package/ plus the built DLL. Deterministic: entries sorted by archive path,
fixed timestamps, forward-slash paths, no build output or manager bookkeeping.
Usage: make_release_zip.py <NemesisCombatAI.dll> <out.zip>"""
import hashlib, os, sys, zipfile

DLL_ARC = '00 Core/SKSE/Plugins/NemesisCombatAI.dll'
BANNED = ('__folder_managed_by_vortex', 'meta.ini', '.meta', 'Thumbs.db', '.pdb', '.log')

dll, out = sys.argv[1], sys.argv[2]
package = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'package')

entries = {}
for d, _, names in os.walk(package):
    for n in names:
        assert not n.endswith(BANNED), f'bookkeeping or debug file in payload: {n}'
        path = os.path.join(d, n)
        entries[os.path.relpath(path, package).replace(os.sep, '/')] = path
assert DLL_ARC not in entries, 'the DLL is a build output and must not be tracked in package/'
entries[DLL_ARC] = dll

tmp = out + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
    for arc in sorted(entries):
        info = zipfile.ZipInfo(arc, date_time=(2026, 10, 30, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, open(entries[arc], 'rb').read())
os.replace(tmp, out)

with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert not any('\\' in n for n in z.namelist())
    print(len(z.namelist()), 'entries')
print('zip sha256', hashlib.sha256(open(out, 'rb').read()).hexdigest())
