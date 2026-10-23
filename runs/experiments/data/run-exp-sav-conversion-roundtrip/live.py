"""Bounded real-original open/order/save/reopen, never replaces a save.

Use --seed-build for the instrumented original's one-turn path; default is the
unmodified executable and a tax order, so acceptance is not inferred from hooks.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'artifacts/run-exp-sav-conversion-roundtrip'
os.environ['IC2_WORK'] = str(ART / 'runtime')
os.environ['DISPLAY_IC2'] = ':151'
sys.path.insert(0, str(ROOT))
from harness.driver import Game, G, ENV, CUR_NATION  # noqa: E402
from harness import environment  # noqa: E402
from state import sav  # noqa: E402

environment.set_data_folder(HERE)
parser = argparse.ArgumentParser()
parser.add_argument('scenario')
parser.add_argument('case')
parser.add_argument('--seed-build', action='store_true')
parser.add_argument('--attempt', default='v1')
args = parser.parse_args()
name = f'live-{args.scenario}-{args.attempt}'
receipt = HERE / (name + '.json')
logpath = HERE / (name + '.txt')
if receipt.exists() or logpath.exists():
    raise SystemExit('Attempt already measured: use another --attempt')
result = {'scenario': args.scenario, 'case': args.case, 'attempt': args.attempt,
          'exe': 'Imperial Conquest 2 fast rollingsave seed.exe' if args.seed_build else 'Imperial Conquest 2.exe',
          'steps': [], 'complete': False, 'runtime': 'Wine/Xvfb, not native Windows'}
out = ART / name
out.mkdir()
display_process = None
game = None

def log(message):
    with logpath.open('a') as f:
        f.write(str(message) + '\n')
    print(str(message), flush=True)

def persist():
    # Append-only progress; final receipt written exactly once in finally.
    with (HERE / (name + '-progress.jsonl')).open('a') as f:
        f.write(json.dumps(result) + '\n')

def archive(path, label):
    dest = out / path.name
    if dest.exists():
        raise RuntimeError('Refusing to replace artifact ' + str(dest))
    shutil.copy2(path, dest)
    state = sav.load(dest)
    meta = {'label': label, 'file': str(dest.relative_to(ART)),
            'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'bytes': dest.stat().st_size,
            'turn': state['turn'], 'current_nation': state['current_nation'],
            'army_count': len(state['armies']), 'fleet_count': len(state['fleets']),
            'tax': state['nations'][state['current_nation']]['tax']}
    result['steps'].append(meta)
    persist()
    return dest

def screenshot(label):
    path = out / (label + '.png')
    p = subprocess.run(['import', '-display', ':151', '-window', 'root', str(path)], capture_output=True, text=True)
    result.setdefault('screenshots', []).append({'file': str(path.relative_to(ART)), 'returncode': p.returncode, 'stderr': p.stderr})

class IsolatedGame(Game):
    def ensure_xvfb(self):
        global display_process
        probe = subprocess.run(['xdpyinfo', '-display', ':151'], capture_output=True)
        if probe.returncode:
            display_process = subprocess.Popen(['Xvfb', ':151', '-screen', '0', '1280x1024x24'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            time.sleep(2)
            if display_process.poll() is not None:
                raise RuntimeError('Private Xvfb failed to start')

try:
    source = ART / 'exports-v2' / (args.scenario + '.SAV')
    result['input'] = {'file': str(source.relative_to(ART)), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    game = IsolatedGame(exe=result['exe'], log=log)
    if args.seed_build:
        result['load_messages'] = game.load(source, seed=12345)
        result['seed_line'] = game.seed_line
    else:
        game.start()
        result['load_messages'] = game.open(source)
    result['loaded'] = game.loaded()
    result['calendar_loaded'] = game.calendar()
    result['environment'] = game.environment
    result['exe_sha256'] = hashlib.sha256((G / result['exe']).read_bytes()).hexdigest()
    screenshot('loaded')
    archive(game.save_as('P151' + args.case + 'I.SAV'), 'immediate-native-save')
    before = sav.load(source)
    me = game.i16(CUR_NATION)
    oldtax = before['nations'][me]['tax']
    newtax = 26 if oldtax != 26 else 24
    result['order'] = {'type': 'taxation', 'before': oldtax, 'requested': newtax,
                        'messages': game.taxation(newtax)}
    changed = archive(game.save_as('P151' + args.case + 'O.SAV'), 'after-tax-order')
    result['order']['verified'] = sav.load(changed)['nations'][me]['tax'] == newtax
    if not result['order']['verified']:
        raise RuntimeError('Tax order did not change the save')
    if args.seed_build:
        # Prefix starts without autosaves. Each invocation moves prior batches aside.
        game.supersede_autosaves()
        auto, messages = game.end_turn(timeout=180, reclick=False, strict_confirm=True)
        result['end_turn'] = {'autosave': auto, 'messages': messages, 'calendar': game.calendar()}
        archive(G / auto, 'autosave-after-one-turn')
        changed = archive(game.save_as('P151' + args.case + 'T.SAV'), 'after-one-turn')
    screenshot('after-order')
    # Restart actual process before opening the NEW original-written save.
    if args.seed_build:
        result['reopen_messages'] = game.load(changed, seed=12345)
    else:
        game.start()
        result['reopen_messages'] = game.open(changed)
    archive(game.save_as('P151' + args.case + 'R.SAV'), 'fresh-reopen-resave')
    screenshot('reopened')
    result['complete'] = True
except Exception as ex:
    result['error'] = {'type': type(ex).__name__, 'message': str(ex), 'traceback': traceback.format_exc()}
    log(result['error']['traceback'])
    try:
        screenshot('failure')
    except Exception:
        pass
finally:
    if game is not None:
        game.kill()
    if display_process is not None:
        display_process.terminate()
        display_process.wait(timeout=10)
    result['input_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == result['input']['sha256'] if 'input' in result else None
    with receipt.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    log('COMPLETE ' + str(result['complete']))
sys.exit(0 if result['complete'] else 1)
