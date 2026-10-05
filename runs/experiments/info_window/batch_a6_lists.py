"""Batch a6: unit lists (right click): quality word for index 0..11 (scrolled right: the 328 px window clips the line), the list stopping at the first
empty slot, 'No. of units' with a gap, the mercenary list at a city (own and foreign), 'capital of' for a captured capital."""
from iw_lib import *
import harness.driver as D
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
rome = base['cities'][85]; cap1 = base['cities'][base['nations'][1]['capital']]
def edits(s):
    for k in range(12):
        s.unit(0, k, label=0, type=k % 5, troops=1000 + 100 * k, quality=k, name='Test unit %d' % k)
    s.unit(1, 1, troops=0)                          # gap in the middle: the list stops, "No. of units" counts to the last used slot
    s.nation(1, capital=97)                         # Cales becomes Carthage's capital while Rome controls it
    def merc(k, x, y, lab, typ, tr, q):
        for j, v in enumerate((x, y, lab, typ, tr, q)): s.put(s.merc0 + 12 * k + 2 * j, v)
    merc(0, rome['x'], rome['y'], 3, 0, 1500, 4); merc(1, rome['x'], rome['y'], 5, 2, 800, 9); merc(2, rome['x'], rome['y'], 7, 4, 0, 0)
    merc(3, rome['x'], rome['y'], 9, 1, -1, 7); merc(4, rome['x'] + 1, rome['y'], 11, 3, 700, 6)
    merc(5, cap1['x'], cap1['y'], 13, 3, 2500, 8)
save = stage_save('a6', BASE, edits, 'A6_lists_quality_mercs.SAV')
g = Game(); launch(g, save)
def rc(c, name, kind, staged):
    x, y = g.show(c['x'], c['y']); rclick(x, y, pause=1.4)
    return capture('a6', save, kind, c['id'], staged, name)
for i in (0, 1):
    a = base['armies'][i]; x, y = g.show(a['x'], a['y']); rclick(x, y, pause=1.4)
    capture('a6', save, 'army_right', i, {'x': a['x'], 'y': a['y']}, 'A6_army%d_right.png' % i)
    scroll_right(12)
    capture('a6', save, 'army_right_scrolled', i, {'x': a['x'], 'y': a['y'], 'scroll_clicks': 12}, 'A6_army%d_right_scrolled.png' % i)
    scroll_home()
    g.click_tile(a['x'], a['y'], pause=1.4)
    capture('a6', save, 'army_left', i, {'x': a['x'], 'y': a['y']}, 'A6_army%d_left.png' % i)
for c, nm in ((rome, 'rome'), (cap1, 'carthago'), (base['cities'][100], 'capua')):
    png, ocr = rc(c, 'A6_merc_%s.png' % nm, 'merc_list', {'city': c['name']})
    print(nm, ' | '.join(l for l in ocr.splitlines() if l.strip()))
    scroll_right(12); capture('a6', save, 'merc_list_scrolled', c['id'], {'city': c['name'], 'scroll_clicks': 12}, 'A6_merc_%s_scrolled.png' % nm); scroll_home()
g.click_tile(base['cities'][97]['x'], base['cities'][97]['y'], pause=1.4)
capture('a6', save, 'city_own', 97, {'name': 'Cales', 'note': 'capital of Carthage by the nation record, controlled by Rome'}, 'A6_city097_Cales.png')
nation_menu(g, 1)
capture('a6', save, 'nation', 1, {'name': 'Carthage', 'capital': 97}, 'A6_nation01_Carthage.png')
stop(g)
