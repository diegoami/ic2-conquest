"""Tests of claims_audit.py: the audit passes on the finding and fails on (a) a literal with one changed space, (b) a doctored line of the code extract, (c) a doctored save,
(d) a doctored OCR reading, (e) a doctored count, (f) a changed play fact. Each doctored copy is made in a temporary folder; nothing tracked is touched.
usage: python3 -m unittest test_claims_audit   (needs the saves: fetch_archive.py)"""
import os, re, json, shutil, sys, tempfile, unittest, glob
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
            p = sorted(glob.glob(os.path.join(a, 'saves', 'REF_UA05b_b*_ctl.SAV')))[-1];  # the latest batch's control save (the audit reads the latest record)
            b = bytearray(open(p, 'rb').read()); b[5000] ^= 1
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
    def cells(self, prefix):
        lines = self.text.split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        hit = sorted(hit, key=lambda i: -len(lines[i]))[:1] if prefix == '| UA04 |' else hit
        self.assertEqual(len(hit), 1, (prefix, hit)); return lines, hit[0]
    def doctor_built(self, prefix, fn, k=1):
        lines, i = self.cells(prefix); cs = lines[i].split(' | ')           # id | literal | ...
        parts = cs[k].split(' + '); parts = fn(parts); cs[k] = ' + '.join(parts); lines[i] = ' | '.join(cs)
        return '\n'.join(lines)
    def test_built_message_reordered_piece(self):
        n, bad = self.audit(self.doctor_built('| P09 |', lambda p: [p[1], p[0]] + p[2:]))
        self.assertTrue(any('P09 built message' in b for b in bad), bad[:3])
    def test_built_message_omitted_piece(self):
        n, bad = self.audit(self.doctor_built('| P09 |', lambda p: [x for x in p if '\u27e8if\u27e9' not in x]))
        self.assertTrue(any('P09 built message' in b for b in bad), bad[:3])
    def test_built_message_duplicated_piece(self):
        n, bad = self.audit(self.doctor_built('| P09 |', lambda p: p[:3] + [p[2]] + p[3:]))
        self.assertTrue(any('P09 built message' in b for b in bad), bad[:3])
    def test_built_message_variable_moved(self):
        n, bad = self.audit(self.doctor_built('| R54 |', lambda p: p[::-1], k=2))
        self.assertTrue(any('R54 built message' in b for b in bad), bad[:3])
    def test_order_changed_consistently_in_both_tables(self):
        t = self.text
        t = t.replace('R02 > R03 > R04', 'R02 > R04 > R03', 1)
        lines = t.split('\n')
        for i, l in enumerate(lines):
            if l.startswith('| R03 |'): lines[i] = l.replace('| 2 of 3 |', '| 3 of 3 |', 1)
            elif l.startswith('| R04 |'): lines[i] = l.replace('| 3 of 3 |', '| 2 of 3 |', 1)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('recomputed' in b and ('R03' in b or 'R04' in b or 'JoinArmies' in b) for b in bad), bad[:3])
    def test_single_condition_play_passed_off_as_combined(self):
        self.assertIn('| UA05c | R03 |', self.text)
        n, bad = self.audit(self.text.replace('| UA05c | R03 |', '| UA05a | R03 |', 1))
        self.assertTrue(any('combined case UA05a: at least two' in b for b in bad), bad[:3])
    def test_staged_play_labelled_natural(self):
        lines, i = self.cells('| UA05b |'); cs = lines[i].split(' | ')
        self.assertTrue(cs[3].startswith('STAGED')); cs[3] = 'fixture, unedited'; lines[i] = ' | '.join(cs)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('UA05b' in b and 'unedited' in b for b in bad), bad[:3])
    def test_natural_play_labelled_staged(self):
        lines, i = self.cells('| UA04 |'); cs = lines[i].split(' | ')
        self.assertEqual(cs[3], 'fixture, unedited'); cs[3] = 'STAGED: army 13 units = 1 x hi 5,900'; lines[i] = ' | '.join(cs)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('UA04' in b and 'STAGED' in b for b in bad), bad[:3])
    def test_play_files_and_rows_columns(self):
        lines, i = self.cells('| UA04 |'); cs = lines[i].split(' | ')
        cs[1] = 'R02'; lines[i] = ' | '.join(cs)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('UA04: rows column' in b for b in bad), bad[:3])
    def test_classes_table(self):
        lines, i = self.cells('| TUnitMap |'); cs = lines[i].split(' | ')
        cs[2] = '28 |'; lines[i] = ' | '.join(cs)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('classes table' in b for b in bad), bad[:3])
    def test_transfer_attribution_swapped_consistently_in_both_tables(self):
        lines = self.text.split('\n')
        i28 = [i for i, l in enumerate(lines) if l.startswith('| R28 |')][0]; i31 = [i for i, l in enumerate(lines) if l.startswith('| R31 |')][0]
        c28 = lines[i28].split(' | '); c31 = lines[i31].split(' | ')
        self.assertEqual(len(c28), len(c31)); c28[-1], c31[-1] = c31[-1], c28[-1]
        lines[i28] = ' | '.join(c28); lines[i31] = ' | '.join(c31)
        for pid, a, b in (('T01', 'R28', 'R31'), ('T01r', 'R31', 'R28')):
            j = [i for i, l in enumerate(lines) if l.startswith('| %s | %s |' % (pid, a))]
            self.assertEqual(len(j), 1); lines[j[0]] = lines[j[0]].replace('| %s | %s |' % (pid, a), '| %s | %s |' % (pid, b), 1)
        n, bad = self.audit('\n'.join(lines))
        self.assertTrue(any('belongs to a handler' in b and ('T01' in b) for b in bad), bad[:4])
    def test_record_without_clicks(self):
        tmp = tempfile.mkdtemp()
        try:
            d = copy_data(tmp)
            for f in glob.glob(d + '/plays_b8.jsonl'):
                rows = [json.loads(l) for l in open(f)]
                for r in rows:
                    if r['play'] == 'T01': r['clicks'] = []
                open(f, 'w').write('\n'.join(json.dumps(r) for r in rows) + '\n')
            n, bad = self.audit(data=d)
            self.assertTrue(any('T01' in b and ('clicks' in b or 'belongs to a handler' in b) for b in bad), bad[:4])
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
        self.assertTrue(any('combined case UA05c' in b for b in bad), bad[:5])
if __name__ == '__main__': unittest.main()
