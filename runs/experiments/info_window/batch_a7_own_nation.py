"""Batch a7: the own-nation lines (Mobilized, Treasury) with their formats, and the own/foreign switch when the current nation is not Rome."""
from iw_lib import *
import harness.driver as D
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
g = Game()
VAR = [(-1500, 0, 5), (0, 100, 40), (123, 7, 0), (1234567, 55, 10), (99999999, 99, 15)]
for k, (tre, mob, tax) in enumerate(VAR):
    save = stage_save('a7', BASE, lambda s: s.nation(0, treasury=tre, mobilization=mob, tax=tax), 'A7_rome_treasury%d.SAV' % k)
    if k == 0: launch(g, save)
    else: g.open(save)
    nation_menu(g, 0)
    png, ocr = capture('a7', save, 'nation', 0, {'treasury': tre, 'mobilization': mob, 'tax': tax}, 'A7_nation00_treasury%d.png' % k)
    print(k, ' | '.join(l for l in ocr.splitlines() if l.strip())[:200])
# current nation = Carthage (1): its own panel, a Carthaginian army and city are 'own', Rome's are foreign
def cur1(s):
    s.put(sav.parse(bytes(s.b))['tail_off'] + 2 * 18, 1)
    s.nation(1, treasury=7777, mobilization=12)
save = stage_save('a7', BASE, cur1, 'A7_current_carthage.SAV')
g.open(save)
p = sav.load(save); print('current', p['current_nation'])
nation_menu(g, 1); capture('a7', save, 'nation', 1, {'current': 1}, 'A7_cur1_nation01.png')
nation_menu(g, 0); capture('a7', save, 'nation', 0, {'current': 1}, 'A7_cur1_nation00.png')
a = base['armies'][2]; g.click_tile(a['x'], a['y'], pause=1.4); capture('a7', save, 'army_left', 2, {'current': 1}, 'A7_cur1_army02_left.png')
a = base['armies'][0]; g.click_tile(a['x'], a['y'], pause=1.4); capture('a7', save, 'army_foreign_left', 0, {'current': 1}, 'A7_cur1_army00_left.png')
c = base['cities'][base['nations'][1]['capital']]; g.click_tile(c['x'], c['y'], pause=1.4); capture('a7', save, 'city_own', c['id'], {'current': 1}, 'A7_cur1_city_carthago.png')
c = base['cities'][85]; g.click_tile(c['x'], c['y'], pause=1.4); capture('a7', save, 'city_foreign', 85, {'current': 1}, 'A7_cur1_city_rome.png')
stop(g)
