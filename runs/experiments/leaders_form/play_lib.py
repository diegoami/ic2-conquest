"""Verified plays of the original's "Human and computer leaders" form (TPickLeaders), copying the approach of runs/experiments/refusal_texts:
own display (:743) and game folder (~/ic2-work-leaders), every click recorded with its reason, every control and state read from the running game
(win_state.exe, a read-only helper that prints each child control's text, enabled/visible, check state, edit limit and focus; the form's controls are located by
their rectangles, never by a fixed coordinate), every click's effect verified (at most three clicks per step), a window tracked by its X id, and a step whose
control or expected state is missing stops the run (DriverError) instead of guessing a click.
Everything a finding may cite is a new versioned tracked file under runs/experiments/data/run-exp-leaders-form/ (CLAUDE.md rule 6)."""
import json, os, re, struct, subprocess, time, shutil, hashlib
import eog
from eog import *                                   # noqa: F401,F403
from eog import _drv, _ids, _geo, _screen_words
from lib import _orig_sh
from common import new_path

TITLE = 'Human and computer leaders'
NATIONS = ['Rome', 'Carthage', 'Seleucid', 'Ptolemaic', 'Macedonia', 'Numidia', 'Gaul', 'Greece', 'Celtiberia', 'Illyria', 'Dacia', 'Bithynia', 'Galatia', 'Armenia', 'Media', 'Thracia']
TURN_ORDER = 0x49EFE8                                # DAT_0049efe8, 16 shorts (all_app_functions / news_log_decomp FUN_00448aa4)
CLICKS = []                                           # every click of the play: {x, y, why}
VERIFIED = []                                         # every verified transition: {step, how, attempts, ...}
CTX = {'why': None, 'tag': None}
KEYS = []                                             # every key / text sent (xdotool), with its reason

def note_verified(**kw): VERIFIED.append(kw)

class Game3(MyGame):
    """MyGame whose every click is recorded with the reason the caller gave (CTX['why']) so that the play's record lists them all."""
    def click(self, x, y, pause=0.4):
        CLICKS.append({'x': x, 'y': y, 'why': CTX.get('why')})
        return MyGame.click(self, x, y, pause)
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        CTX['why'] = 'control %s %r at %d,%d %dx%d' % (c['cls'], c.get('text', ''), c['x'], c['y'], c['w'], c['h'])
        return MyGame.click_control(self, c, fx, fy, pause)
    def key(self, *keys):
        KEYS.append({'keys': list(keys), 'why': CTX.get('why')}); return MyGame.key(self, *keys)
    def type(self, text):
        KEYS.append({'type': text, 'why': CTX.get('why')}); return MyGame.type(self, text)

# ---------------------------------------------------------------- the form's state, read from the game
STATE_EXE = lambda: _drv.WORK / 'win_state.exe'

def read_controls(g, title=TITLE):
    """win_state.exe on the visible window `title`: [{cls, text, x, y, w, h, enabled, visible, check, limit, sel0, sel1, focus, style}] (raw text kept in the first element's 'raw')"""
    out = subprocess.run([_drv.WINE, str(STATE_EXE()), title], env=_drv.ENV, capture_output=True).stdout.decode('latin1')   # the game's ANSI text (Windows-1252 / Latin-1 bytes), never utf-8
    cs = []
    for line in out.splitlines():
        p = line.split('\t')
        if len(p) == 14:
            cs.append({'cls': p[0], 'text': p[1], 'x': int(p[2]), 'y': int(p[3]), 'w': int(p[4]), 'h': int(p[5]), 'enabled': int(p[6]), 'visible': int(p[7]), 'check': int(p[8]), 'limit': int(p[9]),
                       'sel0': int(p[10]), 'sel1': int(p[11]), 'focus': int(p[12]), 'style': p[13]})
    if not cs: raise _drv.DriverError('no controls read for window %r' % title)
    cs[0]['raw'] = out
    return cs

