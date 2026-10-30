"""Generates NemesisCombatAI_Styles.esp (tiered combat styles + pools) and its SkyPatcher INI from one table,
so FormIDs in the INI can never drift from the plugin.
Subrecord layout (EDID, CSGD 40, CSME 32, CSCR 16, CSLR 4, CSFL 32, DATA 4) mirrors vanilla csHumanMeleeLvl5 read
from Skyrim.esm; light plugin, HEDR 1.71, sole master Skyrim.esm. Values stay inside the vanilla styles' ranges.
Also writes the caster style FormIDs the native plugin swaps in, so code and plugin cannot drift.
Usage: make_styles_esp.py <out.esp> <out.ini> [<out.h>]"""
import struct, sys

# ---- style table --------------------------------------------------------------------------------------------
FIELDS = ('off', 'de', 'gr', 'av', 'bash', 'bashAtk', 'bashPow', 'pb', 'asg', 'psg', 'ci', 'fb', 'fl', 'st', 'strafe',
          'sMel', 'sMag', 'sRng', 'sUna', 'sStf')  # s*: equipment score mults (what the NPC prefers to wield)
BASE = dict(off=0.6, de=0.3, gr=0.7, av=0.2, bash=1.0, bashAtk=0.6, bashPow=0.6, pb=1.0, asg=0.57, psg=0.57,
            ci=0.5, fb=0.3, fl=0.2, st=0.2, strafe=0.2, sMel=1.0, sMag=1.0, sRng=1.0, sUna=1.0, sStf=1.0)

def S(**kw):
    unknown = set(kw) - set(FIELDS)
    assert not unknown, unknown
    return {**BASE, **kw}

def M(**kw):  # mage: prefers spells, melee only as a last resort (vanilla csWarlock/csWERangedConjurer ranges)
    return S(sMel=0.40, sMag=4.0, sRng=0.5, sUna=0.5, bash=0.38, bashAtk=0.38, bashPow=0.38, pb=0.72, asg=0.38, psg=0.0, **kw)

