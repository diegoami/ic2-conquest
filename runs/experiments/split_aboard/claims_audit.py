#!/usr/bin/env python3
"""Claims audit: recompute the finding's numbers from the archived saves (state/sav.py) and check every cited decompile line."""
import sys, os, glob
ROOT = '/home/diego/projects/wt-split'
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + '/runs/experiments/split_aboard')
import state.sav as S
from common import write_new, DATA
SRC = open('/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt', errors='replace').read().split('\n')
SV = ROOT + '/artifacts/run-exp-split-aboard/saves/'
checks = []
def C(w, ok): checks.append((w, bool(ok)))
def L(line, *subs):
    for s in subs: C('line %d contains %r' % (line, s), s in SRC[line - 1])
import re
for f in sorted(glob.glob(DATA + '/code_extract_*.txt')):
    bad = n = 0
    for l in open(f).read().split('\n')[1:]:
        m = re.match(r'(\d+)\t(.*)$', l)
        if m:
            n += 1; bad += SRC[int(m.group(1)) - 1] != m.group(2)
    C('%s: %d lines equal to the source' % (os.path.basename(f), n), n and not bad)
for ln, subs in ((47033, ('0x89',)), (47037, ('DAT_0049c282', '* 0xd')), (47039, ('DAT_0047c1f0', 'DAT_004a0320')), (47041, ('DAT_0047c220',)),
                 (47046, ('FUN_00449f08',)), (48724, ('FUN_004492c0', ')1)'.replace(')1)', '1)'))), (48725, ('-1 <', '0xc6')), (48729, ('DAT_0047c1ec',)),
                 (48736, ('DAT_0047c1f4',)), (47942, ('= 2',)), (47943, ('0xb',)), (47960, ('local_1c <=',)), (47961, ('local_16',)), (47969, ('param_1[1]',)),
                 (46976, ('DAT_0047c1f4', '== -1')), (46978, ('on a fleet cannot be combined',))): L(ln, *subs)
s0, s1, s2 = (S.load(SV + n) for n in ('SA_00_start.SAV', 'SA_01_aboard_before_split.SAV', 'SA_02_after_split.SAV'))
ar = lambda d, i: next(a for a in d['armies'] if a['id'] == i)
C('start: army 0 at (101,45), 3 units, 10700, not aboard; fleet 2 at (101,46) 30 ships, carries -1', (ar(s0, 0)['x'], ar(s0, 0)['y'], len(ar(s0, 0)['units']), ar(s0, 0)['troops'], ar(s0, 0)['embarked']) == (101, 45, 3, 10700, False) and (s0['fleets'][2]['x'], s0['fleets'][2]['y'], s0['fleets'][2]['ships'], s0['fleets'][2]['army']) == (101, 46, 30, -1))
C('aboard: army 0 cell -1 at (101,46), moves 0; fleet 2 carries army 0, moves 0', ar(s1, 0)['embarked'] and (ar(s1, 0)['x'], ar(s1, 0)['y'], ar(s1, 0)['moves']) == (101, 46, 0) and (s1['fleets'][2]['army'], s1['fleets'][2]['moves']) == (0, 0))
# the scan of FUN_004492C0 (flag 1): dx outer -1..1, dy inner -1..1, last tile whose map code is 2..11 wins
x0, y0 = 101, 46
last = None; cand = []
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        code = S.cell(s1, x0 + dx, y0 + dy)
        if 2 <= code <= 11: last = (x0 + dx, y0 + dy); cand.append(last)
C('recomputed placement (last land tile of the 3x3 scan, codes 2..11) = %s of candidates %s' % (last, cand), last == (102, 47))
n14 = ar(s2, 14)
C('after split: new army 14 at (102,47), not aboard, 1 unit, 5000 troops, moves 0, supplies 0, purse 0, owner Rome', (n14['x'], n14['y'], n14['embarked'], len(n14['units']), n14['troops'], n14['moves'], n14['supplies'], n14['money'], n14['owner']) == (102, 47, False, 1, 5000, 0, 0, 0, 0))
a0 = ar(s2, 0)
C('after split: army 0 still aboard at (101,46), 2 units, 5700 troops (10700-5000), purse 100; fleet 2 still carries army 0', a0['embarked'] and (a0['x'], a0['y'], len(a0['units']), a0['troops'], a0['money']) == (101, 46, 2, 5700, 100) and s2['fleets'][2]['army'] == 0 and a0['troops'] + n14['troops'] == 10700)
C('other armies unchanged (12 and 13)', all((ar(s1, i)['x'], ar(s1, i)['y'], ar(s1, i)['troops']) == (ar(s2, i)['x'], ar(s2, i)['y'], ar(s2, i)['troops']) for i in (12, 13)))
bad = [c for c in checks if not c[1]]
out = ['# claims audit: %d checks, %d mismatches' % (len(checks), len(bad))] + ['%s\t%s' % ('OK' if ok else 'MISMATCH', w) for w, ok in checks]
print(write_new(os.path.join(DATA, 'claims_audit_output.txt'), '\n'.join(out) + '\n')); print(out[0])
for w, ok in checks:
    if not ok: print('MISMATCH', w)
sys.exit(1 if bad else 0)
