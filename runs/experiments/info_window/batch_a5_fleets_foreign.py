"""Batch a5: fleet panel (UM05): Sea calm/rough from the fleet's +24 field, ships/supply/money/repair/capacity formulas, own vs foreign,
with and without an embarked army; foreign army panel (UM04); right-click lists on own/foreign."""
from iw_lib import *
import harness.driver as D
FX = '/home/diego/ic2-work/fixtures/'
def run_fleets(tag, base, stg, targets, g):
    b = sav.load(base)
    save = stage_save(tag, base, lambda s: [s.fleet(i, **d) for i, d in stg.items()], 'A5_%s.SAV' % tag)
    launch(g, save)
    for i in targets:
        f = b['fleets'][i]
        sel = None
        for _ in range(3):
            g.click_tile(f['x'], f['y'], pause=1.4)
            sel = g.i16(D.SEL_FLEET)
            if sel == i: break
        st = dict(stg.get(i, {}), x=f['x'], y=f['y'], owner=f['owner'], base=os.path.basename(base), sel=sel)
        png, ocr = capture('a5', save, 'fleet_left', i, st, 'A5_%s_fleet%d_left.png' % (tag, i))
        print(tag, i, st, '=>', ' | '.join(l for l in ocr.splitlines() if l.strip())[:360])
        x, y = g.show(f['x'], f['y']); rclick(x, y, pause=1.4)
        png, ocr = capture('a5', save, 'fleet_right', i, st, 'A5_%s_fleet%d_right.png' % (tag, i))
g = Game()
# a: own fleet 2 (army 0 aboard) calm; foreign fleets 0 rough(1), 1 sea=-1
run_fleets('f5a', FX + 'FLEET5_EMBARKED.SAV', {0: {'sea': 1}, 1: {'sea': -1}, 2: {'sea': 0, 'supplies': 50, 'ships': 30, 'money': 123, 'condition': 55}}, [2, 0, 1], g)
# b: own fleet rough (1), 100 ships, supply 800 (=100%), foreign fleet sea=2, other values
run_fleets('f5b', FX + 'FLEET5_EMBARKED.SAV', {0: {'sea': 2, 'ships': 10, 'supplies': 79, 'condition': 1}, 1: {'sea': 0}, 2: {'sea': 1, 'ships': 100, 'supplies': 800, 'money': 5000, 'condition': 100, 'moves': 7}}, [2, 0, 1], g)
# c: foreign (Carthaginian) fleet with an army aboard (FLEET.SAV: fleet 0 + army 3)
run_fleets('f5c', FX + 'FLEET.SAV', {}, [0, 2], g)
# foreign armies (BASE): left click then right click
b = sav.load(FX + 'BASE.SAV')
save = stage_save('a5', FX + 'BASE.SAV', lambda s: None, 'A5_foreign_armies_BASE.SAV')
launch(g, save)
for i in (2, 7, 4):
    a = b['armies'][i]
    g.click_tile(a['x'], a['y'], pause=1.4)
    png, ocr = capture('a5', save, 'army_foreign_left', i, {'owner': a['owner'], 'sel': g.i16(D.SEL_ARMY)}, 'A5_foreign_army%d_left.png' % i)
    print('foreign', i, ' | '.join(l for l in ocr.splitlines() if l.strip())[:300])
    x, y = g.show(a['x'], a['y']); rclick(x, y, pause=1.4)
    png, ocr = capture('a5', save, 'army_foreign_right', i, {'owner': a['owner']}, 'A5_foreign_army%d_right.png' % i)
    print('foreign right', i, ' | '.join(l for l in ocr.splitlines() if l.strip())[:300])
stop(g)
