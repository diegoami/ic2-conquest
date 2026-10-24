"""Rehash both bundles, recover them into a NEW tree and replay retained tools."""
import hashlib
import argparse
import json
import subprocess
import tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
out=BASE/('recovery-smoke-'+a.version);out.mkdir(exist_ok=False);count=0
for version in (1,2,3):
    manifest=json.loads((DATA/f'artifact-batch0{version}-manifest-v1.json').read_text());archive=BASE/manifest['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
    with tarfile.open(archive) as tar:
        for row in manifest['members']:
            name=PurePosixPath(row['name']);assert not name.is_absolute() and '..' not in name.parts
            member=tar.getmember(str(name));assert member.isfile()
            b=tar.extractfile(member).read();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
            p=out/str(name);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(b)
            count+=1
output=out/'from-scores-smoke.jsonl'
with (DATA/('bundle-smoke-execution-'+a.version+'.log')).open('x') as f:
    result=subprocess.run(['/home/diego/.dotnet/dotnet',str(out/'tools-v7/Probe.dll'),'from-scores',str(out),
        str(out/'projections/N-rome-hook-v1-v1'),str(output)],stdout=f,stderr=subprocess.STDOUT)
assert result.returncode==0
expected=DATA/'N-rome-hook-v1/original-target-from-scores-v1.jsonl'
assert output.read_bytes()==expected.read_bytes()
with (DATA/('bundle-verification-'+a.version+'.json')).open('x') as f:json.dump(dict(archives=3,members_verified=count,
    exclusive_recovery=True,latest_tool_executes=True,retained_11_rows_byte_identical=True,
    remote_download_digest_check=False),f,indent=2)
print('PASS three archives,',count,'member hashes and recovered compiled-tool replay;11 rows byte-identical')
