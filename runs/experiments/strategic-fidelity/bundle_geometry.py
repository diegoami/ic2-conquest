"""Preserve the independent terrain/occupancy audit tool as a new supplement."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
archive=BASE/'geometry-audit-tools-batch04.tar.gz';assert not archive.exists();members=[]
names=['Geometry.dll','Geometry.deps.json','Geometry.runtimeconfig.json','IC2.Engine.dll','IC2.Data.dll']
with tarfile.open(archive,'x:gz') as tar:
    for name in names:
        p=ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0'/name;b=p.read_bytes();arc='tools-geometry/'+name
        members.append(dict(name=arc,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));tar.add(p,arcname=arc,recursive=False)
record=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),member_count=len(members),members=members,
    purpose='Independent original-map versus native terrain/passability/occupancy audit; unchanged pinned engine/data.')
with (DATA/'artifact-batch04-manifest-v1.json').open('x') as f:json.dump(record,f,indent=2)
with (DATA/'SAVES.sha256').open('a') as f:
    for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
    f.write(record['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:record[k] for k in ['archive','bytes','sha256','member_count']}))
