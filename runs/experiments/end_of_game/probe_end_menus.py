#!/usr/bin/env python3
"""After a single-human game ends (staged unity 100 -> End of Game -> OK), which menus are usable? Screenshot of the File, Game and Strategy dropdowns (opened by
OCR, as menu_pick does) and the OCR of each dropdown window. Staged scenario; nothing here is natural play."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eog import *
from eog import _drv, _screen_words
batch = sys.argv[1] if len(sys.argv) > 1 else 'b8'
tag = 'EOGM_unity_%s' % batch
L = lambda m: log('menus_%s' % batch, m)
clear_autos()
staged = edit_save(fixture('run0-start-AUTO0720-seed12345.SAV'), SAVEDIR + 'inputs/%s_staged.SAV' % tag, [('unity', 0, 100)], tag)
g = MyGame(); g.load(staged, seed=12345)
press_end_turn_once(g)
w, texts = wait_window(g, r'^End of Game$', 300, 'End of Game')
capture_and_ok(g, tag, batch, 'unity_menus', 'window', L)
time.sleep(5); g.dismiss_popups()
ids = lambda: set(_drv.sh('xdotool', 'search', '--onlyvisible', '--name', '', check=False).split())
for word in ('file', 'game', 'strategy', 'nations'):
    g.reset_ui()
    bar = [w_ for w_ in _screen_words(g, (0, 26, 650, 24)) if w_[0] == word]
    if not bar: L('%s: not found in the menu bar' % word); continue
    before = ids(); g.click(bar[0][1], bar[0][2], pause=1.0)
    new = ids() - before
    pop = None
    for i in new:
        import re
        m = re.search(r'Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)', _drv.sh('xdotool', 'getwindowgeometry', i, check=False), re.S)
        if m: pop = tuple(int(x) for x in m.groups())
    p = new_path(ART + '%s_menu_%s.png' % (tag, word)); g.shot(p)
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    L('%s menu: dropdown window %s; words %s' % (word, pop, [w_[0] for w_ in _screen_words(g, pop)] if pop else None))
g.reset_ui()
L('alive %s title %s windows %s' % (proc_alive(g), main_title(g), all_windows(g)))
