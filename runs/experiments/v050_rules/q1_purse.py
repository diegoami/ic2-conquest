"""Q1 play: purse rules on the 0720 Rome fixture (mobilize-new-army-0720.SAV, a copy; own display :733, own game folder).
Flow A (army 0, purse 100, supplies 170): move to (100,42), adjacent to Rome and Caere (own cities with stock): no automatic resupply.
Flow B (army 1 at Heraclea, purse 100): click the adjacent own city (nothing), Supply army 11 x (+100) (cap at 1000), Split, Supply the partner
11 x (+100), Join armies: the kept army's purse is the sum (2,000, no cap).
Every step is saved (File > Save as) and its state logged to the tracked log; nothing is overwritten."""
import sys; sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
D = sys.modules['harness.driver']
g = MyGame(); xvfb()
log('q1', 'load: %s' % g.load(fixture('mobilize-new-army-0720.SAV'), seed=12345))
A = (0, 1, 14)
snapstate(g, 'Q1_00_start', A)
keep_save(g, 'Q1_00_start.SAV')

pos, texts = g.move(0, 100, 42)
log('q1', 'move army 0 -> %s popups %s' % (pos, texts))
snapstate(g, 'Q1_01_army0_at_100_42_next_to_Rome_and_Caere', A)
keep_save(g, 'Q1_01_army0_at_100_42.SAV')

ax, ay = g.army_pos(1); g.select_army(1, ax, ay); g.click_tile(121, 53, pause=1.5)
log('q1', 'click own city Heraclea with army 1 selected: popups %s, selected now %s' % (g.dismiss_popups(), g.i16(D.SEL_ARMY)))
snapstate(g, 'Q1_02_army1_after_click_on_own_city', A)

log('q1', 'supply army 1 money x11: %s' % supply_dialog(g, 1, money100=11))
snapstate(g, 'Q1_03_army1_supply_11x100', A)
keep_save(g, 'Q1_03_army1_supply_11x100.SAV')

before = set(i for i in range(40) if g.army_state(i)['troops'] > 0)
log('q1', 'split army 1: %s' % g.split_army(1, unit_rows=(0,)))
new = sorted(set(i for i in range(40) if g.army_state(i)['troops'] > 0) - before)
log('q1', 'new armies %s' % new)
assert len(new) == 1
P = new[0]
snapstate(g, 'Q1_04_after_split', A + (P,))
keep_save(g, 'Q1_04_after_split.SAV')

log('q1', 'supply partner %d money x11: %s' % (P, supply_dialog(g, P, money100=11)))
snapstate(g, 'Q1_05_before_join', A + (P,))
keep_save(g, 'Q1_05_before_join.SAV')

log('q1', 'join (army 1 selected): %s' % g.join(1))
snapstate(g, 'Q1_06_after_join', A + (P,))
keep_save(g, 'Q1_06_after_join.SAV')
g.kill()
