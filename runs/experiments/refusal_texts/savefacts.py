"""State facts of a save, as text, for the plays table of the finding and for the audit that recomputes them from the saved files.
spec: 'army:N' 'fleet:N' 'city:N' 'rel:A:B' 'nation:N:mob' ..."""
import os, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, ROOT)
from state import sav
import struct, re

def parse_nation_words(b, n):
    na = struct.unpack_from('<h', b, sav.ARMY_OFF)[0]; of = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN; nf = struct.unpack_from('<h', b, of)[0]
    return of + 2 + nf * sav.FLEET_LEN + n * sav.NATION_LEN

def fact(path, spec):
    b = open(path, 'rb').read(); d = sav.parse(b); k = spec.split(':')
    if k[0] == 'army':
        a = d['armies'][int(k[1])]
        return 'army %s: owner=%d pos=(%d,%d) units=%d troops=%d moves=%d aboard=%s' % (k[1], a['owner'], a['x'], a['y'], len(a['units']), sum(u['troops'] for u in a['units']), a['moves'], 'yes' if a['embarked'] else 'no')
    if k[0] == 'fleet':
        f = d['fleets'][int(k[1])]
        return 'fleet %s: owner=%d pos=(%d,%d) ships=%d carries=%d' % (k[1], f['owner'], f['x'], f['y'], f['ships'], f['army'])
    if k[0] == 'city':
        c = d['cities'][int(k[1])]
        return 'city %s: owner=%d fort=%d pending=%d' % (k[1], c['owner'], c['fort'], c.get('fort_pending', 0))
    if k[0] == 'rel':
        a, c = int(k[1]), int(k[2]); o = parse_nation_words(b, a) + 0x26 + 2 * c
        return 'rel %d-%d: %d' % (a, c, struct.unpack_from('<h', b, o)[0])
    if k[0] == 'nationword':
        n, off = int(k[1]), int(k[2], 16); o = parse_nation_words(b, n) + off
        return 'nation %d +0x%x: %d' % (n, off, struct.unpack_from('<h', b, o)[0])
    raise ValueError(spec)

def regions(b):
    """[(start, end, label)] of the save's blocks (docs/sav-layout-notes.md 'Block sequence')"""
    na = struct.unpack_from('<h', b, sav.ARMY_OFF)[0]; of = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN; nf = struct.unpack_from('<h', b, of)[0]
    on = of + 2 + nf * sav.FLEET_LEN
    return [(0, sav.CITY_OFF, 'map'), (sav.CITY_OFF, sav.ARMY_OFF - 2, 'city'), (sav.ARMY_OFF - 2, sav.ARMY_OFF, 'army count'), (sav.ARMY_OFF, of, 'army'),
            (of, of + 2, 'fleet count'), (of + 2, on, 'fleet'), (on, on + 16 * sav.NATION_LEN, 'nation'), (on + 16 * sav.NATION_LEN, len(b), 'rest (mercenaries, news, trailer)')], on, of

def label(b, i):
    rg, on, of = regions(b)
    for lo, hi, name in rg:
        if lo <= i < hi:
            if name == 'nation': return 'nation %d +0x%x' % ((i - on) // sav.NATION_LEN, (i - on) % sav.NATION_LEN)
            if name == 'army': return 'army %d +%d' % ((i - sav.ARMY_OFF) // sav.ARMY_LEN, (i - sav.ARMY_OFF) % sav.ARMY_LEN)
            if name == 'fleet': return 'fleet %d +%d' % ((i - of - 2) // sav.FLEET_LEN, (i - of - 2) % sav.FLEET_LEN)
            if name == 'city': return 'city %d +%d' % ((i - sav.CITY_OFF) // sav.CITY_LEN, (i - sav.CITY_OFF) % sav.CITY_LEN)
            return name
    return '?'

def diff_text(pa, pb):
    """'identical' or 'N byte(s): <entities>', grouped by entity (a nation's bytes are listed by offset: a nation word at +0x46B..+0x48F is the UI block of docs/sav-layout-notes.md)"""
    a, b = open(pa, 'rb').read(), open(pb, 'rb').read()
    if len(a) != len(b): return 'different length %d vs %d' % (len(a), len(b))
    d = [i for i in range(len(a)) if a[i] != b[i]]
    if not d: return 'identical'
    groups = {}
    for i in d:
        l = label(a, i); m = re.match(r'(nation \d+) (\+0x[0-9a-f]+)$', l)
        if m: groups.setdefault(m.group(1), []).append(m.group(2))
        else:
            m = re.match(r'((?:army|fleet|city) \d+) \+\d+$', l); k = m.group(1) if m else l
            groups.setdefault(k, []).append(None)
    parts = []
    for k, v in groups.items(): parts.append('%s %s' % (k, ', '.join(v)) if v[0] is not None else '%s (%d)' % (k, len(v)))
    return '%d byte(s): %s' % (len(d), '; '.join(parts))

def ui_only(pa, pb):
    """True when every differing byte is in a nation record's UI block (+0x46B..+0x48F, the 'UI fields' row of docs/sav-layout-notes.md section 5)"""
    a, b = open(pa, 'rb').read(), open(pb, 'rb').read()
    if len(a) != len(b): return False
    rg, on, of = regions(a)
    for i in range(len(a)):
        if a[i] != b[i]:
            if not (on <= i < on + 16 * sav.NATION_LEN and 0x46B <= (i - on) % sav.NATION_LEN <= 0x48F): return False
    return True
