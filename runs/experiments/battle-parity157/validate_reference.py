"""Strict fresh recorder identity against preserved golden files, not rebasing."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
ART = ROOT / 'artifacts/run-exp-battle-parity157'
p = argparse.ArgumentParser()
p.add_argument('label')
a = p.parse_args()
run = DATA / a.label
ref = ART / 'reference-v1/battles/hook'
result = json.loads((run / 'result.json').read_text())
hook_path = run / 'hook-after-writeback.json'
if not hook_path.exists():
    hook_path = run / 'hook.json'
hook = json.loads(hook_path.read_text())
fields = ['site', 'eax', 'seed_before', 'seed_after', 'result', 'counter', 'side', 'flag']
with (ref / 'hooklog-mix-rg_s1_r5_hook.csv').open() as f:
    old = [{k: int(r[k], 0) for k in fields} for r in csv.DictReader(f) if r['kind'] == 'random']
new = [{k: r[k] for k in fields} for r in hook['records'] if r['kind'] == 'random']
first = next((dict(index=i, baseline=o, fresh=n) for i, (o, n) in enumerate(zip(old, new)) if o != n), None)
saves = []
game = ART / 'public' / a.label / 'runtime/prefix/drive_c/IC2'
for i in range(1, 16):
    baseline = ref / f'mix-rg_s1_r5_hook_BATTLE{i:02d}.SAV'
    fresh = game / f'BATTLE{i:02d}.SAV'
    b, n = baseline.read_bytes(), fresh.read_bytes() if fresh.exists() else b''
    saves.append(dict(name=fresh.name, present=fresh.exists(), byte_equal=b == n,
                      baseline_sha256=hashlib.sha256(b).hexdigest(), fresh_sha256=hashlib.sha256(n).hexdigest()))
ctl = hook['control']
report = dict(label=a.label, reference_revision='6319802a75067e7730e4f6a27dce3b4e296ddd9b',
              baseline_draws=len(old), fresh_draws=len(new), first_draw_difference=first,
              draws_equal=old == new, saves=saves,
              capture_clean=ctl['magic_ok'] and not any(ctl[k] for k in ['overflow', 'reentered', 'busy', 'truncated_reader'])
                  and not hook['chain_breaks'] and not hook['result_misses'],
              collector_complete=result['complete'])
report['pass'] = report['draws_equal'] and all(s['byte_equal'] for s in saves) and report['capture_clean']
with (DATA / (a.label + '-validation.json')).open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(json.dumps({k: v for k, v in report.items() if k != 'saves'}))
raise SystemExit(0 if report['pass'] else 1)
