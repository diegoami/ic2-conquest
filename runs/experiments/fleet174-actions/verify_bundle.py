"""Recover a NEW tree and rerun retained native path observer against33states."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-fleet-actions174';DATA=ROOT/'runs/experiments/data/run-exp-fleet-actions174'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);options=p.parse_args();out=BASE/('recovery-'+options.version);out.mkdir()
m=json.loads((DATA/'artifact-manifest-v1.json').read_text());archive=BASE/m['archive'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['sha256']
with tarfile.open(archive) as tar:
 for row in m['members']:
  n=PurePosixPath(row['name']);assert not n.is_absolute() and '..' not in n.parts
  b=tar.extractfile(str(n)).read();assert hashlib.sha256(b).hexdigest()==row['sha256']
  target=out/str(n);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(b)
output=out/'native-recovered-paths.json'
with (DATA/('recovery-execution-'+options.version+'.log')).open('x') as f:
 r=subprocess.run(['/home/diego/.dotnet/dotnet',str(out/'tools/Paths.dll'),str(out),str(out),str(out/'data-text/native-actions-v2.json'),str(output)],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0 and output.read_bytes()==(DATA/'native-paths-v1.json').read_bytes()
with (DATA/('recovery-verification-'+options.version+'.json')).open('x') as f:json.dump(dict(members_verified=m['member_count'],native_path_replays_byte_identical=33,original_game_not_relaunched=True,remote_digest_download=False),f,indent=2)
print('PASS all archive members and recovered33native accepted-state/path rows exactly')
