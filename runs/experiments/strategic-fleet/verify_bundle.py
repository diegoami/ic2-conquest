"""Repeat the retained recovery steps under a NEW caller-provided version."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fleet';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fleet'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
out=BASE/('recovery-'+a.version);out.mkdir(exist_ok=False);m=json.loads((DATA/'artifact-manifest-v1.json').read_text())
archive=BASE/m['archive'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['sha256']
with tarfile.open(archive) as tar:
 for r in m['members']:
  n=PurePosixPath(r['name']);assert not n.is_absolute() and '..' not in n.parts
  b=tar.extractfile(str(n)).read();assert hashlib.sha256(b).hexdigest()==r['sha256']
  path=out/str(n);path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(b)
with (DATA/('recovery-execution-'+a.version+'.log')).open('x') as f:
 run=subprocess.run(['/home/diego/.dotnet/dotnet',str(out/'tools/FleetProbe.dll'),str(out/'controls-v1'),str(out),str(out/'native.json')],stdout=f,stderr=subprocess.STDOUT)
assert run.returncode==0 and (out/'native.json').read_bytes()==(DATA/'native-fleet-controls-v1.json').read_bytes()
with (DATA/('recovery-verification-'+a.version+'.json')).open('x') as f:json.dump(dict(member_hashes_verified=m['member_count'],compiled_native_rows_byte_identical=14,fresh_recovery=True),f,indent=2)
