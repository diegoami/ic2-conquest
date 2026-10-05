"""Q5 play: disbanding a unit in Change units: regular units lower the mobilisation rate, mercenaries do not.
Prediction from TChangeArmyUnits_RemoveUnit (:45787-45792) and TChangeArmyUnits_OK (:45820):
  regular unit (slot +0 == 0): mobilisation := max(0, mobilisation - 1 - troops x 1000 div wealth), committed at OK;
  mercenary unit (slot +0 != 0): mobilisation unchanged.
Part A: run0-start-AUTO0720-seed12345.SAV, army 0 at (100,37) next to Arretium (own city): disband HI 5,900 (unit row 3): 30 -> 30 - 1 - 2 = 27 (5900x1000 div 2,577,000 = 2).
Part B: merc-hire-free-0720.SAV, army 1 next to Heraclea (own city): disband the hired Samnite LI 3,868 (unit row 6, a mercenary): 30 -> 30."""
import sys; sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
g = MyGame(); xvfb()
def change_disband(i, row, tag):
    g.army_tool(i, 'change', 'Change units')
    cs = g.controls('Change units')
    lst = g.control(cs, cls='TListBox')
    g.click(lst['x'] + lst['w'] // 2, lst['y'] + 12 + 12 * row, pause=0.5)
    snap(g, 'Q5_%s_selected.png' % tag)
    g.click_control(g.control(cs, text='Disband'), pause=1.0)
    p = snap(g, 'Q5_%s_confirm_or_refusal.png' % tag)
    boxes = [w for w in g.find_windows('.') if w[1] in ('Information', 'Confirm') and w[4] < 600 and w[5] < 300]
    texts = [ocr_text(p, crop='%dx%d+%d+%d' % (w[4], w[5], w[2], w[3])).strip().replace('\n', ' ') for w in boxes]
    g.dismiss_popups()
    snap(g, 'Q5_%s_dialog_after_disband.png' % tag)
    g._close_change_units(cs)
    return texts
log('q5', 'A load: %s' % g.load(fixture('run0-start-AUTO0720-seed12345.SAV'), seed=12345))
snapstate(g, 'Q5A_00_start', (0,)); keep_save(g, 'Q5A_00_start.SAV')
log('q5', 'A disband HI 5,900 (army 0 row 3): %s' % change_disband(0, 3, 'A_hi5900'))
snapstate(g, 'Q5A_01_after_disband_regular', (0,)); keep_save(g, 'Q5A_01_after_disband_regular.SAV')
log('q5', 'B load: %s' % g.load(fixture('merc-hire-free-0720.SAV'), seed=12345))
snapstate(g, 'Q5B_00_start', (1,)); keep_save(g, 'Q5B_00_start.SAV')
log('q5', 'B disband the Samnite mercenary (army 1 row 6): %s' % change_disband(1, 6, 'B_merc'))
snapstate(g, 'Q5B_01_after_disband_merc', (1,)); keep_save(g, 'Q5B_01_after_disband_merc.SAV')
g.kill()
