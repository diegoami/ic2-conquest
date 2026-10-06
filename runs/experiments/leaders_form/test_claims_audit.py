"""Tests of claims_audit.py: the audit passes on the real sources and fails, each time for the right reason, when a literal, a code-extract line, a save, a screenshot, a play record, the resource dump, the pool
table or a count is doctored, and when a claim is removed consistently from every table that mentions it (the plays it needed are then uncited).
Each test works on a fresh copy of the finding, the tracked data and the artifacts (saves, screenshots, memory dumps) in a temporary folder; nothing real is touched.
usage: python3 -m unittest test_claims_audit   (needs the artifacts: run fetch_archive.py first when they are not in artifacts/run-exp-leaders-form)"""
import os, sys, re, json, shutil, tempfile, struct, hashlib, unittest, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths, claims_audit
from state import sav as SAV

FINDING = os.path.join(paths.ROOT, 'findings', '2026-10-06-leaders-form.md')
DATA = paths.DATA
ART = paths.ART

class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(ART + 'saves'): raise unittest.SkipTest('artifacts not present: run fetch_archive.py')
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.finding = os.path.join(self.tmp, 'finding.md'); shutil.copy(FINDING, self.finding)
        self.data = os.path.join(self.tmp, 'data') + '/'; shutil.copytree(DATA.rstrip('/'), self.data.rstrip('/'))
        self.art = os.path.join(self.tmp, 'art') + '/'; shutil.copytree(ART.rstrip('/'), self.art.rstrip('/'))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def audit(self):
        return claims_audit.run(self.finding, self.data, self.art)
    def edit_finding(self, old, new, count=1):
        s = open(self.finding, encoding='utf-8').read(); self.assertIn(old, s); open(self.finding, 'w', encoding='utf-8').write(s.replace(old, new, count))
    def latest(self, name):
        from common import latest
        return latest(os.path.join(self.data, name))
    def edit_file(self, path, old, new):
        s = open(path, encoding='utf-8').read(); self.assertIn(old, s); open(path, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    def fails(self, *needles):
        n, bad = self.audit()
        self.assertTrue(bad, 'the audit passed a doctored source')
        text = '\n'.join(bad)
        for nd in needles: self.assertIn(nd, text)
        return bad

class RealSources(Base):
    def test_the_real_sources_pass(self):
        n, bad = self.audit(); self.assertEqual(bad, []); self.assertGreater(n, 1500)

class Literals(Base):
    def test_a_doctored_control_literal_fails(self):
        self.edit_finding("| `Leader's name` | 185 |", "| `Leader's Name` | 185 |"); self.fails('F04 literal byte for byte')
    def test_a_doctored_rule_literal_fails(self):
        self.edit_finding("| `Are you sure you want to start a new game ?` | TPremierForm_NewGame:58018", "| `Are you sure you want to start a new game?` | TPremierForm_NewGame:58018"); self.fails('C05')
    def test_a_doctored_caption_with_one_space_fails(self):
        self.edit_finding("| `  Rome` |", "| ` Rome` |"); self.fails('F07 literal byte for byte')
    def test_a_doctored_name_limit_fails(self):
        self.edit_finding("| F23 | cbx_rome | TCheckBox | (none) | 100 | 3 | 0 | 100 |", "| F23 | cbx_rome | TCheckBox | (none) | 101 | 3 | 0 | 100 |"); self.fails('F23 left')
    def test_a_doctored_resource_line_fails(self):
        p = self.latest('dfm_TPickLeaders.txt'); self.edit_file(p, 'MaxLength = 25', 'MaxLength = 26'); self.fails('F29')

class ExtractLines(Base):
    def test_a_doctored_extract_line_fails(self):
        p = self.latest('code_extract_leaders.txt'); self.edit_file(p, "if (puVar6[0x490] != '\\0') {", "if (puVar6[0x490] == '\\0') {"); self.fails('O02')
    def test_a_message_box_call_added_to_ok_fails(self):
        p = self.latest('code_extract_leaders.txt'); self.edit_file(p, "    puVar6[0x490] = 0;", "    FUN_0042d750(0); puVar6[0x490] = 0;"); self.fails('O01')
    def test_a_cited_line_moved_to_another_function_fails(self):
        self.edit_finding('TPickLeaders_OK:56930', 'TPickLeaders_Cancel:56930'); self.fails('is in function TPickLeaders_Cancel')
    def test_a_cited_line_that_is_not_in_the_extract_fails(self):
        self.edit_finding('TPickLeaders_OK:56930', 'TPickLeaders_OK:90000'); self.fails('line is in the extract')
    def test_a_doctored_loader_read_changes_the_pool_offset(self):
        p = self.latest('code_extract_leaders.txt'); self.edit_file(p, '(piVar2,&DAT_0045e870,0x15e00)', '(piVar2,&DAT_0045e870,0x15e01)'); self.fails('pool offset')
    def test_a_doctored_pool_name_fails(self):
        self.edit_file(self.latest('dat_leader_pool.tsv'), '\t3\tAppius Claudius', '\t3\tAppius Claudia'); self.fails('draws row P01')

class Saves(Base):
    def p04(self):
        recs = [json.loads(l) for f in sorted(glob.glob(self.data + 'plays_*.jsonl')) for l in open(f)]
        r = [x for x in recs if x['play'] == 'P04' and x['status'] == 'ok'][-1]; return r
    def human_flag_offset(self, path, nation):
        b = open(path, 'rb').read()
        na = struct.unpack_from('<h', b, SAV.ARMY_OFF)[0]; o = SAV.ARMY_OFF + 2 + na * SAV.ARMY_LEN
        nf = struct.unpack_from('<h', b, o)[0]; o += 2 + nf * SAV.FLEET_LEN
        return o + nation * SAV.NATION_LEN + 0x490
    def flip(self, nation=2):
        r = self.p04(); p = self.art + 'saves/' + r['autosave']; off = self.human_flag_offset(p, nation)
        b = bytearray(open(p, 'rb').read()); b[off] ^= 1; open(p, 'wb').write(bytes(b)); return p, r
    def test_a_doctored_save_fails_its_hash(self):
        self.flip(); self.fails('SHA-256 is recorded', 'autosave hash equals')
    def test_a_doctored_save_with_hashes_rewritten_still_fails_its_claims(self):
        p, r = self.flip(); h = hashlib.sha256(open(p, 'rb').read()).hexdigest(); name = os.path.basename(p)
        sf = self.latest('SAVES.sha256'); lines = open(sf).read().splitlines()
        open(sf, 'w').write('\n'.join(l if not l.endswith('  ' + name) else '%s  %s' % (h, name) for l in lines) + '\n')
        for m in glob.glob(self.data + 'MANIFEST-*.txt'):
            t = open(m).read()
            if 'member:saves/' + name in t: open(m, 'w').write(re.sub(r'[0-9a-f]{64}(  member:saves/%s)' % re.escape(name), h + r'\1', t))
        bad = self.fails('P04 save.humans', 'the save and the game memory agree')
    def test_a_doctored_play_record_fails(self):
        f = sorted(glob.glob(self.data + 'plays_b2.jsonl'))[0]; out = []
        for l in open(f):
            r = json.loads(l)
            if r['play'] == 'P04' and r['status'] == 'ok': r['state']['nations'][1]['human'] = 0
            out.append(json.dumps(r))
        open(f, 'w').write('\n'.join(out) + '\n'); self.fails('P04')
    def test_a_missing_screenshot_fails(self):
        os.remove(self.art + 'LF_P04_b2_before_ok_form.png'); self.fails('LF_P04_b2_before_ok_form.png exists')
    def test_a_missing_memory_dump_fails(self):
        os.remove(self.art + 'saves/LF_P02_b2_after_ok_nations.bin'); self.fails('LF_P02_b2_after_ok_nations.bin exists')
    def test_a_replaced_screenshot_fails_its_hash(self):
        p = self.art + 'LF_P04_b2_before_ok_form.png'; b = bytearray(open(p, 'rb').read()); b[-20] ^= 0xFF; open(p, 'wb').write(bytes(b)); self.fails('SHA-256 is recorded')
    def test_a_click_without_a_reason_fails(self):
        f = self.data + 'plays_b2.jsonl'; out = []
        for l in open(f):
            r = json.loads(l)
            if r['play'] == 'P04' and r['status'] == 'ok': r['clicks'][0]['why'] = None
            out.append(json.dumps(r))
        open(f, 'w').write('\n'.join(out) + '\n'); self.fails('every click has a recorded reason')
    def test_an_unverified_tick_click_fails(self):
        f = self.data + 'plays_b2.jsonl'; out = []
        for l in open(f):
            r = json.loads(l)
            if r['play'] == 'P04' and r['status'] == 'ok':
                r['verified'] = [v for v in r['verified'] if not v['step'].startswith('tick Ptolemaic')]
            out.append(json.dumps(r))
        open(f, 'w').write('\n'.join(out) + '\n'); self.fails('tick-box clicks')

class RemovedClaims(Base):
    def remove_rows(self, ids):
        lines = open(self.finding, encoding='utf-8').read().split('\n')
        out = [l for l in lines if not any(l.startswith('| %s |' % i) for i in ids)]
        s = '\n'.join(out)
        for i in ids: s = re.sub(r'(\| [^|]*)\b%s, ' % i, r'\1', s); s = re.sub(r', %s\b' % i, '', s)
        open(self.finding, 'w', encoding='utf-8').write(s)
    def test_the_sixteen_humans_claim_removed_from_the_rules_and_the_clone_table_still_fails(self):
        self.remove_rows(['T06']); n, bad = self.audit()
        text = '\n'.join(bad); self.assertIn('play P05 is cited by at least one rule row', text); self.assertIn('required play is cited by a rule row: 16 humans', text)
    def test_the_escape_and_return_claim_removed_consistently_still_fails(self):
        self.remove_rows(['C04']); n, bad = self.audit(); text = '\n'.join(bad)
        self.assertIn('play P11 is cited', text); self.assertIn('required: the form closed by Escape and by Return', text)
    def test_a_play_removed_from_the_plays_table_fails(self):
        self.remove_rows(['P05'])
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'\n\| P05 \|[^\n]*', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        self.fails('plays table lists exactly the ok plays')
    def test_a_doctored_count_fails(self):
        self.edit_finding('| plays recorded ok | 15 |', '| plays recorded ok | 14 |'); self.fails('count plays recorded ok')
    def test_a_confirmed_row_without_a_screenshot_fails(self):
        self.edit_finding('P06; LF_P06_b3_before_ok_form.png; LF_P06_b3_AUTO0720.SAV | P06 form.before_ok.Carthage.text', 'P06; LF_P06_b3_AUTO0720.SAV | P06 form.before_ok.Carthage.text'); self.fails('N04 confirmed rows cite a screenshot')
    def test_a_derived_row_that_cites_a_play_fails(self):
        self.edit_finding('| [derived] | - | dfm PickLeaders.Caption', '| [derived] | P01 | dfm PickLeaders.Caption'); self.fails('derived rows cite no play')

if __name__ == '__main__': unittest.main()
