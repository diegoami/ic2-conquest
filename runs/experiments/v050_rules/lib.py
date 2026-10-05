"""Shared setup for the v0.5.0 rule-read plays: own display (:733), own IC2_WORK copy, screenshots to the gitignored artifacts
folder, tracked text logs; nothing is overwritten (rule 6). Import before harness.driver."""
import os, sys, time, subprocess, hashlib, glob, struct, shutil
from paths import ROOT, ART, DATA, TMP
WORKDIR = os.environ.get('IC2_WORK_V050', os.path.expanduser('~/ic2-work-v050'))
DISP = ':733'
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
    if not os.path.exists('/tmp/.X11-unix/X733'):
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
        subprocess.Popen(['setsid', _drv.WINE, self.exe], cwd=G, env=_drv.ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows('^Imperial Conquest 2$'), 40, 'main window')
        time.sleep(3)
        attach(self)

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def keep_save(g, name):
    """Save the running game as `name` (File > Save as) and copy it to the artifacts folder under the next free name; log its hash.
    Returns the artifact path."""
    t = g.save_as(name)
    dst = new_path(SAVEDIR + name)
    shutil.copy(t, dst)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(dst), os.path.basename(dst)))
    return dst

def snap(g, name):
    p = new_path(ART + name); g.shot(p)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    return p

def fixture(name):
    """A repo fixture save (read-only source)."""
    return ROOT + '/saves/' + name

def snapstate(g, tag, armies=(), nation=0):
    """One line of memory state: nation treasury/mobilisation/relations and the listed armies (money, supplies, position, moves, troops).
    Appended to the tracked state log; returns the dict."""
    n = g.nation_state(nation)
    d = {'tag': tag, 'turn': g.turn_number(), 'treasury': n['treasury'], 'mob': n['mobilization'], 'tax_base': n['tax_base'],
         'wealth': n['wealth'], 'queue': [(s['slot'], s['type'], s['troops'], s['city'], s['state']) for s in n['recruit_slots']],
         'relations': {k: v for k, v in n['relations'].items() if v}, 'armies': {}}
    for i in armies:
        a = g.army_state(i)
        d['armies'][i] = {'x': a['x'], 'y': a['y'], 'owner': a['owner'], 'moves': a['moves'], 'sup': a['supplies'], 'money': a['money'],
                          'troops': a['troops'], 'units': [(u['type'], u['troops'], u['merc'], u['quality']) for u in a['units']]}
    import json
    with open(DATA + 'state_log.jsonl', 'a') as f: f.write(json.dumps(d) + '\n')
    log('steps', '%s: %s' % (tag, json.dumps(d)))
    return d

def supply_dialog(g, i, money100=0, money10=0, sup100=0, sup10=0, pause=0.25):
    """Supply army with the arrows located by win_controls (this environment's metrics differ from driver.supply's fixed points).
    The two supply arrows are the TUpDowns at y~88 (10s left, 100s right), the two money arrows those at y~281. Up arrow = fy 0.25
    (city -> army, treasury -> purse), down arrow = fy 0.75. Returns the popup texts."""
    g.army_tool(i, 'supply', 'Supply army')
    cs = g.controls('Supply army')
    ups = sorted([c for c in cs if c['cls'] == 'TUpDown'], key=lambda c: (c['y'], c['x']))
    s10, s100, m10_, m100_ = ups[0], ups[1], ups[2], ups[3]
    def press(c, n):
        for _ in range(abs(n)): g.click_control(c, fy=0.25 if n > 0 else 0.75, pause=pause)
    press(s10, sup10); press(s100, sup100); press(m10_, money10); press(m100_, money100)
    texts = g.dismiss_popups()
    for _ in range(3):
        g.click_control(g.control(cs, text='OK'), pause=0.8)
        try:
            g.wait(lambda: not g.find_windows('^Supply army$'), 5, 'Supply army closed'); break
        except _drv.DriverError: pass
    else: raise _drv.DriverError('Supply army did not close')
    return texts

def open_tool(g, name, title, tries=3, wait=6):
    """Open a toolbar dialog, retrying: the first click into an inactive window may only activate it (driver pitfall)."""
    import re as _re
    for _ in range(tries):
        g.tool(name)
        try:
            g.wait(lambda: g.find_windows('^%s$' % _re.escape(title)), wait, title); return
        except _drv.DriverError: pass
    raise _drv.DriverError('%s did not open' % title)

def ocr_text(path, crop=None, scale=3):
    tmp = os.path.join(TMP, 'ic2_v050_ocr_tmp.png')
    cmd = ['convert', path] + (['-crop', crop] if crop else []) + ['-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp]
    subprocess.run(cmd, check=True)
    return subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout
