#!/usr/bin/env python3
"""Archive the binaries not yet archived (saves/*.SAV and screenshots under artifacts/run-exp-cosmetic-gaps/) into a per-batch
tar.gz, write a tracked manifest (MANIFEST-<batch>.txt: sha256 of every member and of the archive) and upload the archive to the
release run-exp-cosmetic-gaps (created at the first batch; CLAUDE.md rule 1: IC2_RELEASE_TOKEN, when the environment holds it, is
used only for these release calls, passed to gh as its GH_TOKEN so it travels as the Bearer header and is never printed or written).
Never overwrites: a batch name that exists gets the next free version.
usage: archive_batch.py BATCH [--no-upload]"""
import sys, os, glob, hashlib, tarfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import new_path, write_new, DATA
from paths import ART
REL = 'run-exp-cosmetic-gaps'
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
    env = dict(os.environ)
    tok = env.get('IC2_RELEASE_TOKEN')
    if tok: env['GH_TOKEN'] = tok                     # gh sends it as the Bearer header; the token is never printed or written
    exists = subprocess.run(['gh', 'release', 'view', REL], capture_output=True, env=env).returncode == 0
    cmd = ['gh', 'release', 'upload', REL, arc] if exists else ['gh', 'release', 'create', REL, arc, '--title', REL,
           '--notes', 'Binaries (saves, screenshots, strace logs) of the cosmetic-gaps experiment, one tar.gz per batch; hashes in runs/experiments/data/run-exp-cosmetic-gaps/MANIFEST-*.txt']
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print('upload', 'OK' if r.returncode == 0 else 'FAILED: ' + r.stderr.strip()[:300] + ' | command: ' + ' '.join(cmd))
