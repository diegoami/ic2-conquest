"""Private original-game probes. Immutable outputs; never delete a measured save."""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runs/experiments/battles'))
for key in ('IC2_WORK', 'DISPLAY_IC2'):
    if not os.environ.get(key):
        raise SystemExit(f'Set a private {key} before importing probe_common')
if os.environ['DISPLAY_IC2'] in (':99', ':453'):
    raise SystemExit('Refusing a shared display')
import harness.driver as drv
from harness import environment
from state import sav
import stage

DATA = Path(__file__).resolve().parent
ART = ROOT / 'artifacts/run-exp-ai-oct16'
ART.mkdir(parents=True, exist_ok=True)
STAMP = time.strftime('%Y%m%d-%H%M%S') + f'-{os.getpid()}'
LOG = DATA / f'probe-{STAMP}.jsonl'
LOG.touch(exist_ok=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def log(event, **fields):
    record = dict(event=event, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **fields)
    with LOG.open('a') as out:
        out.write(json.dumps(record, default=str) + '\n')
        out.flush()
    print(json.dumps(record, default=str), flush=True)


def keep_bytes(name, content):
    path = ART / name
    with path.open('xb') as out:
        out.write(content)
    with (DATA / 'SAVES.sha256').open('a') as out:
        out.write(f'{sha(path)}  {path.name}\n')
    return path


def keep(path, name):
    return keep_bytes(name, Path(path).read_bytes())


def staged(source, tag, edit):
    b = bytearray(Path(source).read_bytes())
    old_len = len(b)
    edits = edit(b)
    assert len(b) == old_len
    parsed = sav.parse(b)
    path = keep_bytes(f'{tag}-{STAMP}.SAV', b)
    log('staged', source=str(source), source_sha256=sha(source), file=path.name,
        sha256=sha(path), edits=edits, turn=parsed['turn'])
    return path


def my_pids():
    result = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            if not (p / 'cmdline').read_bytes().startswith(b'Imperial Conquest'):
                continue
            env = (p / 'environ').read_bytes().split(b'\0')
            if f'WINEPREFIX={drv.PREFIX}'.encode() in env and f'DISPLAY={drv.DISPLAY}'.encode() in env:
                result.append(int(p.name))
        except (OSError, PermissionError):
            continue
    return result


class PrivateGame(drv.Game):
    def ensure_xvfb(self):
        check = subprocess.run(['xdpyinfo', '-display', drv.DISPLAY], capture_output=True)
        if check.returncode == 0:
            return
        subprocess.Popen(['Xvfb', drv.DISPLAY, '-screen', '0', '1280x1024x24', '-nolisten', 'tcp'],
                         start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['xdpyinfo', '-display', drv.DISPLAY], capture_output=True, check=True)

    def start(self):
        self.ensure_xvfb()
        self.kill()  # wineserver is confined to this private WINEPREFIX
        subprocess.Popen(['setsid', drv.WINE, self.exe], cwd=drv.G, env=drv.ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows('^Imperial Conquest 2$'), 60, 'main window')
        time.sleep(3)
        pids = my_pids()
        if len(pids) != 1:
            raise drv.DriverError(f'Expected one private game process, got {pids}')
        self.pid = pids[0]


def snapshot(g):
    cities = []
    raw = g.mem(0x479590, 334 * 34)
    for i in range(334):
        r = raw[i * 34:(i + 1) * 34]
        fields = struct.unpack_from('<10h', r, 14)
        cities.append(dict(id=i, name=sav.cstr(r[:14]), **dict(zip(
            ('x','y','owner','allegiance','loyalty','supplies','fort','pop','max_pop','tribute'), fields))))
    return dict(turn=g.turn_number(), current=g.i16(drv.CUR_NATION),
                seed=struct.unpack('<I', g.mem(drv.RAND_SEED, 4))[0],
                armies=[sav.parse_army(g.army_rec(i), i) for i in range(g.i16(0x4A0324))],
                fleets=[dict(id=i, **dict(zip(
                    ('x','y','dest_x','dest_y','owner','countdown','moves','supplies','money','ships','condition','army','cell'),
                    struct.unpack('<13h', g.fleet_rec(i))))) for i in range(g.i16(0x4A0326))],
                cities=cities,
                nations=[sav.parse_nation(g.mem(drv.NATIONS + i * drv.NATION_LEN, drv.NATION_LEN), i) for i in range(16)])


environment.add_sink(lambda r: log('environment', record=r), key='oct16')
