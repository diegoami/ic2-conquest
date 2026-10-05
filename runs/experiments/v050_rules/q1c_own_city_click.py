"""Q1 (R8 of the PR #47 review): the click on an adjacent own city with an army selected, with a before and an after SAVE.
Start: Q1_00_start.SAV (a copy of mobilize-new-army-0720.SAV saved by q1_purse.py): army 1 at (120,53) next to Heraclea (121,53), an own city.
The selection is not in a save; it is read from memory (SEL_ARMY) and tagged memory-only in the finding."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
D = sys.modules['harness.driver']
g = MyGame(); xvfb()
log('q1c', 'load: %s' % g.load(SAVEDIR + 'Q1_00_start.SAV', seed=12345))
A = (0, 1, 14)
snapstate(g, 'Q1c_00_before_click', A); keep_save(g, 'Q1c_00_before_click.SAV')
ax, ay = g.army_pos(1); g.select_army(1, ax, ay)
log('q1c', 'selected army before the click (memory): %d' % g.i16(D.SEL_ARMY))
g.click_tile(121, 53, pause=1.5)
log('q1c', 'popups %s; selected army after the click (memory only): %d' % (g.dismiss_popups(), g.i16(D.SEL_ARMY)))
snapstate(g, 'Q1c_01_after_click', A); keep_save(g, 'Q1c_01_after_click_own_city.SAV')
g.kill()
