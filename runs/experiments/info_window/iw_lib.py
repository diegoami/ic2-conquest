"""Shared setup for the Information-window runs (run-exp-info-window): own display :730, own game folder
~/ic2-work-info, the NORMAL build ('Imperial Conquest 2.exe'), screenshots to the gitignored artifacts folder,
tracked text logs. Never overwrites (rule 6): every write goes to the next free versioned name.
Import before harness.driver."""
import os, sys, time, subprocess, hashlib, glob, struct, shutil
os.environ['IC2_WORK'] = '/home/diego/ic2-work-info'
os.environ['DISPLAY_IC2'] = ':730'
os.environ['IC2_EXE'] = 'Imperial Conquest 2.exe'
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness.driver as _drv
from harness.driver import Game, G, sh, ENV, WINE
from state import sav
DATA = ROOT + '/runs/experiments/data/run-exp-info-window/'
ART = ROOT + '/artifacts/run-exp-info-window/'
os.makedirs(DATA, exist_ok=True); os.makedirs(ART, exist_ok=True)

def new_path(path):
    if not os.path.exists(path): return path
    d, b = os.path.split(path); stem, ext = os.path.splitext(b); n = 2
    while os.path.exists(os.path.join(d, '%s.v%d%s' % (stem, n, ext))): n += 1
    return os.path.join(d, '%s.v%d%s' % (stem, n, ext))
def write_new(path, data, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    p = new_path(path)
    with open(p, 'xb' if binary else 'x', **({} if binary else {'encoding': 'utf-8'})) as f: f.write(data)
    return p
_orig_sh = _drv.sh
def _sh(*args, **kw):
    if args and args[0] == 'import': args = args[:-1] + (new_path(args[-1]),)
    return _orig_sh(*args, **kw)
_drv.sh = _sh

def xvfb():
    if subprocess.run(['pgrep', '-f', 'Xvfb :730'], capture_output=True).returncode:
        subprocess.Popen(['setsid', 'Xvfb', ':730', '-screen', '0', '1280x1024x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
def my_pids():
    out = []
    for p in glob.glob('/proc/[0-9]*/environ'):
        try:
            env = open(p, 'rb').read()
            if b'DISPLAY=:730\0' in env and b'WINEPREFIX=/home/diego/ic2-work-info/prefix\0' in env:
                pid = int(p.split('/')[2])
                cl = open('/proc/%d/cmdline' % pid, 'rb').read()
                if b'Imperial' in cl: out.append(pid)
        except Exception: pass
    return out
def stop(g):
    """Kill only MY game: wineserver -k with MY prefix (ENV), then wait for my pids to go."""
    subprocess.run(['/usr/lib/wine/wineserver', '-k'], env=ENV, capture_output=True); time.sleep(1.5); g.pid = None
def launch(g, save=None):
    """Fresh process of the normal build on my display; open `save` (a path); returns box texts. g.pid = my game's pid."""
    xvfb(); stop(g)
    subprocess.Popen(['setsid', WINE, g.exe], cwd=G, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    g.wait(lambda: g.find_windows('^Imperial Conquest 2$'), 40, 'main window'); time.sleep(3)
    ps = my_pids()
    if not ps: raise SystemExit('own game process not found')
    g.pid = ps[0]
    return g.open(save) if save else []
def snap(name, crop=None):
    p = new_path(ART + name)
    if crop: sh('import', '-window', 'root', '-crop', crop, p)
    else: sh('import', '-window', 'root', p)
    return p, hashlib.sha256(open(p, 'rb').read()).hexdigest()
def ocr_lines(path, scale=3):
    tmp = '/tmp/claude-1000/ocr_iw.png'
    subprocess.run(['convert', path, '-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp], check=True)
    return subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout

import json, re, csv
CAPLOG = DATA + 'captures.tsv'
COLS = ['batch', 'save', 'kind', 'target', 'staged', 'png', 'png_sha256', 'ocr']
def rclick(x, y, pause=1.0):
    sh('xdotool', 'mousemove', str(x), str(y)); time.sleep(0.25); sh('xdotool', 'click', '3'); time.sleep(pause)
PANEL = '330x730+2+269'
def panel_ocr(png):
    """OCR of the Information window crop: one text line per panel line; '|' separates the caption/value columns by position (two spaces)."""
    tmp = '/tmp/claude-1000/ocr_iw.png'
    subprocess.run(['convert', png, '-resize', '300%', '-colorspace', 'Gray', tmp], check=True)
    return subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout
def log_capture(batch, save, kind, target, staged, png, sha, ocr):
    new = not os.path.exists(CAPLOG)
    with open(CAPLOG, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        if new: w.writerow(COLS)
        w.writerow([batch, os.path.basename(save), kind, target, json.dumps(staged, sort_keys=True), os.path.basename(png), sha, ' | '.join(l for l in ocr.splitlines() if l.strip())])
def capture(batch, save, kind, target, staged, name):
    png, sha = snap(name, PANEL)
    ocr = panel_ocr(png)
    log_capture(batch, save, kind, target, staged, png, sha, ocr)
    return png, ocr
def stage_save(batch, base, edits_fn, name):
    """Copy `base` to ARTIFACTS/saves/<name> (a new versioned name), apply edits_fn(Save), return the path."""
    from stage import Save
    d = ART + 'saves/'; os.makedirs(d, exist_ok=True)
    p = new_path(d + name)
    s = Save(base); edits_fn(s); s.write(p)
    return p

def nation_menu(g, n, pause=1.5):
    """Nations > item n: this build's menu pitch is 17 px (first item centre y=57), not driver.MENU_ITEM_Y's 16."""
    g.reset_ui(); sh('xdotool', 'mousemove', '153', '37'); time.sleep(0.3); sh('xdotool', 'click', '1'); time.sleep(0.8)
    sh('xdotool', 'mousemove', '150', str(57 + 17 * n)); time.sleep(0.4); sh('xdotool', 'click', '1'); time.sleep(pause)

def scroll_right(n=12):
    """Click the Information window's horizontal scroll bar right arrow n times (one click = 8 px)."""
    for _ in range(n):
        sh('xdotool', 'mousemove', '317', '987'); time.sleep(0.15); sh('xdotool', 'click', '1'); time.sleep(0.15)
    time.sleep(0.6)
def scroll_home():
    for _ in range(40):
        sh('xdotool', 'mousemove', '9', '987'); time.sleep(0.1); sh('xdotool', 'click', '1'); time.sleep(0.1)