# pool name -> (comment, [(style name, params)])
POOLS = {
 # Human melee, graded like vanilla csHumanMeleeLvl1..7
 'Rabble': ('Human melee, untrained: straight-line brawlers that rarely block, dodge, flank or retreat', [
   ('Rabble_Brawler',   S(off=0.50, de=0.10, gr=0.40, av=0.05, bash=0.60, bashAtk=0.60, bashPow=0.60, pb=0.60, asg=0.38, psg=0.00, ci=0.20, fb=0.15, fl=0.10, st=0.10)),
   ('Rabble_Mob',       S(off=0.40, de=0.15, gr=0.60, av=0.10, bash=0.70, bashAtk=0.70, bashPow=0.70, pb=0.70, asg=0.40, psg=0.10, ci=0.30, fb=0.20, fl=0.15, st=0.15))]),
 'Trained': ('Human melee, trained: soldiers and guards that mix attack and defence', [
   ('Trained_Soldier',  S(off=0.60, de=0.35, gr=0.65, av=0.20, bash=1.00, bashAtk=0.60, bashPow=0.60, pb=1.00, ci=0.55, fb=0.30, fl=0.25, st=0.25)),
   ('Trained_Guard',    S(off=0.50, de=0.50, gr=0.70, av=0.25, bash=1.20, bashAtk=0.70, bashPow=0.65, pb=1.20, ci=0.40, fb=0.35, fl=0.20, st=0.20))]),
 'Veteran': ('Human melee, veterans: duelists and shield walls', [
   ('Veteran_Duelist',  S(off=0.80, de=0.55, gr=0.80, av=0.35, bash=1.50, bashAtk=0.85, bashPow=0.75, pb=1.80, asg=0.80, psg=0.80, ci=0.75, fb=0.45, fl=0.45, st=0.45)),
   ('Veteran_Shieldwall', S(off=0.65, de=0.75, gr=0.90, av=0.35, bash=2.00, bashAtk=0.90, bashPow=0.80, pb=2.20, asg=0.80, psg=0.90, ci=0.45, fb=0.35, fl=0.30, st=0.30))]),
 'Elite': ('Human melee, masters: bash, block, circle and flank', [
   ('Elite_Master',     S(off=0.90, de=0.75, gr=1.00, av=0.50, bash=2.40, bashAtk=1.50, bashPow=1.50, pb=2.80, asg=1.10, psg=1.20, ci=0.85, fb=0.55, fl=0.70, st=0.60)),
   ('Elite_Bulwark',    S(off=0.75, de=0.85, gr=1.00, av=0.50, bash=2.80, bashAtk=1.70, bashPow=1.70, pb=3.20, asg=1.30, psg=1.30, ci=0.60, fb=0.45, fl=0.45, st=0.40))]),
 # Draugr melee, graded like vanilla csDraugrMeleeLvl1..6: relentless, never backing off
 'DraugrLow': ('Draugr melee, weak: shamblers that never back off', [
   ('Draugr_Shambler',  S(off=0.60, de=0.08, gr=0.45, av=0.05, bash=0.35, bashAtk=0.40, bashPow=0.40, pb=1.30, asg=0.50, psg=0.30, ci=0.05, fb=0.05)),
   ('Draugr_Lurcher',   S(off=0.54, de=0.12, gr=0.50, av=0.10, bash=0.45, bashAtk=0.45, bashPow=0.45, pb=1.40, asg=0.50, psg=0.30, ci=0.08, fb=0.05))]),
 'DraugrMid': ('Draugr melee, seasoned: heavier hitters that hold the line', [
   ('Draugr_Warrior',   S(off=0.72, de=0.15, gr=0.65, av=0.20, bash=0.90, bashAtk=0.60, bashPow=0.60, pb=2.50, asg=0.70, psg=0.60, ci=0.10, fb=0.05)),
   ('Draugr_Stalwart',  S(off=0.66, de=0.24, gr=0.70, av=0.20, bash=1.10, bashAtk=0.60, bashPow=0.60, pb=2.80, asg=0.70, psg=0.60, ci=0.08, fb=0.05))]),
 'DraugrHigh': ('Draugr melee, deathlords: crushing and relentless', [
   ('Draugr_Deathlord', S(off=0.88, de=0.30, gr=0.95, av=0.25, bash=2.00, bashAtk=1.10, bashPow=1.00, pb=5.00, asg=0.90, psg=1.00, ci=0.20, fb=0.05, fl=0.35, st=0.30)),
   ('Draugr_Revenant',  S(off=0.84, de=0.26, gr=0.90, av=0.25, bash=1.70, bashAtk=1.00, bashPow=0.90, pb=5.30, asg=0.90, psg=1.00, ci=0.15, fb=0.05, fl=0.30, st=0.30))]),
 # Archers (csHumanMissile, csSoldierMissile, csCWSoldierMissile)
 'Archer': ('Human archers: keep distance, strafe and fall back', [
   ('Archer_Marksman',  S(off=0.55, de=0.30, gr=0.70, av=0.25, bash=0.38, bashAtk=0.38, bashPow=0.38, pb=0.72, asg=0.38, psg=0.00, ci=0.50, fb=0.75, strafe=0.35, fl=0.30, st=0.30)),
   ('Archer_Skirmisher',S(off=0.70, de=0.25, gr=0.80, av=0.20, bash=0.38, bashAtk=0.38, bashPow=0.38, pb=0.72, asg=0.38, psg=0.00, ci=0.70, fb=0.55, strafe=0.50, fl=0.50, st=0.40)),
   ('Archer_Sentry',    S(off=0.45, de=0.45, gr=0.60, av=0.30, bash=0.38, bashAtk=0.38, bashPow=0.38, pb=0.72, asg=0.38, psg=0.00, ci=0.35, fb=0.85, strafe=0.25, fl=0.20, st=0.20))]),
 # Forsworn (csForswornMelee1H, csForswornMissile)
 'ForswornMelee': ('Forsworn melee: guerrillas that hit, circle and withdraw', [
   ('Forsworn_Skirmisher', S(off=0.60, de=0.30, gr=0.80, av=0.20, bash=1.08, bashAtk=0.70, bashPow=0.70, pb=1.08, ci=0.50, fb=0.40, fl=0.55, st=0.50)),
   ('Forsworn_Reaver',     S(off=0.85, de=0.15, gr=0.85, av=0.15, bash=1.50, bashAtk=0.90, bashPow=0.90, pb=4.00, ci=0.15, fb=0.05, fl=0.30, st=0.30))]),
 'ForswornArcher': ('Forsworn archers: stalk and strike from cover', [
   ('Forsworn_Stalker',    S(off=0.60, de=0.30, gr=0.70, av=0.20, bash=0.60, bashAtk=0.60, bashPow=0.60, pb=0.80, ci=0.60, fb=0.70, strafe=0.45, fl=0.60, st=0.50)),
   ('Archer_Skirmisher_F', None)]),  # shares Archer_Skirmisher; filled below
 # Human bosses (csHumanBoss1H / csHumanBoss2H): stand and trade, but not blindly
 'Boss': ('Human bosses: stand their ground and hit hard', [
   ('Boss_Champion',  S(off=0.75, de=0.55, gr=0.72, av=0.25, bash=4.00, bashAtk=3.00, bashPow=2.43, pb=5.00, asg=2.43, psg=3.00, ci=0.20, fb=0.10, fl=0.30, st=0.30)),
   ('Boss_Warden',    S(off=0.55, de=0.80, gr=0.72, av=0.30, bash=3.50, bashAtk=2.00, bashPow=1.50, pb=5.50, asg=2.43, psg=2.57, ci=0.10, fb=0.08, fl=0.20, st=0.20)),
   ('Boss_Warlord',   S(off=0.85, de=0.45, gr=0.80, av=0.25, bash=2.50, bashAtk=2.00, bashPow=2.00, pb=3.00, asg=2.43, psg=2.57, ci=0.15, fb=0.10, fl=0.35, st=0.30))]),
 # Casters, graded by the caster's own level by the native plugin (vanilla mage styles carry no grade at all)
 'MageRabble': ('Mages, untrained: stand in the open, ignore threats, bolt in a straight line', [
   ('Mage_Hedge',      M(off=0.45, de=0.10, gr=0.50, av=0.05, ci=0.10, fb=0.10, fl=0.10, st=0.10, strafe=0.10)),
   ('Mage_Skittish',   M(off=0.40, de=0.20, gr=0.50, av=0.10, ci=0.20, fb=0.35, fl=0.10, st=0.10, strafe=0.15))]),
 'MageTrained': ('Mages, trained: keep some range and sidestep', [
   ('Mage_Adept',      M(off=0.50, de=0.35, gr=0.55, av=0.15, ci=0.35, fb=0.40, fl=0.20, st=0.20, strafe=0.20)),
   ('Mage_Warder',     M(off=0.45, de=0.50, gr=0.55, av=0.20, ci=0.30, fb=0.50, fl=0.20, st=0.20, strafe=0.20))]),
 'MageVeteran': ('Mages, veterans: kite, flank and pick their moment', [
   ('Mage_Kiter',      M(off=0.55, de=0.50, gr=0.60, av=0.30, ci=0.55, fb=0.60, fl=0.35, st=0.35, strafe=0.35)),
   ('Mage_Ambusher',   M(off=0.65, de=0.40, gr=0.60, av=0.30, ci=0.45, fb=0.45, fl=0.50, st=0.45, strafe=0.30))]),
 'MageElite': ('Mages, masters: hold range, dodge and punish', [
   ('Mage_Archmage',   M(off=0.60, de=0.50, gr=0.65, av=0.50, ci=0.65, fb=0.65, fl=0.45, st=0.40, strafe=0.45)),
   ('Mage_Siegecaster',M(off=0.75, de=0.45, gr=0.70, av=0.40, ci=0.50, fb=0.50, fl=0.60, st=0.55, strafe=0.40))]),
}
# SkyPatcher rules: (comment, [vanilla style FormIDs in Skyrim.esm], pool). Order matters: first match wins.
RULES = [
 ('Draugr melee Lvl1-2', [0x0D0D, 0x72DF5], 'DraugrLow'),
 ('Draugr melee Lvl3-4', [0x72DF6, 0x72DF7], 'DraugrMid'),
 ('Draugr melee Lvl5-6', [0x72DF8, 0x86F4E], 'DraugrHigh'),
 ('Human melee Lvl1-2',  [0x3BE1B, 0x68848], 'Rabble'),
 ('Human melee Lvl3-4 and Civil War soldiers', [0x68849, 0x68847, 0xD3A0D], 'Trained'),
 ('Human melee Lvl5-6',  [0x86F4F, 0xE6C4F], 'Veteran'),
 ('Human melee Lvl7',    [0xE6C50], 'Elite'),
 ('Human, soldier and Civil War archers', [0x3BE1D, 0x46B9D, 0xD3A0E], 'Archer'),
 ('Forsworn melee',      [0x442CC], 'ForswornMelee'),
 ('Forsworn archers',    [0x442CF], 'ForswornArcher'),
 ('Human bosses',        [0x3DECE, 0x3DECF], 'Boss'),
]
# Vanilla pure-caster styles the native plugin retiers by level (hybrids with AllowDualWielding are left alone).
CASTER_SOURCES = [(0x3BE1C, 'csHumanMagic'), (0x101E61, 'csWE31Mage'), (0x10554E, 'csWERangedConjurer'),
                  (0x46B9E, 'csSoldierMagic'), (0x44CD0, 'csWarlock'), (0x442CD, 'csForswornMagic'),
                  (0x2DFB5, 'csVampireMagic'), (0x38A24, 'csDraugrMagic')]
