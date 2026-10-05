"""Shared setup for the v0.5.0 rule-read plays: own display (:733), own IC2_WORK copy, screenshots to the gitignored artifacts
folder, tracked text logs; nothing is overwritten (rule 6). Import before harness.driver."""
import os, sys, time, subprocess, hashlib, glob, struct, shutil
from paths import ROOT, ART, DATA, TMP
WORKDIR = os.environ.get('IC2_WORK_SPLIT', os.path.expanduser('~/ic2-work-split'))
DISP = ':734'
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
    if not os.path.exists('/tmp/.X11-unix/X734'):
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
    tmp = os.path.join(TMP, 'ic2_split_ocr_tmp.png')
    cmd = ['convert', path] + (['-crop', crop] if crop else []) + ['-resize', '%d00%%' % scale, '-colorspace', 'Gray', tmp]
    subprocess.run(cmd, check=True)
    return subprocess.run(['tesseract', tmp, 'stdout', '--psm', '6'], capture_output=True, text=True).stdout

def _screen_words(g, region):
    """OCR words (text, centre x, centre y in screen px) of a screen region (x, y, w, h) of a fresh screenshot (tesseract tsv)."""
    x, y, w, h = region
    full = os.path.join(TMP, 'ic2_split_screen.png'); crop = os.path.join(TMP, 'ic2_split_crop.png')
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

def menu_step(g, click_word, expect_words, tries=3):
    """One calibrated menu transition: find `click_word` in the OCR of the menu region, click its centre, then verify that every word of `expect_words` is
    in the region afterwards (the next menu level). The click is repeated at most twice (3 attempts in all); DriverError if the transition never shows."""
    for attempt in range(tries):
        hit = [w for w in _screen_words(g, MENU_REGION) if w[0] == click_word]
        if hit:
            g.click(hit[0][1], hit[0][2], pause=1.0)
            seen = {w[0] for w in _screen_words(g, MENU_REGION)}
            if all(e in seen for e in expect_words): return True
    raise _drv.DriverError('menu transition %r -> %r did not show after %d attempts' % (click_word, expect_words, tries))

def split_army_via_menu(g, tries=3):
    """Unit map > Army > Split army by the menu (the fleet-selected route: the army toolbar is not shown while a fleet is selected). Every transition is
    verified: the top menu by the words army/fleet/city, the submenu by split/disband, the dialog by its window. At most two retries per transition."""
    for attempt in range(tries):
        g.reset_ui()
        bar = [w for w in _screen_words(g, (0, 26, 650, 24)) if w[0] == 'unit']           # the menu bar, found by OCR (not a fixed point)
        if not bar: continue
        g.click(bar[0][1], bar[0][2], pause=1.0)
        if {'army', 'fleet', 'city'} <= {w[0] for w in _screen_words(g, MENU_REGION)}: break
    else: raise _drv.DriverError('the Unit map menu did not open after %d attempts (menu bar OCR + verification)' % tries)
    menu_step(g, 'army', ['split', 'disband'])
    for attempt in range(tries):
        hit = [w for w in _screen_words(g, MENU_REGION) if w[0] == 'split']
        if hit:
            g.click(hit[0][1], hit[0][2], pause=2.0)
            if g.find_windows('^Split army$'): return True
    raise _drv.DriverError('Split army did not open the Split army dialog after %d attempts' % tries)

def embark_verified(g, army, fleet, tries=3):
    """Embark `army` on `fleet` (Game.embark) and verify it in memory: the fleet's carried-army field is the army's index. The click is repeated only
    while nothing changed, at most twice (3 attempts in all); DriverError otherwise. Returns the popup texts seen."""
    texts = []
    for attempt in range(tries):
        if g.fleet_state(fleet)['army'] == army: return texts
        texts += g.embark(army, fleet) or []
        log('split', 'embark attempt %d: fleet %d carries %d, army %d embarked %s' % (attempt + 1, fleet, g.fleet_state(fleet)['army'], army, g.army_state(army)['embarked']))
        if g.fleet_state(fleet)['army'] == army: return texts
    raise _drv.DriverError('embark of army %d on fleet %d not seen in memory after %d attempts' % (army, fleet, tries))

def _region_hash(g, c):
    """SHA-256 of the raw pixels of a control's rectangle on a fresh screenshot (to see whether a click changed it)."""
    full = os.path.join(TMP, 'ic2_split_screen.png')
    _orig_sh('import', '-window', 'root', full)
    px = subprocess.run(['convert', full, '-crop', '%dx%d+%d+%d' % (c['w'], c['h'], c['x'], c['y']), '+repage', 'rgb:-'], capture_output=True, check=True).stdout
    return hashlib.sha256(px).hexdigest()

def transfer_first_unit(g, cs, tries=3):
    """In the open Split army dialog, select the first unit of the left list and press Transfer, each step verified on the screen: the selection by a change
    of the left list's pixels (the highlight), the transfer by a change of both lists and OCR text appearing in the right (new army's) list. Each click is
    repeated at most twice; DriverError otherwise. Returns the OCR words of the right list."""
    left = g.control(cs, cls='TListBox', index=0); right = g.control(cs, cls='TListBox', index=1)
    transfer = sorted((c for c in cs if c['text'] == 'Transfer'), key=lambda c: c['x'])[0]
    words = lambda c: [w[0] for w in _screen_words(g, (c['x'], c['y'], c['w'], c['h']))]
    r0 = words(right)
    if r0: raise _drv.DriverError('the right list is not empty before the transfer: %s' % r0)
    for attempt in range(tries):
        h0 = _region_hash(g, left)
        g.click(left['x'] + left['w'] // 2, left['y'] + 12, pause=0.4)
        if _region_hash(g, left) != h0: break
        log('split', 'unit selection attempt %d: the left list did not change' % (attempt + 1))
    else: raise _drv.DriverError('selecting the first unit did not change the left list after %d attempts' % tries)
    log('split', 'unit selected (left list changed, attempt %d)' % (attempt + 1))
    for attempt in range(tries):
        hl, hr = _region_hash(g, left), _region_hash(g, right)
        g.click_control(transfer, pause=0.6)
        r1 = words(right)
        if r1 and _region_hash(g, right) != hr and _region_hash(g, left) != hl:
            log('split', 'transfer verified (attempt %d): right list now reads %s' % (attempt + 1, r1)); return r1
        log('split', 'transfer attempt %d: no change seen (right list %s)' % (attempt + 1, r1))
    raise _drv.DriverError('Transfer did not move a unit to the right list after %d attempts' % tries)
