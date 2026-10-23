"""Recover the pinned private corpus for strict read-only native replay only."""
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
ART=ROOT/'artifacts/run-exp-battle-residual157'
REV='6319802a75067e7730e4f6a27dce3b4e296ddd9b'
archive=ART/'private-fixture-corpus-v1.tar.gz'
with archive.open('xb') as f:
    r=subprocess.run(['gh','api',f'repos/diegoami/ic2-test-fixtures/tarball/{REV}'],stdout=f,stderr=subprocess.PIPE,text=False)
receipt=dict(revision=REV,returncode=r.returncode,stderr=r.stderr.decode(errors='replace'),archive_bytes=archive.stat().st_size,
             archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),private_input_archive=True)
with (DATA/'full-corpus-download-v1.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
assert r.returncode==0,'Partial archive preserved; do not retry over it'
dest=ART/'full-fixtures-v1';dest.mkdir(exist_ok=False)
count=0;roots=set()
with tarfile.open(archive) as tf:
    for m in tf:
        parts=Path(m.name).parts
        if not parts:continue
        roots.add(parts[0])
        rel=Path(*parts[1:])
        if not m.isfile() or not rel.parts or rel.parts[0]!='battles':continue
        assert not rel.is_absolute() and '..' not in rel.parts
        path=dest/rel;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as out:out.write(tf.extractfile(m).read())
        count+=1
assert len(roots)==1 and count>1000
# Configuration tests require a DAT beside battles/. Copy the pinned original
# DAT privately as a separately hashed input; never include it in public archives.
dat=Path('/home/diego/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat').read_bytes()
assert hashlib.sha256(dat).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
with (dest/'Imperial Conquest 2.dat').open('xb') as f:f.write(dat)
with (DATA/'full-corpus-recovery-v1.json').open('x') as f:json.dump(dict(revision=REV,archive_sha256=receipt['archive_sha256'],battle_files=count,root_prefix=next(iter(roots)),dat_pin_verified=True,scope='Private immutable battles corpus and pinned DAT; no working checkout, code executed or fixture modified'),f,indent=2);f.write('\n')
print('Recovered',count,'private corpus files for native verification',flush=True)
