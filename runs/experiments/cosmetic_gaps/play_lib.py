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
CLICKS = []                                           # every click of the play: {x, y, why, pointer, target}
VERIFIED = []                                         # every verified transition: {step, how, attempts, clicks: [first, end), keys: [first, end), ...}
CTX = {'why': None, 'tag': None, 'target': None}
KEYS = []                                             # every key / text sent (xdotool), with its reason
RUNNER = 3                                            # the runner version recorded in every play: 2 = pointer-verified clicks, verified resets and menus, immediate post-tick state; 3 = also the full 16-row state and the helper's raw output before and after every form step, and a memory dump (nation records + turn order, current nation, calendar words) for every state read

def note_verified(**kw): VERIFIED.append(kw)
def step_begin(): return (len(CLICKS), len(KEYS))
def note_step(b, **kw):
    """Record a verified transition together with the clicks and keys it used (index ranges into the play's CLICKS and KEYS): every click and key of a play belongs to exactly one step."""
    VERIFIED.append(dict(kw, clicks=[b[0], len(CLICKS)], keys=[b[1], len(KEYS)]))

ROOT_ID = [None]
def root_window_id():
    """The X id of the root window (xwininfo -root): what the pointer reports as the window under it when it is over bare screen."""
    if ROOT_ID[0] is None:
        m = re.search(r'Window id: (\d+)', _drv.sh('xwininfo', '-root', '-int'))
        if not m: raise _drv.DriverError('the root window id could not be read')
        ROOT_ID[0] = int(m.group(1))
    return ROOT_ID[0]

def pointer_at(x, y):
    def __helper_unused__(): pass
    """Move the pointer to (x, y) and read it back from the X server (xdotool getmouselocation): {x, y, window}, window = the X id of the top-level window under the pointer (the root id over bare screen)."""
    _drv.sh('xdotool', 'mousemove', str(x), str(y)); time.sleep(0.2)
    d = dict(p.split('=') for p in _drv.sh('xdotool', 'getmouselocation', '--shell').split() if '=' in p)
    return {'x': int(d['X']), 'y': int(d['Y']), 'window': int(d['WINDOW'])}

REQUIRED_FIELDS = {
    'tooltip': ('x', 'y'),
    'win_state': ('x', 'y', 'w', 'h', 'line'),
    'win_controls': ('x', 'y', 'w', 'h', 'line'),
    'ocr': ('word', 'region', 'x', 'y'),
    'driver tile targeting': ('tile',),
    'xdotool getmouselocation': ('root', 'pointer'),
    'panel + form resource': ('button', 'panel_line', 'rect', 'hint'),
}

def check_guard_ok(x, y, p, why, target, target_multi=1):
    """The single click guard used by both the production click (Game3.click) and the tests. Returns
    (ok, problem_text). Every check the production path enforces is also enforced here - removing any of
    them from one path will break the other."""
    if p is None or (p.get('x'), p.get('y')) != (x, y):
        return False, 'pointer not at (%s,%s)' % (p, (x, y))
    if not why:
        return False, 'no reason'
    if target is None and target_multi <= 1:
        return False, 'no target proof'
    if target is not None:
        src_ = target.get('src')
        if src_ not in REQUIRED_FIELDS:
            return False, 'unknown target src %r' % src_
        for k in REQUIRED_FIELDS[src_]:
            if k not in target: return False, '%s target missing %r' % (src_, k)
        if src_ in ('win_state', 'win_controls'):
            if not (target['x'] <= x <= target['x'] + target['w'] and target['y'] <= y <= target['y'] + target['h']):
                return False, 'click outside control rectangle'
        elif src_ == 'tooltip':
            if abs(target['x'] - x) > 3: return False, 'click not at tooltip x'
        elif src_ == 'panel + form resource':
            rx, ry, rw, rh = target['rect']
            if not (rx <= x < rx + rw and ry <= y < ry + rh):
                return False, 'click outside speed-button rectangle'
    return True, ''

