"""Helpers of the leaders-form experiment (copied from runs/experiments/refusal_texts/eog.py without the staging and End of Game parts): memory reads of the nation records, text read from the window (screenshot + OCR) and from game memory, and the verified End turn / OK / Abdicate steps.
Import lib first (it sets the private game folder and display)."""
import json, os, re, struct, subprocess, sys, time, shutil, hashlib
from lib import *                                   # noqa: F401,F403  (sets IC2_WORK, DISPLAY_IC2, patches driver.sh)
import lib
from lib import _drv, _orig_sh, _screen_words, DATA, ART, SAVEDIR, ROOT, log, sha, MyGame, attach, xvfb
from common import new_path, write_new
from state import sav as SAV                        # noqa: E402

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

def _harvested_save_index():
    """Every keep in SAVEDIR: a dict {live_auto_name -> sha256 of the harvested copy}. Used by clear_autos
    (review R1/R5 - by-content match; an older same-name copy whose contents differ does not authorise
    deletion of a freshly measured save)."""
    out = {}
    for f in sorted(os.listdir(SAVEDIR)):
        if not f.endswith('.SAV'): continue
        i = f.rfind('_AUTO')
        if i >= 0: key = f[i + 1:]
        elif f.startswith('AUTO'): key = f
        else: continue
        try:
            out[key] = sha(SAVEDIR + f)
        except OSError: pass
    return out

def clear_autos():
    """Remove the AUTO*.SAV and AUTOSAVE.LOG of MY game folder before a scenario - only when every live
    AUTO*.SAV has been HARVESTED (a <tag>_<autoname> copy in SAVEDIR) AND the harvested copy's sha256
    matches the live save's sha256 (review R1/R5: the same basename alone is not sufficient - a fresh
    measurement differs from an old archive and would be silently deleted)."""
    harvested = _harvested_save_index()
    for f in list(_drv.G.glob('AUTO*')):
        if f.suffix != '.SAV':
            f.unlink(); continue
        kept = harvested.get(f.name)
        if not kept:
            raise _drv.DriverError('clear_autos: %s was not harvested (no <tag>_%s in %s); harvest it first or rename this plays tag' % (f.name, f.name, SAVEDIR))
        try:
            live_sha = sha(str(f))
        except OSError:
            raise _drv.DriverError('clear_autos: cannot read live %s to compare' % f.name)
        if kept != live_sha:
            raise _drv.DriverError('clear_autos: %s differs from its harvested copy (kept sha %s, live sha %s); the archive is stale - harvest again before deleting' % (f.name, kept, live_sha))
        f.unlink()

def _ids():
    return set(_drv.sh('xdotool', 'search', '--onlyvisible', '--name', '', check=False).split())

def _geo(i):
    m = re.search(r'Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)', _drv.sh('xdotool', 'getwindowgeometry', i, check=False), re.S)
    return tuple(int(x) for x in m.groups()) if m else None

def main_title(g):
    return [w[1] for w in g.find_windows('^Imperial Conquest 2')]

def all_windows(g):
    return [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1 and w[5] > 1]

def proc_alive(g):
    return os.path.exists('/proc/%d' % g.pid)

def autosave_lines():
    f = _drv.G / 'AUTOSAVE.LOG'
    return len(f.read_text().splitlines()) if f.exists() else 0
