#!/usr/bin/env python3
"""Claims audit: recompute every number and line citation of the findings from the raw saves (state/sav.py on the archived copies in
artifacts/run-exp-v050-rules/saves/) and from the decompile (all_app_functions.txt, and the tracked code extracts). Writes
claims_audit_output[.vN].txt next to the data and exits 1 on any mismatch.
Each check is ('Qn', description, bool); line checks are L(line, must_contain)."""
import sys, os, re, glob
ROOT = '/home/diego/projects/wt-rules'
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'runs/experiments/v050_rules'))
import state.sav as S
from common import write_new, DATA
SRC = open('/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt', errors='replace').read().split('\n')
SAVES = ROOT + '/artifacts/run-exp-v050-rules/saves/'
checks = []
def C(q, what, ok): checks.append((q, what, bool(ok)))
def L(q, line, *subs):
    t = SRC[line - 1] if line <= len(SRC) else ''
    for s in subs: C(q, 'line %d contains %r' % (line, s), s in t)
def sav(name): return S.load(SAVES + name)
def army(d, i): return next(a for a in d['armies'] if a['id'] == i)

# ---- the code extracts are verbatim copies of the source lines
for f in sorted(glob.glob(DATA + '/code_extract_*.txt')):
    bad = 0; n = 0
    for l in open(f).read().split('\n')[1:]:
        m = re.match(r'(\d+)\t(.*)$', l)
        if m:
            n += 1
            if SRC[int(m.group(1)) - 1] != m.group(2): bad += 1
    C('extract', '%s: %d lines, all equal to the source line' % (os.path.basename(f), n), n > 0 and bad == 0)

# ---- Q1: line citations
L('Q1', 43119, '1000 - (short)'); L('Q1', 43125, 'DAT_00474aa8'); L('Q1', 43134, 'DAT_0047c1f8')
L('Q1', 43041, '* 5)'); L('Q1', 43080, 'DAT_0047c1f8'); L('Q1', 44056, '1000 - *(short *)(param_1 + 600)')
L('Q1', 44631, 'DAT_0047c1f8'); L('Q1', 46992, 'DAT_0047c1f8'); L('Q1', 46997, 'DAT_0047c1f2'); L('Q1', 47110, 'DAT_00474aa8')
L('Q1', 48740, 'DAT_0047c1f8', '= 0'); L('Q1', 49648, 'DAT_0047c1f8'); L('Q1', 49687, 'DAT_0047c1f8')
L('Q1', 53092, '1000 <', 'DAT_0047c1f8'); L('Q1', 53096, '= 1000'); L('Q1', 53098, '< 500'); L('Q1', 53100, '+ 500'); L('Q1', 53106, '/ 5')
L('Q1', 53201, '/ 3'); L('Q1', 53981, 'psVar5[4]'); L('Q1', 54765, 'psVar11[4]'); L('Q1', 54759, 'psVar11[4] < 1'); L('Q1', 54772, 'psVar11[4]')
L('Q1', 57618, 'DAT_0047c1f8'); L('Q1', 43633, 'DAT_0047c1f8'); L('Q1', 52246, 'FUN_0044f6d8'); L('Q1', 51655, 'FUN_0044f6d8')
L('Q1', 46384, '0x14', '0x15b'); L('Q1', 46385, 'TUnitMap_CheckForMove'); L('Q1', 46427, 'TUnitMap_SelectUnit')
# ---- Q1: saves
s0, s1, s3, s4, s5, s6, b1 = (sav(n) for n in ('Q1_00_start.SAV', 'Q1_01_army0_at_100_42.SAV', 'Q1_03_army1_supply_11x100.SAV', 'Q1_04_after_split.SAV', 'Q1_05_before_join.SAV', 'Q1_06_after_join.SAV', 'Q1b_01_after_one_up_click.SAV'))
tr = lambda d: d['nations'][0]['treasury']
C('Q1', 'start: treasury 2101, army 0 purse 100 sup 170 moves 8, army 1 purse 100', tr(s0) == 2101 and (army(s0, 0)['money'], army(s0, 0)['supplies'], army(s0, 0)['moves']) == (100, 170, 8) and army(s0, 1)['money'] == 100)
C('Q1', 'after the move: army 0 at (100,42), moves 0, purse 100, supplies 170 (no refill), treasury 2101', (army(s1, 0)['x'], army(s1, 0)['y'], army(s1, 0)['moves'], army(s1, 0)['money'], army(s1, 0)['supplies']) == (100, 42, 0, 100, 170) and tr(s1) == 2101)
rome_adj = [c['name'] for c in s1['cities'] if c['owner'] == 0 and max(abs(c['x'] - 100), abs(c['y'] - 42)) == 1 and c['supplies'] > 0]
C('Q1', 'army 0 at (100,42) is adjacent to own cities with stock: %s' % rome_adj, set(rome_adj) >= {'Rome', 'Caere'})
C('Q1', 'supply 11 x 100: army 1 purse 1000, treasury 1201 (-900)', army(s3, 1)['money'] == 1000 and tr(s3) == 1201)
new = [a for a in s4['armies'] if a['id'] == 15][0]
C('Q1', 'split: partner army 15 at (121,54), purse 0, moves 0, supplies 0, 5500 troops', (new['x'], new['y'], new['money'], new['moves'], new['supplies'], new['troops']) == (121, 54, 0, 0, 0, 5500))
C('Q1', 'partner supplied: army 15 purse 1000, treasury 201 (-1000)', army(s5, 15)['money'] == 1000 and tr(s5) == 201)
C('Q1', 'join: army 1 purse 2000 = 1000 + 1000, troops 25868, 7 units, moves 0, army 15 gone, treasury 201',
  army(s6, 1)['money'] == 2000 == army(s5, 1)['money'] + army(s5, 15)['money'] and army(s6, 1)['troops'] == 25868 and len(army(s6, 1)['units']) == 7 and army(s6, 1)['moves'] == 0 and army(s6, 15)['troops'] == 0 and tr(s6) == 201)
