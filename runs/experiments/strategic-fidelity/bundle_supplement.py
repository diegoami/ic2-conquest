"""Retain the added scarcity case and latest diagnostic tool without replacing batch01."""
import hashlib
import json
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
case='L-ptolemaic-isolated';label=case+'-hook-v1';files={}
def add(p,n):
    assert p.is_file() and p.suffix.lower() not in {'.exe','.dat','.pdb','.png'} and 'runtime' not in p.parts
    assert n not in files;files[n]=p
add(BASE/'inputs-v1'/(case+'.SAV'),'inputs/'+case+'.SAV')
for p in sorted((BASE/'original'/label).glob('*.SAV')):add(p,'original/'+label+'/'+p.name)
add(BASE/'original'/label/'records.bin','original/'+label+'/records.bin')
for p in sorted((BASE/'original'/label/'snapshots').glob('*.ram')):add(p,'snapshots/'+label+'/'+p.name)
for p in sorted((BASE/'projections'/(label+'-v1')).iterdir()):add(p,'projections/'+label+'-v1/'+p.name)
for p in sorted((BASE/'native'/(case+'-v1')).glob('*.json')):add(p,'native/'+case+'-v1/'+p.name)
for name in ['Probe.dll','Probe.deps.json','Probe.runtimeconfig.json','IC2.Engine.dll','IC2.Data.dll']:
    add(ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0'/name,'tools-v7/'+name)
archive=BASE/'isolated-scarcity-and-tools-batch02.tar.gz';assert not archive.exists()
canaries={hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/run-exp-battle1355/private-v1/inputs').iterdir() if p.is_file()}
members=[]
for n,p in files.items():
    digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest not in canaries
    members.append(dict(name=n,bytes=p.stat().st_size,sha256=digest))
with tarfile.open(archive,'x:gz') as tar:
    for n,p in files.items():tar.add(p,arcname=n,recursive=False)
with tarfile.open(archive) as tar:
    for m in members:assert hashlib.sha256(tar.extractfile(m['name']).read()).hexdigest()==m['sha256']
record=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    member_count=len(members),members=members,owner_input_hash_canaries_absent=True,
    note='Append-only supplement to batch01. tools-v7 adds original-score branch counterfactual; do not overwrite batch01 tools.')
with (DATA/'artifact-batch02-manifest-v1.json').open('x') as f:json.dump(record,f,indent=2)
with (DATA/'SAVES.sha256').open('a') as f:
    for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
    f.write(record['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:record[k] for k in ['archive','bytes','sha256','member_count']}))
