#!/usr/bin/env python3
"""One single-human End of Game scenario on a STAGED copy of the run-0 start save (Rome human, seed 12345): the staged field(s) make one reason hold, End turn
is pressed once, the window is captured (screenshot, OCR, memory), OK is pressed, and the state afterwards is recorded.

usage: run_single.py REASON [BATCH]        REASON in: debt debt_wealth unity y250 victory unity_debt y250_unity abdicate control
Every scenario is STAGED (the saves are edited; see staging_log.tsv); nothing here is natural play."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eog import *
from eog import _drv, _screen_words

reason = sys.argv[1]; batch = sys.argv[2] if len(sys.argv) > 2 else 'b1'
SRC = fixture('run0-start-AUTO0720-seed12345.SAV')
ROME_WEALTH = 2577000                                         # read from the fixture below, not typed into a claim
SC = {
    'control':     [],
    'debt':        [('treasury', 0, -30000)],                  # below -20000
    'debt_wealth': [('treasury', 0, -9000)],                   # above -20000, below -(wealth div 500) = -5154
    'unity':       [('unity', 0, 100)],
    'y250':        [('calendar', 'year', 251), ('calendar', 'season', 3), ('calendar', 'week', 11)],
    'victory':     [('ncities', 0, 334)],                      # the city-count word only: the cities' owners and lists are untouched
    'victory_full': [('own_all', 0)],                          # every city owned by Rome, Rome's list = all 334, the other 15 nations emptied (unity 0)
    'victory_y250': [('ncities', 0, 334), ('calendar', 'year', 251), ('calendar', 'season', 3), ('calendar', 'week', 11)],
    'unity_debt':  [('unity', 0, 100), ('treasury', 0, -30000)],
    'y250_unity':  [('calendar', 'year', 251), ('calendar', 'season', 3), ('calendar', 'week', 11), ('unity', 0, 100)],
    'abdicate':    [],
}[reason]
tag = 'EOG_%s_%s' % (reason, batch)
L = lambda m: log('single_%s' % batch, '[%s] %s' % (reason, m))

clear_autos()
staged = edit_save(SRC, SAVEDIR + 'inputs/%s_staged.SAV' % tag, SC, tag)
s0 = read_save(staged)
g = MyGame()
texts = g.load(staged, seed=12345)
L('loaded %s; popups at load: %s' % (os.path.basename(staged), texts))
before = world_state(g, 'loaded')
jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': 'loaded', **before})
rome = before['seats'][0]
L('before: %s' % json.dumps(rome))
assert before['cur_nation'] == 0 and before['humans'] == [0], before['humans']
# the staged field(s) reached the game (memory check of every edited field)
for op in SC:
    if op[0] == 'treasury': assert rome['treasury'] == op[2], rome
    if op[0] == 'unity': assert rome['unity'] == op[2], rome
    if op[0] == 'ncities': assert rome['cities'] == op[2], rome
    if op[0] == 'own_all': assert rome['cities'] == 334, rome
    if op[0] == 'calendar': assert before['calendar'][{'year': 'year_bc'}.get(op[1], op[1])] == op[2], before['calendar']
snap(g, '%s_00_loaded.png' % tag)

if reason == 'abdicate':
    L('Game > Abdicate by OCR menu pick')
    menu_pick(g, 'game', 'abdicate', expect=r'^Confirm$')
    w = g.find_windows(r'^Confirm$')[0]
    p, t6, t4 = ocr_window(g, w[0], tag + '_01_confirm')
    L('Confirm OCR: %s' % ' '.join(t6.split()))
    jlog('ocr_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'window': 'Confirm', 'png': os.path.basename(p), 'psm6': t6, 'psm4': t4,
                                  'geometry': w[2:], 'controls': g.controls('Confirm')})
    pre = world_state(g, 'confirm_open')
    jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': 'confirm_open', **pre})
    L('Confirm answered: %s' % answer_confirm(g, 'Confirm', '&Yes'))
    for k in range(8):                                       # a timeline: the state does not change at once
        time.sleep(2)
        st = world_state(g, 'after_yes_t%d' % (2 * (k + 1)))
        st.update({'windows': all_windows(g), 'title': main_title(g), 'alive': proc_alive(g), 'boxes': [(p[1], g.read_popup(p)) for p in g.popups()]})
        jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': 'after_yes_t%d' % (2 * (k + 1)), **st})
        L('t+%ds: humans %s windows %s boxes %s' % (2 * (k + 1), st['humans'], st['windows'], st['boxes']))
    snap(g, '%s_02_after_yes.png' % tag)
    L('harvested %s' % harvest(tag))
    sys.exit(0)

try:
    press_end_turn_once(g)
except _drv.DriverError as e:
    L('End turn: no sign (%s); not clicking again blindly' % e); raise
L('End turn registered')
w, texts = wait_window(g, r'^End of Game$', 300, 'End of Game window')
L('End of Game window up: %s; boxes closed on the way: %s' % (w, texts))
time.sleep(1)
w = eog_window(g)
at_window = world_state(g, 'window_open')
jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': 'window_open', **at_window})
L('state at window: %s' % json.dumps(at_window['seats']))
snap(g, '%s_03_window_context.png' % tag)
p, t6, t4 = ocr_window(g, w[0], tag + '_04_window')
mem = mem_strings(g, ['The game is over for', 'You have reached the end', 'Your unpopularity', 'Your army have', 'Your nation has been', 'You have conquerred',
                      'in power in', 'Population ', 'Cities   ', 'Treasury '], full=['in power in'])
jlog('ocr_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'window': 'End of Game', 'png': os.path.basename(p), 'psm6': t6, 'psm4': t4, 'geometry': w[2:],
                              'controls': g.controls('End of Game'), 'memory_strings': mem})
L('OCR: %s' % ' | '.join(l for l in t6.splitlines() if l.strip()))
L('memory strings: %s' % json.dumps(mem))
L('autosaves so far: %s' % harvest(tag))
n_ok = click_ok(g, 'End of Game')
L('OK pressed (%d click(s)); window closed' % n_ok)
time.sleep(4)
for _ in range(3):
    texts = close_boxes(g)
    if not texts: break
    L('boxes after OK: %s' % texts)
aft = world_state(g, 'after_ok')
aft.update({'windows': all_windows(g), 'title': main_title(g), 'alive': proc_alive(g), 'loaded': g.loaded(), 'boxes': texts})
jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': 'after_ok', **aft})
L('after OK: %s' % json.dumps({k: aft[k] for k in ('cur_nation', 'humans', 'windows', 'title', 'alive', 'loaded', 'calendar')}))
snap(g, '%s_05_after_ok.png' % tag)
L('harvested %s' % harvest(tag))
L('menu bar OCR after OK: %s' % [w_[0] for w_ in _screen_words(g, (0, 26, 650, 24))])
