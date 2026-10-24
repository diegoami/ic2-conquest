"""Allowlist this generated action batch; never archive a prefix/owner tree."""
import hashlib,json,tarfile
from common import *
files={}
def add(p,n):
 assert p.is_file() and 'runtime' not in p.parts and p.suffix.lower() not in {'.exe','.dat','.pdb','.png'}
 assert n not in files;files[n]=p
for folder in ['inputs-v1','original-v1','affordability-v1','native-v1','native-v2','live-input-v1','live-phase-replay-v1']:
 for p in sorted((BASE/folder).rglob('*')):
  if p.is_file() and p.suffix in {'.SAV','.ram','.json'}:add(p,folder+'/'+str(p.relative_to(BASE/folder)))
for run in sorted((BASE/'live').iterdir()):
 for p in sorted(run.iterdir()):
  if p.is_file() and p.suffix in {'.SAV','.json','.bin'}:add(p,'live/'+run.name+'/'+p.name)
 for p in sorted((run/'snapshots').glob('*.ram')):add(p,'live/'+run.name+'/snapshots/'+p.name)
for p in sorted((ROOT/'artifacts/run-exp-strategic-fidelity/source-v1/data').rglob('*')):
 if p.is_file() and p.suffix in {'.json','.b64'}:add(p,'data/'+str(p.relative_to(ROOT/'artifacts/run-exp-strategic-fidelity/source-v1/data')))
for name in ['Actions','Paths','PortChecks']:
 for suffix in ['.dll','.deps.json','.runtimeconfig.json']:add(ROOT/'runs/experiments/fleet174-actions/bin/Debug/net10.0'/(name+suffix),'tools/'+name+suffix)
for name in ['IC2.Engine.dll','IC2.Data.dll']:add(ROOT/'runs/experiments/fleet174-actions/bin/Debug/net10.0'/name,'tools/'+name)
for name in ['case-manifest-v1.json','original-actions-v1.json','native-actions-v2.json','native-paths-v1.json','summary-v3.json','accepted-port-affordability-v1.json','live-phase-replay-v1.json']:
 add(DATA/name,'data-text/'+name)
canaries={hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts/run-exp-battle1355/private-v1/inputs').iterdir() if p.is_file()}
members=[]
for name,p in files.items():
 h=hashlib.sha256(p.read_bytes()).hexdigest();assert h not in canaries;members.append(dict(name=name,bytes=p.stat().st_size,sha256=h))
archive=BASE/'fleet-actions-batch01.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
 for name,p in files.items():tar.add(p,arcname=name,recursive=False)
with tarfile.open(archive) as tar:
 for m in members:assert hashlib.sha256(tar.extractfile(m['name']).read()).hexdigest()==m['sha256']
receipt=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),members=members,member_count=len(members),
 owner_hash_canaries_absent=True,original_EXE_DAT_runtime_credentials_excluded=True)
with (DATA/'artifact-manifest-v1.json').open('x') as f:json.dump(receipt,f,indent=2)
with (DATA/'SAVES.sha256').open('x') as f:
 for m in members:f.write(m['sha256']+'  '+m['name']+'\n')
 f.write(receipt['sha256']+'  '+archive.name+'\n')
print(json.dumps({k:receipt[k] for k in ['archive','bytes','sha256','member_count']}))
