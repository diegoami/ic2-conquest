#!/usr/bin/env python3
"""Archive the binaries not yet archived (saves/*.SAV and screenshots under artifacts/run-exp-refusal-texts/) into a per-batch tar.gz,
write a tracked manifest (MANIFEST-<batch>.txt: sha256 of every member and of the archive) and upload the archive to the release
run-exp-refusal-texts (created at the first batch). Never overwrites: a batch name that exists gets the next free version.
usage: archive_batch.py BATCH [--no-upload]"""
import sys, os, glob, hashlib, tarfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import new_path, write_new, DATA
from paths import ART
REL = 'run-exp-refusal-texts'
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
batch = sys.argv[1]
done = set()
for m in glob.glob(os.path.join(DATA, 'MANIFEST-*.txt')):
    for l in open(m):
        p = l.split()
        if len(p) == 2 and p[1].startswith('member:'): done.add(p[1][7:])
members = sorted(os.path.relpath(f, ART) for f in glob.glob(ART + '**/*', recursive=True)
                 if os.path.isfile(f) and not f.endswith('.tar.gz') and os.path.relpath(f, ART) not in done)
if not members: sys.exit('nothing new to archive')
arc = new_path(ART + 'batch-%s.tar.gz' % batch)
with tarfile.open(arc, 'w:gz') as t:
    for m in members: t.add(ART + m, arcname=m)
lines = ['# batch %s: archive %s' % (batch, os.path.basename(arc)), '%s  archive:%s' % (sha(arc), os.path.basename(arc))]
lines += ['%s  member:%s' % (sha(ART + m), m) for m in members]
mp = write_new(os.path.join(DATA, 'MANIFEST-%s.txt' % batch), '\n'.join(lines) + '\n')
print(mp, len(members), 'members', os.path.getsize(arc), 'bytes')
if '--no-upload' not in sys.argv:
    exists = subprocess.run(['gh', 'release', 'view', REL], capture_output=True).returncode == 0
    cmd = ['gh', 'release', 'upload', REL, arc] if exists else ['gh', 'release', 'create', REL, arc, '--title', REL,
           '--notes', 'Binaries (saves, screenshots) of the refusal-texts experiment, one tar.gz per batch; hashes in runs/experiments/data/run-exp-refusal-texts/MANIFEST-*.txt']
    r = subprocess.run(cmd, capture_output=True, text=True)
    print('upload', 'OK' if r.returncode == 0 else 'FAILED: ' + r.stderr.strip()[:300] + ' | command: ' + ' '.join(cmd))
