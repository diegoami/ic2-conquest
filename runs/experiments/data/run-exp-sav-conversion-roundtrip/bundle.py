"""Archive measured saves/JSON/screenshots only, never executables or prefixes."""
import hashlib
import json
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parents[3] / 'artifacts/run-exp-sav-conversion-roundtrip'
name = sys.argv[1]
dest = ART / (name + '.tar.gz')
if dest.exists():
    raise SystemExit('Archive already exists')
files = list((ART / 'native-v1').glob('*.json')) + list((ART / 'exports-v2').glob('*'))
for receipt in HERE.glob('live-*.json'):
    r = json.loads(receipt.read_text())
    if r['complete']:
        files += list((ART / receipt.stem).glob('*'))
files = sorted(p for p in files if p.is_file() and p.suffix.lower() in {'.sav', '.json', '.png'})
manifest = [{'file': str(p.relative_to(ART)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
             'bytes': p.stat().st_size} for p in files]
with tarfile.open(dest, 'x:gz') as tar:
    for path in files:
        tar.add(path, arcname=str(path.relative_to(ART)))
with (HERE / (name + '-manifest.json')).open('x') as f:
    json.dump({'archive': dest.name, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
               'bytes': dest.stat().st_size, 'files': manifest}, f, indent=2)
with (HERE / (name + '-SAVES.sha256')).open('x') as f:
    for entry in manifest:
        f.write(entry['sha256'] + '  ' + entry['file'] + '\n')
print(dest, 'bytes', dest.stat().st_size, 'files', len(files))
