"""Bounded unchanged-original replay with read-only pre-click runtime capture.

Uses immutable resupply31 inputs and preserves fresh saves under unique names.
No source save or executable is edited. Wine results are not native Windows.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--work', type=Path, required=True)
p.add_argument('--display', default=':732')
p.add_argument('stem')
a = p.parse_args()
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'runs/experiments/data/run-exp-resupply33'
ART = ROOT.parent / 'artifacts'
OLD = ROOT.parent.parent / 'resupply31/artifacts'
ART.mkdir(exist_ok=True)
sys.dont_write_bytecode = True
os.environ.update(IC2_WORK=str(a.work), DISPLAY_IC2=a.display)
sys.path.insert(0, str(ROOT))
from harness import driver as drv
from harness import environment
from state import sav

stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{os.getpid()}'
logfile = DATA / f'replay-{stamp}.jsonl'
logfile.touch(exist_ok=False)


def log(event, **fields):
    with logfile.open('a') as out:
        out.write(json.dumps(dict(event=event, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **fields)) + '\n')
    if event != 'driver':
        print(event, fields.get('summary', ''), flush=True)


def keep(kind, raw):
    name = a.stem + '-replay-' + stamp + '-' + kind + '.SAV'
    with (ART / name).open('xb') as out:
        out.write(raw)
    digest = hashlib.sha256(raw).hexdigest()
    with (DATA / 'SAVES.sha256').open('a') as out:
        out.write(f'{digest}  {name}\n')
    return name, digest


class PrivateGame(drv.Game):
    def ensure_xvfb(self):
        if subprocess.run(['xdpyinfo', '-display', drv.DISPLAY], capture_output=True).returncode:
            child = subprocess.Popen(['Xvfb', drv.DISPLAY, '-screen', '0', '1280x1024x24', '-nolisten', 'tcp'],
                                     start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log('display_started', pid=child.pid, display=drv.DISPLAY)
            time.sleep(2)
        subprocess.run(['xdpyinfo', '-display', drv.DISPLAY], capture_output=True, check=True)

    def start(self):
        self.ensure_xvfb()
        self.kill()
        subprocess.Popen(['setsid', drv.WINE, self.exe], cwd=drv.G, env=drv.ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows('^Imperial Conquest 2$'), 60, 'main window')
        time.sleep(3)
        pids = []
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():
                continue
            try:
                if not (proc / 'cmdline').read_bytes().startswith(b'Imperial Conquest'):
                    continue
                env = (proc / 'environ').read_bytes().split(b'\0')
                if f'WINEPREFIX={drv.PREFIX}'.encode() in env and f'DISPLAY={drv.DISPLAY}'.encode() in env:
                    pids.append(int(proc.name))
            except (OSError, PermissionError):
                pass
        assert len(pids) == 1, pids
        self.pid = pids[0]

    def tool(self, name, pause=1.0):
        if name != 'end_turn':
            return super().tool(name, pause)
        if not self.toolbar_x:
            self.calibrate_toolbar()
        self.reset_ui()
        x, y = self.toolbar_x.get(name, drv.TOOLBAR[name]), drv.TOOLBAR_Y
        drv.sh('xdotool', 'mousemove', str(x), str(y))
        time.sleep(0.25)
        regions = [(0x478fb0, 200, 'unit_stats'), (0x4794e8, 64, 'regions'), (0x479528, 24, 'coasts')]
        runtime = dict(provenance='Read-only live Wine memory immediately before End-turn click; not an AI-phase-entry observation.',
                       seed=struct.unpack('<I', self.mem(0x45e030, 4))[0],
                       globals_address='0x4a031c', globals_hex=self.mem(0x4a031c, 40).hex(),
                       current_nation=self.i16(0x4a0320),
                       treasuries=[struct.unpack('<i', self.mem(0x474aa8 + i * 1172, 4))[0] for i in range(16)],
                       runtime_tables=[dict(name=label, address=hex(address), hex=self.mem(address, size).hex())
                                       for address, size, label in regions])
        runtime_name = f'runtime-preclick-{stamp}.json'
        with (DATA / runtime_name).open('x') as out:
            json.dump(runtime, out, indent=2)
            out.write('\n')
        log('runtime_preclick', file=runtime_name, seed=runtime['seed'], current=runtime['current_nation'])
        drv.sh('xdotool', 'click', '1')
        time.sleep(pause)


source = OLD / (a.stem + '-input.SAV')
expected_loaded = (OLD / (a.stem + '-loaded.SAV')).read_bytes()
expected_post = (OLD / (a.stem + '-post.SAV')).read_bytes()
assert hashlib.sha256((drv.G / drv.EXE).read_bytes()).hexdigest() == '354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
log('provenance', source=source.name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    expected_loaded_sha256=hashlib.sha256(expected_loaded).hexdigest(),
    expected_post_sha256=hashlib.sha256(expected_post).hexdigest(), work=str(a.work), display=a.display)
environment.add_sink(lambda record: log('environment', record=record), key='resupply33')
g = PrivateGame(log=lambda message: log('driver', message=message))
try:
    g.load(source, seed=12345)
    loaded = g.save_as(f'r33_{os.getpid()}_loaded.SAV').read_bytes()
    name, digest = keep('loaded', loaded)
    actual, expected = sav.parse(loaded), sav.parse(expected_loaded)
    assert all(actual[k] == expected[k] for k in ('cities', 'armies', 'fleets', 'nations', 'map', 'turn_order'))
    log('loaded', file=name, sha256=digest, whole_save_identical=loaded == expected_loaded)
    auto, texts = g.end_turn(timeout=180, reclick=False)
    auto_name, auto_hash = keep('auto', (drv.G / auto).read_bytes())
    post = g.save_as(f'r33_{os.getpid()}_post.SAV').read_bytes()
    name, digest = keep('post', post)
    log('post', file=name, sha256=digest, auto=auto_name, auto_sha256=auto_hash,
        whole_save_identical=post == expected_post, texts=texts,
        summary=dict(treasury=sav.parse(post)['nations'][0]['treasury']))
    assert post == expected_post, 'Fresh whole post save differs; retain for investigation'
except BaseException as exc:
    log('failure', exception=repr(exc))
    raise
finally:
    g.kill()
