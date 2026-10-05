"""Helpers of the End of Game experiment: staged saves (one field per operation, every edit's byte range checked and logged), memory reads of the
fall state, text read from the window (screenshot + OCR) and from game memory, and the verified End turn / OK / Abdicate steps.
Import lib first (it sets the private game folder and display)."""
import json, os, re, struct, subprocess, sys, time, shutil, hashlib
from lib import *                                   # noqa: F401,F403  (sets IC2_WORK, DISPLAY_IC2, patches driver.sh)
import lib
from lib import _drv, _orig_sh, _screen_words, DATA, ART, SAVEDIR, ROOT, log, sha, MyGame, attach, xvfb
from common import new_path, write_new
sys.path.insert(0, os.path.join(ROOT, 'runs', 'experiments', 'battles'))
import stage as STAGE                               # noqa: E402  (save edits)
from state import sav as SAV                        # noqa: E402

NATION_OFF = {'treasury': (0x438, 4), 'unity': (0x440, 2), 'ncities': (0x446, 2)}
CAL_OFF = {'year': (42, 2), 'week': (40, 2), 'season': (44, 2)}      # tail offsets (docs/sav-layout-notes.md section 8)

def nation_base(b, n):
    return STAGE._nation(b, n)

def tail_off(b):
    return SAV.parse(bytes(b))['tail_off']

def edit_save(src, dst, ops, tag):
    """dst = src with `ops` applied, each operation writing only its own field. ops: ('treasury', n, v) ('unity', n, v) ('ncities', n, v)
    ('city', c, {field: v}) ('calendar', field, v) with field in year/week/season. No ops: byte-identical copy. The byte offsets that differ are checked to
    lie inside the declared fields and the edit is appended to the tracked staging log. Returns dst."""
    src = str(src); dst = str(dst)
    b = bytearray(open(src, 'rb').read()); orig = bytes(b)
    allowed = []                                        # (offset, length, label)
    for op in ops:
        k = op[0]
        if k in NATION_OFF:
            off, ln = NATION_OFF[k]; allowed.append((nation_base(b, op[1]) + off, ln, '%s nation %d' % (k, op[1])))
            STAGE.apply(b, [op])
        elif k == 'city':
            for f in op[2]:
                allowed.append((SAV.CITY_OFF + op[1] * SAV.CITY_LEN + STAGE.CITY_FIELDS[f], 2, 'city %d %s' % (op[1], f)))
            STAGE.apply(b, [op])
        elif k == 'own_all':                    # ('own_all', n): every city's owner = n, n's list = all 334 cities, every other nation: empty list, 0 cities, unity 0, capital 0xFFFF
            n = op[1]
            for c in range(SAV.CITY_N):
                o = SAV.CITY_OFF + c * SAV.CITY_LEN + STAGE.CITY_FIELDS['owner']; allowed.append((o, 2, 'city %d owner' % c)); struct.pack_into('<h', b, o, n)
            for m in range(16):
                base = nation_base(b, m)
                if m == n:
                    allowed.append((base + 0x48, 668, 'nation %d city list' % m)); allowed.append((base + 0x446, 2, 'nation %d count' % m))
                    for i in range(SAV.CITY_N): struct.pack_into('<H', b, base + 0x48 + 2 * i, i)
                    struct.pack_into('<h', b, base + 0x446, SAV.CITY_N)
                else:
                    allowed += [(base + 0x48, 2, 'nation %d list head' % m), (base + 0x446, 2, 'nation %d count' % m), (base + 0x440, 2, 'nation %d unity' % m),
                                (base + 0x444, 2, 'nation %d capital' % m)]
                    struct.pack_into('<H', b, base + 0x48, 0xFFFF); struct.pack_into('<h', b, base + 0x446, 0)
                    struct.pack_into('<h', b, base + 0x440, 0); struct.pack_into('<H', b, base + 0x444, 0xFFFF)
        elif k == 'calendar':
            off, ln = CAL_OFF[op[1]]; o = tail_off(b) + off
            allowed.append((o, ln, 'calendar ' + op[1])); struct.pack_into('<h', b, o, op[2])
        else:
            raise ValueError('unknown edit %r' % (op,))
    diff = [i for i in range(len(b)) if b[i] != orig[i]]
    for i in diff:
        if not any(o <= i < o + l for o, l, _ in allowed):
            raise ValueError('byte %d changed outside the declared fields' % i)
    if not ops and diff:
        raise ValueError('no operation but bytes differ')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    dst = new_path(dst)
    with open(dst, 'xb') as f: f.write(bytes(b))
    with open(DATA + 'staging_log.tsv', 'a') as f:
        f.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (time.strftime('%F %T'), tag, os.path.basename(src), sha(src), os.path.basename(dst), sha(dst),
                json.dumps([[a, b_, c] for a, b_, c in allowed]) + ' ops=' + json.dumps(ops)))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    log('stage', '%s: %s -> %s, %d bytes changed %s' % (tag, os.path.basename(src), os.path.basename(dst), len(diff), ops))
    return dst

