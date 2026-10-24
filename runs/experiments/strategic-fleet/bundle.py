"""Explicit generated fleet-control bundle; no runtime/owner/private tree walk."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fleet';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fleet'
files={}
for p in sorted((BASE/'controls-v1').rglob('*')):
 if p.is_file() and p.suffix in {'.ram','.SAV','.json'}:files['controls-v1/'+str(p.relative_to(BASE/'controls-v1'))]=p
for p in sorted((ROOT/'artifacts/run-exp-strategic-fidelity/source-v1/data').rglob('*')):
 if p.is_file() and p.suffix in {'.json','.b64'}:files['data/'+str(p.relative_to(ROOT/'artifacts/run-exp-strategic-fidelity/source-v1/data'))]=p
for n in ['FleetProbe.dll','FleetProbe.deps.json','FleetProbe.runtimeconfig.json','IC2.Engine.dll','IC2.Data.dll']:files['tools/'+n]=ROOT/'runs/experiments/strategic-fleet/bin/Debug/net10.0'/n
canaries={hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/run-exp-battle1355/private-v1/inputs').iterdir() if p.is_file()}
members=[]
for n,p in files.items():
 assert p.suffix.lower() not in {'.exe','.dat','.pdb'} and 'runtime' not in p.parts
 digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest not in canaries
 members.append(dict(name=n,bytes=p.stat().st_size,sha256=digest))
archive=BASE/'fleet-controls-batch01.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
 for n,p in files.items():tar.add(p,arcname=n,recursive=False)
with tarfile.open(archive) as tar:
 for m in members:assert hashlib.sha256(tar.extractfile(m['name']).read()).hexdigest()==m['sha256']
record=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),member_count=len(members),members=members,
 source_pin='55d96876a98ba3bb7142ca7c1ecc0d1b61095c18',owner_hash_canaries_absent=True,original_EXE_DAT_runtime_excluded=True)
with (DATA/'artifact-manifest-v1.json').open('x') as f:json.dump(record,f,indent=2)
with (DATA/'SAVES.sha256').open('x') as f:
 for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
 f.write(record['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:record[k] for k in ['archive','bytes','sha256','member_count']}))
