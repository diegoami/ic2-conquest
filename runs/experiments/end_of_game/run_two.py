#!/usr/bin/env python3
"""Two-human End of Game scenarios (Rome seat 11 and Gaul seat 14 of the turn order, seed 12345) on STAGED copies of the unedited two-human start save.

usage: run_two.py SCENARIO [BATCH]        SCENARIO in: debt_gaul abdicate_rome y250_both conquest
  debt_gaul     Gaul's treasury staged to -30000; Rome ends its turn; Gaul's turn starts and Gaul falls; does Rome play on?
  abdicate_rome Rome abdicates (Game > Abdicate > Yes); does the game go on with Gaul?
  y250_both     calendar staged to 251 BC Winter week 11: at 250 BC Rome falls, then Gaul (the last human)
  conquest      Gaul's city-count word staged to 5 and Felsina's loyalty/fort/pop staged to 1/0/1; Rome's army 0 is marched next to Felsina over two turns
                (Rome, then Gaul ends its turn) and besieges it: Felsina falls, Gaul is left with fewer than 6 cities and is conquered
Every scenario is STAGED; nothing here is natural play."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eog import *
from eog import _drv, _screen_words

scen = sys.argv[1]; batch = sys.argv[2] if len(sys.argv) > 2 else 'b2'
BASE = SAVEDIR + 'inputs/EOG_2h_base_AUTO0720.SAV'
ops = {
    'debt_gaul':     [('treasury', 6, -30000)],
    'abdicate_rome': [],
    'y250_both':     [('calendar', 'year', 251), ('calendar', 'season', 3), ('calendar', 'week', 11)],
    'conquest':      [('ncities', 6, 5), ('city', 79, {'loyalty': 1, 'fort': 0, 'pop': 1})],
}[scen]
tag = 'EOG2_%s_%s' % (scen, batch)
L = lambda m: log('two_%s' % batch, '[%s] %s' % (scen, m))
J = lambda step, **kw: jlog('states_%s.jsonl' % batch, {'reason': scen, 'tag': tag, 'step': step, **kw})

clear_autos()
staged = edit_save(BASE, SAVEDIR + 'inputs/%s_staged.SAV' % tag, ops, tag)
g = MyGame()
texts = g.load(staged, seed=12345)
st = world_state(g, 'loaded'); J('loaded', **st)
L('loaded %s; popups %s; humans %s cur %s' % (os.path.basename(staged), texts, st['humans'], st['cur_nation']))
assert st['humans'] == [0, 6] and st['cur_nation'] == 0, st
L('Rome: %s' % json.dumps(st['seats'][0])); L('Gaul: %s' % json.dumps(st['seats'][6]))
snap(g, '%s_00_loaded.png' % tag)

def after(step, wait_for_nation=None):
    """State after a window/menu step: the humans, the current nation, the windows, the title; a Save As when a game is still running."""
    time.sleep(3)
    for _ in range(3):
        t = close_boxes(g)
        if not t: break
        L('boxes: %s' % t)
    s = world_state(g, step); s.update({'windows': all_windows(g), 'title': main_title(g), 'alive': proc_alive(g), 'loaded': g.loaded()})
    J(step, **s)
    L('%s: humans %s cur %s windows %s title %s' % (step, s['humans'], s['cur_nation'], [w[0] for w in s['windows']], s['title']))
    snap(g, '%s_%s.png' % (tag, step))
    return s

if scen == 'debt_gaul':
    n0 = autosave_lines()
    press_end_turn_once(g)
    kind, texts = wait_turn_of(g, 6, 300, L, n0)
    L('after Rome ended its turn: %s %s' % (kind, texts))
    if kind != 'window':
        w, t = wait_window(g, r'^End of Game$', 60, 'End of Game window')
    n_win = autosave_lines()                                     # Gaul's turn autosave is already written: Rome's turn will add the next line
    at, t6, n_ok = capture_and_ok(g, tag, batch, scen, 'gaul', L)
    assert at['cur_nation'] == 6
    # the fall ends Gaul's turn by itself (HumanLeaderFalls): wait for Rome's turn
    kind, texts = wait_turn_of(g, 0, 300, L, n_win)
    L('wait for Rome: %s %s' % (kind, texts))
    s = after('after_ok_rome_turn')
    L('autosaves %s' % harvest(tag))
    p = keep_save_ocr(g, 'EOG2_%s_after_gaul_falls.SAV' % scen); L('saved %s' % p)
elif scen == 'abdicate_rome':
    n0 = autosave_lines()
    menu_pick(g, 'game', 'abdicate', expect=r'^Confirm$')
    w = g.find_windows(r'^Confirm$')[0]
    p, t6, t4 = ocr_window(g, w[0], tag + '_01_confirm')
    L('Confirm OCR: %s' % ' '.join(t6.split()))
    L('Confirm answered: %s' % answer_confirm(g, 'Confirm', '&Yes'))
    kind, texts = wait_turn_of(g, 6, 300, L, n0)
    L('wait for Gaul: %s %s' % (kind, texts))
    s = after('after_yes_gaul_turn')
    L('autosaves %s' % harvest(tag))
    p = keep_save_ocr(g, 'EOG2_%s_after.SAV' % scen); L('saved %s' % p)
elif scen == 'y250_both':
    n0 = autosave_lines()
    press_end_turn_once(g)                                       # Rome (251 BC Winter week 11); Gaul, the next human seat, plays before the year turns
    kind, texts = wait_turn_of(g, 6, 300, L, n0); L('Gaul turn (251 BC): %s %s' % (kind, texts))
    assert kind == 'turn'
    n1 = autosave_lines()
    press_end_turn_once(g)
    w, texts = wait_window(g, r'^End of Game$', 400, 'first End of Game window'); L('boxes on the way %s' % texts)
    at1, t6, n_ok = capture_and_ok(g, tag, batch, scen, 'first', L)
    L('first window was for nation %s (cur nation at the window)' % at1['cur_nation'])
    time.sleep(2)
    w2 = None; t0 = time.time()
    while time.time() - t0 < 400:                                # the second window (the other human), or the end of the game
        if g.find_windows(r'^End of Game$'): w2 = True; break
        if not world_state(g, 'poll')['humans']: break
        close_boxes(g); time.sleep(1)
    if w2:
        at2, t6b, n_ok2 = capture_and_ok(g, tag, batch, scen, 'second', L)
        L('second window was for nation %s' % at2['cur_nation'])
    s = after('after_both')
    L('autosaves %s' % harvest(tag))
elif scen == 'conquest':
    # turn 1 (Rome): march army 0 to (99,34), the move used by tests/test_orders.py test_attack
    n0 = autosave_lines()
    a0 = g.army_pos(0); L('army 0 at %s' % (a0,))
    g.move(0, 99, 34)
    L('army 0 after the move order: %s; texts %s' % (g.army_pos(0), close_boxes(g)))
    press_end_turn_once(g)
    kind, texts = wait_turn_of(g, 6, 300, L, n0); L('Gaul turn: %s %s' % (kind, texts))
    s = after('gaul_turn_0720')
    n1 = autosave_lines()
    press_end_turn_once(g)
    kind, texts = wait_turn_of(g, 0, 300, L, n1); L('Rome turn: %s %s' % (kind, texts))
    s = after('rome_turn_0721')
    p = keep_save_ocr(g, 'EOG2_%s_before_siege.SAV' % scen); L('saved %s' % p)
    fx, fy = [(c['x'], c['y']) for c in read_save(p)['cities'] if c['id'] == 79][0]
    L('Felsina at %s; army 0 at %s' % ((fx, fy), g.army_pos(0)))
    for step in [(99, 33), (99, 32)]:
        if max(abs(g.army_pos(0)[0] - fx), abs(g.army_pos(0)[1] - fy)) == 1: break
        g.move(0, *step); L('army 0 at %s' % (g.army_pos(0),))
    assert max(abs(g.army_pos(0)[0] - fx), abs(g.army_pos(0)[1] - fy)) == 1, g.army_pos(0)
    p = keep_save_ocr(g, 'EOG2_%s_adjacent.SAV' % scen); L('saved %s' % p)
    # the siege: select army 0, click Felsina; "Are you sure" is answered Yes by its controls; then the End of Game window of Gaul appears
    ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
    g.click_tile(fx, fy, pause=1.5)
    got = None
    t0 = time.time()
    while time.time() - t0 < 60:
        if g.find_windows(r'^End of Game$'): got = 'window'; break
        if g.find_windows('^Confirm$'):                                # the siege confirmation: answered through answer_confirm (X id tracked, verified gone, 3 attempts in all)
            L('Confirm: %s' % answer_confirm(g, 'Confirm', '&Yes')); continue
        t = close_boxes(g)
        if t: L('boxes: %s' % t)
        time.sleep(1)
    L('after the siege click: %s' % got)
    assert got == 'window'
    at, t6, n_ok = capture_and_ok(g, tag, batch, scen, 'gaul', L)
    s = after('after_ok')
    L('autosaves %s' % harvest(tag))
    p = keep_save_ocr(g, 'EOG2_%s_after_gaul_conquered.SAV' % scen); L('saved %s' % p)