def form_state(g):
    """The 16 rows (a panel with its checkbox and edit, matched by containment of the control in the panel's rectangle) and the buttons."""
    cs = read_controls(g)
    panels = [c for c in cs if c['cls'] == 'TPanel']
    rows = {}
    for p in panels:
        name = p['text'].strip()
        if name not in NATIONS: raise _drv.DriverError('unknown panel %r' % p['text'])
        inside = lambda c: p['x'] <= c['x'] and c['x'] + c['w'] <= p['x'] + p['w'] and p['y'] <= c['y'] and c['y'] + c['h'] <= p['y'] + p['h'] + 4
        cb = [c for c in cs if c['cls'] == 'TCheckBox' and inside(c)]; ed = [c for c in cs if c['cls'] == 'TEdit' and inside(c)]
        if len(cb) != 1 or len(ed) != 1: raise _drv.DriverError('panel %s: %d checkboxes, %d edits' % (name, len(cb), len(ed)))
        rows[NATIONS.index(name)] = {'nation': name, 'panel': p, 'cb': cb[0], 'ed': ed[0]}
    if sorted(rows) != list(range(16)):
        return {'rows': rows, 'buttons': {c['text']: c for c in cs if c['cls'] == 'TButton'}, 'cs': cs, 'complete': False}
    return {'rows': rows, 'buttons': {c['text']: c for c in cs if c['cls'] == 'TButton'}, 'cs': cs, 'complete': True}

def summary(fs):
    """Compact per-row record: [nation, check, checkbox enabled, edit text, edit enabled, edit limit]"""
    return [[fs['rows'][i]['nation'], fs['rows'][i]['cb']['check'], fs['rows'][i]['cb']['enabled'], fs['rows'][i]['ed']['text'], fs['rows'][i]['ed']['enabled'], fs['rows'][i]['ed']['limit']] for i in sorted(fs['rows'])]

def form_wid(g):
    w = g.find_windows('^%s$' % re.escape(TITLE))
    return w[0][0] if w else None

def record_form(g, tag, step, rec):
    """Keep the form's state as read now (raw win_state output, tracked) and a screenshot of the whole screen (artifact, hashed)."""
    fs = form_state(g)
    snap(g, '%s_%s_form.png' % (tag, step))
    rec['forms'][step] = {'rows': summary(fs), 'raw': fs['cs'][0]['raw'], 'focus': [c['cls'] + ':' + c['text'] for c in fs['cs'] if c['focus']],
                          'windows': [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1]}
    return fs