def read_save(p):
    return SAV.parse(open(p, 'rb').read())

# ---------------------------------------------------------------- memory
def seat_state(g, n):
    """The fall-relevant fields of nation n from game memory (the same offsets as the save)."""
    r = g.nation_rec(n)
    i32 = lambda o: struct.unpack_from('<i', r, o)[0]
    i16 = lambda o: struct.unpack_from('<h', r, o)[0]
    cs = lambda o, ln: r[o:o + ln].split(b'\0')[0].decode('latin1')
    return {'nation': n, 'name': cs(0, 11), 'leader': cs(0x0B, 27), 'wealth': i32(0x430), 'wealth_start': i32(0x434), 'treasury': i32(0x438),
            'treasury_start': i32(0x43C), 'unity': i16(0x440), 'mob': i16(0x442), 'cities': i16(0x446), 'cities_start': i16(0x448),
            'conquered_by': i16(0x44E), 'human': r[0x490]}

def world_state(g, label):
    d = {'label': label, 'time': time.strftime('%F %T'), 'calendar': g.calendar(), 'turn': g.turn_number(), 'cur_nation': g.i16(_drv.CUR_NATION),
         'year_word_0x4a0332': g.i16(0x4A0332), 'seat_0x4a032c': g.i16(0x4A032C),
         'humans': [n for n in range(16) if g.nation_rec(n)[0x490] != 0]}
    d['seats'] = {n: seat_state(g, n) for n in set(d['humans']) | {d['cur_nation']}}
    return d

def jlog(name, obj):
    with open(DATA + name, 'a') as f: f.write(json.dumps(obj) + '\n')

def mem_strings(g, needles, full=()):
    """Search game memory (read only) for each ASCII needle and return the NUL-terminated strings found (the label captions of the window as the game holds them)."""
    out = {n: [] for n in list(needles) + ['FULL:' + f for f in full]}
    maps = open('/proc/%d/maps' % g.pid).read().splitlines()
    with open('/proc/%d/mem' % g.pid, 'rb', 0) as m:
        for line in maps:
            a, perm = line.split()[0], line.split()[1]
            if not perm.startswith('rw'): continue
            lo, hi = [int(x, 16) for x in a.split('-')]
            if hi > 0x80000000: continue
            try:
                m.seek(lo); data = m.read(hi - lo)
            except Exception: continue
            for nd in needles:
                for mt in re.finditer(re.escape(nd.encode('latin1')), data):
                    e = data.find(b'\0', mt.start()); s = data[mt.start():e if e > 0 else mt.start() + 200].decode('latin1')
                    if s not in out[nd]: out[nd].append(s)
            for nd in full:                      # the whole NUL-delimited string that contains the needle (a heap string is preceded by its length dword, whose high bytes are NUL)
                for mt in re.finditer(re.escape(nd.encode('latin1')), data):
                    b0 = data.rfind(b'\0', 0, mt.start()) + 1; e = data.find(b'\0', mt.start())
                    s = data[b0:e if e > 0 else mt.start() + 200].decode('latin1')
                    if s not in out['FULL:' + nd]: out['FULL:' + nd].append(s)
    return out

