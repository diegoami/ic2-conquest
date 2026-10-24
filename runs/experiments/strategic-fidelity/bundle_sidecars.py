"""Add missing pinned native terrain sidecars; preserve both earlier bundles."""
import hashlib
import json
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
paths=sorted((BASE/'source-v1/data').rglob('*.b64'));assert paths
archive=BASE/'terrain-sidecars-batch03.tar.gz';assert not archive.exists();members=[]
with tarfile.open(archive,'x:gz') as tar:
    for p in paths:
        name='data/'+str(p.relative_to(BASE/'source-v1/data'));b=p.read_bytes()
        members.append(dict(name=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        tar.add(p,arcname=name,recursive=False)
with tarfile.open(archive) as tar:
    for m in members:assert hashlib.sha256(tar.extractfile(m['name']).read()).hexdigest()==m['sha256']
record=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    members=members,member_count=len(members),reason='Required native terrain sidecars omitted by batch01 JSON-only selector; batch01/02 preserved.',
    source_pin='55d96876a98ba3bb7142ca7c1ecc0d1b61095c18')
with (DATA/'artifact-batch03-manifest-v1.json').open('x') as f:json.dump(record,f,indent=2)
with (DATA/'SAVES.sha256').open('a') as f:
    for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
    f.write(record['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:record[k] for k in ['archive','bytes','sha256','member_count']}))
