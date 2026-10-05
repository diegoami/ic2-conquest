"""Q6 play: is a refused attack a war declaration? Gaul human (fixture S06_Gaul_AUTO0720.SAV from release run-exp-civ-sweep): army 9 (40,500, 8 moves) at (93,28),
Genua (89,30) belongs to Greece, relation Gaul-Greece 0 (peace); Greece has no ally. Prediction from TUnitMap_SelectUnit (:46514-46547):
the legality (an army selected, moves >= 1, target at Chebyshev exactly 1) is computed first (:46514-46521); only if it holds does the prompt come (:46541) and,
after Yes, the war declaration FUN_00449b40(me, target, 3) (:46544-46545) and then the siege FUN_0044B27C (:46547). A refused click declares nothing.
 C: army 4 tiles away, click Genua: silent, relation unchanged;  B: adjacent with 5 moves, click Genua: prompt; No: nothing changes;
 A: adjacent with 0 moves (moves burnt by stepping around the city), click Genua: no prompt, relation unchanged;
 E: reload the adjacent state with 5 moves, click Genua, Yes: relation 3 at once, news 'declares war', the siege."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
D = sys.modules['harness.driver']
IN = ART + 'inputs/S06_Gaul_AUTO0720.SAV'
g = MyGame(); xvfb()
GREECE, ME, A9 = 7, 6, 9
def rel(): return g.nation_state(ME)['relations'].get('Greece')
def state(tag): 
    s = snapstate(g, tag, (A9,), nation=ME); a = s['armies'][A9]
    log('q6', '   %s: relation Gaul->Greece %s, Greece->Gaul %s, army 9 at (%d,%d) moves %d, selected %d, news lines %s' % (
        tag, rel(), g.nation_state(GREECE)['relations'].get('Gaul'), a['x'], a['y'], a['moves'], g.i16(D.SEL_ARMY), 'n/a'))
    return s
def click_city(tag, answer=None):
    ax, ay = g.army_pos(A9); g.select_army(A9, ax, ay)
    g.click_tile(89, 30, pause=1.5)
    p = snap(g, 'Q6_%s_after_click.png' % tag)
    boxes = [w for w in g.find_windows('.') if w[1] in ('Information', 'Confirm') and w[4] < 600 and w[5] < 300]
    texts = [(w[1], ocr_text(p, crop='%dx%d+%d+%d' % (w[4], w[5], w[2], w[3])).strip().replace('\n', ' ')) for w in boxes]
    if answer is not None and any(t[0] == 'Confirm' for t in texts):
        g.answer('Confirm', yes=answer); time.sleep(2.0)
        snap(g, 'Q6_%s_after_answer.png' % tag)
    left = g.dismiss_popups()
    return texts, left
log('q6', 'load: %s' % g.load(IN, seed=12345))
state('Q6_00_start'); keep_save(g, 'Q6_00_start.SAV')
log('q6', 'C: army 4 tiles from Genua, click Genua: %s' % (click_city('C_far'),))
state('Q6_01_after_far_click'); keep_save(g, 'Q6_01_after_far_click.SAV')
log('q6', 'move army 9 to (90,29): %s' % (g.move(A9, 90, 29),))
state('Q6_02_adjacent_moves5'); keep_save(g, 'Q6_02_adjacent_moves5.SAV')
log('q6', 'B: adjacent with moves, click Genua, answer No: %s' % (click_city('B_no', answer=False),))
state('Q6_03_after_prompt_no'); keep_save(g, 'Q6_03_after_prompt_no.SAV')
for k, (x, y) in enumerate([(90, 30), (90, 29), (90, 30), (90, 29), (90, 30)]):
    g.move(A9, x, y)
state('Q6_04_adjacent_moves0'); keep_save(g, 'Q6_04_adjacent_moves0.SAV')
log('q6', 'A: adjacent with 0 moves, click Genua: %s' % (click_city('A_zero_moves', answer=False),))
state('Q6_05_after_zero_move_click'); keep_save(g, 'Q6_05_after_zero_move_click.SAV')
log('q6', 'E: reload Q6_02 (adjacent, 5 moves), click Genua, answer Yes')
log('q6', 'E load: %s' % g.load(SAVEDIR + 'Q6_02_adjacent_moves5.SAV', seed=12345))
state('Q6_06_reloaded_before_yes')
log('q6', 'E: %s' % (click_city('E_yes', answer=True),))
state('Q6_07_after_yes'); keep_save(g, 'Q6_07_after_yes.SAV')
g.kill()
