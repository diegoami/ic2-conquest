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

def mem_strings(g, needles):
    """Search game memory (read only) for each ASCII needle and return the NUL-terminated strings found (the label captions of the window as the game holds them)."""
    out = {n: [] for n in needles}
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
    return out

# ---------------------------------------------------------------- window
def ocr_window(g, wid, tag, scale=3):
    """Screenshot of a window (a versioned file in the artifacts) and its OCR text (tesseract psm 6 and psm 4 on a 3x grey image). Returns (path, text6, text4)."""
    p = new_path(ART + tag + '.png'); g.shot(p, window=str(wid))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    tmp = os.path.join(lib.TMP, 'ic2_eog_ocr.png')
    subprocess.run(['convert', p, '-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp], check=True)
    t = [subprocess.run(['tesseract', tmp, 'stdout', '--psm', str(psm)], capture_output=True, text=True).stdout for psm in (6, 4)]
    return p, t[0], t[1]

def eog_window(g):
    w = g.find_windows(r'^End of Game$')
    return w[0] if w else None

def wait_window(g, pattern, timeout, what, on_other=None):
    """Wait for a visible window; between polls, information boxes (news, offers) are closed with OK and their texts logged (never the End of Game window)."""
    t0 = time.time(); texts = []
    while time.time() - t0 < timeout:
        w = g.find_windows(pattern)
        if w: return w[0], texts
        if g.find_windows(r'^End turn \?$'):
            texts.append('CONFIRM ' + g.read_popup(g.find_windows(r'^End turn \?$')[0]))
            cs = g.controls('End turn ?'); g.click_control(g.control(cs, text='End turn'), pause=1.5); continue
        texts += g.dismiss_popups()
        time.sleep(1)
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

def menu_pick(g, bar_word, item_word, expect=None, tries=3):
    """Open a top-level menu and pick an item, both located by OCR (no fixed point). The menu bar word is clicked and the dropdown is PROVEN open by a new
    unnamed top-level window (as `Game.open_file_dialog` does); the item word is found by OCR inside that window's own rectangle and clicked; `expect`
    (a window title regex) must then appear, else the sequence is repeated (at most 2 retries)."""
    ids = lambda: set(_drv.sh('xdotool', 'search', '--onlyvisible', '--name', '', check=False).split())
    for attempt in range(tries):
        g.reset_ui()
        bar = [w for w in _screen_words(g, (0, 26, 650, 24)) if w[0] == bar_word]
        if not bar: continue
        before = ids()
        g.click(bar[0][1], bar[0][2], pause=1.0)
        new = ids() - before
        pop = None
        for i in new:
            geo = _drv.sh('xdotool', 'getwindowgeometry', i, check=False)
            m = re.search(r'Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)', geo, re.S)
            if m and _drv.sh('xdotool', 'getwindowname', i, check=False).strip() == '': pop = tuple(int(x) for x in m.groups())
        if not pop: continue
        hit = [w for w in _screen_words(g, pop) if w[0] == item_word]
        if not hit: continue
        g.click(hit[0][1], hit[0][2], pause=1.5)
        if expect is None or g.find_windows(expect): return attempt + 1
    raise _drv.DriverError('menu %s > %s did not give %s after %d attempts' % (bar_word, item_word, expect, tries))

def main_title(g):
    return [w[1] for w in g.find_windows('^Imperial Conquest 2')]

def all_windows(g):
    return [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1 and w[5] > 1]

def proc_alive(g):
    return os.path.exists('/proc/%d' % g.pid)

def save_as_ocr(g, name, timeout=20):
    """File > Save as located by OCR (menu_pick: the menu word 'as' of 'Save as'), the name typed in the file dialog once a new window proves it is open
    (as `Game.open_file_dialog`), and the file proven written. Returns the path in the game folder."""
    ids = lambda: set(_drv.sh('xdotool', 'search', '--onlyvisible', '--name', '', check=False).split())
    target = _drv.G / name; target.unlink(missing_ok=True)
    before = ids()
    menu_pick(g, 'file', 'as')
    g.wait(lambda: ids() - before, 8, 'Save as dialog window')
    time.sleep(0.5)
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
                          'in power in', 'Population ', 'Cities   ', 'Treasury '])
    jlog('ocr_%s.jsonl' % batch, {'reason': reason, 'tag': tag, 'step': step, 'window': 'End of Game', 'png': os.path.basename(p), 'psm6': t6, 'psm4': t4,
                                  'geometry': w[2:], 'controls': g.controls('End of Game'), 'memory_strings': mem})
    L('[%s] OCR: %s' % (step, ' | '.join(l for l in t6.splitlines() if l.strip())))
    L('[%s] memory strings: %s' % (step, json.dumps(mem)))
    n_ok = click_ok(g, 'End of Game')
    L('[%s] OK pressed (%d click(s))' % (step, n_ok))
    return at, t6, n_ok

def wait_turn_of(g, nation, timeout, L, not_before_log=0):
    """Wait until it is `nation`'s turn (current nation, an autosave line written since `not_before_log`), closing information boxes and logging them.
    Never touches an End of Game window (a caller handles it)."""
    logf = _drv.G / 'AUTOSAVE.LOG'; t0 = time.time(); texts = []
    while time.time() - t0 < timeout:
        if g.find_windows(r'^End of Game$'): return 'window', texts
        if g.i16(_drv.CUR_NATION) == nation and logf.exists() and len(logf.read_text().splitlines()) > not_before_log:
            time.sleep(2); texts += g.dismiss_popups(); return 'turn', texts
        if g.find_windows(r'^End turn \?$'):
            texts.append('CONFIRM ' + g.read_popup(g.find_windows(r'^End turn \?$')[0]))
            cs = g.controls('End turn ?'); g.click_control(g.control(cs, text='End turn'), pause=1.5); continue
        texts += g.dismiss_popups(); time.sleep(1)
    raise _drv.DriverError('timeout waiting for the turn of %d' % nation)

def autosave_lines():
    f = _drv.G / 'AUTOSAVE.LOG'
    return len(f.read_text().splitlines()) if f.exists() else 0
