#!/usr/bin/env python3
"""Prepare the artifacts folder for the audit: download the per-batch archives of the release (or take them from --dir), check each archive's SHA-256
against its tracked MANIFEST-<batch>.txt, and extract into <artifacts> (default <repo>/artifacts/run-exp-end-of-game; members carry relative paths).
NEVER overwrites: before anything is written every member is preflighted against the manifest hash; an existing file with the same hash is skipped, an existing
file with a different hash makes the whole run refuse (nothing is touched). Members are written one by one to a new file (open 'xb') and re-checked.
usage: fetch_archive.py [--dir DOWNLOADED_TARBALLS_DIR] [--dest ARTIFACTS_DIR]"""
import sys, os, glob, hashlib, tarfile, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ART, DATA
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
def arg(k): return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
def fetch(data=DATA, dest=ART, src_dir=None, release='run-exp-end-of-game', repo='diegoami/ic2-conquest'):
    dest = dest.rstrip('/') + '/'
    d = src_dir
    if d is None:
        d = tempfile.mkdtemp(); subprocess.run(['gh', 'release', 'download', release, '-R', repo, '-p', 'batch-*.tar.gz', '-D', d], check=True)
    plan = []                                                    # (tarpath, member, hash)
    for m in sorted(glob.glob(os.path.join(data, 'MANIFEST-*.txt'))):
        lines = [l.split() for l in open(m) if l.strip() and not l.startswith('#')]
        arc = [l for l in lines if l[1].startswith('archive:')][0]; name = arc[1][8:]; p = os.path.join(d, name)
        if not os.path.exists(p): raise SystemExit('missing archive %s' % name)
        if sha(p) != arc[0]: raise SystemExit('archive hash mismatch %s' % name)
        plan += [(p, mem[7:], h) for h, mem in lines if mem.startswith('member:')]
    for p, mem, h in plan:                                       # preflight: refuse before writing anything
        t = dest + mem
        if os.path.exists(t) and sha(t) != h: raise SystemExit('REFUSED: %s exists with a different hash; nothing was written' % t)
    done = skipped = 0
    for p, mem, h in plan:
        t = dest + mem
        if os.path.exists(t): skipped += 1; continue
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with tarfile.open(p) as tf, tf.extractfile(mem) as src, open(t, 'xb') as out: out.write(src.read())
        if sha(t) != h: raise SystemExit('member hash mismatch after extraction: %s' % mem)
        done += 1
    return done, skipped
if __name__ == '__main__':
    done, skipped = fetch(src_dir=arg('--dir'), dest=arg('--dest') or ART)
    print('archive ready: %d members written, %d already present with the right hash' % (done, skipped))