C('Q1', 'over-cap trim: army 1 purse 1000, treasury 1201 (+1000)', army(b1, 1)['money'] == 1000 and tr(b1) == 1201)

# ---- Q2
q2a, q2b = sav('Q2_00_start_tax10.SAV'), sav('Q2_01_tax20.SAV')
n = q2a['nations'][0]
trade = sum(m['tax_base'] // 12 for m in q2a['nations'] if n['relations'].get(m['name']) in (1, 2))
rows = {}
tsv = sorted(glob.glob(DATA + '/q2_balance_values*.tsv'))[-1]
for l in open(tsv).read().split('\n')[1:]:
    p = l.split('\t')
    if len(p) == 3 and p[2]: rows[(p[0], p[1])] = int(p[2].replace(',', ''))
def sheet(tag, d, tax):
    nn = d['nations'][0]; tb = nn['tax_base']
    exp = {'Taxes': tb * tax // 100, 'Tribute': tb >> 2, 'Trade': trade, 'Administration': nn['wealth'] // 20000 + nn['cities_count'] * 7}
    exp['Total revenue'] = exp['Taxes'] + exp['Tribute'] + exp['Trade']
    got = {k: rows.get(('Q2_%s_balance_sheet.png' % tag, k)) for k in exp}
    for k in exp: C('Q2', '%s %s: recomputed %s, read from the screenshot %s' % (tag, k, exp[k], got[k]), exp[k] == got[k])
    C('Q2', '%s tax rate in the save is %d' % (tag, tax), nn['tax'] == tax)
sheet('00_tax10', q2a, 10); sheet('01_tax20', q2b, 20)

live = sum((c['tribute'] * c['pop'] // c['max_pop']) << 2 for c in q2a['cities'] if c['owner'] == 0)
C('Q2', 'stored taxBase 2528 differs from the live sum of city contributions << 2 (%d)' % live, n['tax_base'] == 2528 and live == 2464)
dl = n['wealth'] // 500
dl = 20000 if dl > 20000 else dl
dl = dl - dl % 100 if dl < 0x1389 else (dl - dl % 500 if dl - 0x1389 < 5000 else dl)
C('Q2', 'debt limit recomputed %d = 5000 read' % dl, dl == 5000 == rows[('Q2_00_tax10_balance_sheet.png', 'Debt limit')])
C('Q2', 'Rome trades only with Illyria (relation 1)', {k: v for k, v in n['relations'].items() if v} == {'Macedonia': -8, 'Gaul': 3, 'Illyria': 1})
C('Q2', 'taxBase 2528 -> Tribute 632 in both sheets, tax-independent', n['tax_base'] == 2528 and q2b['nations'][0]['tax_base'] == 2528)
for ln, sub in ((55439, '474abc'), (55440, '474aba'), (55445, '0x44c'), (55449, '>> 2'), (55456, '>> 2'), (55457, 'FUN_004499ec'), (55466, '/ 20000'), (54875, '0x44c'), (54876, '>> 2'), (54878, 'FUN_004499ec'), (48430, '/ 0xc')): L('Q2', ln, sub)

# ---- Q3
q3 = [sav(n) for n in ('Q3_00_start.SAV', 'Q3_01_after_disband_hi3200.SAV', 'Q3_02_after_disband_hi4000.SAV')]
nat = lambda d: d['nations'][0]
W = nat(q3[0])['wealth']
C('Q3', 'start: treasury 1880, mobilisation 32, 5 queued units (the last HI 3200)', (nat(q3[0])['treasury'], nat(q3[0])['mobilization'], len(nat(q3[0])['recruit_slots'])) == (1880, 32, 5) and nat(q3[0])['recruit_slots'][4]['troops'] == 3200)
C('Q3', 'disband HI 3200: treasury unchanged 1880, queue 4 units, mobilisation 32 -> %d = 32 - 1 - 3200*1000//%d' % (nat(q3[1])['mobilization'], W), nat(q3[1])['treasury'] == 1880 and len(nat(q3[1])['recruit_slots']) == 4 and nat(q3[1])['mobilization'] == 32 - 1 - 3200 * 1000 // W)
C('Q3', 'disband HI 4000: treasury unchanged 1880, queue 3 units, mobilisation 30 -> %d = 30 - 1 - 4000*1000//%d (floor; rounding would give 27)' % (nat(q3[2])['mobilization'], W), nat(q3[2])['treasury'] == 1880 and len(nat(q3[2])['recruit_slots']) == 3 and nat(q3[2])['mobilization'] == 30 - 1 - 4000 * 1000 // W and round(4000 * 1000 / W) == 2)
C('Q3', 'recruiting HI 3200 cost 3200//200 * 20 = 320 = 2200 - 1880 (fixtures run0-start and recruit-hi3200)', S.load(ROOT + '/saves/run0-start-AUTO0720-seed12345.SAV')['nations'][0]['treasury'] - 1880 == 3200 // 200 * 20)
for ln, sub in ((56158, '1000'), (56162, '1000'), (56164, 'FUN_00448fd8'), (56167, 'FUN_0044a610'), (49007, '0x2ec'), (55996, '0x438'), (55999, '0x23e'), (56000, '* 1000'), (56001, '0x442')): L('Q3', ln, sub)

# extra sections are appended by later steps (Q4-Q6)
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'claims_audit_q*.py'))):
    exec(open(f).read())

bad = [c for c in checks if not c[2]]
out = ['# claims audit: %d checks, %d mismatches' % (len(checks), len(bad))] + ['%s\t%s\t%s' % (q, 'OK' if ok else 'MISMATCH', w) for q, w, ok in checks]
print(write_new(os.path.join(DATA, 'claims_audit_output.txt'), '\n'.join(out) + '\n'))
print(out[0])
for q, w, ok in bad: print('MISMATCH', q, w)
sys.exit(1 if bad else 0)
