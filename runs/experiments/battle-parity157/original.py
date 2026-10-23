"""Versioned original battle collector. Owner traces stay private.

Uses a fresh copied runtime, no live-memory writes, no repeated End clicks.
Never overwrite/delete any save or output. Logs survive failed runs.
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument('--label', required=True)
p.add_argument('--input', type=Path, required=True)
p.add_argument('--exe', type=Path, required=True)
p.add_argument('--attacker', type=int, required=True)
p.add_argument('--defender', type=int, required=True)
p.add_argument('--observer', action='store_true')
p.add_argument('--protocol', choices=['cg-only', 'cg-end'], default='cg-end')
p.add_argument('--private', action='store_true')
p.add_argument('--display', default=':757')
p.add_argument('--screen', default='1280x1024')
p.add_argument('--waypoint', help='One explicit approach cell X,Y before attacking')
a = p.parse_args()
assert a.label.replace('-', '').replace('_', '').isalnum()
BASE = ROOT / 'artifacts/run-exp-battle-parity157'
OUT = BASE / ('private' if a.private else 'public') / a.label
OUT.mkdir(parents=True, exist_ok=False)
WORK = OUT / 'runtime'
SOURCE = Path('/home/diego/ic2-work')
shutil.copytree(SOURCE / 'prefix', WORK / 'prefix', symlinks=True,
                ignore=lambda d, n: ['IC2'] if Path(d) == SOURCE / 'prefix/drive_c' else [])
GAME = WORK / 'prefix/drive_c/IC2'
GAME.mkdir()
for path in (SOURCE / 'prefix/drive_c/IC2').iterdir():
    if path.is_file() and path.suffix.lower() in {'.dat', '.hlp', '.cnt', '.ini', '.dll', '.bmp'}:
        shutil.copy2(path, GAME / path.name)
    if path.name.upper() == 'WAVS':
        shutil.copytree(path, GAME / path.name)
for path in SOURCE.iterdir():
    if path.name in {'win_controls.exe', 'win_slider.exe', 'toolbar.json', 'army_toolbar.json', 'battle_toolbar.json'}:
        shutil.copy2(path, WORK / path.name)
EXE = 'Imperial Conquest 2 parity.exe'
shutil.copy2(a.exe, GAME / EXE)
shutil.copy2(a.input, GAME / 'INPUT.SAV')
os.environ['IC2_WORK'] = str(WORK)
os.environ['DISPLAY_IC2'] = a.display
sys.path.insert(0, str(ROOT))
from harness import driver as D, environment
from state import hook_log as L, sav
if a.observer:
    sys.path.insert(0, str(ROOT / 'runs/experiments/tactical25-trace'))
    import observer as O
    O.configure()
    L.BUF = O.H.BUF

DATA = OUT if a.private else ROOT / 'runs/experiments/data/run-exp-battle-parity157' / a.label
DATA.mkdir(exist_ok=True)
environment.set_data_folder(DATA)

def write(name, value):
    with (DATA / name).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def log(message):
    with (DATA / 'driver.log').open('a') as f:
        f.write(str(message) + '\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PrivateGame(D.Game):
    def ensure_xvfb(self):
        if subprocess.run(['xdpyinfo', '-display', D.DISPLAY], capture_output=True).returncode == 0:
            raise RuntimeError('Dedicated display already in use')
        self.xvfb = subprocess.Popen(['Xvfb', D.DISPLAY, '-screen', '0', a.screen + 'x24', '-nolisten', 'tcp'],
                                    start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['xdpyinfo', '-display', D.DISPLAY], capture_output=True, check=True)

    def start(self):
        self.ensure_xvfb()
        subprocess.Popen(['setsid', D.WINE, self.exe], cwd=D.G, env=D.ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows('^Imperial Conquest 2$'), 60, 'main window')
        time.sleep(3)
        mine = []
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():
                continue
            try:
                if ((path / 'cmdline').read_bytes().startswith(b'Imperial Conquest') and
                    ('WINEPREFIX=' + str(D.PREFIX)).encode() in (path / 'environ').read_bytes().split(b'\0')):
                    mine.append(int(path.name))
            except (OSError, PermissionError):
                pass
        assert len(mine) == 1, mine
        self.pid = mine[0]

    def show(self, x, y):
        w = self.find_windows('^Unit map$')[0]
        D.VIEW_COLS = max(1, (w[4] - 20) // 32)
        D.VIEW_ROWS = max(1, (w[5] - 70) // 32)
        D.UNIT_PAINT = (335 + w[2] - 333, 96 + w[3] - 75)
        return super().show(x, y)

g = PrivateGame(exe=EXE, log=log)
rec = dict(label=a.label, complete=False, protocol=a.protocol, observer=a.observer)
try:
    rec.update(exe_sha256=digest(GAME / EXE), input_sha256=digest(a.input), input_turn=sav.load(a.input)['turn'])
    g.start()
    rec['environment'] = g.environment
    rec['load_messages'] = g.open(GAME / 'INPUT.SAV', strict=False)
    attacker, defender = g.army_state(a.attacker), g.army_state(a.defender)
    if a.waypoint:
        x, y = map(int, a.waypoint.split(','))
        g.select_army(a.attacker, attacker['x'], attacker['y'])
        g.click_tile(x, y, pause=1)
        time.sleep(2)
        attacker = g.army_state(a.attacker)
        assert (attacker['x'], attacker['y']) == (x, y), 'Approach did not reach specified cell'
    assert max(abs(attacker['x'] - defender['x']), abs(attacker['y'] - defender['y'])) <= 1
    g.select_army(a.attacker, attacker['x'], attacker['y'])
    g.click_tile(defender['x'], defender['y'], pause=0)
    g.wait(lambda: g.in_battle() and g.find_windows(' v '), 45, 'battle opens')
    rec['entry'] = g.battle_state()
    rec['entry_seed'] = struct.unpack('<I', g.mem(D.RAND_SEED, 4))[0]
    rec['entry_flags'] = list(g.mem(0x45e6a4, 4))
    rec['entry_claims'] = list(struct.unpack('<40h', g.mem(0x45e6b0, 80)))
    write('entry.json', rec)
    g.calibrate_battle_toolbar()
    rec['toolbar'] = g.battle_x
    rec['commands'] = []
    g.click(g.battle_x['computer'], D.BATTLE_TOOLBAR_Y, pause=.1)
    rec['commands'].append(dict(command='computer', time=time.monotonic(), flags=list(g.mem(0x45e6a4, 4))))
    if a.protocol == 'cg-end' and g.in_battle() and not g.find_windows('Battle ended'):
        g.click(g.battle_x['end_turn'], D.BATTLE_TOOLBAR_Y, pause=.1)
        rec['commands'].append(dict(command='end', time=time.monotonic(), flags=list(g.mem(0x45e6a4, 4))))
    g.wait(lambda: g.find_windows('Battle ended'), 900, 'battle result', step=.5)
    rec['result_text'] = g.read_popup(g.find_windows('Battle ended')[0])
    # battle_state deliberately refuses a cleared flag: terminal slots remain readable.
    rec['terminal_slots_hex'] = g.mem(D.BATTLE_SLOTS, 2096).hex()
    rec['terminal_counter'] = g.i16(0x4a0b7a)
    rec['terminal_seed'] = struct.unpack('<I', g.mem(D.RAND_SEED, 4))[0]
    rec['terminal_flag'] = g.in_battle()
    g.shot(OUT / 'result.png')
    if a.observer:
        ctl, records = L.read_process(g.mem)
        write('hook.json', dict(control=ctl, records=records, chain_breaks=L.chain_check(records), result_misses=L.result_check(records)))
        overflow = struct.unpack('<I', g.mem(O.OVERFLOW, 4))[0]
        n = min(ctl['index'], O.STATE_CAP)
        raw = g.mem(O.STATE_BUF, n * O.STATE_REC)
        with (OUT / 'statebuf.bin').open('xb') as f:
            f.write(raw)
        snapshots = [O.decode_snapshot(raw[r['seq'] * O.STATE_REC:(r['seq'] + 1) * O.STATE_REC], r)
                     for r in records if r['counter'] <= 6 and r['seq'] < O.STATE_CAP]
        write('states.json', dict(overflow=overflow, records=snapshots))
        assert not overflow and ctl['magic_ok']
        assert not any(ctl[k] for k in ['overflow', 'reentered', 'busy', 'truncated_reader'])
        assert not L.chain_check(records) and not L.result_check(records)
    cs = g.controls('Battle ended')
    g.click_control(g.control(cs, text='OK'), pause=1.5)
    if g.find_windows('^Offer of peace$'):
        g.answer_battle_peace(False)
    g.dismiss_popups(strict=False)
    final = g.save_as(a.label + '-AFTER.SAV')
    shutil.copy2(final, OUT / final.name)
    rec['final_save'] = dict(name=final.name, sha256=digest(final))
    if a.observer:
        ctl, records = L.read_process(g.mem)
        write('hook-after-writeback.json', dict(control=ctl, records=records,
              chain_breaks=L.chain_check(records), result_misses=L.result_check(records)))
        assert not any(ctl[k] for k in ['overflow', 'reentered', 'busy', 'truncated_reader'])
        assert ctl['magic_ok'] and not L.chain_check(records) and not L.result_check(records)
    g.kill()
    # Restart on the existing display without creating another X server.
    g.ensure_xvfb = lambda: None
    g.start()
    rec['reopen_messages'] = g.open(final, strict=False)
    again = g.save_as(a.label + '-REOPEN.SAV')
    shutil.copy2(again, OUT / again.name)
    rec['reopen_save'] = dict(name=again.name, sha256=digest(again), byte_equal=final.read_bytes() == again.read_bytes())
    assert rec['reopen_save']['byte_equal']
    rec['complete'] = True
except BaseException:
    rec['error'] = traceback.format_exc()
    print(rec['error'], flush=True)
    try:
        g.shot(OUT / 'failure.png')
    except Exception:
        pass
finally:
    g.kill()
    if hasattr(g, 'xvfb'):
        g.xvfb.terminate()
        g.xvfb.wait(timeout=10)
    rec['boundary_saves'] = [dict(name=s.name, sha256=digest(s)) for s in sorted(GAME.glob('BATTLE*.SAV'))]
    write('result.json', rec)
print(json.dumps(dict(label=a.label, complete=rec['complete'], counter=rec.get('terminal_counter'), error=bool(rec.get('error')))), flush=True)
sys.exit(0 if rec['complete'] else 1)
