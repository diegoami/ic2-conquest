"""Batch a2: (b) the fortification bracket (which slots it sums) and the foreign-city tribute word band (+ the number it shows above 10000)."""
from iw_lib import *
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
cart = [c for c in base['cities'] if c['owner'] == 1]
cap = base['nations'][1]['capital']
TRIB = [0, 10, 11, 30, 31, 100, 101, 5000, 10000, 10001, 20000, 40000, 65535]
tcities = [c['id'] for c in cart if c['id'] != cap][:len(TRIB)]
trib = dict(zip(tcities, TRIB))
def edits(s):
    # Rome (0): slots at 90: state 0 1000 + state 24 2000 (expect 3,000); at 91: state 13, 500; at 85 (Rome): none (baseline 14,000 removed)
    s.slot(0, 0, 0, 0, 1000, 90); s.slot(0, 1, 24, 1, 2000, 90); s.slot(0, 2, 13, 2, 500, 91); s.slot(0, 3, 17, 3, 0, 85)
    # Carthage (1): slot at its capital (a foreign city): 12000 at state 24; a slot at Rome's Cales (97): must NOT show at Cales
    s.slot(1, 0, 24, 0, 12000, cap); s.slot(1, 1, 5, 1, 777, 97)
    for cid, t in trib.items(): s.city(cid, tribute=t, pop=20, max_pop=20)
save = stage_save('a2', BASE, edits, 'A2_bracket_tribute.SAV')
g = Game(); launch(g, save)
targets = [('own', 90, {'expect_bracket': 3000}), ('own', 91, {'expect_bracket': 500}), ('own', 85, {'expect_bracket': None}),
           ('own', 97, {'expect_bracket': None, 'note': 'Carthage slot city=97, controller Rome'}), ('foreign', cap, {'expect_bracket': 12000})]
targets += [('foreign', cid, {'tribute_raw': t}) for cid, t in trib.items()]
for kind, cid, st in targets:
    c = base['cities'][cid]
    g.click_tile(c['x'], c['y'], pause=1.4)
    png, ocr = capture('a2', save, 'city_' + kind, cid, dict(st, name=c['name'], owner=c['owner']), 'A2_city_%03d_%s.png' % (cid, c['name']))
    print(kind, cid, c['name'], st, '=>', ' | '.join(l for l in ocr.splitlines() if l.strip())[:300])
stop(g)
