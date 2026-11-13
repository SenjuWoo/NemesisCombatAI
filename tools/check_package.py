"""Static checks on package/ that need no Skyrim and no compiler (run by CI):
 - the generated styles plugin, SkyPatcher INI and src/StyleIds.h equal what tools/make_styles_esp.py produces now;
 - the MCM config is strict JSON, the FOMOD files parse and every folder they install exists;
 - no build output, logs or manager bookkeeping files are tracked in the payload;
 - the version in xmake.lua is the one in the installer, INSTALL.txt, README and the top changelog entry.
Usage: python tools/check_package.py"""
import json, os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
pkg = os.path.join(root, 'package')
errors = []

# 1. generated files in sync
with tempfile.TemporaryDirectory() as tmp:
    esp, ini, hdr = (os.path.join(tmp, n) for n in ('s.esp', 's.ini', 'StyleIds.h'))
    subprocess.run([sys.executable, '-I', os.path.join(root, 'tools', 'make_styles_esp.py'), esp, ini, hdr], check=True)
    for fresh, tracked in ((esp, 'package/10 Tactics/NemesisCombatAI_Styles.esp'),
                           (ini, 'package/10 Tactics/SKSE/Plugins/SkyPatcher/npc/NemesisCombatAI_Styles.esp.ini'),
                           (hdr, 'src/StyleIds.h')):
        if open(fresh, 'rb').read() != open(os.path.join(root, tracked), 'rb').read():
            errors.append(f'{tracked} is out of sync with tools/make_styles_esp.py')

# 2. MCM JSON and FOMOD
json.load(open(os.path.join(pkg, '00 Core/MCM/Config/NemesisCombatAI/config.json'), encoding='utf-8'))
for name in ('ModuleConfig.xml', 'info.xml'):
    ET.parse(os.path.join(pkg, 'fomod', name))
cfg = ET.parse(os.path.join(pkg, 'fomod', 'ModuleConfig.xml')).getroot()
for folder in cfg.iter('folder'):
    src = folder.get('source')
    if not os.path.isdir(os.path.join(pkg, src)):
        errors.append(f'fomod installs missing folder: {src}')

# 3. payload hygiene
for d, _, names in os.walk(pkg):
    for n in names:
        if n.endswith(('.dll', '.pdb', '.log', '.meta')) or n in ('meta.ini', 'Thumbs.db') or n.startswith('__folder_managed'):
            errors.append(f'unexpected file in payload: {os.path.join(d, n)}')

# 4. one version everywhere
def text(rel):
    return open(os.path.join(root, rel), encoding='utf-8').read()
version = re.search(r'set_version\("([^"]+)"\)', text('xmake.lua')).group(1)
info = ET.parse(os.path.join(pkg, 'fomod', 'info.xml')).getroot().find('Version')
claims = {
    'package/fomod/info.xml <Version>': info.text.strip(),
    'package/fomod/info.xml MachineVersion': info.get('MachineVersion'),
    'package/fomod/ModuleConfig.xml moduleName': cfg.find('moduleName').text.rsplit(' ', 1)[-1],
    'package/00 Core/INSTALL.txt first line': text('package/00 Core/INSTALL.txt').splitlines()[0].rsplit(' ', 1)[-1],
    'CHANGELOG.md top entry': re.search(r'^## (\d+\.\d+\.\d+)', text('CHANGELOG.md'), re.M).group(1),
}
readme = text('README.md')
for found in set(re.findall(r'--expect-version (\d+\.\d+\.\d+)', readme)) | set(re.findall(r'Beta build \((\d+\.\d+\.\d+)\)', readme)):
    claims[f'README.md ({found})'] = found
for where, found in claims.items():
    if found != version:
        errors.append(f'{where} says {found}, xmake.lua says {version}')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('package checks passed')
