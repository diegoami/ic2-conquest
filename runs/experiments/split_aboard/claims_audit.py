#!/usr/bin/env python3
"""Claims audit. Rule inputs: the tracked code extract (data/code_extract_*.txt), NOT the Ghidra dump (check_dump_vs_extract.py compares them, optionally).
Expected values are derived from the raw saves (state/sav.py) of BOTH runs (the first, and the re-run with the calibrated runner: the `.v2` saves):
the placement is replayed from the scan the extract shows, on the map of the before-save; the unit/troop arithmetic from the saves themselves.
usage: claims_audit.py [--artifacts DIR]   (default <repo>/artifacts/run-exp-split-aboard; fetch_archive.py prepares it)"""
import sys, os, glob, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from paths import ROOT, ART, DATA
sys.path.insert(0, ROOT)
import state.sav as S
from common import write_new
art = (sys.argv[sys.argv.index('--artifacts') + 1] if '--artifacts' in sys.argv else ART).rstrip('/') + '/'
L = {}
for f in sorted(glob.glob(DATA + 'code_extract_*.txt')):
    for l in open(f, errors='replace').read().split('\n')[1:]:
        m = re.match(r'(\d+)\t(.*)$', l)
        if m: L[int(m.group(1))] = m.group(2)
checks = []
def C(w, ok): checks.append((w, bool(ok)))
def line(n, *subs):
    for s in subs: C('extract line %d contains %r' % (n, s), s in L.get(n, ''))
for n, subs in ((47033, ('0x89',)), (47037, ('DAT_0049c282', '* 0xd')), (47039, ('DAT_0047c1f0', 'DAT_004a0320')), (47041, ('DAT_0047c220',)), (47046, ('FUN_00449f08',)), (47047, ('-1 <',)),
                (48724, ('FUN_004492c0',)), (48725, ('-1 <', '0xc6')), (48729, ('DAT_0047c1ec',)), (48736, ('DAT_0047c1f4',)), (47937, ('== \'\\0\'',)), (47942, ('= 2',)), (47943, ('0xb',)), (47960, ('local_1c <=',)),
                (47961, ('local_16',)), (47969, ('param_1[1]',)), (46976, ('DAT_0047c1f4', '== -1')), (46978, ('on a fleet cannot be combined',))):
    line(n, *subs)
# the scan of FUN_004492C0 as the extract shows it: offsets -1..1, outer loop x (:47948-47967), inner y (:47949-47965), codes lo..hi from :47942-47943, the LAST match wins (:47960-47963)
lo, hi = int(re.search(r'= (\d+);', L[47942]).group(1)), int(L[47943].split('=')[1].strip().rstrip(';'), 16)
def last_tile(d, x0, y0):
    last = None; cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if lo <= S.cell(d, x0 + dx, y0 + dy) <= hi: last = (x0 + dx, y0 + dy); cand.append(last)
    return last, cand
ar = lambda d, i: next((a for a in d['armies'] if a['id'] == i), None)
pairs = [l.split('\t') for l in open(DATA + 'save_pairs.tsv').read().split('\n')[1:] if l]            # which saves belong to which run (tracked)
runs = [(p[1][:-4], p[2][:-4], p[3][:-4]) for p in pairs]
C('two runs listed (the first and the calibrated re-run): %s' % [p[0] for p in pairs], len(runs) == 2 and all(os.path.exists(art + 'saves/' + n + '.SAV') for r in runs for n in r))
for (n0, n1, n2), p in zip(runs, pairs):
    n0 = p[1][:-4]
    s0, s1, s2 = (S.load(art + 'saves/' + n + '.SAV') for n in (n0, n1, n2))
    me = s0['current_nation']
    fl = next(f for f in s0['fleets'] if f['owner'] == me and f['army'] == -1 and f['ships'] > 0 and not f['building'])
    # the army that embarked: in s1 the army whose cell is -1 at the fleet's tile
    emb = [a for a in s1['armies'] if a['embarked'] and (a['x'], a['y']) == (fl['x'], fl['y'])]
    C('%s: exactly one army aboard fleet %d at (%d,%d) in the before-save; the fleet carries it' % (n1, fl['id'], fl['x'], fl['y']), len(emb) == 1 and s1['fleets'][fl['id']]['army'] == emb[0]['id'] and not ar(s0, emb[0]['id'])['embarked'])
    e = emb[0]; e2 = ar(s2, e['id'])
    new = [a for a in s2['armies'] if a['troops'] > 0 and a['id'] not in {x['id'] for x in s1['armies'] if x['troops'] > 0}]
    C('%s: exactly one new army appeared' % n2, len(new) == 1)
    nw = new[0]
    last, cand = last_tile(s1, fl['x'], fl['y'])
    C('%s: placement replayed from the extract (last tile with map code %d..%d of the 3x3 around (%d,%d)) = %s of %s; the new army is at %s' % (n1, lo, hi, fl['x'], fl['y'], last, cand, (nw['x'], nw['y'])), last == (nw['x'], nw['y']))
    C('%s: the new army is on land (not aboard), a free map code, adjacent to the fleet; purse/supplies/moves 0; owner %d' % (n2, me), not nw['embarked'] and max(abs(nw['x'] - fl['x']), abs(nw['y'] - fl['y'])) == 1 and (nw['money'], nw['supplies'], nw['moves']) == (0, 0, 0) and nw['owner'] == me and lo <= S.cell(s1, nw['x'], nw['y']) <= hi)
    C('%s: the original army stays aboard at the fleet tile, the fleet still carries it, troops split %d = %d + %d, units %d = %d + %d, purse unchanged' % (n2, e['troops'], e2['troops'], nw['troops'], len(e['units']), len(e2['units']), len(nw['units'])),
      e2['embarked'] and (e2['x'], e2['y']) == (fl['x'], fl['y']) and s2['fleets'][fl['id']]['army'] == e['id'] and e2['troops'] + nw['troops'] == e['troops'] and len(e2['units']) + len(nw['units']) == len(e['units']) and e2['money'] == e['money'])
    C('%s: before the split the army had more than one unit (the gate of :47041)' % n1, len(e['units']) > 1)
    others = [a for a in s1['armies'] if a['id'] != e['id'] and a['troops'] > 0]
    C('%s: no other army changed' % n2, all((ar(s2, a['id'])['x'], ar(s2, a['id'])['y'], ar(s2, a['id'])['troops']) == (a['x'], a['y'], a['troops']) for a in others))
bad = [c for c in checks if not c[1]]
out = ['# claims audit: %d checks, %d mismatches' % (len(checks), len(bad))] + ['%s\t%s' % ('OK' if ok else 'MISMATCH', w) for w, ok in checks]
if '--no-write' not in sys.argv: print(write_new(os.path.join(DATA, 'claims_audit_output.txt'), '\n'.join(out) + '\n'))
print(out[0])
for w, ok in checks:
    if not ok: print('MISMATCH', w)
sys.exit(1 if bad else 0)
