"""Q3 play: disbanding queued recruitments (Army recruits > Disband) on recruit-hi3200-0720.SAV (Rome, treasury 1,880, mobilisation 32, five queued units at Rome).
Prediction from TArmyRecruits_DisbandUnits (:56157-56167) and FUN_0044a610 (:49003-49014): no treasury change at all (nothing is refunded), the slot is removed
(the queue shifts), mobilisation falls by 1 + troops x 1000 div wealth(2,577,000), floored at 0:
  HI 3,200 (not ready):  32 -> 32 - 1 - 1 = 30
  HI 4,000 (very poor):  30 -> 30 - 1 - 1 = 28   (floor 1.55 = 1; a rounding rule would give 27)"""
import sys; sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
g = MyGame(); xvfb()
log('q3', 'load: %s' % g.load(fixture('recruit-hi3200-0720.SAV'), seed=12345))
snapstate(g, 'Q3_00_start')
keep_save(g, 'Q3_00_start.SAV')

def disband(city_row, unit_row):
    open_tool(g, 'recruit', 'Army recruits')
    cs = g.controls('Army recruits')
    cities = g.control(cs, cls='TListBox', index=0); units = g.control(cs, cls='TListBox', index=1)
    g.click(cities['x'] + cities['w'] // 2, cities['y'] + 12 + 12 * city_row, pause=0.6)
    g.click(units['x'] + units['w'] // 2, units['y'] + 12 + 12 * unit_row, pause=0.4)
    snap(g, 'Q3_selected_row%d.png' % unit_row)
    g.click_control(g.control(cs, text='Disband'), pause=1.0)
    snap(g, 'Q3_confirm_row%d.png' % unit_row)
    texts = g.dismiss_popups()
    cs = g.controls('Army recruits'); snap(g, 'Q3_after_row%d.png' % unit_row)
    g.close_controls('Army recruits', cs)
    return texts
log('q3', 'disband queue row 4 (HI 3,200): %s' % disband(1, 4))
snapstate(g, 'Q3_01_after_disband_hi3200')
keep_save(g, 'Q3_01_after_disband_hi3200.SAV')
log('q3', 'disband queue row 2 (HI 4,000): %s' % disband(1, 2))
snapstate(g, 'Q3_02_after_disband_hi4000')
keep_save(g, 'Q3_02_after_disband_hi4000.SAV')
g.kill()
