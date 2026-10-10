"""Shared setup for the feature-inventory EXPLORE runs: own display, own IC2_WORK copy, screenshots to the
gitignored artifacts folder, a tracked text log. Import before harness.driver."""
import os, sys, time, subprocess
os.environ.setdefault('IC2_WORK', '/home/diego/ic2-work-inv')
os.environ.setdefault('DISPLAY_IC2', ':700')
ROOT = '/home/diego/projects/wt-inventory'
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + '/runs/experiments/feature_inventory')
from common import new_path
import harness.driver as _drv
from harness.driver import Game, G
_orig_sh = _drv.sh
def sh(*args, **kw):
    """driver.sh, but a screenshot (`import ... <file>`) goes to the next free versioned name: EXPLORE runs never overwrite (rule 6)."""
    if args and args[0] == 'import': args = args[:-1] + (new_path(args[-1]),)
    return _orig_sh(*args, **kw)
_drv.sh = sh
ART = ROOT + '/artifacts/run-exp-feature-inventory/'
LOGD = ROOT + '/runs/experiments/data/run-exp-feature-inventory/explore/'
os.makedirs(ART, exist_ok=True); os.makedirs(LOGD, exist_ok=True)
def xvfb():
    if subprocess.run(['pgrep', '-f', 'Xvfb :700'], capture_output=True).returncode:
        subprocess.Popen(['setsid', 'Xvfb', ':700', '-screen', '0', '1280x1024x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
def log(batch, msg):
    with open(LOGD + batch + '.log', 'a') as f: f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    print(msg)
from harness import environment as _env   # every start records the Wine/font environment in a log named `environment` (harness/environment.py)
_env.add_sink(lambda rec: log('environment', _env.sink_line(rec)))
def wins(g, batch, tag):
    ws = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows('.') if w[4] > 1 and w[5] > 1]
    log(batch, '%s windows: %s' % (tag, ws)); return ws
def rclick(g, x, y, pause=0.8):
    sh('xdotool', 'mousemove', str(x), str(y)); time.sleep(0.25); sh('xdotool', 'click', '3'); time.sleep(pause)
def attach(g):
    """Set g.pid to MY game process (DISPLAY=:700), never one of another session's."""
    import glob
    for p in glob.glob('/proc/[0-9]*/environ'):
        try:
            env = open(p, 'rb').read()
            if b'DISPLAY=:700\0' in env and b'WINEPREFIX=/home/diego/ic2-work-inv/prefix' in env:
                pid = int(p.split('/')[2])
                if open('/proc/%d/cmdline' % pid, 'rb').read().startswith(b'C:\\IC2\\Imperial') or b'Imperial' in open('/proc/%d/cmdline' % pid, 'rb').read():
                    g.pid = pid; return pid
        except Exception: pass
    raise SystemExit('own game process not found')

import hashlib, re as _re
def snap(g, name, crop=None):
    """Screenshot to a NEW file (never overwrites; rule 6). Returns (path, sha256)."""
    p = new_path(ART + name)
    if crop: sh('import', '-window', 'root', '-crop', crop, p)
    else: g.shot(p)
    return p, hashlib.sha256(open(p, 'rb').read()).hexdigest()
def ocr_words(path, scale=3):
    """OCR words with centres: [(text, x, y)] in the screenshot's own pixels."""
    tmp = '/tmp/claude-1000/ocr_tmp.png'
    subprocess.run(['convert', path, '-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp], check=True)
    out = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '11', 'tsv'], capture_output=True, text=True).stdout
    res = []
    for l in out.splitlines()[1:]:
        f = l.split('\t')
        if len(f) == 12 and f[11].strip():
            res.append((f[11].strip(), (int(f[6]) + int(f[8]) // 2) // scale, (int(f[7]) + int(f[9]) // 2) // scale))
    return res
