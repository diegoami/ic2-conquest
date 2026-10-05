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
if __name__ == '__main__': unittest.main()