class Game3(MyGame):
    """MyGame whose every click is recorded with its reason, the pointer position read back from the X server before the click (it must be where the click goes) and the target it was aimed at
    (the control's verbatim line as a fresh win_state / win_controls read gave it, or the OCR word); every key and text is recorded with its reason. The pointer/why/target guard IS click_guard_ok - both the production click and the
    test_runner share the predicate (review R6: removing any single check from the production path now breaks
    the tests)."""
    def click(self, x, y, pause=0.4):
        p = pointer_at(x, y)
        ok, why = check_guard_ok(x, y, p, CTX.get('why'), CTX.get('target'), CTX.get('target_multi', 1))
        if not ok:
            raise _drv.DriverError('click guard rejected click at %d,%d: %s: nothing clicked' % (x, y, why))
        CLICKS.append({'x': x, 'y': y, 'why': CTX.get('why'), 'pointer': p, 'target': CTX.get('target')})
        if CTX.get('target_multi', 1) > 1:
            CTX['target_multi'] -= 1          # a helper whose driver retries (select_army clicks up to 3x) keeps proving the same target
        else:
            CTX['target'] = None; CTX['why'] = None; CTX.pop('target_multi', None)
        return MyGame.click(self, x, y, pause)
    def fresh_target(self, c):
        """Prove, by a fresh read of the running game, that control c (cls, text, x, y, w, h) is where the caller says: the form's controls by win_state, a message box's by win_controls. Returns the record of the target."""
        same = lambda d: all(d[k] == c[k] for k in ('cls', 'text', 'x', 'y', 'w', 'h'))
        if form_wid(self):
            hit = [d for d in read_controls(self) if same(d)]
            if len(hit) == 1: return {'src': 'win_state', 'window': TITLE, 'line': hit[0]['line'], 'cls': c['cls'], 'x': c['x'], 'y': c['y'], 'w': c['w'], 'h': c['h']}
        else:
            for w in self.popups():
                hit = [d for d in self.controls(w[1]) if same(d)]
                if len(hit) == 1: return {'src': 'win_controls', 'window': w[1], 'line': '\t'.join(str(hit[0][k]) for k in ('cls', 'text', 'x', 'y', 'w', 'h')), 'cls': c['cls'], 'x': c['x'], 'y': c['y'], 'w': c['w'], 'h': c['h']}
        raise _drv.DriverError('control %s %r at %d,%d %dx%d is not in a fresh read of the game: nothing clicked' % (c['cls'], c.get('text'), c['x'], c['y'], c['w'], c['h']))
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        tgt = self.fresh_target(c)
        CTX['why'] = 'control %s %r at %d,%d %dx%d' % (c['cls'], c.get('text', ''), c['x'], c['y'], c['w'], c['h']); CTX['target'] = tgt
        return MyGame.click_control(self, c, fx, fy, pause)
    def key(self, *keys):
        KEYS.append({'keys': list(keys), 'why': CTX.get('why')}); return MyGame.key(self, *keys)
    def type(self, text):
        KEYS.append({'type': text, 'why': CTX.get('why')}); return MyGame.type(self, text)

# ---------------------------------------------------------------- the form's state, read from the game
STATE_EXE = lambda: _drv.WORK / 'win_state.exe'

def read_controls(g, title=TITLE):
    """win_state.exe on the visible window `title`: [{cls, text, x, y, w, h, enabled, visible, check, limit, sel0, sel1, focus, style, line}] (`line` = the helper's verbatim output line of that control; raw text kept in the first element's 'raw')"""
    out = subprocess.run([_drv.WINE, str(STATE_EXE()), title], env=_drv.ENV, capture_output=True).stdout.decode('latin1')   # the game's ANSI text (Windows-1252 / Latin-1 bytes), never utf-8
    cs = []
    for line in out.splitlines():
        p = line.split('\t')
        if len(p) == 14:
            cs.append({'cls': p[0], 'text': p[1], 'x': int(p[2]), 'y': int(p[3]), 'w': int(p[4]), 'h': int(p[5]), 'enabled': int(p[6]), 'visible': int(p[7]), 'check': int(p[8]), 'limit': int(p[9]),
                       'sel0': int(p[10]), 'sel1': int(p[11]), 'focus': int(p[12]), 'style': p[13], 'line': line})
    if not cs: raise _drv.DriverError('no controls read for window %r' % title)
    cs[0]['raw'] = out
    return cs

def form_state(g):
    """The 16 rows (a panel with its checkbox and edit, matched by containment of the control in the panel's rectangle) and the buttons; `complete` is False when a row is missing (callers that act use need_form)."""
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
    return {'rows': rows, 'buttons': {c['text']: c for c in cs if c['cls'] == 'TButton'}, 'cs': cs, 'complete': sorted(rows) == list(range(16))}

