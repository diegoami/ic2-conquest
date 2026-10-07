#!/usr/bin/env python3
"""Probe: why does clicking OK not close the Supply army dialog? One interaction at a time, the window state
read after each (click / windowactivate+click / Return / space), every step printed to a tracked log (rule 6).
Read-only on the game state apart from the probe's own clicks/keys (fixture load + dialog open + close attempts).
usage: probe_close.py > ../data/run-exp-cosmetic-gaps/probe_close_b5.txt 2>&1"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenarios as S
import cg, eog
from play_lib import start_game, new_rec, finish, CTX
from eog import _drv
import subprocess

def wins(g):
    return [(w[0], w[1], w[4], w[5]) for w in g.find_windows('^Supply army$')]

rec = new_rec('PROBE', 'close-probe', 12345, 'why does OK not close the Supply army dialog (b5)')
rec['tag'] = 'CG_CLOSE_PROBE_b5'
g = start_game(12345)
try:
    S.load_fixture(g, rec, S.FIX_START, 'start')
    S.army_button(g, 0, 'supply')
    wid, seen = S.wait_supply_dialog(g)
    print('dialog:', wid, 'seen meanwhile:', seen, flush=True)
    time.sleep(1.5)
    cs = S.read_controls_retry(g)
    ok = [c for c in cs if c['cls'] == 'TButton' and c['text'] == 'OK'][0]
    x, y = ok['x'] + ok['w'] // 2, ok['y'] + ok['h'] // 2
    print('OK centre', x, y, 'line', ok['line'], flush=True)

    print('--- a) plain click, then poll 5 s', flush=True)
    _drv.sh('xdotool', 'mousemove', str(x), str(y)); time.sleep(0.3)
    _drv.sh('xdotool', 'click', '1')
    for k in range(10):
        time.sleep(0.5)
        w = wins(g)
        if not w: print('CLOSED after plain click at t+%.1fs' % ((k + 1) * 0.5), flush=True); raise SystemExit
    print('still open:', w, flush=True)

    print('--- b) windowactivate --sync, click again, poll 5 s', flush=True)
    _drv.sh('xdotool', 'windowactivate', '--sync', str(wid[0])); time.sleep(1.0)
    _drv.sh('xdotool', 'click', '1')
    for k in range(10):
        time.sleep(0.5)
        w = wins(g)
        if not w: print('CLOSED after activate+click at t+%.1fs' % ((k + 1) * 0.5), flush=True); raise SystemExit
    print('still open:', w, flush=True)

    print('--- c) key Return, poll 5 s', flush=True)
    _drv.sh('xdotool', 'key', '--window', str(wid[0]), 'Return')
    for k in range(10):
        time.sleep(0.5)
        w = wins(g)
        if not w: print('CLOSED after Return at t+%.1fs' % ((k + 1) * 0.5), flush=True); raise SystemExit
    print('still open:', w, flush=True)

    print('--- d) key space, poll 5 s', flush=True)
    _drv.sh('xdotool', 'key', '--window', str(wid[0]), 'space')
    for k in range(10):
        time.sleep(0.5)
        w = wins(g)
        if not w: print('CLOSED after space at t+%.1fs' % ((k + 1) * 0.5), flush=True); raise SystemExit
    print('still open after everything:', w, flush=True)
    eog.snap(g, 'CG_CLOSE_PROBE_b5_still_open.png')
finally:
    finish(rec, g, 'close-probe')
