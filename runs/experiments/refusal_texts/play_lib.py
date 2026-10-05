"""Shared helpers of the refusal-text plays (CLAUDE.md rule 6: every output is a new versioned tracked file under runs/experiments/data/run-exp-refusal-texts/).
A play = STAGE (or take a fixture) -> load in a fresh game -> a CONTROL save (the state as the game holds it) -> issue ONE order -> the box(es) that appear are
captured (X window id, title, geometry, controls, screenshot, OCR) and closed with a tracked, bounded click -> an AFTER save, compared byte for byte with the control.
Every staged save is labelled staged (staging_log.tsv: which bytes, which operation). Import eog first (it sets the display and the private game folder)."""
import json, os, re, struct, time, shutil, hashlib, subprocess
import lib
from eog import *                                   # noqa: F401,F403
from pathlib import Path
from eog import _drv, _screen_words, _ids, _geo
from harness.driver import Game
from lib import _region_hash
import eog
from common import new_path, write_new
from state import sav as SAV
import stage as STAGE

ARMY_Y = _drv.ARMY_TOOLBAR_Y

def stage_edit(src, dst, ops, tag):
    """dst = src with `ops` applied (a new versioned file; byte ranges of every changed byte checked against the declared fields; logged in staging_log.tsv).
    ops: STAGE ops ('units', army, [(type, troops, quality[, label[, name]])]), ('supplies'|'money'|'moves'|'owner', army, v), ('city', c, {...}), ('relation', a, b, v),
    plus ('fleet', f, field, v) field in ships|supplies|money|moves|condition, ('nation', n, off, v) (a nation word) and ('nation32', n, off, v)."""
    src, dst = str(src), str(dst)
    b = bytearray(open(src, 'rb').read()); orig = bytes(b); allowed = []
    for op in ops:
        k = op[0]
        if k == 'units':
            a0 = STAGE._army(b, op[1]); allowed.append((a0 + 16, 640, 'army %d unit slots' % op[1])); STAGE.apply(b, [op])
        elif k in STAGE.ARMY_FIELDS:
            allowed.append((STAGE._army(b, op[1]) + STAGE.ARMY_FIELDS[k], 2, 'army %d %s' % (op[1], k))); STAGE.apply(b, [op])
        elif k == 'city':
            for f in op[2]: allowed.append((SAV.CITY_OFF + op[1] * SAV.CITY_LEN + STAGE.CITY_FIELDS[f], 2, 'city %d %s' % (op[1], f)))
            STAGE.apply(b, [op])
        elif k == 'relation':
            allowed.append((STAGE._nation(b, op[1]) + 0x26 + 2 * op[2], 2, 'relation %d-%d' % (op[1], op[2])))
            allowed.append((STAGE._nation(b, op[2]) + 0x26 + 2 * op[1], 2, 'relation %d-%d' % (op[2], op[1]))); STAGE.apply(b, [op])
        elif k == 'fleet':
            f0 = STAGE._offsets(b)['army0'] + STAGE._offsets(b)['na'] * SAV.ARMY_LEN + 2
            off = {'ships': 18, 'supplies': 14, 'money': 16, 'moves': 12, 'condition': 20}[op[2]]
            allowed.append((f0 + op[1] * SAV.FLEET_LEN + off, 2, 'fleet %d %s' % (op[1], op[2]))); struct.pack_into('<h', b, f0 + op[1] * SAV.FLEET_LEN + off, op[3])
        elif k == 'nation':
            allowed.append((STAGE._nation(b, op[1]) + op[2], 2, 'nation %d +0x%x' % (op[1], op[2]))); struct.pack_into('<h', b, STAGE._nation(b, op[1]) + op[2], op[3])
        elif k == 'nation32':
            allowed.append((STAGE._nation(b, op[1]) + op[2], 4, 'nation %d +0x%x (i32)' % (op[1], op[2]))); struct.pack_into('<i', b, STAGE._nation(b, op[1]) + op[2], op[3])
        else: raise ValueError('unknown op %r' % (op,))
    diff = [i for i in range(len(b)) if b[i] != orig[i]]
    for i in diff:
        if not any(o <= i < o + l for o, l, _ in allowed): raise ValueError('byte %d changed outside the declared fields' % i)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    dst = new_path(dst)
    with open(dst, 'xb') as f: f.write(bytes(b))
    with open(DATA + 'staging_log.tsv', 'a') as f:
        f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (time.strftime('%F %T'), tag, os.path.basename(src), sha(src), os.path.basename(dst), sha(dst),
                json.dumps([[a, b_, c] for a, b_, c in allowed]) + ' ops=' + json.dumps(ops)))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    log('stage', '%s: %s -> %s, %d bytes changed, ops %s' % (tag, os.path.basename(src), os.path.basename(dst), len(diff), ops))
    return dst

