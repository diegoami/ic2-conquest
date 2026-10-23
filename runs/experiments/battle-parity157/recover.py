"""Recover only the pinned observer reference case; never replace an input."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
DEST = ROOT / 'artifacts/run-exp-battle-parity157/reference-v1'
REV = '6319802a75067e7730e4f6a27dce3b4e296ddd9b'
REPO = 'diegoami/ic2-test-fixtures'

def api(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint]))

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=False)
    tree = api(f'repos/{REPO}/git/trees/{REV}?recursive=1')
    assert not tree['truncated']
    names = {'battles/hook/hooklog-mix-rg_s1_r5_hook.csv',
             'battles/starts/FLD-RG_0743_rome_army0_at_86_28.SAV'}
    names.update(f'battles/hook/mix-rg_s1_r5_hook_BATTLE{i:02d}.SAV' for i in range(1, 16))
    entries = {e['path']: e for e in tree['tree']}
    rows = []
    for name in sorted(names):
        e = entries[name]
        blob = api(f'repos/{REPO}/git/blobs/{e["sha"]}')
        assert blob['encoding'] == 'base64'
        raw = base64.b64decode(blob['content'])
        assert len(raw) == e['size']
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == e['sha']
        path = DEST / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(raw)
        rows.append(dict(path=name, bytes=len(raw), git_blob=e['sha'], sha256=hashlib.sha256(raw).hexdigest()))
        print('recovered', name, flush=True)
    with (DATA / 'reference-recovery-v1.json').open('x') as f:
        json.dump(dict(revision=REV, files=rows, scope='17 reference files; not the full 318-series corpus'), f, indent=2)
        f.write('\n')
