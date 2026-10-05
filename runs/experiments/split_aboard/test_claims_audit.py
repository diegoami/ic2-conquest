"""A doctored save must make the audit fail (needs the archive: fetch_archive.py). Run: python3 -m unittest runs/experiments/split_aboard/test_claims_audit.py"""
import os, sys, subprocess, shutil, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from paths import ART
class T(unittest.TestCase):
    def run_audit(self, art): return subprocess.run([sys.executable, HERE + '/claims_audit.py', '--artifacts', art, '--no-write'], capture_output=True, text=True)
    def test_clean(self): self.assertEqual(self.run_audit(ART).returncode, 0)
    def test_doctored_save_fails(self):
        d = tempfile.mkdtemp(); shutil.copytree(ART + 'saves', d + '/saves')
        p = d + '/saves/SA_02_after_split.v2.SAV'; b = bytearray(open(p, 'rb').read())
        import state.sav as S; sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
        s = S.parse(bytes(b)); n = [a for a in s['armies'] if a['troops'] > 0 and not a['embarked'] and a['owner'] == s['current_nation'] and a['moves'] == 0][-1]['id']
        off = S.ARMY_OFF + 2 + n * S.ARMY_LEN; b[off:off + 2] = (101).to_bytes(2, 'little', signed=True)      # move the new army's x to 101: not the replayed tile
        open(p, 'wb').write(bytes(b)); r = self.run_audit(d); self.assertEqual(r.returncode, 1, r.stdout)


class FetchArchive(unittest.TestCase):
    def test_never_overwrites(self):
        import tempfile, glob, shutil, tarfile, hashlib
        import fetch_archive as F
        from paths import DATA
        sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
        src, dest, data = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        m = sorted(glob.glob(DATA + 'MANIFEST-*.txt'))[0]
        lines = [l.split() for l in open(m) if l.strip() and not l.startswith('#')]
        members = [mem[7:] for h, mem in lines if mem.startswith('member:')]
        arc = [l for l in lines if l[1].startswith('archive:')][0][1][8:]
        with tarfile.open(os.path.join(src, arc), 'w:gz') as t:
            for mem in members: t.add(ART + mem, arcname=mem)
        open(os.path.join(data, os.path.basename(m)), 'w').write(open(m).read().replace(lines[0][0], sha(os.path.join(src, arc)), 1))
        sav = [x for x in members if x.endswith('.SAV')]
        victim = os.path.join(dest, sav[0]); os.makedirs(os.path.dirname(victim), exist_ok=True); open(victim, 'wb').write(b'a different, measured file')
        with self.assertRaises(SystemExit): F.fetch(data=data, dest=dest, src_dir=src)
        self.assertEqual(open(victim, 'rb').read(), b'a different, measured file'); self.assertFalse(os.path.exists(os.path.join(dest, sav[1])))
        os.remove(victim)
        self.assertEqual(F.fetch(data=data, dest=dest, src_dir=src), (len(members), 0))
        self.assertEqual(F.fetch(data=data, dest=dest, src_dir=src), (0, len(members)))

if __name__ == '__main__': unittest.main()