CASTER_POOLS = ('MageRabble', 'MageTrained', 'MageVeteran', 'MageElite')
FORM_VERSION = 44
MASTER_INDEX = 1  # Skyrim.esm is index 0, this plugin is index 1

# ---- binary writer ------------------------------------------------------------------------------------------
def sub(tag, data): return tag + struct.pack('<H', len(data)) + data
def rec(sig, local, subs):
    body = b''.join(subs)
    return struct.pack('<4sIIIIHH', sig, len(body), 0, (MASTER_INDEX << 24) | local, 0, FORM_VERSION, 0) + body
def group(label, records):
    body = b''.join(records)
    return struct.pack('<4sI4sIHHI', b'GRUP', 24 + len(body), label, 0, 0, 0, 0) + body
def z(s): return s.encode('ascii') + b'\0'

def csty(local, edid, p):
    f = lambda *x: struct.pack('<%df' % len(x), *x)
    return rec(b'CSTY', local, [
        sub(b'EDID', z(edid)),
        sub(b'CSGD', f(p['off'], p['de'], p['gr'], p['sMel'], p['sMag'], p['sRng'], 1, p['sUna'], p['sStf'], p['av'])),  # score mults: melee,magic,ranged,shout,unarmed,staff
        sub(b'CSME', f(p['asg'], p['psg'], p['pb'], p['bash'], p['bash'], p['bashAtk'], p['bashPow'], 0.1)),
        sub(b'CSCR', f(p['ci'], p['fb'], p['fl'], p['st'])),
        sub(b'CSLR', f(p['strafe'])),
        sub(b'CSFL', f(0.33, 1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.75)),
        sub(b'DATA', struct.pack('<I', 1)),                                      # Dueling, as vanilla styles
    ])

