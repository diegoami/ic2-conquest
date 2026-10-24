"""Explicit generated allowlist only. Never walk runtime/source/private trees."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];B=ROOT/'artifacts/run-exp-strategic-tracks';D=ROOT/'runs/experiments/data/run-exp-strategic-tracks';files={}
def add(path,name):
 assert path.is_file() and not path.is_symlink()
 assert path.suffix.lower() not in {'.exe','.dat','.png','.jpg','.mp4'}
 assert not any(x in {'runtime','prefix','private','owner','credentials'} for x in Path(name).parts)
 if name in files:raise ValueError(name)
 files[name]=path
for label in ['ST-rom-hook-v1','ST-rom-plain-v1']:
 base=B/'live'/label
 for p in base.iterdir():
  if p.is_file() and p.suffix in {'.SAV','.json','.bin'}:add(p,'live/'+label+'/'+p.name)
 if (base/'snapshots').exists():
  for p in sorted((base/'snapshots').glob('*.ram')):add(p,'live/'+label+'/snapshots/'+p.name)
for name in ['phase-replay-v1','synthetic-v1','fleet-controls-v1','fleet-controls-v2','fleet-controls-v3','native-v1','native-v2','native-synthetic-v1','native-fleet-v1','native-fleet-v2','native-fleet-v3']:
 base=B/name
 for p in sorted(base.rglob('*')):
  if p.is_file() and p.suffix in {'.SAV','.ram','.json'}:add(p,name+'/'+p.relative_to(base).as_posix())
for p in sorted((B/'source-v2/data').rglob('*')):
 if p.is_file() and p.suffix in {'.json','.b64'}:add(p,'data/'+p.relative_to(B/'source-v2/data').as_posix())
for p in sorted((ROOT/'runs/experiments/strategic-tracks/bin/Debug/net10.0').iterdir()):
 if p.is_file() and p.suffix in {'.dll','.json'}:add(p,'tools/'+p.name)
for p in sorted(D.rglob('*')):
 if p.is_file() and p.suffix in {'.json','.jsonl','.log','.sha256'}:add(p,'data-text/'+p.relative_to(D).as_posix())
manifest=[dict(name=n,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for n,p in sorted(files.items())]
M=B/'batch01-manifest.json'
with M.open('x') as f:json.dump(manifest,f,indent=2)
archive=B/'strategic-tracks-batch01.tar.gz'
with archive.open('xb') as stream:
 with tarfile.open(fileobj=stream,mode='w:gz') as tar:
  for name,path in sorted(files.items()):tar.add(path,arcname=name,recursive=False)
  tar.add(M,arcname='manifest.json',recursive=False)
with tarfile.open(archive) as tar:
 assert set(tar.getnames())==set(files)|{'manifest.json'}
 for row in manifest:
  assert hashlib.sha256(tar.extractfile(row['name']).read()).hexdigest()==row['sha256']
receipt=dict(archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,members=len(files)+1,all_member_hashes_verified=True,scope='explicit generated controls/captured states/native tools and public data only; no original binary/DAT/runtime/owner input')
with (D/'artifact-manifest-v1.json').open('x') as f:json.dump(receipt,f,indent=2)
with (D/'SAVES-v2.sha256').open('x') as f:
 for row in manifest:
  if row['name'].endswith(('.SAV','.ram','.bin','.dll')):f.write(row['sha256']+'  '+row['name']+'\n')
print(json.dumps(receipt))
