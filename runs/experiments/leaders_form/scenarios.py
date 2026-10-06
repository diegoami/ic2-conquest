"""The plays of the leaders-form experiment. One function per play id; each gets (g, tag, rec). Every step is a verified helper of play_lib (no click at a guessed position)."""
from play_lib import *
from eog import _screen_words, _drv
import play_lib as P
import eog

MENU_EXPECT = {'file': 'save', 'game': 'abdicate'}     # a word of the dropdown, seen in every earlier probe of the menu (greyed or not)

def menu_probe(g, tag, rec, step, word):
    """Open the menu `word` (verified: its dropdown word must be seen), keep a screenshot of it (the grey / black state of its items) and the OCR words, then close it with Escape and prove it closed. Every transition is a recorded step;
    a menu that does not open stops the play."""
    hit, attempts = menu_open(g, word, MENU_EXPECT[word], [DROP])
    p = snap_rec(g, rec, 'menu_%s_%s' % (step, word), '%s_%s_menu_%s.png' % (tag, step, word))
    words = [w[0] for w in _screen_words(g, DROP)]
    rec.setdefault('menu_probe', {})[step + '_' + word] = words
    menu_close(g, word, MENU_EXPECT[word], [DROP])

def ticks(g, rows):
    for n in rows: set_tick(g, n, True)

# ---- P01: the form as it opens (seed 12345), its tab order, then Cancel with nothing ticked
def p01(g, tag, rec):
    open_form(g, tag, rec); fs = record_form(g, tag, 'default', rec)
    rec['tab_walk'] = tab_walk(g, 8); record_form(g, tag, 'after_tabs', rec)
    press_button(g, 'Cancel'); rec['humans_ticked'] = []
    time.sleep(2); rec['state'] = game_state(g); snap_rec(g, rec, 'after_cancel', '%s_after_cancel_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_cancel')); rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])

# ---- P02: zero humans, OK
def p02(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'before_ok', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = []
    after_ok(g, tag, rec, [])
    menu_probe(g, tag, rec, 'after_ok', 'file'); menu_probe(g, tag, rec, 'after_ok', 'game')

# ---- P03: Cancel after ticking and editing (the changes are discarded)
def p03(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    ticks(g, [1, 3]); edit_text(g, 1, 'Zed Cancelled'); record_form(g, tag, 'before_cancel', rec)
    press_button(g, 'Cancel'); rec['humans_ticked'] = [1, 3]
    time.sleep(2); rec['state'] = game_state(g); snap_rec(g, rec, 'after_cancel', '%s_after_cancel_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_cancel')); rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])
    menu_probe(g, tag, rec, 'after_cancel', 'file'); menu_probe(g, tag, rec, 'after_cancel', 'game')

# ---- P04: two humans (Carthage, Ptolemaic), one name edited, OK
def p04(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    ticks(g, [1, 3]); edit_text(g, 1, 'Zed Carthage'); record_form(g, tag, 'before_ok', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = [1, 3]
    after_ok(g, tag, rec, [1, 3])

# ---- P05: all sixteen humans, OK
def p05(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    ticks(g, list(range(16))); record_form(g, tag, 'before_ok', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = list(range(16))
    after_ok(g, tag, rec, list(range(16)))

LONG = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef'
ODD = 'ünal-ö "Q" |;,'

# ---- P06: the odd names in one OK: empty (Rome), spaces (Carthage), the same name twice (Seleucid, Ptolemaic), over-long (Macedonia), odd characters (Numidia)
def p06(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    ticks(g, [0, 1, 2, 3, 4, 5])
    edit_text(g, 0, ''); edit_text(g, 1, '   '); edit_text(g, 2, 'Twin'); edit_text(g, 3, 'Twin'); edit_text(g, 4, LONG); edit_text(g, 5, ODD)
    record_form(g, tag, 'before_ok', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = [0, 1, 2, 3, 4, 5]
    after_ok(g, tag, rec, [0, 1, 2, 3, 4, 5])

# ---- P07: a computer nation's name box is greyed; ticking and unticking restores the drawn name; then one human with an edited name
def p07(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    rec['greyed_edit'] = try_edit_disabled(g, 0, 'Xyz')
    set_tick(g, 1, True); edit_text(g, 1, 'Zed Temp'); record_form(g, tag, 'carthage_ticked_edited', rec)
    set_tick(g, 1, False); record_form(g, tag, 'carthage_unticked', rec)
    set_tick(g, 3, True); edit_text(g, 3, 'Cleo'); record_form(g, tag, 'before_ok', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = [3]
    after_ok(g, tag, rec, [3])

# ---- P08 (seeds 111, 222, 333): the draw: open the form and Cancel
def p08(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    press_button(g, 'Cancel'); rec['humans_ticked'] = []
    time.sleep(2); rec['state'] = game_state(g); snap_rec(g, rec, 'after_cancel', '%s_after_cancel_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_cancel')); rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])

# ---- P09: a second New Game in the same process, with another seed, after a game with a human; Cancel; then New Game again
def p09(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'first_default', rec)
    set_tick(g, 1, True); press_button(g, 'OK'); rec['humans_ticked'] = [1]
    after_ok(g, tag, rec, [1])
    rec['state_first_game'] = rec['state']
    g.set_seed(SEED2)
    open_form(g, tag, rec, answer='Yes'); snap_rec(g, rec, 'second_confirm_done', '%s_second_confirm_done.png' % tag); record_form(g, tag, 'second_default', rec)
    press_button(g, 'Cancel'); time.sleep(2); rec['state_after_cancel'] = game_state(g); snap_rec(g, rec, 'after_cancel', '%s_after_cancel_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_cancel')); rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])
    open_form(g, tag, rec); record_form(g, tag, 'third_default', rec)
    press_button(g, 'Cancel'); time.sleep(2); rec['state'] = game_state(g)

SEED2 = 777

# ---- P10: a game with one human; File > New; the Confirm box answered No: the game stays
def p10(g, tag, rec):
    open_form(g, tag, rec); set_tick(g, 1, True); press_button(g, 'OK'); rec['humans_ticked'] = [1]
    after_ok(g, tag, rec, [1])
    rec['state_before_new'] = rec['state']
    open_form(g, tag, rec, answer='No'); snap_rec(g, rec, 'after_no', '%s_after_no.png' % tag)
    time.sleep(2); rec['state_after_no'] = game_state(g)
    if form_wid(g): raise _drv.DriverError('the form opened after No')

# ---- P11: the Escape key closes the form like Cancel (ticks and edits discarded)
def p11(g, tag, rec):
    open_form(g, tag, rec); set_tick(g, 1, True); edit_text(g, 1, 'Zed Escape'); record_form(g, tag, 'before_escape', rec)
    press_key_close(g, 'Escape'); rec['humans_ticked'] = [1]
    time.sleep(2); rec['state'] = game_state(g); snap_rec(g, rec, 'after_escape', '%s_after_escape_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_escape')); rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])

