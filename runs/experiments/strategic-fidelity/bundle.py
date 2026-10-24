"""Explicit generated-evidence allowlist; never walk a Wine/private-owner tree."""
import hashlib
import json
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
archive=BASE/'pilot-evidence-batch01.tar.gz';assert not archive.exists()
files={}
def add(path,name):
    assert path.is_file() and 'runtime' not in path.parts
    assert path.suffix.lower() not in {'.exe','.dat','.pdb','.png'}
    assert name not in files
    files[name]=path
for path in sorted((BASE/'inputs-v1').glob('*.SAV')):add(path,'inputs/'+path.name)
for run in sorted((BASE/'original').iterdir()):
    for path in sorted(run.glob('*.SAV')):add(path,'original/'+run.name+'/'+path.name)
    for path in sorted((run/'snapshots').glob('*.ram')):add(path,'snapshots/'+run.name+'/'+path.name)
    raw=run/'records.bin'
    if raw.exists():add(raw,'original/'+run.name+'/records.bin')
for run in sorted((BASE/'projections').iterdir()):
    for path in sorted(run.iterdir()):
        if path.suffix in {'.SAV','.json'}:add(path,'projections/'+run.name+'/'+path.name)
for run in sorted((BASE/'native').iterdir()):
    for path in sorted(run.glob('*.json')):add(path,'native/'+run.name+'/'+path.name)
for path in sorted((BASE/'resupply-controls-v1').iterdir()):add(path,'resupply-controls/'+path.name)
for path in sorted((BASE/'source-v1/data').rglob('*.json')):add(path,'data/'+str(path.relative_to(BASE/'source-v1/data')))
for name in ['Probe.dll','Probe.deps.json','Probe.runtimeconfig.json','IC2.Engine.dll','IC2.Data.dll']:
    add(ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0'/name,'tools/'+name)
canaries={hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/run-exp-battle1355/private-v1/inputs').iterdir() if p.is_file()}
members=[]
for name,path in files.items():
    digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest not in canaries
    members.append(dict(name=name,bytes=path.stat().st_size,sha256=digest))
with tarfile.open(archive,'x:gz') as tar:
    for name,path in files.items():tar.add(path,arcname=name,recursive=False)
with tarfile.open(archive) as tar:
    assert tar.getnames()==list(files)
    for m in members:
        stream=tar.extractfile(m['name']);assert stream and hashlib.sha256(stream.read()).hexdigest()==m['sha256']
record=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    members=members,member_count=len(members),owner_hash_canaries_absent=True,
    excludes=['all original EXE/DAT files','all Wine prefixes/runtime trees','all owner1355/1388 inputs/states/hashes','credentials','PDB/debug files'],
    includes_generated_RAM_snapshots=True,note='Generated-case evidence only; diagnostic projections are not original Save As. No sharing change requested.')
with (DATA/'artifact-batch01-manifest-v1.json').open('x') as f:json.dump(record,f,indent=2)
with (DATA/'SAVES.sha256').open('x') as f:
    for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
    f.write(record['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:record[k] for k in ['archive','bytes','sha256','member_count']}))
