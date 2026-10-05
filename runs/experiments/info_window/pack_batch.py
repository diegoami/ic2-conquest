"""Pack the not-yet-packed binaries of artifacts/run-exp-info-window/ (screenshots, staged saves) into a per-batch tar.gz, write the tracked manifest
(MANIFEST-<batch>.txt: path, size, SHA-256 of every member), append the SHA-256 lines to SAVES.sha256 (append-only), and print the release command.
    python3 pack_batch.py <batch-name>
Never deletes or overwrites: an existing archive/manifest name gets the next .vN."""
import sys, os, hashlib, tarfile, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ART, new_path
name = sys.argv[1]
packed = set()
for m in glob.glob(DATA + 'MANIFEST-*.txt*') + glob.glob(DATA + 'MANIFEST-*.v*.txt'):
    for l in open(m):
        if l.strip() and not l.startswith('#'): packed.add(l.split('\t')[0])
files = []
for root, _, fs in os.walk(ART):
    for f in fs:
        p = os.path.relpath(os.path.join(root, f), ART)
        if p.endswith(('.png', '.SAV', '.sav')) and p not in packed and not p.endswith('.tar.gz'): files.append(p)
files.sort()
if not files: print('nothing new'); sys.exit(0)
tgz = new_path(ART + 'batch-%s.tar.gz' % name)
lines = ['# batch %s: %d files in %s (release run-exp-info-window)\n' % (name, len(files), os.path.basename(tgz))]
sha_lines = []
with tarfile.open(tgz, 'x:gz') as t:
    for p in files:
        h = hashlib.sha256(open(ART + p, 'rb').read()).hexdigest()
        t.add(ART + p, arcname=p)
        lines.append('%s\t%d\t%s\n' % (p, os.path.getsize(ART + p), h)); sha_lines.append('%s  %s\n' % (h, p))
man = new_path(DATA + 'MANIFEST-%s.txt' % name)
open(man, 'x').write(''.join(lines))
open(DATA + 'SAVES.sha256', 'a').write(''.join(sha_lines))
print(tgz, man, len(files))
print('gh release upload run-exp-info-window %s   (create first with: gh release create run-exp-info-window %s -t run-exp-info-window -n "Information window experiment: per-batch screenshot/save archives, manifests in runs/experiments/data/run-exp-info-window/")' % (tgz, tgz))