def layout():
    """Returns (style ids by name, ordered style list, pool ids by name, pool member names)."""
    styles, ids, local = [], {}, 0x800
    for pool, (_, members) in POOLS.items():
        for name, p in members:
            if p is None: continue
            ids[name] = local; styles.append((local, name, p)); local += 1
    members = {pool: [n if p is not None else 'Archer_Skirmisher' for n, p in m] for pool, (_, m) in POOLS.items()}
    pool_ids = {}
    for pool in POOLS:
        pool_ids[pool] = local; local += 1
    return ids, styles, pool_ids, members

def build():
    ids, styles, pool_ids, members = layout()
    style_recs = [csty(l, f'NCAI_CS_{n}', p) for l, n, p in styles]
    pool_recs = [rec(b'FLST', pool_ids[pool], [sub(b'EDID', z(f'NCAI_CS_Pool_{pool}'))] +
                     [sub(b'LNAM', struct.pack('<I', (MASTER_INDEX << 24) | ids[n])) for n in members[pool]]) for pool in POOLS]
    next_id = (MASTER_INDEX << 24) | (max(pool_ids.values()) + 1)
    hedr = struct.pack('<fII', 1.71, len(style_recs) + len(pool_recs) + 2, next_id)
    body = (sub(b'HEDR', hedr) + sub(b'CNAM', z('GennyWoo')) + sub(b'SNAM', z('Nemesis Combat AI 3.0 - tiered combat styles'))
            + sub(b'MAST', z('Skyrim.esm')) + sub(b'DATA', struct.pack('<Q', 0)))
    tes4 = struct.pack('<4sIIIIHH', b'TES4', len(body), 0x200, 0, 0, FORM_VERSION, 0) + body  # 0x200 = light
    return tes4 + group(b'CSTY', style_recs) + group(b'FLST', pool_recs)

