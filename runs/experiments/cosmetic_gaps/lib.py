"""Shared setup for the cosmetic-gaps plays (docs/tasks/cosmetic-gaps.md), copying runs/experiments/leaders_form/lib.py:
own display (:744), own IC2_WORK copy (~/ic2-work-cosmetic), screenshots to the gitignored artifacts folder, tracked text logs;
nothing is overwritten (rule 6). IC2_STRACE=path starts the game under strace -f (sound plays: the WAV a PlaySoundA opens is the
event's evidence). Import before harness.driver."""
import os, sys, time, subprocess, hashlib, glob, struct, shutil
from paths import ROOT, ART, DATA, TMP
WORKDIR = os.environ.get('IC2_WORK_REF', os.path.expanduser('~/ic2-work-cosmetic'))
DISP = ':744'
os.environ['IC2_WORK'] = WORKDIR
os.environ['DISPLAY_IC2'] = DISP
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import new_path, write_new
import harness.driver as _drv
from harness.driver import Game, G
_orig_sh = _drv.sh
def sh(*args, **kw):
    """driver.sh, but a screenshot goes to the next free versioned name (never overwrites)."""
    if args and args[0] == 'import' and str(args[-1]).startswith(ART): args = args[:-1] + (new_path(args[-1]),)
    return _orig_sh(*args, **kw)
_drv.sh = sh
os.makedirs(ART, exist_ok=True); os.makedirs(DATA, exist_ok=True)
SAVEDIR = ART + 'saves/'
os.makedirs(SAVEDIR, exist_ok=True)

def xvfb():
    if not os.path.exists('/tmp/.X11-unix/X744'):
        subprocess.Popen(['setsid', 'Xvfb', DISP, '-screen', '0', '1280x1024x24', '-nolisten', 'tcp'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

def log(name, msg):
    """Append to a tracked per-batch log (append-only)."""
    with open(DATA + name + '.log', 'a') as f: f.write(time.strftime('%H:%M:%S ') + str(msg) + '\n')
    print(msg, flush=True)

def attach(g):
    """Set g.pid to MY game process (my DISPLAY and WINEPREFIX), never another session's."""
    for p in glob.glob('/proc/[0-9]*/environ'):
        try:
            env = open(p, 'rb').read()
            if (b'DISPLAY=' + DISP.encode() + b'\0') in env and (b'WINEPREFIX=' + WORKDIR.encode() + b'/prefix\0') in env:
                pid = int(p.split('/')[2])
                cl = open('/proc/%d/cmdline' % pid, 'rb').read()
                if b'Imperial' in cl:
                    try:
                        with open('/proc/%d/mem' % pid, 'rb') as m:
                            m.seek(0x47C1EC); m.read(16)
                    except Exception: continue
                    g.pid = pid; return pid
        except Exception: pass
    raise SystemExit('own game process not found')

class MyGame(Game):
    def ensure_xvfb(self):
        xvfb()
    def start(self):
        self.ensure_xvfb(); self.kill()
        cmd = [_drv.WINE, self.exe]
        logp = os.environ.get('IC2_STRACE')
        if logp:
            cmd = ['strace', '-f', '-e', 'trace=openat,open', '-o', logp, '-s', '256'] + cmd
            open(logp, 'w').close()                      # a fresh log per start (the previous one was harvested)
        subprocess.Popen(['setsid'] + cmd, cwd=G, env=_drv.ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows('^Imperial Conquest 2$'), 40, 'main window')
        time.sleep(3)
        attach(self)

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def snap(g, name):
    p = new_path(ART + name); g.shot(p)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    return p

def fixture(name):
    """A repo fixture save (read-only source)."""
    return ROOT + '/saves/' + name

def _screen_words(g, region):
    """OCR words (text, centre x, centre y in screen px) of a screen region (x, y, w, h) of a fresh screenshot (tesseract tsv)."""
    x, y, w, h = region
    full = os.path.join(TMP, 'ic2_cg_screen.png'); crop = os.path.join(TMP, 'ic2_cg_crop.png')
    _orig_sh('import', '-window', 'root', full)
    subprocess.run(['convert', full, '-crop', '%dx%d+%d+%d' % (w, h, x, y), '+repage', '-resize', '300%', '-colorspace', 'Gray', crop], check=True)
    out = subprocess.run(['tesseract', crop, 'stdout', '--psm', '11', 'tsv'], capture_output=True, text=True).stdout
    res = []
    for l in out.splitlines()[1:]:
        f = l.split('\t')
        if len(f) == 12 and f[11].strip():
            res.append((f[11].strip().lower(), x + (int(f[6]) + int(f[8]) // 2) // 3, y + (int(f[7]) + int(f[9]) // 2) // 3))
    return res

MENU_REGION = (240, 40, 420, 190)       # the strip under the menu bar in which the Unit map menu and its Army submenu open (1280x1024 screen)