# ---------------------------------------------------------------- menus
def ocr_word(g, regions, word, tries=3):
    """The centre (x, y, psm) of the OCR word `word` inside one of `regions` ((x, y, w, h), or a list of them, tried in order) of a fresh screenshot: for each region psm 11, 7 and 6 on a 400% grey crop;
    None when no pass sees it. A found word is only ever clicked by the caller after its own verification of the effect."""
    if isinstance(regions[0], int): regions = [regions]
    for region in regions:
        for psm in (11, 7, 6):
            full = os.path.join(lib.TMP, 'ic2_lead_screen.png'); crop = os.path.join(lib.TMP, 'ic2_lead_crop.png')
            _orig_sh('import', '-window', 'root', full)
            x, y, w, h = region
            subprocess.run(['convert', full, '-crop', '%dx%d+%d+%d' % (w, h, x, y), '+repage', '-resize', '400%', '-colorspace', 'Gray', crop], check=True)
            out = subprocess.run(['tesseract', crop, 'stdout', '--psm', str(psm), 'tsv'], capture_output=True, text=True).stdout
            for l in out.splitlines()[1:]:
                f = l.split('\t')
                if len(f) == 12 and f[11].strip().lower() == word: return (x + (int(f[6]) + int(f[8]) // 2) // 4, y + (int(f[7]) + int(f[9]) // 2) // 4, psm)
    return None

def menu_new(g, tries=3):
    """File > New: 'File' is found by OCR in the menu bar and clicked; 'New' is found by OCR in the dropdown below it and clicked; the form window (X id) must appear.
    Every attempt re-opens the menu from a reset state; at most `tries` attempts; DriverError (nothing else clicked) when a word is not seen or the form does not appear.
    With a game running the 'Are you sure you want to start a new game ?' Confirm box comes first: the caller handles it (confirm_new)."""
    for attempt in range(tries):
        CTX['why'] = 'reset menus (Escape, Escape, a click on the bare root window)'; g.reset_ui()
        CTX['why'] = 'menu bar word File (OCR)'
        f = ocr_word(g, (0, 26, 650, 24), 'file')
        if not f: continue
        g.click(f[0], f[1], pause=1.0)
        CTX['why'] = 'dropdown word New (OCR)'
        n = ocr_word(g, [(0, 47, 100, 20), (0, 44, 120, 24), (0, 46, 78, 90)], 'new')
        if not n: continue
        g.click(n[0], n[1], pause=2.0)
        t0 = time.time()
        while time.time() - t0 < 6:
            if form_wid(g) or g.find_windows('^Confirm$'): note_verified(step='File > New', how='form or Confirm window appeared', attempts=attempt + 1); return form_wid(g)
            time.sleep(0.4)
    raise _drv.DriverError('File > New: no form and no Confirm after %d attempts' % tries)

def confirm_new(g, answer):
    """Answer the 'Are you sure you want to start a new game ?' Confirm box through its own button (tracked by X id, bounded)."""
    ws = g.find_windows('^Confirm$')
    if not ws: raise _drv.DriverError('no Confirm box')
    text = g.read_popup(ws[0])
    answer_confirm(g, 'Confirm', answer)
    return text

def open_form(g, tag, rec, answer='Yes'):
    """File > New until the leaders form is up (answering the Confirm box with `answer` when a game is running); returns the form's X id."""
    wid = menu_new(g)
    if not wid and g.find_windows('^Confirm$'):
        rec['confirm_text'] = confirm_new(g, answer)
        if answer != 'Yes': return None
        t0 = time.time()
        while time.time() - t0 < 30 and not form_wid(g): time.sleep(0.5)
        wid = form_wid(g)
    if not wid: raise _drv.DriverError('the leaders form did not open')
    rec['form_wid'] = wid; time.sleep(1.0)
    return wid

# ---------------------------------------------------------------- form actions, each verified
def settle_state(g, cond, timeout=3.0):
    t0 = time.time(); fs = None
    while time.time() - t0 < timeout:
        fs = form_state(g)
        if cond(fs): return fs, True
        time.sleep(0.3)
    return fs, False

def others_unchanged(a, b, n):
    return all(summary(a)[i] == summary(b)[i] for i in range(16) if i != n)

def set_tick(g, n, want, tries=3):
    """Click nation n's human tick box (the checkbox rectangle read from the form) until the box shows the wanted state AND its edit shows the HumanOrComputer state (edit enabled iff
    ticked); the other 15 rows must not change; at most `tries` clicks; DriverError otherwise (the click did not register, or did something else)."""
    before = form_state(g); row = before['rows'][n]
    if bool(row['cb']['check']) == want: raise _drv.DriverError('%s: the tick already is %s: the click would prove nothing' % (row['nation'], want))
    for k in range(tries):
        c = form_state(g)['rows'][n]['cb']
        g.click_control(c, pause=0.8)
        fs, ok = settle_state(g, lambda f: bool(f['rows'][n]['cb']['check']) == want)
        if ok:
            r = fs['rows'][n]
            note_verified(step='tick %s %s' % (row['nation'], 'on' if want else 'off'), how='checkbox state read after the click (BM_GETCHECK) and edit state', attempts=k + 1,
                          before=summary(before)[n], after=summary(fs)[n], others_unchanged=others_unchanged(before, fs, n))
            if not others_unchanged(before, fs, n): raise _drv.DriverError('a click on the %s tick changed another row' % row['nation'])
            return fs
    raise _drv.DriverError('%s: the tick did not change after %d clicks' % (row['nation'], tries))

def edit_text(g, n, text, tries=3, expect=None):
    """Put `text` into nation n's name box: click the edit (rectangle from the form), prove the focus is on it, select all (End, shift+Home) and delete, type `text`; the box's text (WM_GETTEXT) must equal
    `expect` (default: text cut to 25 characters, the box's own limit); at most `tries` rounds; DriverError otherwise. The other rows must not change."""
    before = form_state(g); row = before['rows'][n]
    if not row['ed']['enabled']: raise _drv.DriverError('%s: the name box is greyed (disabled): not edited' % row['nation'])
    want = text[:25] if expect is None else expect
    for k in range(tries):
        c = form_state(g)['rows'][n]['ed']
        g.click_control(c, pause=0.5)
        fs, ok = settle_state(g, lambda f: f['rows'][n]['ed']['focus'] == 1, 2.0)
        if not ok: continue
        CTX['why'] = 'select all and delete in the %s name box' % row['nation']
        g.key('End'); g.key('shift+Home'); g.key('BackSpace')
        if text:
            CTX['why'] = 'type the %s name' % row['nation']; g.type(text); time.sleep(0.6)
        fs = form_state(g)
        if fs['rows'][n]['ed']['text'] == want:
            note_verified(step='name %s' % row['nation'], how='edit text read (WM_GETTEXT) after typing', attempts=k + 1, typed=text, read=fs['rows'][n]['ed']['text'], limit=fs['rows'][n]['ed']['limit'],
                          others_unchanged=others_unchanged(before, fs, n))
            return fs
    raise _drv.DriverError('%s: the name box did not read %r after %d rounds (read %r)' % (row['nation'], want, tries, form_state(g)['rows'][n]['ed']['text']))

def try_edit_disabled(g, n, text):
    """The greyed name box of a computer nation: click it and type; the state must NOT change (the play proves the box refuses the edit). Returns (before, after) summaries."""
    before = form_state(g); row = before['rows'][n]
    if row['ed']['enabled']: raise _drv.DriverError('%s: the name box is enabled' % row['nation'])
    g.click_control(row['ed'], pause=0.5)
    CTX['why'] = 'type into the greyed %s name box' % row['nation']; g.type(text); time.sleep(0.6)
    after = form_state(g)
    same = summary(before) == summary(after)
    note_verified(step='greyed name box %s refuses typing' % row['nation'], how='all 16 rows read before and after', typed=text, unchanged=same, focus_after=[c['cls'] for c in after['cs'] if c['focus']])
    if not same: raise _drv.DriverError('the greyed name box changed: %s' % (summary(after)[n],))
    return summary(before)[n], summary(after)[n]

def press_button(g, text, tries=3):
    """Click the form's button `text` (OK or Cancel; rectangle from the form) until the form window (tracked by its X id) is gone; at most `tries` clicks; DriverError otherwise."""
    wid = form_wid(g)
    if not wid: raise _drv.DriverError('no form')
    for k in range(tries):
        eog.spend(wid, 'leaders form', tries)
        b = form_state(g)['buttons'].get(text)
        if b is None: raise _drv.DriverError('no %s button in the form: nothing clicked' % text)
        g.click_control(b, pause=1.0)
        if eog.gone(g, wid, timeout=5):
            note_verified(step='press %s' % text, how='form window (X id %d) gone' % wid, attempts=k + 1); return k + 1
    raise _drv.DriverError('the form did not close after %d clicks on %s' % (tries, text))

def focus_checkbox_by_tab(g, n, max_tabs=24):
    """Send Tab (a key) until the focus is on nation n's tick box (compared by its rectangle from the form), at most `max_tabs` presses; DriverError otherwise. Returns the number of presses."""
    for i in range(max_tabs + 1):
        fs = form_state(g); cb = fs['rows'][n]['cb']
        if cb['focus'] == 1: return i
        if i == max_tabs: break
        CTX['why'] = 'Tab towards the %s tick box' % fs['rows'][n]['nation']; g.key('Tab'); time.sleep(0.3)
    raise _drv.DriverError('the focus did not reach the %s tick box after %d Tab presses' % (NATIONS[n], max_tabs))

def key_toggle(g, n, tries=2):
    """With the focus on nation n's tick box press the space bar (a key) and verify the box changed state; returns (before, after) summaries of the row"""
    before = form_state(g)
    for k in range(tries):
        CTX['why'] = 'space on the %s tick box' % NATIONS[n]; g.key('space'); time.sleep(0.6)
        after = form_state(g)
        if after['rows'][n]['cb']['check'] != before['rows'][n]['cb']['check']:
            note_verified(step='space on tick %s' % NATIONS[n], how='checkbox state read after the key', attempts=k + 1, before=summary(before)[n], after=summary(after)[n], others_unchanged=others_unchanged(before, after, n))
            return summary(before)[n], summary(after)[n]
    raise _drv.DriverError('the space bar did not change the %s tick box' % NATIONS[n])

def press_key_close(g, key, tries=2):
    """Close the form with a key (Escape = the Cancel button, Return = the default OK button, as the DFM declares): the key is sent to the form, its X id must be gone; at most `tries` sends"""
    wid = form_wid(g)
    if not wid: raise _drv.DriverError('no form')
    for k in range(tries):
        eog.spend(wid, 'leaders form', tries)
        CTX['why'] = 'key %s to close the form' % key; g.key(key)
        if eog.gone(g, wid, timeout=5):
            note_verified(step='key %s' % key, how='form window (X id %d) gone' % wid, attempts=k + 1); return k + 1
    raise _drv.DriverError('the form did not close after %d sends of %s' % (tries, key))

def tab_walk(g, n):
    """Press Tab n times (a key, no click) and record which control has the focus after each press (the form's tab order as the running form has it)"""
    seq = []
    for i in range(n):
        CTX['why'] = 'Tab %d' % (i + 1); g.key('Tab'); time.sleep(0.3)
        cs = read_controls(g)
        f = [c for c in cs if c['focus']]
        seq.append([(c['cls'], c['text'], c['y']) for c in f])
    return seq

# ---------------------------------------------------------------- game state after the form
def cstr(b): return b.split(b'\0')[0].decode('latin1')

def game_state(g):
    """Everything read from game memory (read only): the 16 nation records' name, leader, human flag and the words the form touches, the turn order, the current nation, the calendar, the window titles"""
    nat = []
    for n in range(16):
        r = g.nation_rec(n)
        nat.append({'n': n, 'name': cstr(r[:11]), 'leader': cstr(r[0x0B:0x0B + 26]), 'leader_hex': r[0x0B:0x0B + 26].hex(), 'human': r[0x490], 'score_0x440': struct.unpack_from('<h', r, 0x440)[0],
                    'treasury_0x438': struct.unpack_from('<i', r, 0x438)[0], 'view_0x486': struct.unpack_from('<h', r, 0x486)[0], 'view_0x488': struct.unpack_from('<h', r, 0x488)[0], 'sha': hashlib.sha256(r).hexdigest()})
    return {'nations': nat, 'turn_order': list(struct.unpack('<16h', g.mem(TURN_ORDER, 32))), 'cur_nation': g.i16(_drv.CUR_NATION), 'seat_0x4a032c': g.i16(0x4A032C),
            'calendar': {'season': g.i16(_drv.SEASON), 'week': g.i16(_drv.WEEK), 'year_bc': g.i16(_drv.YEAR_BC)}, 'windows': [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1]}

def keep_binary(path, name):
    dst = new_path(SAVEDIR + name); shutil.copy(path, dst)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    return dst

def keep_memory(g, tag, step):
    """The 16 nation records as the game holds them (raw bytes, artifact, hashed): the evidence for a state that has no save"""
    p = new_path(SAVEDIR + '%s_%s_nations.bin' % (tag, step)); open(p, 'wb').write(b''.join(g.nation_rec(n) for n in range(16)))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    return p

def after_ok(g, tag, rec, humans, timeout=150):
    """After OK: with at least one human, wait for the first autosave line (the game's own save at the first human turn), clear the start-of-turn boxes through their OK controls (eog.close_boxes:
    a box without an OK control stops the run) and keep the autosave; with none, wait for the form to be gone and settle. Records the memory state and the screen."""
    if humans:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if (_drv.G / 'AUTOSAVE.LOG').exists() and (_drv.G / 'AUTOSAVE.LOG').read_text().strip(): break
            time.sleep(1)
        else: raise _drv.DriverError('no autosave line after OK with humans %s' % humans)
        time.sleep(3)
        rec['boxes_at_start'] = eog.close_boxes(g)
        line = (_drv.G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
        rec['autosave_log'] = (_drv.G / 'AUTOSAVE.LOG').read_text().splitlines()
        src = _drv.G / line.split()[1]
        rec['autosave'] = os.path.basename(keep_binary(src, '%s_%s' % (tag, src.name)))
        rec['autosave_sha'] = sha(SAVEDIR + rec['autosave'])
    else:
        time.sleep(3)
        rec['boxes_at_start'] = []
    rec['state'] = game_state(g)
    snap(g, '%s_after_ok_screen.png' % tag)
    rec['nations_bin'] = os.path.basename(keep_memory(g, tag, 'after_ok'))
    rec['nations_bin_sha'] = sha(SAVEDIR + rec['nations_bin'])

def jlog(name, obj):
    with open(DATA + name, 'a') as f: f.write(json.dumps(obj) + '\n')

def start_game(seed):
    """A fresh game process with SEED.TXT = seed (read at program start; New Game reseeds from it too), no autosave files left over."""
    g = Game3(); g.set_seed(seed)
    clear_autos()
    g.start()
    eog._ATTEMPTS.clear()
    return g

def new_rec(play, batch, seed, note):
    return {'play': play, 'batch': batch, 'seed': seed, 'note': note, 'forms': {}, 'time': time.strftime('%F %T')}

def finish(rec, g, batch):
    rec['clicks'] = [dict(c) for c in CLICKS]; rec['keys'] = [dict(k) for k in KEYS]; rec['verified'] = [dict(v) for v in VERIFIED]
    jlog('plays_%s.jsonl' % batch, rec)
    del CLICKS[:]; del KEYS[:]; del VERIFIED[:]
    g.kill()