# ---------------------------------------------------------------- window
def ocr_window(g, wid, tag, scale=3):
    """Screenshot of a window (a versioned file in the artifacts) and its OCR text (tesseract psm 6 and psm 4 on a 3x grey image). Returns (path, text6, text4)."""
    p = new_path(ART + tag + '.png'); g.shot(p, window=str(wid))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    tmp = os.path.join(lib.TMP, 'ic2_ref_ocr.png')
    subprocess.run(['convert', p, '-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp], check=True)
    t = [subprocess.run(['tesseract', tmp, 'stdout', '--psm', str(psm)], capture_output=True, text=True).stdout for psm in (6, 4)]
    return p, t[0], t[1]

def eog_window(g):
    w = g.find_windows(r'^End of Game$')
    return w[0] if w else None

BOX_TITLES = ('Information', 'Confirm', 'Warning', 'Error', '')
_ATTEMPTS = {}                                                   # X window id -> clicks spent on it (all loops share this budget)

def spend(wid, what, limit=3):
    """One click attempt on window `wid`; the 4th attempt on the same window raises (at most three attempts in all, never a click per poll)."""
    _ATTEMPTS[wid] = _ATTEMPTS.get(wid, 0) + 1
    if _ATTEMPTS[wid] > limit:
        raise _drv.DriverError('%s (window %d) is still open after %d attempts' % (what, wid, limit))

def gone(g, wid, pattern=None, timeout=5):
    """True when the window with X id `wid` has disappeared within `timeout` s."""
    try:
        g.wait(lambda: wid not in [w[0] for w in g.find_windows('.')], timeout, 'window %d gone' % wid); return True
    except _drv.DriverError:
        return False

def answer_confirm(g, title, button, tries=3):
    """Press `button` ('&Yes', 'End turn', ...; located by Game.controls) on the dialog `title`. The dialog's X id is tracked: after each click it must be gone
    (verified), at most `tries` attempts in all, then DriverError. Returns the dialog's OCR text."""
    ws = g.find_windows('^%s$' % re.escape(title))
    if not ws: raise _drv.DriverError('no %s dialog' % title)
    wid = ws[0][0]; text = g.read_popup(ws[0])
    for attempt in range(tries):
        spend(wid, title, tries)
        cs = g.controls(title); c = next((c for c in cs if c['text'].replace('&', '').lower() == button.replace('&', '').lower()), None)
        if c is None: raise _drv.DriverError('%s: no %s button in %s' % (title, button, [x['text'] for x in cs]))
        g.click_control(c, pause=1.0)
        if gone(g, wid): return text
        log('eog', '%s click %d on dialog %d did not close it' % (title, attempt + 1, wid))
    raise _drv.DriverError('%s (window %d) did not close after %d attempts' % (title, wid, tries))

def close_boxes(g, tries=3):
    """Close the information boxes (news, offers) with their OK control, enumerated by Game.controls: a box without an OK control raises DriverError and NOTHING is clicked (no geometric
    fallback). Each box's X id is tracked and verified gone after each click, at most `tries` attempts in all. A Confirm box is NOT answered here (DriverError). Returns the texts."""
    texts = []
    for p in g.popups():
        wid, name, x, y, wd, ht = p
        if name not in BOX_TITLES or wd >= 600 or ht >= 300: continue
        if name == 'Confirm': raise _drv.DriverError('unexpected Confirm box: ' + g.read_popup(p))
        texts.append(g.read_popup(p))
        cs = g.controls(name); ok = next((c for c in cs if c['text'].replace('&', '').lower() == 'ok'), None)
        if ok is None: raise _drv.DriverError('box %d (%r): no OK control in %s: nothing clicked' % (wid, texts[-1], [c['text'] for c in cs]))
        for attempt in range(tries):
            spend(wid, 'box', tries)
            g.click_control(ok, pause=0.6)
            if gone(g, wid, timeout=3): break
        else: raise _drv.DriverError('box %d (%r) did not close after %d attempts' % (wid, texts[-1], tries))
    return texts

def poll_dialogs(g):
    """One poll: the End turn ? confirmation (answered End turn, bounded) and information boxes. Returns the texts."""
    texts = []
    if g.find_windows(r'^End turn \?$'): texts.append('CONFIRM ' + answer_confirm(g, 'End turn ?', 'End turn'))
    return texts + close_boxes(g)

def wait_window(g, pattern, timeout, what):
    """Wait for a visible window; between polls dialogs are handled by poll_dialogs (bounded per window id)."""
    t0 = time.time(); texts = []
    while time.time() - t0 < timeout:
        w = g.find_windows(pattern)
        if w: return w[0], texts
        texts += poll_dialogs(g); time.sleep(1)
    raise _drv.DriverError('timeout waiting for ' + what)

def press_end_turn_once(g, timeout=10):
    """One End turn click, with proof that it registered (calendar, current nation, an autosave line, a window or a battle changed). No second click is made
    here: if no sign shows in `timeout` s a DriverError is raised and the caller decides (the click may be queued)."""
    logf = _drv.G / 'AUTOSAVE.LOG'
    n = len(logf.read_text().splitlines()) if logf.exists() else 0
    cal, me = g.calendar(), g.i16(_drv.CUR_NATION)
    started = lambda: (g.i16(_drv.CUR_NATION) != me or g.calendar() != cal or (logf.exists() and len(logf.read_text().splitlines()) > n)
                       or g.popups() or g.in_battle() or g.find_windows(r'^End of Game$'))
    g.tool('end_turn')
    g.wait(started, timeout, 'sign that End turn registered', step=0.25)

def click_ok(g, title, tries=3):
    """Press OK of the named window, located by Game.controls (not a fixed point); verified by THAT window (its X id) disappearing (a second window with the same
    title may open at once, as with two human seats falling in a row); at most two retries. Returns the number of clicks used."""
    w0 = g.find_windows('^%s$' % re.escape(title))[0][0]
    for attempt in range(tries):
        cs = g.controls(title)
        g.click_control(g.control(cs, text='OK'), pause=1.5)
        try:
            g.wait(lambda: w0 not in [w[0] for w in g.find_windows('^%s$' % re.escape(title))], 6, title + ' closed'); return attempt + 1
        except _drv.DriverError:
            log('eog', 'OK click %d on %s (window %d) did not close it' % (attempt + 1, title, w0))
    raise _drv.DriverError('%s did not close' % title)

def harvest(tag):
    """Copy every AUTO*.SAV of the game folder not yet kept into the artifacts (named <tag>_AUTOnnnn.SAV, hashed in SAVES.sha256). Returns the kept names."""
    out = []
    for f in sorted(_drv.G.glob('AUTO*.SAV')):
        dst = SAVEDIR + '%s_%s' % (tag, f.name)
        if os.path.exists(dst): continue
        shutil.copy(f, dst)
        with open(DATA + 'SAVES.sha256', 'a') as h: h.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
        out.append(os.path.basename(dst))
    return out

def clear_autos():
    """Remove the AUTO*.SAV and AUTOSAVE.LOG of MY game folder before a scenario (copies of them were harvested after earlier scenarios)."""
    for f in list(_drv.G.glob('AUTO*')): f.unlink()

def _ids():
    return set(_drv.sh('xdotool', 'search', '--onlyvisible', '--name', '', check=False).split())

def _geo(i):
    m = re.search(r'Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)', _drv.sh('xdotool', 'getwindowgeometry', i, check=False), re.S)
    return tuple(int(x) for x in m.groups()) if m else None

def menu_pick(g, bar_word, item_word, expect=None, new_window=False, tries=3):
    """Open a top-level menu and pick an item, both located by OCR (no fixed point). Every transition is verified, at most `tries` attempts in all:
    (1) the menu bar word is clicked and the dropdown must show as a new unnamed top-level window (its id and rectangle are kept);
    (2) the item word is found by OCR inside that rectangle and clicked;
    (3) the click must have had an effect: with `expect` (a window title regex) that window appears; with `new_window` a top-level window that is neither in the
        baseline taken before the menu was opened nor the dropdown appears AND the dropdown is gone; otherwise the dropdown must be gone.
    Returns (attempt number, ids of the new windows)."""
    for attempt in range(tries):
        g.reset_ui()
        bar = [w for w in _screen_words(g, (0, 26, 650, 24)) if w[0] == bar_word]
        if not bar: continue
        base = _ids()
        g.click(bar[0][1], bar[0][2], pause=1.0)
        drop = [(i, _geo(i)) for i in _ids() - base if _drv.sh('xdotool', 'getwindowname', i, check=False).strip() == '' and _geo(i)]
        if len(drop) != 1: continue
        did, pop = drop[0]
        hit = [w for w in _screen_words(g, pop) if w[0] == item_word]
        if not hit: continue
        g.click(hit[0][1], hit[0][2], pause=1.5)
        now = _ids(); dropdown_gone = did not in now
        if expect is not None:
            if g.find_windows(expect): return attempt + 1, set()
        elif new_window:
            new = now - base - {did}
            if dropdown_gone and new: return attempt + 1, new
        elif dropdown_gone: return attempt + 1, set()
        log('eog', 'menu %s > %s: attempt %d had no verified effect' % (bar_word, item_word, attempt + 1))
    raise _drv.DriverError('menu %s > %s had no verified effect after %d attempts' % (bar_word, item_word, tries))

def main_title(g):
    return [w[1] for w in g.find_windows('^Imperial Conquest 2')]

def all_windows(g):
    return [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1 and w[5] > 1]

def proc_alive(g):
    return os.path.exists('/proc/%d' % g.pid)

def save_as_ocr(g, name, timeout=20):
    """File > Save as: the menu word 'as' is picked by OCR with every transition verified (menu_pick, new_window=True: the dropdown is gone and a distinct window
    exists); that window must be a file dialog, proven by its OCR containing the word 'name' (File name) and by being larger than the dropdown, BEFORE
    anything is typed; then the name is typed and the file proven written. Returns the path in the game folder."""
    target = _drv.G / name; target.unlink(missing_ok=True)
    _, new = menu_pick(g, 'file', 'as', new_window=True)
    dlg = [(i, _geo(i)) for i in new if _geo(i) and _geo(i)[2] > 200 and _geo(i)[3] > 150]
    if len(dlg) != 1: raise _drv.DriverError('Save as: no single file-dialog-sized window among the new ones: %s' % [(i, _geo(i)) for i in new])
    words = [w[0] for w in _screen_words(g, dlg[0][1])]
    log('eog', 'Save as dialog %s: words %s' % (dlg[0], words[:12]))
    if not any('name' in w for w in words): raise _drv.DriverError('Save as: the new window does not read as a file dialog (OCR %s)' % words[:12])
    g.replace_field(name); g.key('Return')
    g.wait(lambda: target.exists() and target.stat().st_size > 100000, timeout, 'save ' + name)
    time.sleep(0.5)
    return target

def keep_save_ocr(g, name):
    """save_as_ocr, then a copy under the next free name in the artifacts, hashed in SAVES.sha256. Returns the artifact path."""
    t = save_as_ocr(g, name)
    dst = new_path(SAVEDIR + name); shutil.copy(t, dst)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    return dst

def capture_and_ok(g, tag, batch, reason, step, L):
    """The End of Game window is open: record the state at the window (memory), the window screenshot and its OCR, the strings in game memory and the
    window's controls; press OK (located by Game.controls, verified by the window closing, at most two retries); return (state_at_window, ocr text6, n_ok_clicks)."""
    w = eog_window(g)
    at = world_state(g, 'window_open')
    jlog('states_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': step + '_window_open', **at})
    snap(g, '%s_%s_context.png' % (tag, step))
    p, t6, t4 = ocr_window(g, w[0], '%s_%s_window' % (tag, step))
    mem = mem_strings(g, ['The game is over for', 'You have reached the end', 'Your unpopularity', 'Your army have', 'Your nation has been', 'You have conquerred',
                          'in power in', 'Population ', 'Cities   ', 'Treasury '], full=['in power in'])
    jlog('ocr_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': step, 'window': 'End of Game', 'png': os.path.basename(p), 'psm6': t6, 'psm4': t4,
                                  'geometry': w[2:], 'controls': g.controls('End of Game'), 'memory_strings': mem})
    L('[%s] OCR: %s' % (step, ' | '.join(l for l in t6.splitlines() if l.strip())))
    L('[%s] memory strings: %s' % (step, json.dumps(mem)))
    n_ok = click_ok(g, 'End of Game')
    L('[%s] OK pressed (%d click(s))' % (step, n_ok))
    return at, t6, n_ok

def wait_turn_of(g, nation, timeout, L, not_before_log=0):
    """Wait until it is `nation`'s turn (current nation, an autosave line written since `not_before_log`), handling dialogs with poll_dialogs (bounded per
    window id). Never touches an End of Game window (a caller handles it)."""
    logf = _drv.G / 'AUTOSAVE.LOG'; t0 = time.time(); texts = []
    while time.time() - t0 < timeout:
        if g.find_windows(r'^End of Game$'): return 'window', texts
        if g.i16(_drv.CUR_NATION) == nation and logf.exists() and len(logf.read_text().splitlines()) > not_before_log:
            time.sleep(2); texts += close_boxes(g); return 'turn', texts
        texts += poll_dialogs(g); time.sleep(1)
    raise _drv.DriverError('timeout waiting for the turn of %d' % nation)

def autosave_lines():
    f = _drv.G / 'AUTOSAVE.LOG'
    return len(f.read_text().splitlines()) if f.exists() else 0
