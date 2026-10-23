"""Declared 12-case synthetic pilot, real original then native controls.

Every input/output has a unique name. Resume completed work; never delete or
overwrite a save/measurement. Review failures before supplying another label.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runs/experiments/battles'))
import stage
from state import sav

DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
ART = ROOT / 'artifacts/run-exp-battle-parity157'
REF = ART / 'reference-v1/battles/starts/FLD-RG_0743_rome_army0_at_86_28.SAV'
MIX = ['hi', 'li', 'ar']
# label, attacker types, defender types, quality, army morale, nation pair
CASES = [
    ('P01-hi-duel', ['hi'], ['hi'], 6, 70, (0, 6)),
    ('P02-li-duel', ['li'], ['li'], 6, 70, (0, 6)),
    ('P03-ranged', ['ar'], ['hi'], 6, 70, (0, 6)),
    ('P04-heavy-cavalry-ps', ['hc'], ['li'], 6, 70, (3, 2)),
    ('P05-light-cavalry-cn', ['lc'], ['ar'], 6, 70, (1, 5)),
    ('P06-mixed', MIX, MIX, 6, 70, (0, 6)),
    ('P07-permuted', ['ar', 'hi', 'li'], MIX, 6, 70, (0, 6)),
    ('P08-quality4', MIX, MIX, 4, 70, (0, 6)),
    ('P09-quality9', MIX, MIX, 9, 70, (0, 6)),
    ('P10-morale50', MIX, MIX, 6, 50, (0, 6)),
    ('P11-morale90', MIX, MIX, 6, 90, (0, 6)),
    ('P12-mixed-ps', ['lc', 'hi', 'ar'], ['hi', 'ar', 'li'], 6, 70, (3, 2)),
]

def prepare():
    out = ART / 'pilot-inputs-v1'
    out.mkdir(exist_ok=False)
    rows = []
    for label, attack, defend, quality, morale, nations in CASES:
        raw = bytearray(REF.read_bytes())
        for index, types, nation in [(0, attack, nations[0]), (10, defend, nations[1])]:
            # Each type gets a standard battalion; stable names survive permutations.
            stage.set_units(raw, index, [(t, stage.STD[t], quality, 0, 'Pilot ' + t.upper()) for t in types])
            stage.set_army_field(raw, index, 'morale', morale)
            stage.set_army_field(raw, index, 'moves', 8)
            stage.set_army_field(raw, index, 'supplies', 2000)
            stage.set_army_field(raw, index, 'money', 2000)
            stage.set_army_field(raw, index, 'owner', nation)
            state = sav.parse(raw)
            army = state['armies'][index]
            size = 200 if army['troops'] < 25000 else 216 if army['troops'] < 50000 else 232
            struct.pack_into('<h', raw, 2 * (army['x'] * 140 + army['y']), size + nation)
        stage.set_relation(raw, *nations, 3)
        for n in range(16):
            raw[stage._nation(raw, n) + 0x490] = int(n == nations[0])
        state = sav.parse(raw)
        tail = state['tail_off']
        struct.pack_into('<2h', raw, tail + 36, nations[0], state['turn_order'].index(nations[0]))
        path = out / (label + '.SAV')
        with path.open('xb') as f:
            f.write(raw)
        check = sav.parse(raw)
        assert check['current_nation'] == nations[0] and not check['battle_flag']
        assert check['armies'][0]['owner'] == nations[0] and check['armies'][10]['owner'] == nations[1]
        rows.append(dict(label=label, attacker=attack, defender=defend, quality=quality, army_morale=morale,
                         nations=list(nations), seed=1, source_turn=check['turn'], filename=path.name,
                         sha256=hashlib.sha256(raw).hexdigest(), synthetic=True))
    with (DATA / 'pilot-manifest-v1.json').open('x') as f:
        json.dump(dict(cases=rows, scope='Synthetic strategic edits; actual original copy-in/placement, then matched native entry. Not a fresh new-game or conversion-export test.'), f, indent=2)
        f.write('\n')

def execute(labels):
    for label, *_ in CASES:
        if labels and label not in labels:
            continue
        folder = DATA / label
        result = folder / 'result.json'
        if not result.exists():
            args = [sys.executable, str(Path(__file__).with_name('original.py')), '--label', label,
                    '--input', str(ART / 'pilot-inputs-v1' / (label + '.SAV')),
                    '--exe', str(ART / 'observer-v1.exe'), '--attacker', '0', '--defender', '10',
                    '--observer', '--protocol', 'cg-only']
            receipt = DATA / (label + '-execution-v1.json')
            if receipt.exists():
                raise RuntimeError('Previous failed execution needs review: ' + label)
            r = subprocess.run(args, capture_output=True, text=True)
            with receipt.open('x') as f:
                json.dump(dict(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr), f, indent=2)
                f.write('\n')
            print(label, 'original', r.returncode, flush=True)
        else:
            print(label, 'resume retained original', flush=True)
        if not result.exists() or not json.loads(result.read_text())['complete']:
            print(label, 'failed; retained for review', flush=True)
            continue
        native = folder / 'native-decisions-v1.json'
        if native.exists():
            continue
        args = ['/home/diego/.dotnet/dotnet', str(ART / 'native-build-v6/bin/DecisionProbe/debug/DecisionProbe.dll'),
                str(folder / 'states.json'), '/home/diego/projects/imperial_conquest_2', str(native), str(result)]
        r = subprocess.run(args, capture_output=True, text=True)
        with (DATA / (label + '-native-execution-v1.json')).open('x') as f:
            json.dump(dict(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr), f, indent=2)
            f.write('\n')
        print(label, 'native', r.returncode, flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['prepare', 'run'])
    p.add_argument('labels', nargs='*')
    args = p.parse_args()
    prepare() if args.action == 'prepare' else execute(args.labels)
