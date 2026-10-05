"""Shared helpers of the refusal-text plays (CLAUDE.md rule 6: every output is a new versioned tracked file under runs/experiments/data/run-exp-refusal-texts/).
A play = STAGE (or take a fixture) -> load in a fresh game -> a CONTROL save (the state as the game holds it) -> issue ONE order -> the box(es) that appear are
captured (X window id, title, geometry, controls, screenshot, OCR) and closed with a tracked, bounded click -> an AFTER save, compared byte for byte with the control.
Every staged save is labelled staged (staging_log.tsv: which bytes, which operation). Import eog first (it sets the display and the private game folder)."""
import json, os, re, struct, time, shutil, hashlib, subprocess
import lib
from eog import *                                   # noqa: F401,F403
from eog import _drv, _screen_words, _ids, _geo
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

def army_button(g, i, tool):
    """Select army i (verified through the game's selection word, three attempts at most) and click the army-toolbar button `tool`; the button x comes from the
    tooltip calibration (a missed button raises: a fallback x is never used)."""
    ax, ay = g.army_pos(i); g.select_army(i, ax, ay)
    if not g.army_x: g.calibrate_army_toolbar()
    if tool not in g.army_x or g.army_x[tool] == g.ARMY_TOOLS[tool] and False: raise _drv.DriverError('army toolbar button %s not calibrated' % tool)
    g.click(g.army_x[tool], ARMY_Y, pause=1.5)

def fleet_button(g, i, tool):
    g.select_fleet(i)
    if not g.fleet_x: g.calibrate_fleet_toolbar()
    g.click(g.fleet_x[tool], ARMY_Y, pause=1.5)

def capture(g, tag, play_id, batch, step):
    """Capture every box open now: for each its X id, title, geometry, controls (Wine's own list), screenshot and OCR; the screenshot of the whole screen too. Returns the records."""
    out = []
    for (wid, title, x, y, w, h) in boxes(g):
        p, t6, t4 = ocr_window(g, wid, '%s_%s_box%d' % (tag, step, wid))
        try: cs = g.controls(title)
        except Exception as e: cs = 'ERR %s' % e
        tmp = os.path.join(lib.TMP, 'ic2_ref_crop.png')            # the message text only (the box's icon is on the left, the button at the bottom)
        subprocess.run(['convert', p, '-crop', '%dx%d+%d+0' % (int(w * 0.72), int(h * 0.68), int(w * 0.28)), '+repage', '-resize', '300%', '-colorspace', 'Gray', tmp], check=True)
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
            if c: g.click_control(c, pause=1.0)
            else: g.click(x + w // 2, y + h - 24, pause=1.0)
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

def play(play_id, batch, src, ops, act, note, seed=12345, staged=True, expect=None, fixture_note='', pre=None, post=None):
    """One play. `act(g)` issues the order (no dismissal of boxes). Records everything; returns the record."""
    tag = 'REF_%s_%s' % (play_id, batch)
    L = lambda m: log('play_%s' % batch, '[%s] %s' % (play_id, m))
    clear_autos()
    if ops: inp = stage_edit(src, SAVEDIR + 'inputs/%s_staged.SAV' % tag, ops, tag)
    else: inp = as_fixture(src, SAVEDIR + 'inputs/%s_fixture.SAV' % tag)
    g = MyGame()
    texts = g.load(inp, seed=seed)
    L('loaded %s (%s); popups at load: %s' % (os.path.basename(inp), 'STAGED' if ops else 'fixture, unedited', texts))
    snap(g, '%s_00_loaded.png' % tag)
    if pre:
        pre(g); L('pre-order step done (a normal game order, before the control save)')
        if boxes(g): L('boxes after the pre step: %s' % close_all(g, tag))
    ctl = keep_save_ocr(g, '%s_ctl.SAV' % tag)
    L('control save %s %s' % (os.path.basename(ctl), sha(ctl)))
    if boxes(g): raise _drv.DriverError('a box is open before the order')
    CTX.update(tag=tag, play=play_id, batch=batch, log=L)
    act(g)
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
           'fixture_note': fixture_note, 'pre': bool(pre), 'time': time.strftime('%F %T')}
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
    g.raise_window(w[0][0]); return w[0][0]

def select_rows(g, title, rows, cls_index=0):
    """Select the rows of the dialog's `cls_index`-th list box (ctrl-click for the 2nd and later); the rows' positions come from Game.controls (list box rectangle,
    12 px per row as the driver's own helpers use)."""
    cs = g.controls(title); lst = g.control(cs, cls='TListBox', index=cls_index)
    for k, r in enumerate(rows):
        if k: _drv.sh('xdotool', 'keydown', 'ctrl')
        g.click(lst['x'] + lst['w'] // 2, lst['y'] + 12 + 12 * r, pause=0.4)
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