def need_form(g):
    """form_state, but a form that does not list all 16 rows stops the run (nothing is acted on)."""
    fs = form_state(g)
    if not fs.get('complete'): raise _drv.DriverError('the form lists %d of 16 rows: nothing acted on' % len(fs['rows']))
    return fs

def summary(fs):
    """Compact per-row record: [nation, check, checkbox enabled, edit text, edit enabled, edit limit]"""
    return [[fs['rows'][i]['nation'], fs['rows'][i]['cb']['check'], fs['rows'][i]['cb']['enabled'], fs['rows'][i]['ed']['text'], fs['rows'][i]['ed']['enabled'], fs['rows'][i]['ed']['limit']] for i in sorted(fs['rows'])]

def row_post(fs, n):
    """What the form shows of row n right now: the tick, the name box's state (enabled, focus, selection, text) and where the focus is."""
    r = fs['rows'][n]; e = r['ed']
    return {'check': r['cb']['check'], 'cb_enabled': r['cb']['enabled'], 'cb_focus': r['cb']['focus'], 'edit_enabled': e['enabled'], 'edit_focus': e['focus'], 'sel0': e['sel0'], 'sel1': e['sel1'], 'text': e['text'], 'textlen': len(e['text']),
            'focus': [c['cls'] + ':' + c['text'] for c in fs['cs'] if c['focus']]}

def form_wid(g):
    w = g.find_windows('^%s$' % re.escape(TITLE))
    return w[0][0] if w else None

def record_form(g, tag, step, rec):
    """Keep the form's state as read now (raw win_state output, tracked) and a screenshot of the whole screen (artifact, hashed, its name and hash recorded with the state it was taken with)."""
    fs = need_form(g)
    p = snap(g, '%s_%s_form.png' % (tag, step))
    ng = rec.get('new_games', [])
    rec['forms'][step] = {'rows': summary(fs), 'raw': fs['cs'][0]['raw'], 'focus': [c['cls'] + ':' + c['text'] for c in fs['cs'] if c['focus']], 'png': os.path.basename(p), 'png_sha': sha(p),
                          'new_game': len(ng) - 1, 'seed': ng[-1]['seed'] if ng else None, 'windows': [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1]}
    return fs

def snap_rec(g, rec, key, name):
    """A screenshot of the whole screen, kept under the next free name and recorded (name and hash) in the play's `screens`."""
    p = snap(g, name); rec.setdefault('screens', {})[key] = {'png': os.path.basename(p), 'png_sha': sha(p)}
    return p

