#!/usr/bin/env python3
"""Prepare the artifacts folder for the audit: download the per-batch archives of release run-exp-v050-rules, check each archive's SHA-256 against its
tracked MANIFEST-<batch>.txt, extract into <artifacts> (default <repo>/artifacts/run-exp-v050-rules; members are stored with relative paths such as
saves/Q1_00_start.SAV, inputs/..., *.png), and check every member's SHA-256. usage: fetch_archive.py [--dir DOWNLOADED_TARBALLS_DIR]  (without --dir, `gh release download` is used)"""
import sys, os, glob, hashlib, tarfile, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ART, DATA
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
d = sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv else tempfile.mkdtemp()
if '--dir' not in sys.argv: subprocess.run(['gh', 'release', 'download', 'run-exp-v050-rules', '-R', 'diegoami/ic2-conquest', '-p', 'batch-*.tar.gz', '-D', d], check=True)
bad = 0
for m in sorted(glob.glob(DATA + 'MANIFEST-*.txt')):
    lines = [l.split() for l in open(m) if l.strip() and not l.startswith('#')]
    arc = [l for l in lines if l[1].startswith('archive:')][0]; name = arc[1][8:]
    p = os.path.join(d, name)
    if not os.path.exists(p): print('missing archive', name); bad += 1; continue
    if sha(p) != arc[0]: print('archive hash mismatch', name); bad += 1; continue
    os.makedirs(ART, exist_ok=True)
    with tarfile.open(p) as t: t.extractall(ART)
    for h, mem in lines:
        if mem.startswith('member:') and sha(ART + mem[7:]) != h: print('member hash mismatch', mem); bad += 1
    print('extracted', name)
print('FAILED' if bad else 'archive ready in %s' % ART); sys.exit(1 if bad else 0)