def as_fixture(src, dst):
    """An unedited save used as it is: copied to the inputs with a hash (nothing is staged)."""
    dst = new_path(str(dst)); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(str(src), dst)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    return dst

def boxes(g):
    """The small modal boxes now open: [(wid, title, x, y, w, h)]."""
    return [p for p in g.popups() if p[1] in BOX_TITLES and p[4] < 600 and p[5] < 300]

def wait_boxes(g, timeout=8, settle=1.5):
    """Wait for at least one box, then `settle` more seconds (a second box may follow); returns the list (maybe empty)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if boxes(g):
            time.sleep(settle); return boxes(g)
        time.sleep(0.3)
    return []

def verified_x(g, bar, tool):
    """The x of a toolbar button from a tooltip scan made NOW with this run's own game: the button's tooltip window must appear while the pointer is over x. A cached or recorded x is only
    a hint for where to look first (a narrow window, then the whole bar); it is never clicked unless a tooltip proved it. DriverError (nothing clicked) when the tooltip is not found."""
    labels, y, full, cache = {'army': (_drv.ARMY_TOOLBAR_LABELS, _drv.ARMY_TOOLBAR_Y, (336, 540), g.army_x), 'fleet': (_drv.FLEET_TOOLBAR_LABELS, _drv.ARMY_TOOLBAR_Y, (336, 540), g.fleet_x),
                              'main': (_drv.TOOLBAR_LABELS, _drv.TOOLBAR_Y, (4, 232), g.toolbar_x)}[bar]
    hint = (cache or {}).get(tool)
    windows = ([(max(full[0], hint - 15), min(full[1], hint + 16))] if hint else []) + [full]
    for lo, hi in windows:
        found = g._scan_bar(y, {tool: labels[tool]}, lo, hi, 0.5)
        if tool in found:
            log('toolbar', '%s button %s: tooltip %r seen, x=%d (hint %s)' % (bar, tool, labels[tool], found[tool], hint)); note_click(kind='toolbar', bar=bar, tool=tool, tooltip=labels[tool], x=found[tool]); return found[tool]
    raise _drv.DriverError('%s toolbar: the tooltip %r of %s was not seen: nothing clicked' % (bar, labels[tool], tool))

def army_button(g, i, tool):
    """Select army i (verified through the game's selection word, three attempts at most) and click the army-toolbar button `tool` at the x a tooltip proved."""
    ax, ay = g.army_pos(i); g.select_army(i, ax, ay)
    x = verified_x(g, 'army', tool)
    g.click(x, ARMY_Y, pause=1.5)

def fleet_button(g, i, tool):
    g.select_fleet(i)
    x = verified_x(g, 'fleet', tool)
    g.click(x, ARMY_Y, pause=1.5)

def main_tool(g, name, pause=1.5):
    """A button of the main toolbar (relations, build_fleet, recruit ...) at the x a tooltip proved"""
    g.reset_ui()
    x = verified_x(g, 'main', name)
    g.click(x, _drv.TOOLBAR_Y, pause=pause)

class Game2(MyGame):
    """MyGame whose File > Open is the toolbar's Open button found by its tooltip (verified_x: no fixed menu coordinate; the menu's Open word is not reliably read by OCR), and whose dialog
    is proven to be the Open dialog by its words before anything is typed."""
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        CLICKS.append({'kind': 'control', 'dialog': CTX.get('dialog'), 'cls': c['cls'], 'text': c['text'], 'x': c['x'], 'y': c['y']})
        return Game.click_control(self, c, fx, fy, pause)

    def open(self, save, strict=True):
        """The runner's own load path (Game.open ends in Game.dismiss_popups, which clicks an assumed bottom-centre OK): File > Open through `open_file_dialog`, then every box that
        appears is cleared only through its enumerated OK control (close_all: no OK control = DriverError, nothing clicked; each box verified gone within a bounded budget). A Confirm box at
        load is answered No through its control. Returns the box texts (the load popups)."""
        src = Path(save)
        if src.parent.resolve() != _drv.G.resolve(): shutil.copy(src, _drv.G / src.name)
        self.open_file_dialog(src.name)
        self.wait(lambda: self.loaded() or boxes(self), 30, 'game window or a message box after load')
        time.sleep(3)
        texts = [t for _, t in close_all(self, 'load')]
        if not self.loaded():
            self.wait(self.loaded, 30, 'game window after the box was closed')
            texts += [t for _, t in close_all(self, 'load')]
        LOAD_POPUPS[:] = texts
        return texts

    def controls(self, title):
        """Game.controls, retried for up to 8 s: a dialog's controls are not always enumerable the instant its window exists"""
        for k in range(8):
            try: return Game.controls(self, title)
            except _drv.DriverError:
                if k == 7: raise
                if k == 1:                               # the button's own tooltip (same title, visible while the pointer rests on the button) can hide the dialog from win_controls: move the pointer away (a move, not a click)
                    x, y = self.neutral_point(); _drv.sh('xdotool', 'mousemove', str(x), str(y))
                time.sleep(1)

    def open_file_dialog(self, name):
        base = _ids(); self.reset_ui()
        x = verified_x(self, 'main', 'open'); self.click(x, _drv.TOOLBAR_Y, pause=1.0)
        try: self.wait(lambda: [i for i in _ids() - base if _geo(i) and _geo(i)[2] > 200 and _geo(i)[3] > 150], 8, 'Open dialog window')
        except _drv.DriverError: raise _drv.DriverError('the Open button opened no file-dialog-sized window (nothing typed)')
        dlg = [(i, _geo(i)) for i in _ids() - base if _geo(i) and _geo(i)[2] > 200 and _geo(i)[3] > 150]
        if len(dlg) != 1: raise _drv.DriverError('Open: not a single new file-dialog-sized window: %s' % dlg)
        time.sleep(0.5)
        words = [w[0] for w in _screen_words(self, dlg[0][1])]
        log('toolbar', 'Open dialog %s: words %s' % (dlg[0], words[:12]))
        if 'save' in words or not any(w.startswith('open') or w.startswith('look') for w in words): raise _drv.DriverError('the new window does not read as the Open dialog (OCR %s)' % words[:12])
        self.replace_field(name); self.key('Return')

def city_button(g, x, y, tool_label='Fortify city'):
    g.reset_ui(); g.click_tile(x, y, pause=1.0)
    found = g._scan_bar(ARMY_Y, {'fortify': tool_label}, 336, 420, 0.5)
    if 'fortify' not in found: raise _drv.DriverError('city toolbar: no %s tooltip: nothing clicked' % tool_label)
    note_click(kind='toolbar', bar='city', tool='fortify', tooltip=tool_label, x=found['fortify']); g.click(found['fortify'], ARMY_Y, pause=1.5)

def click_row(g, lst, r, tries=3):
    note_click(kind='row', dialog=CTX.get('dialog'), row=r, list_x=lst['x'])
    """Select row r of a list box (12 px per row inside the control's own rectangle, from Game.controls) and prove the selection by the change of the list's pixels; at most `tries` clicks"""
    for k in range(tries):
        before = _region_hash(g, lst); g.click(lst['x'] + lst['w'] // 2, lst['y'] + 12 + 12 * r, pause=0.5)
        if _region_hash(g, lst) != before: return k + 1
    raise _drv.DriverError('list row %d: no change in the list after %d clicks' % (r, tries))

def click_verified(g, c, what, tries=3):
    """Click a control and prove it changed: the pixels of its rectangle (SHA-256 of the raw screenshot crop) must differ from before; at most `tries` clicks (the first into an inactive window may only activate it)"""
    for k in range(tries):
        before = _region_hash(g, c); g.click_control(c, pause=0.7)
        if _region_hash(g, c) != before: return k + 1
    raise _drv.DriverError('%s: no change in the control after %d clicks' % (what, tries))

def capture(g, tag, play_id, batch, step):
    """Capture every box open now: for each its X id, title, geometry, controls (Wine's own list), screenshot and OCR; the screenshot of the whole screen too. Returns the records."""
    out = []
    for (wid, title, x, y, w, h) in boxes(g):
        p, t6, t4 = ocr_window(g, wid, '%s_%s_box%d' % (tag, step, wid))
        try: cs = g.controls(title)
        except Exception as e: cs = 'ERR %s' % e
        tmp = os.path.join(lib.TMP, 'ic2_ref_crop.png')            # the message text only (the box's icon is on the left, the button at the bottom)
        subprocess.run(['convert', p, '-crop', '%dx%d+%d+0' % (int(w * 0.81), int(h * 0.62), int(w * 0.19)), '+repage', '-resize', '300%', '-colorspace', 'Gray', tmp], check=True)
        tc = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout
        rec = {'play': play_id, 'text_crop': ' '.join(tc.split()), 'tag': tag, 'step': step, 'wid': wid, 'title': title, 'geometry': [x, y, w, h], 'controls': cs, 'png': os.path.basename(p),
               'psm6': t6, 'psm4': t4, 'text': ' '.join(t6.split())}
        jlog('ocr_%s.jsonl' % batch, rec); out.append(rec)
    snap(g, '%s_%s_screen.png' % (tag, step))
    return out

def close_all(g, tag, answer_no=True):
    """Close every box open: an Information/Warning/Error box with OK, a Confirm box with 'No' when it has one (else OK). Each box tracked by its X id with a bounded
    budget (3 attempts per window). Returns the list of (title, text)."""
    done = []
    for _ in range(6):
        bs = boxes(g)
        if not bs: break
        wid, title, x, y, w, h = bs[0]
        text = g.read_popup(bs[0])
        try: cs = g.controls(title)
        except Exception: cs = []
        names = [c['text'].replace('&', '').lower() for c in cs]
        want = 'no' if (title == 'Confirm' and answer_no and 'no' in names) else 'ok'
        for attempt in range(3):
            spend(wid, title, 3)
            c = next((c for c in cs if c['text'].replace('&', '').lower() == want), None)
            if c is None: raise _drv.DriverError('box %d (%s): no %s control in %s: nothing clicked' % (wid, title, want, [c_['text'] for c_ in cs]))
            g.click_control(c, pause=1.0)
            if gone(g, wid): break
        else: raise _drv.DriverError('box %d (%s) did not close' % (wid, title))
        done.append((title, text))
    return done

def diff_saves(a, b):
    """(byte count, ranges, parsed differences) between two saves"""
    x, y = open(a, 'rb').read(), open(b, 'rb').read()
    if len(x) != len(y): return {'equal': False, 'len': (len(x), len(y))}
    d = [i for i in range(len(x)) if x[i] != y[i]]
    rng = []
    for i in d:
        if rng and i == rng[-1][1] + 1: rng[-1][1] = i
        else: rng.append([i, i])
    return {'equal': not d, 'n_bytes': len(d), 'ranges': rng[:40]}

CTX = {}
STEPS = []
CLICKS = []                                           # the clicks of the order itself (act), recorded at play time: toolbar buttons (with their tooltip), dialog controls, tiles, radios
LOAD_POPUPS = []

def note_click(**kw): CLICKS.append(kw)

def play(play_id, batch, src, ops, act, note, seed=12345, staged=True, expect=None, fixture_note='', pre=None, post=None):
    """One play. `act(g)` issues the order (no dismissal of boxes). Records everything; returns the record."""
    tag = 'REF_%s_%s' % (play_id, batch)
    eog._ATTEMPTS.clear()                              # X window ids are reused by a new game process: the click budget is per play
    L = lambda m: log('play_%s' % batch, '[%s] %s' % (play_id, m))
    clear_autos()
    if ops: inp = stage_edit(src, SAVEDIR + 'inputs/%s_staged.SAV' % tag, ops, tag)
    else: inp = as_fixture(src, SAVEDIR + 'inputs/%s_fixture.SAV' % tag)
    g = Game2()
    texts = g.load(inp, seed=seed)
    eog._ATTEMPTS.clear()                              # the load boxes' window ids are reused by the order's boxes
    L('loaded %s (%s); popups at load: %s' % (os.path.basename(inp), 'STAGED' if ops else 'fixture, unedited', texts))
    snap(g, '%s_00_loaded.png' % tag)
    if pre:
        pre(g); L('pre-order step done (a normal game order, before the control save)')
        if boxes(g): L('boxes after the pre step: %s' % close_all(g, tag))
    ctl = keep_save_ocr(g, '%s_ctl.SAV' % tag)
    L('control save %s %s' % (os.path.basename(ctl), sha(ctl)))
    if boxes(g): raise _drv.DriverError('a box is open before the order')
    CTX.update(tag=tag, play=play_id, batch=batch, log=L, dialog=None); del CLICKS[:]
    act(g)
    clicks = [dict(c) for c in CLICKS]
    bx = wait_boxes(g)
    recs = capture(g, tag, play_id, batch, 'box')
    recs = STEPS[:] + recs; del STEPS[:]
    L('boxes after the order: %s' % [(r['title'], r['text']) for r in recs])
    closed = close_all(g, tag)
    if post: post(g)
    time.sleep(1.0)
    after = keep_save_ocr(g, '%s_after.SAV' % tag)
    d = diff_saves(ctl, after)
    L('after save %s %s; vs control: %s' % (os.path.basename(after), sha(after), json.dumps(d)))
    rec = {'play': play_id, 'batch': batch, 'note': note, 'staged': bool(ops), 'ops': ops, 'src': os.path.basename(str(src)), 'src_sha': sha(src), 'input': os.path.basename(inp),
           'input_sha': sha(inp), 'control': os.path.basename(ctl), 'control_sha': sha(ctl), 'after': os.path.basename(after), 'after_sha': sha(after),
           'boxes': [{'title': r['title'], 'text': r['text'], 'text_crop': r['text_crop'], 'wid': r['wid'], 'png': r['png'], 'controls': r['controls']} for r in recs], 'closed': closed, 'diff_ctl_after': d,
           'fixture_note': fixture_note, 'clicks': clicks, 'load_popups': list(LOAD_POPUPS), 'pre': bool(pre), 'time': time.strftime('%F %T')}
    jlog('plays_%s.jsonl' % batch, rec)
    g.kill()
    return rec

def open_dialog_tracked(g, title, opener, tries=2):
    """Run `opener()` (a click) until a window with this title exists; returns its X id. At most `tries` openings (a second window with the title is never opened)."""
    for k in range(tries):
        if g.find_windows('^%s$' % re.escape(title)): break
        opener(); time.sleep(1.2)
    w = g.find_windows('^%s$' % re.escape(title))
    if not w: raise _drv.DriverError('%s did not open' % title)
    CTX['dialog'] = title; g.raise_window(w[0][0]); return w[0][0]

def select_rows(g, title, rows, cls_index=0):
    """Select the rows of the dialog's `cls_index`-th list box (ctrl-click for the 2nd and later); the rows' positions come from Game.controls (list box rectangle,
    12 px per row as the driver's own helpers use)."""
    cs = g.controls(title); lst = g.control(cs, cls='TListBox', index=cls_index)
    for k, r in enumerate(rows):
        if k: _drv.sh('xdotool', 'keydown', 'ctrl')
        click_row(g, lst, r)
        if k: _drv.sh('xdotool', 'keyup', 'ctrl')
    return cs

def press(g, title, text, wait_new_box=True):
    cs = g.controls(title); g.click_control(g.control(cs, text=text), pause=1.2)

def close_dialog_cancel(g, title, button='Cancel', tries=3):
    """Close the dialog `title` with its Cancel (or `button`) tracked by its X id, at most `tries` attempts."""
    w = g.find_windows('^%s$' % re.escape(title))
    if not w: return
    wid = w[0][0]
    for _ in range(tries):
        spend(wid, title, tries)
        cs = g.controls(title); g.click_control(g.control(cs, text=button), pause=1.2)
        if gone(g, wid): return
    raise _drv.DriverError('%s did not close' % title)

def confirm_step(g, answer='Yes', timeout=8):
    """Inside an act(): wait for a Confirm box, capture it (screenshot, OCR, controls, X id), answer it with `answer` through its own button (tracked, bounded),
    and keep its record for the play (STEPS). Returns the record."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        w = g.find_windows(r'^Confirm$')
        if w: break
        time.sleep(0.3)
    else: raise _drv.DriverError('no Confirm box')
    time.sleep(0.8)
    recs = capture(g, CTX['tag'], CTX['play'], CTX['batch'], 'confirm')
    STEPS.extend(recs)
    CTX['log']('Confirm box %s answered %s' % ([r['text'] for r in recs], answer))
    answer_confirm(g, 'Confirm', answer)
    time.sleep(1.0)
    return recs[0]