# ---- P12: the Return key closes the form like OK (the default button): one human ticked, focus in its name box
def p12(g, tag, rec):
    open_form(g, tag, rec); set_tick(g, 3, True); record_form(g, tag, 'before_return', rec)
    press_key_close(g, 'Return'); rec['humans_ticked'] = [3]
    after_ok(g, tag, rec, [3])

# ---- P13: the keyboard: Tab to Carthage's tick box and press space (the handler is OnMouseDown: does the name box wake up?), then OK
def p13(g, tag, rec):
    open_form(g, tag, rec); record_form(g, tag, 'default', rec)
    rec['tabs_to_carthage'] = focus_checkbox_by_tab(g, 1)
    rec['space'] = key_toggle(g, 1); record_form(g, tag, 'after_space', rec)
    press_button(g, 'OK'); rec['humans_ticked'] = [1]
    after_ok(g, tag, rec, [1])

SC = {'P01': dict(seed=12345, fn=p01, note='the form as it opens, tab order, Cancel with nothing ticked'),
      'P02': dict(seed=12345, fn=p02, note='zero humans, OK'),
      'P03': dict(seed=12345, fn=p03, note='Cancel after ticking Carthage and Ptolemaic and editing Carthage'),
      'P04': dict(seed=12345, fn=p04, note='two humans (Carthage, Ptolemaic), Carthage renamed, OK'),
      'P05': dict(seed=12345, fn=p05, note='all sixteen humans, OK'),
      'P06': dict(seed=12345, fn=p06, note='six humans with an empty, a spaces-only, two equal, an over-long and an odd-character name, one OK'),
      'P07': dict(seed=12345, fn=p07, note='greyed computer name box; tick, edit, untick restores; one human with an edited name'),
      'P08a': dict(seed=111, fn=p08, note='draw, seed 111'), 'P08b': dict(seed=222, fn=p08, note='draw, seed 222'), 'P08c': dict(seed=333, fn=p08, note='draw, seed 333'),
      'P09': dict(seed=12345, fn=p09, note='second New Game with another seed, Cancel, New Game again'),
      'P11': dict(seed=12345, fn=p11, note='Escape closes the form like Cancel'),
      'P12': dict(seed=12345, fn=p12, note='Return closes the form like OK'),
      'P13': dict(seed=12345, fn=p13, note='keyboard: Tab to the Carthage tick box, space, OK'),
      'P10': dict(seed=12345, fn=p10, note='File > New with a game running, Confirm answered No')}

def run(pid, batch):
    sc = SC[pid]; tag = 'LF_%s_%s' % (pid, batch)
    import glob, json as _json
    for f in glob.glob(DATA + 'plays_*.jsonl'):          # a recording is never replaced: a tag already recorded is refused (a re-run uses a new batch name)
        for l in open(f):
            if l.strip() and (_json.loads(l).get('tag') or 'LF_%s_%s' % (_json.loads(l)['play'], _json.loads(l)['batch'])) == tag: raise _drv.DriverError('the tag %s is already recorded in %s: use a new batch name' % (tag, f))
    eog._ATTEMPTS.clear(); del CLICKS[:]; del KEYS[:]; del VERIFIED[:]
    g = start_game(sc['seed']); rec = new_rec(pid, batch, sc['seed'], sc['note']); rec['tag'] = tag
    CTX.update(tag=tag, why=None, target=None)
    try:
        sc['fn'](g, tag, rec); rec['status'] = 'ok'
    except Exception as e:
        rec['status'] = 'FAILED'; rec['error'] = repr(e)
        try: snap(g, '%s_failure.png' % tag)
        except Exception: pass
        raise
    finally:
        finish(rec, g, batch)
    return rec
