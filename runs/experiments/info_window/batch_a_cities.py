"""Batch a1: city panel. Loyalty band edges, fortification display branches, population percent, tribute (own), supply.
One save, 25 Rome cities each with its own staged values; each city is left-clicked and the Information window captured."""
from iw_lib import *
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
rome = [c['id'] for c in base['cities'] if c['owner'] == 0]
LOY = [-10, -9, -1, 0, 10, 20, 30, 40, 49, 50, 59, 60, 69, 70, 79, 80, 89, 90, 99, 100, 109]
FORT = [0, 50, 99, 100, 101, 150, 199, 200, 250]       # 100 vs 101 is the display branch; >100: pending, shown as value % 100
POP = [(23, 23), (23, 27), (1, 7), (26, 27), (100, 300), (5, 7)]
stage = {}
for k, cid in enumerate(rome):
    st = {'loyalty': LOY[k] if k < len(LOY) else 74}
    st['fort'] = FORT[k % len(FORT)]
    p, m = POP[k % len(POP)]
    st['pop'], st['max_pop'] = p, m
    stage[cid] = st
def edits(s):
    for cid, st in stage.items(): s.city(cid, **st)
save = stage_save('a1', BASE, edits, 'A1_cities_loyalty_fort.SAV')
g = Game()
launch(g, save)
for cid, st in stage.items():
    c = base['cities'][cid]
    g.click_tile(c['x'], c['y'], pause=1.4)
    png, ocr = capture('a1', save, 'city', cid, dict(st, name=c['name']), 'A1_city_%03d_%s.png' % (cid, c['name']))
    print(cid, c['name'], st, '=>', ' | '.join(ocr.splitlines()[:9]))
stop(g)
