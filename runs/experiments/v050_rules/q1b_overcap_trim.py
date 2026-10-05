"""Q1 play, part 2: a purse above 1,000 (the 2,000 left by Join armies, save Q1_06_after_join.SAV) opened in Supply army: one click on the
money 100s up arrow is predicted by TAFSupply_ChangeMoney (:43118-43135) to move min(100, 1000 - 2000) = -1000, i.e. the purse falls
to 1,000 and the treasury gains 1,000. Then one more click (nothing: min(100, 0))."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
g = MyGame(); xvfb()
log('q1b', 'load: %s' % g.load(SAVEDIR + 'Q1_06_after_join.SAV', seed=12345))
A = (0, 1, 14)
snapstate(g, 'Q1b_00_loaded_Q1_06', A)
log('q1b', 'supply army 1: one click money 100s up: %s' % supply_dialog(g, 1, money100=1))
snapstate(g, 'Q1b_01_after_one_up_click', A)
keep_save(g, 'Q1b_01_after_one_up_click.SAV')
log('q1b', 'supply army 1: one more click: %s' % supply_dialog(g, 1, money100=1))
snapstate(g, 'Q1b_02_after_second_up_click', A)
g.kill()
