"""Tests of claims_audit.py: the audit passes on the finding and fails on (a) a literal with one changed space, (b) a doctored line of the code extract, (c) a doctored save,
(d) a doctored OCR reading, (e) a doctored count, (f) a changed play fact. Each doctored copy is made in a temporary folder; nothing tracked is touched.
usage: python3 -m unittest test_claims_audit   (needs the saves: fetch_archive.py)"""
import os, re, shutil, sys, tempfile, unittest, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from claims_audit import run
FINDING = os.path.join(paths.ROOT, 'findings', '2026-10-05-refusal-texts-and-conditions.md')
EXE = os.environ.get('IC2_ORIG_EXE', os.path.expanduser('~/ic2-work/build/Imperial Conquest 2.exe'))

def copy_data(tmp):
    d = os.path.join(tmp, 'data'); shutil.copytree(paths.DATA, d); return d

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = open(FINDING, encoding='utf-8').read()
    def audit(self, finding_text=None, data=None, art=None):
        tmp = tempfile.mkdtemp()
        try:
            f = FINDING
            if finding_text is not None:
                f = os.path.join(tmp, 'finding.md'); open(f, 'w', encoding='utf-8').write(finding_text)
            return run(f, data or paths.DATA, art or paths.ART, EXE)
        finally: shutil.rmtree(tmp)
    def test_clean(self):
        n, bad = self.audit()
        self.assertEqual(bad, [], bad[:5]); self.assertGreater(n, 500)
    def doctor_line(self, prefix, old, new):
        lines = self.text.split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        self.assertEqual(len(hit), 1, (prefix, hit)); self.assertIn(old, lines[hit[0]])
        lines[hit[0]] = lines[hit[0]].replace(old, new, 1)
        return '\n'.join(lines)
    def test_doctored_literal_one_space(self):
        lit = 'You can not split an army containing only 1 unit.'
        n, bad = self.audit(self.doctor_line('| R01 |', '`' + lit + '`', '`' + lit.replace('can not', 'can  not') + '`'))
        self.assertTrue(any('R01 literal byte for byte' in b for b in bad), bad[:5])
    def test_doctored_literal_space_before_question_mark(self):
        lit = 'The army is too large for this fleet ?'
        n, bad = self.audit(self.doctor_line('| R06 |', '`' + lit + '`', '`' + lit.replace(' ?', '?') + '`'))
        self.assertTrue(any('R06 literal byte for byte' in b for b in bad), bad[:5])
    def test_doctored_literal_clone_table(self):
        lit = 'These 2 armies combined contain more than 20 units.'
        lines = [l for l in self.text.split('\n') if l.startswith('| UA05 |') and lit in l]
        self.assertEqual(len(lines), 1)
        n, bad = self.audit(self.text.replace(lines[0], lines[0].replace('`' + lit + '`', '`' + lit[:-1] + ' .`')))
        self.assertTrue(any('clone table' in b for b in bad), bad[:5])
    def test_doctored_extract_line(self):
        tmp = tempfile.mkdtemp()
        try:
            d = copy_data(tmp)
            p = sorted(glob.glob(d + '/code_extract_refusals*.txt'))[-1]
            s = open(p, encoding='utf-8').read()
            self.assertIn('< 0x15', s)
            open(p, 'w', encoding='utf-8').write(s.replace('< 0x15', '< 0x16', 1))
            n, bad = self.audit(data=d)
            self.assertTrue(any('cited line 46984' in b for b in bad), bad[:5])
        finally: shutil.rmtree(tmp)
    def test_doctored_call_literal_in_extract(self):
        tmp = tempfile.mkdtemp()
        try:
            d = copy_data(tmp); p = sorted(glob.glob(d + '/code_extract_refusals*.txt'))[-1]
            s = open(p, encoding='utf-8').read()
            open(p, 'w', encoding='utf-8').write(s.replace('You can not split an army', 'You can not split a army', 1))
            n, bad = self.audit(data=d)
            self.assertTrue(any('R01 literal byte for byte' in b for b in bad), bad[:5])
        finally: shutil.rmtree(tmp)
    def test_doctored_save(self):
        tmp = tempfile.mkdtemp()
        try:
            a = os.path.join(tmp, 'art'); shutil.copytree(paths.ART, a, ignore=shutil.ignore_patterns('*.png', '*.tar.gz'))
            p = os.path.join(a, 'saves', 'REF_UA05b_b1_ctl.SAV'); b = bytearray(open(p, 'rb').read()); b[5000] ^= 1
            open(p, 'wb').write(bytes(b))
            n, bad = self.audit(art=a)
            self.assertTrue(any('UA05b' in x and ('hash' in x or 'facts' in x) for x in bad), bad[:5])
        finally: shutil.rmtree(tmp)
    def test_doctored_ocr(self):
        tmp = tempfile.mkdtemp()
        try:
            d = copy_data(tmp)
            for f in glob.glob(d + '/plays_*.jsonl') + glob.glob(d + '/ocr_*.jsonl'):
                s = open(f, encoding='utf-8').read()
                s = s.replace('You can only rename regular units', 'You can only delete regular units').replace('only rename regular units', 'only delete regular units')
                open(f, 'w', encoding='utf-8').write(s)
            n, bad = self.audit(data=d)
            self.assertTrue(any('D05b' in x for x in bad), bad[:5])
        finally: shutil.rmtree(tmp)
    def test_doctored_count(self):
        n, bad = self.audit(self.text.replace('| refusals catalogued | 57 |', '| refusals catalogued | 58 |'))
        self.assertTrue(any('refusal rows' in b for b in bad), bad[:5])
    def test_doctored_state_fact(self):
        n, bad = self.audit(self.text.replace('army 13: owner=0 pos=(102,44) units=1', 'army 13: owner=0 pos=(102,44) units=2', 1))
        self.assertTrue(any('UA04' in b and 'facts' in b for b in bad), bad[:5])
    def test_doctored_combined_order(self):
        self.assertIn('| UA05c | R03 |', self.text)
        n, bad = self.audit(self.text.replace('| UA05c | R03 |', '| UA05c | R04 |', 1))
        self.assertTrue(any('combined play UA05c' in b for b in bad), bad[:5])
if __name__ == '__main__': unittest.main()
