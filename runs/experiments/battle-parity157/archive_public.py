"""Archive explicit public reference assets only; never walk private/runtime trees."""
import hashlib
import json
import tarfile
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'artifacts/run-exp-battle-parity157'
DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
p = argparse.ArgumentParser()
p.add_argument('--name', default='reference-batch01.tar.gz')
p.add_argument('--labels', nargs='*', default=['reference-cgend-v1', 'reference-cgonly-v1', 'reference-cgonly-v2'])
a = p.parse_args()
name = a.name
assert Path(name).name == name and name.endswith('.tar.gz')
target = ART / name
assert not target.exists()
files = []
for label in a.labels:
    assert label.replace('-', '').isalnum()
    folder = ART / 'public' / label
    files.extend(folder.glob('*.SAV'))
    files.extend(folder.glob('*.png'))
    files.extend(folder.glob('*.bin'))
    files.extend((folder / 'runtime/prefix/drive_c/IC2').glob('BATTLE*.SAV'))
rows = []
with tarfile.open(target, 'x:gz') as tf:
    for path in sorted(files):
        assert 'private' not in path.parts and path.suffix.lower() in {'.sav', '.png', '.bin'}
        # Flatten only the unique label and basename; no runtime registry/config/EXE.
        label = path.relative_to(ART).parts[1]
        arcname = label + '/' + path.name
        tf.add(path, arcname=arcname, recursive=False)
        rows.append(dict(name=arcname, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for label in a.labels:
        path = ART / 'pilot-inputs-v1' / (label + '.SAV')
        if path.exists():
            arcname = 'synthetic-inputs/' + path.name
            tf.add(path, arcname=arcname, recursive=False)
            rows.append(dict(name=arcname, bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
with tarfile.open(target) as tf:
    members = tf.getmembers()
    assert len(members) == len(rows)
    for member, row in zip(members, rows, strict=True):
        assert member.name == row['name'] and member.isfile()
        assert hashlib.sha256(tf.extractfile(member).read()).hexdigest() == row['sha256']
receipt = dict(archive=name, bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
               members=rows, private_files_included=False, exe_dat_prefix_included=False)
with (DATA / (name.removesuffix('.tar.gz') + '-manifest.json')).open('x') as f:
    json.dump(receipt, f, indent=2)
    f.write('\n')
with (DATA / 'SAVES.sha256').open('a') as f:
    for row in rows:
        f.write(row['sha256'] + '  ' + row['name'] + '\n')
print(json.dumps({k: v for k, v in receipt.items() if k != 'members'}))
