"""Static checks on package/ that need no Skyrim and no compiler (run by CI):
 - the generated styles plugin, SkyPatcher INI and src/StyleIds.h equal what tools/make_styles_esp.py produces now;
 - the MCM config is strict JSON, the FOMOD files parse and every folder they install exists;
 - no build output, logs or manager bookkeeping files are tracked in the payload.
Usage: python tools/check_package.py"""
import json, os, subprocess, sys, tempfile
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

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('package checks passed')
