"""Batch a4: own-army panel and unit list. All 14 armies are made Rome's (owner 0); each gets its own morale (the word band edges), cell
(Terrain line), supplies, moves and money, so the left-click panel (UM03) and the right-click unit list (ShowArmyUnits) can be read per army."""
from iw_lib import *
import harness.driver as D
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
MOR = [50, 51, 54, 55, 58, 59, 62, 63, 66, 67, 70, 71, 74, 75]
CELL = [2, 3, 4, 5, 2, 6, 11, 0, 1, 2, 3, 4, 5, 2]
st = {}
for a in base['armies']:
    i = a['id']
    st[i] = {'owner': 0, 'morale': MOR[i], 'cell': CELL[i], 'supplies': (a['supplies'] + 37 * i) % 900 + 3, 'moves': (i * 3) % 11, 'money': 17 * i + 5}
def edits(s):
    for i, d in st.items(): s.army(i, **d)
    # unit quality / troop edge values on army 0: quality 0..9 across slots 0-9 would exceed its 6 units; done in batch a6
    s.unit(1, 0, troops=199); s.unit(1, 1, troops=399); s.unit(1, 2, troops=200)   # troops/200 truncation in the cost formula
save = stage_save('a4', BASE, edits, 'A4_armies_own.SAV')
g = Game(); launch(g, save)
for a in base['armies']:
    i = a['id']
    sel = None
    for _ in range(3):
        g.click_tile(a['x'], a['y'], pause=1.4)
        sel = g.i16(D.SEL_ARMY)
        if sel == i: break
    png, ocr = capture('a4', save, 'army_left', i, dict(st[i], sel=sel, x=a['x'], y=a['y']), 'A4_army_%02d_left.png' % i)
    print(i, st[i], 'sel', sel, '=>', ' | '.join(l for l in ocr.splitlines() if l.strip())[:330])
    x, y = g.show(a['x'], a['y'])
    rclick(x, y, pause=1.4)
    png, ocr = capture('a4', save, 'army_right', i, dict(st[i], x=a['x'], y=a['y']), 'A4_army_%02d_right.png' % i)
stop(g)
