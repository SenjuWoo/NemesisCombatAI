"""Builds the FOMOD release archive: package/ plus the built DLL. Deterministic: entries sorted by archive path,
fixed timestamps, forward-slash paths, no build output or manager bookkeeping.
Usage: make_release_zip.py <NemesisCombatAI.dll> <out.zip> [--expect-version X.Y.Z]
The version check reads the SKSE version block out of the DLL, so a stale build cannot be packaged by mistake."""
import hashlib, os, subprocess, sys, zipfile

DLL_ARC = '00 Core/SKSE/Plugins/NemesisCombatAI.dll'
BANNED = ('__folder_managed_by_vortex', 'meta.ini', '.meta', 'Thumbs.db', '.pdb', '.log')

args = sys.argv[1:]
expect = None
if '--expect-version' in args:
    i = args.index('--expect-version')
    expect = args[i + 1]
    del args[i:i + 2]
if len(args) != 2:
    sys.exit(__doc__)
dll, out = args

if expect:
    verifier = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_version_block.py')
    check = subprocess.run([sys.executable, verifier, dll, '--expect-version', expect], capture_output=True, text=True)
    if check.returncode != 0:
        print(check.stdout, check.stderr)
        sys.exit(f'packaging aborted: the DLL does not carry version {expect}')
    print(f'dll version verified: {expect}')
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
