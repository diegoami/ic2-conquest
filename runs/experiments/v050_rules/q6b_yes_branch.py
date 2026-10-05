"""Q6 play, part 2: the Yes branch from Q6_02_adjacent_moves5.SAV (Gaul army 9 at (90,29), 5 moves, next to Genua, relation to Greece 0):
click Genua, answer Yes: the relation must be 3 both ways at once (FUN_00449b40 :46545), then the siege runs (FUN_0044B27C :46547)."""
import sys; sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
D = sys.modules['harness.driver']
g = MyGame(); xvfb()
GREECE, ME, A9 = 7, 6, 9
def state(tag):
    s = snapstate(g, tag, (A9,), nation=ME)
    log('q6b', '   %s: relation Gaul->Greece %s, Greece->Gaul %s, army 9 moves %d troops %d' % (tag, g.nation_state(ME)['relations'].get('Greece'), g.nation_state(GREECE)['relations'].get('Gaul'), s['armies'][A9]['moves'], s['armies'][A9]['troops']))
log('q6b', 'load: %s' % g.load(SAVEDIR + 'Q6_02_adjacent_moves5.SAV', seed=12345))
state('Q6b_00_reloaded_before_yes')
ax, ay = g.army_pos(A9); g.select_army(A9, ax, ay)
g.click_tile(89, 30, pause=1.5)
p = snap(g, 'Q6b_prompt.png')
boxes = [w for w in g.find_windows('.') if w[1] in ('Information', 'Confirm') and w[4] < 600 and w[5] < 300]
log('q6b', 'boxes: %s' % [(w[1], ocr_text(p, crop='%dx%d+%d+%d' % (w[4], w[5], w[2], w[3])).strip().replace('\n', ' ')) for w in boxes])
g.answer('Confirm', yes=True); time.sleep(2.5)
snap(g, 'Q6b_after_yes.png')
log('q6b', 'popups after Yes: %s' % g.dismiss_popups())
state('Q6b_01_after_yes'); keep_save(g, 'Q6b_01_after_yes.SAV')
log('q6b', 'news tail (information panel is not read; the save carries the news log)')
g.kill()