def ini():
    _, _, pool_ids, _ = layout()
    out = ['; Generated by tools/make_styles_esp.py from the same table as NemesisCombatAI_Styles.esp. Do not edit by hand.',
           '; Nemesis Combat AI 3.0 - tiered combat styles (brain: tactics and formation). Movesets stay with For Honor / BFCO.',
           ';',
           '; Vanilla already grades its human melee styles csHumanMeleeLvl1..7 and its Draugr styles csDraugrMeleeLvl1..6',
           '; from untrained to masterful. These rules keep that grading but hand each grade a pool of two or three',
           '; distinct styles, so fighters of one grade no longer all act alike. Rules match only the listed vanilla',
           '; styles, so bosses of other kinds, creatures and faction-themed styles are never touched here. Mages are',
           '; regraded by the native plugin from each caster level (see NemesisCombatAI.d), not by this file.',
           ';',
           '; File order: SkyPatcher applies INIs alphabetically. This file (N...) runs before "SkyTactics - Dynamic Combat',
           '; Styles.esp.ini" (S...), and this pack covers the same ground, so SkyTactics can be disabled.',
           '; This file only loads while NemesisCombatAI_Styles.esp is active; disable that plugin to turn all of this off.',
           '']
    for comment, forms, pool in RULES:
        out.append(f'; {comment} -> NCAI_CS_Pool_{pool}: {POOLS[pool][0]}')
        out.append('filterByCombatStyle=' + ', '.join(f'Skyrim.esm|{f:08X}' for f in forms)
                   + f':setRandomCombatStyle=NemesisCombatAI_Styles.esp|{pool_ids[pool]:X}')
    return '\n'.join(out) + '\n'

def header():
    ids, _, _, members = layout()
    rows = ',\n'.join('        { ' + ', '.join(f'0x{ids[n]:X}' for n in members[pool]) + ' }' for pool in CASTER_POOLS)
    srcs = ', '.join(f'0x{f:X}' for f, _ in CASTER_SOURCES)
    names = ', '.join(n for _, n in CASTER_SOURCES)
    return ('// Generated by tools/make_styles_esp.py from the same table as NemesisCombatAI_Styles.esp. Do not edit by hand.\n'
            '#pragma once\n#include <cstdint>\n\nnamespace NCAI::Styles\n{\n'
            '    inline constexpr const char* kPlugin = "NemesisCombatAI_Styles.esp";\n'
            f'    // Skyrim.esm pure-caster styles that get regraded: {names}\n'
            f'    inline constexpr std::uint32_t kCasterSources[] = {{ {srcs} }};\n'
            '    // Local FormIDs in kPlugin, one row per tier (Rabble, Trained, Veteran, Elite), two styles each\n'
            f'    inline constexpr std::uint32_t kCasterPools[4][2] = {{\n{rows}\n    }};\n}}\n')

if __name__ == '__main__':
    open(sys.argv[1], 'wb').write(build())
    open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(ini())
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w', encoding='utf-8', newline='\n').write(header())
