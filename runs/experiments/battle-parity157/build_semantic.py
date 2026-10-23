"""Build only after current-source CPU validation, into a new artifact."""
import hashlib
import json
from pathlib import Path
import semantic_observer as O

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
cpu = json.loads((DATA / 'semantic-cpu-v1.json').read_text())
source_hash = hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest()
assert cpu['exit'] == 0 and cpu['observer_sha256'] == source_hash and len(cpu['active_payload_cases']) == 24
raw = Path('/home/diego/ic2-work/build/Imperial Conquest 2 lab s1.exe').read_bytes()
assert hashlib.sha256(raw).hexdigest() == '06bc469dff70ae8c83438e82ef4266a584bab7796752024521d00f8d8d46ec40'
b = bytearray(raw)
info = O.apply(b)
out = ROOT / 'artifacts/run-exp-battle-parity157/semantic-observer-v1.exe'
with out.open('xb') as f:
    f.write(b)
report = dict(source_sha256=source_hash, exe_sha256=hashlib.sha256(b).hexdigest(),
              base_sha256=hashlib.sha256(raw).hexdigest(), cpu='semantic-cpu-v1.json', info=info)
with (DATA / 'semantic-build-v1.json').open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
print(out.name, report['exe_sha256'])
