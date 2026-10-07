#!/usr/bin/env python3
"""Probe: how long after its OK click does the Supply army dialog close? (review R5: the first probe clicked through raw
xdotool; this one goes through the verified runner - every click carries its win_state line, pointer read-back and target -
keeps a screenshot of the measured dialog, and writes its log as a tracked, versioned output itself.) The measured claim in
the finding is the disappearance time after the click; the first probe's output (probe_close_b5.txt) is retained unchanged.
usage: probe_close.py"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenarios as S
import cg, eog
from play_lib import start_game, new_rec, finish, CTX, CLICKS, KEYS, VERIFIED, step_begin, note_step, read_controls, snap
from eog import _drv
from common import write_new, DATA

def run_probe():
    rec = new_rec('PROBE2', 'close-probe2', 12345, 'how long after the OK click does the Supply army dialog close (verified clicks)')
    rec['tag'] = 'CG_CLOSE_PROBE2'
    g = start_game(12345)
    try:
        S.load_fixture(g, rec, S.FIX_START, 'start')
        S.army_button(g, 0, 'supply')
        wid, seen = S.wait_supply_dialog(g)
        rec['dialog'] = {'wid': wid[0], 'geo': [wid[2], wid[3], wid[4], wid[5]], 'windows_seen': {str(k): v for k, v in seen.items()}}
        cs = S.read_controls_retry(g)
        ok = [c for c in cs if c['cls'] == 'TButton' and c['text'] == 'OK'][0]
        rec['ok_control'] = ok['line']
        snap(g, 'CG_CLOSE_PROBE2_dialog_open.png')
        t0 = time.time()
        CTX['why'] = 'close the Supply army dialog with its own OK control (fresh win_state read)'
        CTX['target'] = {'src': 'win_state', 'window': 'Supply army', 'line': ok['line'], 'cls': 'TButton', 'x': ok['x'], 'y': ok['y'], 'w': ok['w'], 'h': ok['h']}
        g.click(ok['x'] + ok['w'] // 2, ok['y'] + ok['h'] // 2, pause=0.0)
        rec['click_at'] = t0
        closed = None
        while time.time() - t0 < 12:
            time.sleep(0.25)
            if not [w for w in g.find_windows('^Supply army$') if w[4] >= 200]:
                closed = time.time(); break
        rec['closed_at'] = closed
        rec['seconds_after_click'] = round(closed - t0, 2) if closed else None
        snap(g, 'CG_CLOSE_PROBE2_after_click.png')
        if closed is None:
            raise _drv.DriverError('the Supply army dialog did not close within 12 s of the OK click')
        rec['status'] = 'ok'
        return rec
    except Exception as e:
        rec['status'] = 'FAILED'; rec['error'] = repr(e)
        try: snap(g, 'CG_CLOSE_PROBE2_failure.png')
        except Exception: pass
        raise
    finally:
        lines = ['close probe 2 (%s): dialog closed %s s after the OK click' % (rec['tag'], rec.get('seconds_after_click')),
                 'ok control line: %s' % rec.get('ok_control'),
                 'dialog: %r' % rec.get('dialog'), 'click at %.3f, closed at %s' % (rec.get('click_at', 0), rec.get('closed_at'))]
        print(write_new(os.path.join(DATA, 'probe_close2.txt'), '\n'.join(lines) + '\n'))
        finish(rec, g, 'close-probe2')

if __name__ == '__main__':
    run_probe()