# ---------------------------------------------------------------- reset and menus: located, verified, bounded
def locate_bare_root(g):
    """A point of the screen proven bare: candidates are derived from the screen's size (corners and edge midpoints of the bottom and right strips), skipped when a visible window's rectangle covers them,
    and accepted only when, with the pointer moved there, the X server reports the ROOT window as the window under the pointer. Returns (x, y, pointer record, windows); DriverError when no candidate is bare."""
    sw, sh_ = g.screen_size()
    wins = [w for w in g.find_windows('.') if w[4] > 1 and w[5] > 1]
    covered = lambda x, y: any(w[2] <= x < w[2] + w[4] and w[3] <= y < w[3] + w[5] for w in wins)
    cands = [(sw - 8, sh_ - 8), (sw // 2, sh_ - 8), (8, sh_ - 8), (sw - 8, sh_ // 2), (sw - 8, sh_ // 4), (8, sh_ // 2)]
    for x, y in cands:
        if covered(x, y): continue
        p = pointer_at(x, y)
        if (p['x'], p['y']) == (x, y) and p['window'] == root_window_id(): return x, y, p, [(w[0], w[1], w[2], w[3], w[4], w[5]) for w in wins]
    raise _drv.DriverError('no point of the screen is bare root window (%d windows): nothing clicked' % len(wins))

def verified_reset(g):
    """Close any open menu without a click at a fixed point: Escape twice (keys), then a click on a point located now and verified bare (locate_bare_root: no window covers it and the X server reports the root window under
    the pointer there). The step records the point, the pointer read back, the root id and the windows. Replaces the driver's reset_ui, whose click goes to a fixed point (NEUTRAL) when no window covers it."""
    b = step_begin()
    CTX['why'] = 'reset menus: Escape, Escape'; g.key('Escape'); g.key('Escape')
    x, y, p, wins = locate_bare_root(g)
    CTX['why'] = 'bare root window: point located now, X server reports the root window under the pointer'; CTX['target'] = {'src': 'xdotool getmouselocation', 'root': root_window_id(), 'pointer': p}
    g.click(x, y, pause=0.2)
    note_step(b, step='reset', ok=True, how='click on a located point whose pointer window is the root window', point=[x, y], pointer=p, root=root_window_id(), windows=wins, attempts=1)

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

BAR = (0, 26, 650, 24)                                 # the menu bar strip
NEW_REGIONS = [(0, 47, 100, 20), (0, 44, 120, 24), (0, 46, 78, 90)]       # where the File dropdown's word New can be
DROP = (0, 40, 260, 140)                               # the strip under the menu bar in which a dropdown opens

def menu_open(g, word, expect, regions, tries=3):
    """Open the menu bar word `word` and PROVE it opened: reset (verified_reset), the bar word found by OCR and clicked once, then the dropdown's word `expect` must be found by OCR in `regions` (each transition a recorded
    step, `ok` False for an attempt that did not show it: an activation-only click, a missing word); at most `tries` attempts; DriverError when the menu never shows. Returns (OCR hit of `expect`, attempt number)."""
    for attempt in range(tries):
        verified_reset(g)
        b = step_begin(); CTX['why'] = 'menu bar word %s (OCR)' % word
        f = ocr_word(g, BAR, word)
        if not f:
            note_step(b, step='menu open %s' % word, ok=False, how='the bar word %s was not seen: nothing clicked' % word, attempts=attempt + 1); continue
        CTX['target'] = {'src': 'ocr', 'word': word, 'region': list(BAR), 'x': f[0], 'y': f[1], 'psm': f[2]}
        g.click(f[0], f[1], pause=1.0)
        hit = ocr_word(g, regions, expect)
        note_step(b, step='menu open %s' % word, ok=hit is not None, how='the dropdown word %s must be seen by OCR after the click' % expect, expect=expect, hit=list(hit) if hit else None, attempts=attempt + 1)
        if hit: return hit, attempt + 1
    raise _drv.DriverError('menu %s did not open (its word %s not seen) after %d attempts' % (word, expect, tries))

def menu_close(g, word, expect, regions, tries=2):
    """Close an open menu with Escape (a key, no click) and prove the dropdown's word `expect` is gone; at most `tries` sends; DriverError otherwise."""
    for k in range(tries):
        b = step_begin(); CTX['why'] = 'Escape closes the %s menu' % word; g.key('Escape'); g.key('Escape'); time.sleep(0.4)
        gone_ = ocr_word(g, regions, expect) is None
        note_step(b, step='menu close %s' % word, ok=gone_, how='the dropdown word %s must be gone' % expect, attempts=k + 1)
        if gone_: return k + 1
    raise _drv.DriverError('the %s menu did not close after %d tries' % (word, tries))

def menu_new(g, tries=3):
    """File > New with both transitions verified: menu_open('file') proves the dropdown opened (its word New seen by OCR), then New is clicked at that OCR hit and the form window (X id) or the Confirm box must appear
    within 6 s (recorded step, `ok` False when not). Every attempt starts from verified_reset; at most `tries` attempts; DriverError (nothing else clicked) when a transition does not show.
    With a game running the 'Are you sure you want to start a new game ?' Confirm box comes first: the caller handles it (confirm_new)."""
    for attempt in range(tries):
        try: n, _ = menu_open(g, 'file', 'new', NEW_REGIONS, tries=1)
        except _drv.DriverError: continue
        b = step_begin(); CTX['why'] = 'dropdown word New (OCR)'; CTX['target'] = {'src': 'ocr', 'word': 'new', 'region': NEW_REGIONS, 'x': n[0], 'y': n[1], 'psm': n[2]}
        g.click(n[0], n[1], pause=2.0)
        t0 = time.time()
        while time.time() - t0 < 6:
            if form_wid(g) or g.find_windows('^Confirm$'):
                note_step(b, step='menu item New', ok=True, how='form or Confirm window appeared', attempts=attempt + 1); return form_wid(g)
            time.sleep(0.4)
        note_step(b, step='menu item New', ok=False, how='neither the form nor a Confirm box appeared in 6 s', attempts=attempt + 1)
    raise _drv.DriverError('File > New: no form and no Confirm after %d attempts' % tries)

def confirm_new(g, answer):
    """Answer the 'Are you sure you want to start a new game ?' Confirm box through its own button (tracked by X id, bounded)."""
    ws = g.find_windows('^Confirm$')
    if not ws: raise _drv.DriverError('no Confirm box')
    text = g.read_popup(ws[0]); b = step_begin()
    answer_confirm(g, 'Confirm', answer)
    note_step(b, step='confirm %s' % answer, ok=True, how='Confirm window (X id %d) gone' % ws[0][0], attempts=sum(1 for c in CLICKS[b[0]:]))
    return text

def read_seed():
    """The SEED.TXT the game reads at program start and at every New Game (the harness build)."""
    return int((_drv.G / 'SEED.TXT').read_text().strip())

def open_form(g, tag, rec, answer='Yes'):
    """File > New until the leaders form is up (answering the Confirm box with `answer` when a game is running); returns the form's X id. Records the seed file's content at each New Game (rec['new_games'])."""
    seed = read_seed()
    wid = menu_new(g)
    if not wid and g.find_windows('^Confirm$'):
        rec['confirm_text'] = confirm_new(g, answer)
        if answer != 'Yes': return None
        t0 = time.time()
        while time.time() - t0 < 30 and not form_wid(g): time.sleep(0.5)
        wid = form_wid(g)
    if not wid: raise _drv.DriverError('the leaders form did not open')
    rec.setdefault('new_games', []).append({'seed': seed, 'form_wid': wid, 'index': len(rec.get('new_games', []))})
    rec['form_wid'] = wid; time.sleep(1.0)
    return wid

# ---------------------------------------------------------------- form actions, each verified
def settle_state(g, cond, timeout=3.0):
    t0 = time.time(); fs = None
    while time.time() - t0 < timeout:
        fs = form_state(g)
        if fs.get('complete') and cond(fs): return fs, True
        time.sleep(0.3)
    return fs, False

def others_unchanged(a, b, n):
    return all(summary(a)[i] == summary(b)[i] for i in range(16) if i != n)

def drawn_leader(g, n):
    """The nation's stored leader as the game holds it in memory (record +0x0B, 26 bytes): what an untick must put back."""
    return cstr(g.nation_rec(n)[0x0B:0x0B + 26])

def set_tick(g, n, want, tries=3):
    """Click nation n's human tick box (the rectangle read from the form, re-read before each click) with the MOUSE until the box shows the wanted state AND the row shows what HumanOrComputer must do (read from the running form):
    ticking: the name box enabled, FOCUSED, its WHOLE text SELECTED (selection 0 to the text's length); unticking: the name box greyed, without focus, showing the nation's stored leader (read from game memory); the other 15 rows
    unchanged. Preflight: the form lists 16 rows, the tick box is enabled, and its state is not already the wanted one. A click that changes another row raises at once. At most `tries` clicks; DriverError otherwise.
    The state right after the click (post) and a screenshot of the screen taken right then are recorded with the step."""
    b = step_begin(); before = need_form(g); row = before['rows'][n]
    if not row['cb']['enabled']: raise _drv.DriverError('%s: the tick box is disabled: nothing clicked' % row['nation'])
    if bool(row['cb']['check']) == want: raise _drv.DriverError('%s: the tick already is %s: the click would prove nothing' % (row['nation'], want))
    stored = drawn_leader(g, n)
    def woke(f):
        r = f['rows'][n]
        if want: return bool(r['cb']['check']) and r['ed']['enabled'] == 1 and r['ed']['focus'] == 1 and r['ed']['sel0'] == 0 and r['ed']['sel1'] == len(r['ed']['text'])
        return (not r['cb']['check']) and r['ed']['enabled'] == 0 and r['ed']['focus'] == 0 and r['ed']['text'] == stored
    for k in range(tries):
        c = need_form(g)['rows'][n]['cb']
        CTX['why'] = 'tick box of %s' % row['nation']
        g.click_control(c, pause=0.8)
        fs, ok = settle_state(g, woke)
        if fs is not None and fs.get('complete') and not others_unchanged(before, fs, n):
            raise _drv.DriverError('a click on the %s tick changed another row' % row['nation'])
        if ok:
            png = snap(g, '%s_tick_%s_%s_post.png' % (CTX.get('tag') or 'LF', row['nation'], 'on' if want else 'off'))
            note_step(b, step='tick %s %s' % (row['nation'], 'on' if want else 'off'), ok=True, how='check state (BM_GETCHECK), name box enabled / focus / selection / restored text read right after the click', attempts=k + 1,
                      before=summary(before)[n], after=summary(fs)[n], post=row_post(fs, n), stored=stored, post_png=os.path.basename(png), post_png_sha=sha(png), others_unchanged=others_unchanged(before, fs, n),
                      rows_before=summary(before), rows_after=summary(fs), raw_before=before['cs'][0]['raw'], raw_after=fs['cs'][0]['raw'])
            return fs
    raise _drv.DriverError('%s: the tick did not reach the wanted state (%s, name box woke / greyed with %r) after %d clicks' % (row['nation'], want, stored, tries))

def edit_text(g, n, text, tries=3, expect=None):
    """Put `text` into nation n's name box: preflight (16 rows, the name box enabled), click the edit (rectangle from the form) and prove the focus is on it, press End and shift+Home and prove the whole text is selected
    (selection 0 to the text's length), press BackSpace and prove the box is empty, type `text`; the box's text (WM_GETTEXT) must equal `expect` (default: text cut to 25 characters, the box's own limit). After every stage the
    other rows must be unchanged (raises at once). A stage that does not show retries the whole round (at most `tries` rounds); DriverError otherwise."""
    b = step_begin(); before = need_form(g); row = before['rows'][n]
    if not row['ed']['enabled']: raise _drv.DriverError('%s: the name box is greyed (disabled): not edited' % row['nation'])
    want = text[:25] if expect is None else expect
    def guard(f):
        if not others_unchanged(before, f, n): raise _drv.DriverError('editing the %s name box changed another row' % row['nation'])
    stages = {}
    for k in range(tries):
        c = need_form(g)['rows'][n]['ed']
        CTX['why'] = 'name box of %s' % row['nation']
        g.click_control(c, pause=0.5)
        fs, ok = settle_state(g, lambda f: f['rows'][n]['ed']['focus'] == 1, 2.0)
        if not ok: continue
        guard(fs); stages['focus'] = dict(row_post(fs, n), raw=fs['cs'][0]['raw']); length = len(fs['rows'][n]['ed']['text'])
        CTX['why'] = 'select all in the %s name box' % row['nation']
        g.key('End'); g.key('shift+Home'); time.sleep(0.3)
        fs = need_form(g); guard(fs); stages['selected'] = dict(row_post(fs, n), raw=fs['cs'][0]['raw'])
        if not (fs['rows'][n]['ed']['sel0'] == 0 and fs['rows'][n]['ed']['sel1'] == length and fs['rows'][n]['ed']['text'] == stages['focus']['text']): continue
        CTX['why'] = 'delete the selection in the %s name box' % row['nation']
        g.key('BackSpace'); time.sleep(0.3)
        fs = need_form(g); guard(fs); stages['deleted'] = dict(row_post(fs, n), raw=fs['cs'][0]['raw'])
        if fs['rows'][n]['ed']['text'] != '': continue
        if text:
            CTX['why'] = 'type the %s name' % row['nation']; g.type(text); time.sleep(0.6)
        fs = need_form(g); guard(fs)
        if fs['rows'][n]['ed']['text'] == want:
            note_step(b, step='name %s' % row['nation'], ok=True, how='focus, selection of the whole text, deletion and typing each read back (WM_GETTEXT, EM_GETSEL); other rows unchanged', attempts=k + 1, typed=text, read=fs['rows'][n]['ed']['text'],
                      limit=fs['rows'][n]['ed']['limit'], stages=stages, others_unchanged=others_unchanged(before, fs, n),
                      rows_before=summary(before), rows_after=summary(fs), raw_before=before['cs'][0]['raw'], raw_after=fs['cs'][0]['raw'])
            return fs
    raise _drv.DriverError('%s: the name box did not read %r after %d rounds (read %r)' % (row['nation'], want, tries, form_state(g)['rows'].get(n, {}).get('ed', {}).get('text')))

def try_edit_disabled(g, n, text):
    """The greyed name box of a computer nation: click it and type; the state must NOT change (the play proves the box refuses the edit). Returns (before, after) summaries."""
    b = step_begin(); before = need_form(g); row = before['rows'][n]
    if row['ed']['enabled']: raise _drv.DriverError('%s: the name box is enabled' % row['nation'])
    CTX['why'] = 'name box of %s (greyed)' % row['nation']
    g.click_control(row['ed'], pause=0.5)
    CTX['why'] = 'type into the greyed %s name box' % row['nation']; g.type(text); time.sleep(0.6)
    after = need_form(g)
    same = summary(before) == summary(after)
    note_step(b, step='greyed name box %s refuses typing' % row['nation'], ok=same, how='all 16 rows read before and after', typed=text, unchanged=same, attempts=1, focus_after=[c['cls'] for c in after['cs'] if c['focus']],
              before=summary(before)[n], after=summary(after)[n], rows_before=summary(before), rows_after=summary(after), raw_before=before['cs'][0]['raw'], raw_after=after['cs'][0]['raw'])
    if not same: raise _drv.DriverError('the greyed name box changed: %s' % (summary(after)[n],))
    return summary(before)[n], summary(after)[n]

def press_button(g, text, tries=3):
    """Click the form's button `text` (OK or Cancel; rectangle from the form, enabled) until the form window (tracked by its X id) is gone; at most `tries` clicks; DriverError otherwise."""
    wid = form_wid(g); b = step_begin()
    if not wid: raise _drv.DriverError('no form')
    for k in range(tries):
        eog.spend(wid, 'leaders form', tries)
        btn = need_form(g)['buttons'].get(text)
        if btn is None: raise _drv.DriverError('no %s button in the form: nothing clicked' % text)
        if not btn['enabled']: raise _drv.DriverError('the %s button is disabled: nothing clicked' % text)
        CTX['why'] = 'button %s' % text
        g.click_control(btn, pause=1.0)
        if eog.gone(g, wid, timeout=5):
            note_step(b, step='press %s' % text, ok=True, how='form window (X id %d) gone' % wid, attempts=k + 1); return k + 1
    raise _drv.DriverError('the form did not close after %d clicks on %s' % (tries, text))

def focus_checkbox_by_tab(g, n, max_tabs=24):
    """Send Tab (a key) until the focus is on nation n's tick box (compared by its rectangle from the form), at most `max_tabs` presses; DriverError otherwise. Returns the number of presses."""
    b = step_begin()
    for i in range(max_tabs + 1):
        fs = need_form(g); cb = fs['rows'][n]['cb']
        if cb['focus'] == 1:
            note_step(b, step='tab to %s tick box' % NATIONS[n], ok=True, how='focus read from the form after each Tab', attempts=i); return i
        if i == max_tabs: break
        CTX['why'] = 'Tab towards the %s tick box' % fs['rows'][n]['nation']; g.key('Tab'); time.sleep(0.3)
    raise _drv.DriverError('the focus did not reach the %s tick box after %d Tab presses' % (NATIONS[n], max_tabs))

def key_toggle(g, n, tries=2):
    """With the focus on nation n's tick box press the space bar (a key) and verify the box changed state; preflight: 16 rows, the tick box enabled and focused; a change of another row raises at once; the state of the
    name box after the key is recorded (post), not required. Returns (before, after) summaries of the row."""
    b = step_begin(); before = need_form(g); cb = before['rows'][n]['cb']
    if not cb['enabled'] or cb['focus'] != 1: raise _drv.DriverError('the %s tick box is not enabled and focused: no key sent' % NATIONS[n])
    for k in range(tries):
        CTX['why'] = 'space on the %s tick box' % NATIONS[n]; g.key('space'); time.sleep(0.6)
        after = need_form(g)
        if not others_unchanged(before, after, n): raise _drv.DriverError('the space bar changed another row than %s' % NATIONS[n])
        if after['rows'][n]['cb']['check'] != before['rows'][n]['cb']['check']:
            note_step(b, step='space on tick %s' % NATIONS[n], ok=True, how='checkbox state read after the key; other rows unchanged', attempts=k + 1, before=summary(before)[n], after=summary(after)[n], post=row_post(after, n), others_unchanged=True, rows_before=summary(before), rows_after=summary(after), raw_before=before['cs'][0]['raw'], raw_after=after['cs'][0]['raw'])
            return summary(before)[n], summary(after)[n]
    raise _drv.DriverError('the space bar did not change the %s tick box' % NATIONS[n])

def press_key_close(g, key, tries=2):
    """Close the form with a key (Escape = the Cancel button, Return = the default OK button, as the DFM declares): the key is sent to the form, its X id must be gone; at most `tries` sends"""
    wid = form_wid(g); b = step_begin()
    if not wid: raise _drv.DriverError('no form')
    for k in range(tries):
        eog.spend(wid, 'leaders form', tries)
        CTX['why'] = 'key %s to close the form' % key; g.key(key)
        if eog.gone(g, wid, timeout=5):
            note_step(b, step='key %s' % key, ok=True, how='form window (X id %d) gone' % wid, attempts=k + 1); return k + 1
    raise _drv.DriverError('the form did not close after %d sends of %s' % (tries, key))

def tab_walk(g, n):
    """Press Tab n times (a key, no click) and record which control has the focus after each press (the form's tab order as the running form has it)"""
    seq = []; b = step_begin()
    for i in range(n):
        CTX['why'] = 'Tab %d' % (i + 1); g.key('Tab'); time.sleep(0.3)
        cs = read_controls(g)
        f = [c for c in cs if c['focus']]
        seq.append([(c['cls'], c['text'], c['y']) for c in f])
    note_step(b, step='tab walk', ok=True, how='focus read after each of %d Tab presses' % n, attempts=n)
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

def keep_globals(g, tag, step):
    """The game words outside the nation records that the finding reads, as raw bytes (artifact, hashed): the turn order (DAT_0049efe8, 16 shorts), the current nation, the seat word 0x4A032C, season, week and year BC (little-endian shorts, in that order)"""
    p = new_path(SAVEDIR + '%s_%s_globals.bin' % (tag, step))
    open(p, 'wb').write(g.mem(TURN_ORDER, 32) + b''.join(g.mem(a, 2) for a in (_drv.CUR_NATION, 0x4A032C, _drv.SEASON, _drv.WEEK, _drv.YEAR_BC)))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    return p

def capture(g, tag, rec, key, step):
    """Read the game state now into rec[key] (JSON, as before) AND keep the raw bytes it comes from (the 16 nation records and the globals words) as hashed artifacts, recorded in rec['dumps'][key]: the audit decodes every nation field
    and every global from these bytes, never from the JSON."""
    rec[key] = game_state(g)
    n = keep_memory(g, tag, step); gl = keep_globals(g, tag, step)
    log = _drv.G / 'AUTOSAVE.LOG'
    rec.setdefault('autosave_seen', {})[key] = {'files': sorted(f.name for f in _drv.G.glob('AUTO*.SAV')), 'log': log.read_text() if log.exists() else None}      # what the game folder holds when the state is read: an absent autosave is observed, not assumed
    rec.setdefault('dumps', {})[key] = {'nations_bin': os.path.basename(n), 'nations_bin_sha': sha(n), 'globals_bin': os.path.basename(gl), 'globals_bin_sha': sha(gl)}
    return rec[key]

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
        b = step_begin(); rec['boxes_at_start'] = eog.close_boxes(g)
        note_step(b, step='close start boxes', ok=True, how='each box closed through its own OK control and gone (eog.close_boxes)', boxes=len(rec['boxes_at_start']), attempts=len(CLICKS) - b[0])
        line = (_drv.G / 'AUTOSAVE.LOG').read_text().splitlines()[-1]
        rec['autosave_log'] = (_drv.G / 'AUTOSAVE.LOG').read_text().splitlines()
        src = _drv.G / line.split()[1]
        rec['autosave'] = os.path.basename(keep_binary(src, '%s_%s' % (tag, src.name)))
        rec['autosave_sha'] = sha(SAVEDIR + rec['autosave'])
    else:
        time.sleep(8)                                       # no human: wait long enough for an autosave to show if the game wrote one
        rec['boxes_at_start'] = []
    capture(g, tag, rec, 'state', 'after_ok')
    snap_rec(g, rec, 'after_ok', '%s_after_ok_screen.png' % tag)

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
    return {'play': play, 'batch': batch, 'seed': seed, 'note': note, 'forms': {}, 'new_games': [], 'time': time.strftime('%F %T'), 'runner': RUNNER}

def finish(rec, g, batch):
    rec['clicks'] = [dict(c) for c in CLICKS]; rec['keys'] = [dict(k) for k in KEYS]; rec['verified'] = [dict(v) for v in VERIFIED]
    jlog('plays_%s.jsonl' % batch, rec)
    del CLICKS[:]; del KEYS[:]; del VERIFIED[:]
    g.kill()
