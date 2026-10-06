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

def rewrite(path, fn):
    """rewrite every record of a plays file through fn(record) (fn mutates in place)"""
    out = []
    for l in open(path):
        if not l.strip(): continue
        r = json.loads(l); fn(r); out.append(json.dumps(r))
    open(path, 'w').write('\n'.join(out) + '\n')

class RealSources(Base):
    def test_the_real_sources_pass(self):
        n, bad = self.audit(); self.assertEqual(bad, []); self.assertGreater(n, 4000)
    def test_a_missing_requested_exe_fails(self):
        n, bad = claims_audit.run(self.finding, self.data, self.art, exe=os.path.join(self.tmp, 'no-such.exe')); self.assertIn('requested --exe exists', '\n'.join(bad))
    def test_a_missing_requested_dat_fails(self):
        n, bad = claims_audit.run(self.finding, self.data, self.art, dat=os.path.join(self.tmp, 'no-such.dat')); self.assertIn('requested --dat exists', '\n'.join(bad))
    def test_an_unrequested_exe_and_dat_are_not_checked(self):
        n, bad = self.audit(); self.assertNotIn('requested', '\n'.join(bad))

class Literals(Base):
    def test_a_doctored_control_literal_fails(self):
        self.edit_finding("| `Leader's name` | 185 |", "| `Leader's Name` | 185 |"); self.fails('F04 literal byte for byte')
    def test_a_doctored_rule_literal_fails(self):
        self.edit_finding("| `Are you sure you want to start a new game ?` | TPremierForm_NewGame:58018", "| `Are you sure you want to start a new game?` | TPremierForm_NewGame:58018"); self.fails('C05')
    def test_a_doctored_caption_with_one_space_fails(self):
        self.edit_finding("| `  Rome` |", "| ` Rome` |"); self.fails('F07 literal byte for byte')
    def test_a_doctored_control_position_fails(self):
        self.edit_finding("| B01 | cbx_rome | TCheckBox | (none) | 100 |", "| B01 | cbx_rome | TCheckBox | (none) | 101 |"); self.fails('B01 left')
    def test_a_doctored_control_property_fails(self):
        self.edit_finding("Width=170; Height=19", "Width=171; Height=19"); self.fails('properties equal the resource')
    def test_an_invented_control_property_fails(self):
        self.edit_finding("| ed_rome | TEdit | (none) | 170 | 1 | 1 | 108 | ", "| ed_rome | TEdit | (none) | 170 | 1 | 1 | 108 | Enabled=False; "); self.fails('properties equal the resource')
    def test_a_doctored_resource_line_fails(self):
        p = self.latest('dfm_TPickLeaders.txt'); self.edit_file(p, 'MaxLength = 25', 'MaxLength = 26'); self.fails('F29')
    def test_a_control_removed_from_the_controls_table_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'\n\| F04 \|[^\n]*', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        self.fails('resource object Label4 (TLabel) has a row in the controls table')
    def test_an_edit_box_removed_from_the_controls_table_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'\n\| B32 \|[^\n]*', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        self.fails('resource object ed_thracia (TEdit) has a row')

class Prose(Base):
    """every number of a rule's prose must be bound to a passing check of its row; a word that claims an operation needs the operation checked"""
    def test_a_changed_number_in_the_prose_fails(self):
        self.edit_finding("The name box limit is 25 characters", "The name box limit is 26 characters"); self.fails('N01 prose number 26')
    def test_a_changed_hex_number_in_the_prose_fails(self):
        self.edit_finding("at most 0x1a bytes, so 25 characters", "at most 0x1b bytes, so 25 characters"); self.fails('O03 prose number 0x1b')
    def test_a_changed_count_in_the_answer_fails(self):
        self.edit_finding("(25 characters at most)", "(26 characters at most)"); self.fails('section "Answer", item', 'the number 26 is bound by a row the item cites')
    def test_a_changed_number_in_a_clone_row_fails(self):
        self.edit_finding("One name box per nation, 25 characters", "One name box per nation, 24 characters"); self.fails('clone row X03: the number 24')
    def test_a_changed_count_in_a_fact_fails(self):
        self.edit_finding("lie between 532 (Greece, the lowest) and 838", "lie between 531 (Greece, the lowest) and 838"); self.fails('V01 statement number 531')
    def test_the_word_at_least_without_the_operation_check_fails(self):
        s = open(self.finding, encoding='utf-8').read()
        s = re.sub(r'( ;; code fn FUN_00448fd8 seq [^|]*?return param_1;)( ;; calc 0x1a)', r'\2', s, count=1); open(self.finding, 'w', encoding='utf-8').write(s); self.fails('O03 prose says')

class ExtractLines(Base):
    def mutate(self, old, new): p = self.latest('code_extract_leaders.txt'); self.edit_file(p, old, new)
    def test_a_doctored_extract_line_fails(self):
        self.mutate("if (puVar6[0x490] != '\\0') {", "if (puVar6[0x490] == '\\0') {"); self.fails('O02')
    def test_a_message_box_call_added_to_ok_fails(self):
        self.mutate("    puVar6[0x490] = 0;", "    FUN_0042d750(0); puVar6[0x490] = 0;"); self.fails('O01')
    def test_a_second_return_in_ok_fails(self):
        self.mutate("    puVar6[0x490] = 0;", "    return; puVar6[0x490] = 0;"); self.fails('O01')
    def test_the_maximum_changed_to_a_minimum_fails_the_rules_that_use_it(self):
        self.mutate("if ((short)param_1 <= (short)param_2) {", "if ((short)param_1 >= (short)param_2) {"); self.fails('O02', 'O03')
    def test_a_changed_floor_fails(self):
        self.mutate("CONCAT22(uVar5,500)", "CONCAT22(uVar5,400)"); self.fails('O02', 'V01')
    def test_a_changed_offset_of_the_word_fails(self):
        self.mutate("CONCAT22(extraout_var_00,*(undefined2 *)(puVar6 + 0x440))", "CONCAT22(extraout_var_00,*(undefined2 *)(puVar6 + 0x442))"); self.fails('O02')
    def test_a_changed_result_offset_fails(self):
        self.mutate("56951\t      *(short *)(puVar6 + 0x440) = (short)uVar2;", "56951\t      *(short *)(puVar6 + 0x442) = (short)uVar2;"); self.fails('O03')
    def test_the_human_flag_set_to_clear_fails(self):
        self.mutate("puVar6[0x490] = 1;", "puVar6[0x490] = 0;"); self.fails('O03')
    def test_a_changed_copy_length_fails(self):
        self.mutate("FUN_00412c6c(piVar3,puVar6 + 0xb,0x1a);", "FUN_00412c6c(piVar3,puVar6 + 0xb,0x1b);"); self.fails('O03')
    def test_a_changed_nation_stride_fails(self):
        self.mutate("puVar6 = puVar6 + 0x494;", "puVar6 = puVar6 + 0x495;"); self.fails('O02', 'F27', 'N09')
    def test_a_changed_pool_stride_fails(self):
        self.mutate("puStack_14 = puStack_14 + 0x138;", "puStack_14 = puStack_14 + 0x139;"); self.fails('O02')
    def test_a_changed_selection_message_fails(self):
        self.mutate("Msg = 0xb1;", "Msg = 0xb0;"); self.fails('H02')
    def test_a_changed_modal_result_fails(self):
        self.mutate("param_1[0x4a] = 2;", "param_1[0x4a] = 1;"); self.fails('C01')
    def test_a_cited_line_moved_to_another_function_fails(self):
        self.edit_finding('TPickLeaders_OK:56930', 'TPickLeaders_Cancel:56930'); self.fails('is in function TPickLeaders_Cancel')
    def test_a_cited_line_that_is_not_in_the_extract_fails(self):
        self.edit_finding('TPickLeaders_OK:56930', 'TPickLeaders_OK:90000'); self.fails('line is in the extract')
    def test_a_cited_line_no_check_reads_fails(self):
        self.edit_finding('TPickLeaders_OK:56930, TPickLeaders_OK:56931', 'TPickLeaders_OK:56930, TPickLeaders_OK:56934'); self.fails('O02 source TPickLeaders_OK:56934 is read by a check')
    def test_a_doctored_loader_read_changes_the_pool_offset(self):
        self.mutate('(piVar2,&DAT_0045e870,0x15e00)', '(piVar2,&DAT_0045e870,0x15e01)'); self.fails('pool offset')
    def test_a_doctored_pool_name_fails(self):
        self.edit_file(self.latest('dat_leader_pool.tsv'), '\t3\tAppius Claudius', '\t3\tAppius Claudia'); self.fails('draws row P01')

class Inventory(Base):
    """the claims, controls, handlers and plays the task requires must be in the finding, from sources other than the finding"""
    def remove_rows(self, ids, table_cols=True):
        lines = open(self.finding, encoding='utf-8').read().split('\n')
        out = [l for l in lines if not any(l.startswith('| %s |' % i) for i in ids)]
        s = '\n'.join(out)
        for i in ids: s = re.sub(r'(\| [^|]*)\b%s, ' % i, r'\1', s); s = re.sub(r', %s\b' % i, '', s); s = re.sub(r'(\| )%s(?= \|)' % i, r'\1-', s)
        open(self.finding, 'w', encoding='utf-8').write(s)
    def test_the_spaces_claim_removed_consistently_still_fails(self):
        self.remove_rows(['N04']); n, bad = self.audit(); self.assertIn('required claim in the finding: a name of spaces is saved as typed', '\n'.join(bad))
    def test_the_empty_name_claim_removed_consistently_still_fails(self):
        self.remove_rows(['N03']); n, bad = self.audit(); self.assertIn('required claim in the finding: an empty name is saved as typed', '\n'.join(bad))
    def test_the_duplicate_name_claim_removed_consistently_still_fails(self):
        self.remove_rows(['N05']); n, bad = self.audit(); self.assertIn('a duplicate name is saved as typed', '\n'.join(bad))
    def test_the_over_long_claim_removed_consistently_still_fails(self):
        self.remove_rows(['N02']); n, bad = self.audit(); self.assertIn('the over-long', '\n'.join(bad))
    def test_the_sixteen_humans_claim_removed_from_the_rules_and_the_clone_table_still_fails(self):
        self.remove_rows(['T06']); n, bad = self.audit()
        text = '\n'.join(bad); self.assertIn('play P05: a recording of runner 3 is cited by a rule row', text); self.assertIn('16 human(s) ticked: the flags in the save are the ticked nations', text)
    def test_the_escape_and_return_claim_removed_consistently_still_fails(self):
        self.remove_rows(['C04']); n, bad = self.audit(); text = '\n'.join(bad)
        self.assertIn('play P11: a recording of runner 3 is cited', text); self.assertIn('Escape discards the ticks', text)
    def test_the_cancel_handler_removed_from_every_derived_row_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'(, )?TPickLeaders_Cancel:\d+', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        n, bad = self.audit(); self.assertIn('handler TPickLeaders_Cancel of the task is read by a derived rule', '\n'.join(bad))
    def test_a_play_removed_from_the_plays_table_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'\n\| P05 \|[^\n]*', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        self.fails('plays table lists exactly the play ids')
    def test_a_play_with_a_doctored_seed_in_the_plays_table_fails(self):
        self.edit_finding('| 12345 then 777 | ok |', '| 12345 then 778 | ok |'); self.fails('plays table: P09 seed')
    def test_a_confirmed_row_without_a_screenshot_fails(self):
        self.edit_finding('P06; LF_P06_b8_before_ok_form.png; LF_P06_b8_AUTO0720.SAV | P06 form.before_ok.Carthage.text', 'P06; LF_P06_b8_AUTO0720.SAV | P06 form.before_ok.Carthage.text'); self.fails('N04 evidence files are exactly', 'N04 confirmed rows cite a screenshot')
    def test_a_derived_row_that_cites_a_play_fails(self):
        self.edit_finding('| [derived] | - | dfm PickLeaders.Caption', '| [derived] | P01 | dfm PickLeaders.Caption'); self.fails('derived rows cite no play')
    def test_a_derived_row_that_reads_a_play_fails(self):
        self.edit_finding('dfm PickLeaders.Caption == @literal ;; dfm PickLeaders.ClientWidth', 'dfm PickLeaders.Caption == @literal ;; P01 form.default.limits len== 16 ;; dfm PickLeaders.ClientWidth'); self.fails('F25 derived rows read no play')

class Evidence(Base):
    """a screenshot is bound to the state the check reads; an earlier runner's recording is not evidence"""
    def test_the_before_ok_screenshot_replaced_by_the_default_one_fails(self):
        self.edit_finding('LF_P06_b8_before_ok_form.png', 'LF_P06_b8_default_form.png', count=1)
        n, bad = self.audit(); self.assertTrue(any('evidence files are exactly the files the checks read' in b for b in bad))
    def test_a_screenshot_of_another_play_fails(self):
        self.edit_finding('LF_P06_b8_before_ok_form.png', 'LF_P05_b8_before_ok_form.png', count=1); self.fails('belongs to a cited play')
    def test_a_cited_recording_of_an_earlier_runner_fails(self):
        self.edit_finding('LF_P04_b8_AUTO0720.SAV', 'LF_P04_b2_AUTO0720.SAV', count=1)
        n, bad = self.audit(); self.assertTrue(any('earlier recordings are kept but are not evidence' in b or 'exactly one recording' in b for b in bad))
    def test_an_unused_file_cited_fails(self):
        self.edit_finding('LF_P06_b8_AUTO0720.SAV', 'LF_P06_b8_AUTO0720.SAV; LF_P06_b8_after_ok_screen.png', count=1); self.fails('evidence files are exactly the files the checks read')
    def test_a_missing_screenshot_fails(self):
        os.remove(self.art + 'LF_P04_b8_before_ok_form.png'); self.fails('LF_P04_b8_before_ok_form.png exists')
    def test_a_missing_memory_dump_fails(self):
        os.remove(self.art + 'saves/LF_P02_b8_after_ok_nations.bin'); self.fails('LF_P02_b8_after_ok_nations.bin exists')
    def test_a_replaced_screenshot_fails_its_hash(self):
        p = self.art + 'LF_P04_b8_before_ok_form.png'; b = bytearray(open(p, 'rb').read()); b[-20] ^= 0xFF; open(p, 'wb').write(bytes(b)); self.fails('SHA-256 is recorded')
    def test_the_immediate_post_tick_state_doctored_fails(self):
        def f(r):
            if r['tag'] == 'LF_P07_b8':
                for v in r['verified']:
                    if v['step'] == 'tick Carthage on': v['post']['sel1'] = 2
        rewrite(self.data + 'plays_b8.jsonl', f); self.fails('H04', 'name box woke at once')
    def test_the_immediate_post_tick_screenshot_missing_fails(self):
        for fn in glob.glob(self.art + 'LF_P07_b8_tick_Carthage_on_post*.png') + glob.glob(self.art + 'saves/LF_P07_b8_tick_Carthage_on_post*.png'): os.remove(fn)
        self.fails('LF_P07_b8_tick_Carthage_on_post.png exists')
    def test_the_post_tick_screenshot_dropped_from_h04_fails(self):
        self.edit_finding('LF_P07_b8_tick_Carthage_on_post.png; ', '', count=1); self.fails('H04 evidence files are exactly')

class Saves(Base):
    def rec(self, play='P04'):
        recs = [json.loads(l) for f in sorted(glob.glob(self.data + 'plays_*.jsonl')) for l in open(f) if l.strip()]
        return [x for x in recs if x['play'] == play and x['status'] == 'ok' and x.get('runner') == 2][-1]
    def human_flag_offset(self, path, nation):
        b = open(path, 'rb').read()
        na = struct.unpack_from('<h', b, SAV.ARMY_OFF)[0]; o = SAV.ARMY_OFF + 2 + na * SAV.ARMY_LEN
        nf = struct.unpack_from('<h', b, o)[0]; o += 2 + nf * SAV.FLEET_LEN
        return o + nation * SAV.NATION_LEN + 0x490
    def flip(self, nation=2):
        r = self.rec(); p = self.art + 'saves/' + r['autosave']; off = self.human_flag_offset(p, nation)
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
        for rr in glob.glob(self.data + 'plays_b8.jsonl'): rewrite(rr, lambda x: x.update(autosave_sha=h) if x.get('autosave') == name else None)
        bad = self.fails('P04 save.humans', 'the save and the game memory agree')
    def test_a_doctored_play_record_fails(self):
        def f(r):
            if r['tag'] == 'LF_P04_b8': r['state']['nations'][1]['human'] = 0
        rewrite(self.data + 'plays_b8.jsonl', f); self.fails('P04')

class Recordings(Base):
    """every recording is kept by its unique tag and audited; the clicks of runner 3 carry an independent pointer and target, and every click and key belongs to a verified step"""
    def edit(self, tag, fn):
        for f in glob.glob(self.data + 'plays_*.jsonl'):
            if tag in open(f).read(): rewrite(f, lambda r: fn(r) if r.get('tag') == tag else None); return
        raise AssertionError(tag)
    def test_a_duplicated_recording_fails(self):
        f = self.data + 'plays_b8.jsonl'; lines = open(f).read().splitlines(); open(f, 'w').write('\n'.join(lines + [lines[0]]) + '\n'); self.fails('is unique')
    def test_a_recording_removed_changes_the_counts_and_fails(self):
        f = self.data + 'plays_b1.jsonl'; lines = open(f).read().splitlines(); open(f, 'w').write('\n'.join(lines[:-1]) + '\n'); self.fails('count ')
    def test_a_doctored_count_fails(self):
        self.edit_finding('| successful recordings (all runners) | 34 |', '| successful recordings (all runners) | 15 |'); self.fails('count successful recordings (all runners)')
    def test_unique_play_ids_and_recordings_are_counted_apart(self):
        self.edit_finding('| unique play ids recorded ok | 15 |', '| unique play ids recorded ok | 34 |'); self.fails('count unique play ids recorded ok')
    def test_a_click_without_a_reason_fails(self):
        def f(r): r['clicks'][0]['why'] = None
        self.edit('LF_P04_b8', f); self.fails('every click has a recorded reason')
    def test_a_click_and_its_reason_moved_together_still_fails_against_the_helpers_own_line(self):
        def f(r):
            c = [c for c in r['clicks'] if c['why'].startswith('control TCheckBox')][0]
            c['x'] += 400; c['pointer']['x'] += 400; c['why'] = c['why'].replace(' at %d,' % (c['x'] - 400), ' at %d,' % (c['x'] - 400))     # the click leaves the control; the reason and the pointer follow
            m = re.match(r"control (\w+) '(.*)' at (\d+),(\d+) (\d+)x(\d+)$", c['why']); c['why'] = "control %s '%s' at %d,%s %sx%s" % (m.group(1), m.group(2), int(m.group(3)) + 400, m.group(4), m.group(5), m.group(6)); c['target']['x'] += 400
        self.edit('LF_P04_b8', f); self.fails('lies inside the rectangle of the helper')
    def test_a_reset_step_removed_before_a_menu_opening_fails(self):
        def f(r):
            i = [k for k, v in enumerate(r['verified']) if v['step'] == 'reset'][0]; r['verified'][i]['step'] = 'tab walk'
        self.edit('LF_P04_b8', f); n, bad = self.audit(); self.assertTrue(any('is directly preceded by a verified reset' in b for b in bad))
    def test_a_reset_point_inside_a_window_fails(self):
        def f(r):
            v = [v for v in r['verified'] if v['step'] == 'reset'][0]; v['windows'].append([5, 'x', v['point'][0] - 1, v['point'][1] - 1, 10, 10])
        self.edit('LF_P04_b8', f); self.fails('clicked a point no window covers')
    def test_a_menu_item_click_without_the_menu_proven_open_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'menu open file': v['ok'] = False; v['hit'] = None; break
        self.edit('LF_P04_b8', f); n, bad = self.audit(); self.assertTrue(any('follows an opened menu' in b for b in bad))
    def test_a_pointer_that_differs_from_the_click_fails(self):
        def f(r): r['clicks'][1]['pointer']['x'] += 5
        self.edit('LF_P04_b8', f); self.fails('went where the pointer was read')
    def test_a_click_without_a_pointer_record_fails(self):
        def f(r): del r['clicks'][2]['pointer']
        self.edit('LF_P04_b8', f); self.fails('records the pointer read back')
    def test_a_reset_click_not_on_the_root_window_fails(self):
        def f(r):
            c = r['clicks'][0]; c['pointer']['window'] = c['pointer']['window'] + 1
        self.edit('LF_P04_b8', f); self.fails('bare root window')
    def test_a_click_outside_every_step_fails(self):
        def f(r): r['verified'] = [v for v in r['verified'] if not v['step'].startswith('tick Ptolemaic')]
        self.edit('LF_P04_b8', f); self.fails('every click belongs to exactly one verified step')
    def test_a_key_outside_every_step_fails(self):
        def f(r): r['keys'].append({'keys': ['space'], 'why': 'x'})
        self.edit('LF_P04_b8', f); self.fails('every key and typed text belongs to exactly one verified step')
    def test_a_step_with_more_clicks_than_attempts_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('tick '): v['attempts'] = 2; break
        self.edit('LF_P04_b8', f); self.fails('clicks equal the attempts')
    def test_a_step_without_the_other_rows_unchanged_field_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('tick '): del v['others_unchanged']; break
        self.edit('LF_P04_b8', f); self.fails('records that the other 15 rows are unchanged')
    def test_a_step_that_reports_the_other_rows_changed_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('name '): v['others_unchanged'] = False; break
        self.edit('LF_P04_b8', f); self.fails('records that the other 15 rows are unchanged')
    def test_a_failed_non_menu_step_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('press '): v['ok'] = False; break
        self.edit('LF_P04_b8', f); self.fails('failed attempt of a retried transition')
    def test_a_tick_step_without_the_post_state_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('tick ') and v['step'].endswith(' on'): del v['post']; break
        try: self.edit('LF_P04_b8', f)
        except Exception: pass
        n, bad = self.audit(); self.assertTrue(bad)
    def test_a_seed_recorded_for_a_new_game_that_differs_from_the_form_fails(self):
        def f(r): r['new_games'][0]['seed'] = 999
        self.edit('LF_P01_b8', f); self.fails('the New Games it started each record their seed', 'the first New Game used the seed')
    def test_the_draws_table_seed_doctored_fails_for_every_row_even_the_second_new_game(self):
        self.edit_finding('| 777 | P09 |', '| 778 | P09 |'); self.fails('draws row P09: the seed 778')
        self.setUp(); self.edit_finding('| 111 | P08a |', '| 112 | P08a |'); self.fails('draws row P08a: the seed 112')
    def test_a_doctored_slot_fails(self):
        self.edit_finding('`3; 6; 10; 5; 5; 2; 6; 11; 8; 7; 11; 2; 10; 3; 8; 6`', '`3; 6; 10; 5; 5; 2; 6; 11; 8; 7; 11; 2; 10; 3; 8; 7`'); self.fails('draws row P01')
    def test_the_turn_order_of_a_recording_doctored_fails_the_fact_and_the_rule(self):
        def f(r): r['state']['turn_order'] = list(reversed(r['state']['turn_order']))
        self.edit('LF_P04_b8', f); self.fails('W07', 'V02')
    def test_a_nation_score_below_the_floor_in_a_record_fails_the_fact(self):
        def f(r): r['state']['nations'][7]['score_0x440'] = 400
        self.edit('LF_P02_b8', f); self.fails('V01')
    def test_a_default_form_that_is_not_greyed_fails_the_fact(self):
        def f(r):
            r['forms']['default']['rows'][3][4] = 1
        self.edit('LF_P08a_b8', f); self.fails('V04')
    def test_an_initial_current_nation_that_is_not_first_in_the_order_fails_the_fact(self):
        def f(r): r['state']['cur_nation'] = (r['state']['turn_order'][0] + 1) % 16
        self.edit('LF_P01_b8', f); self.fails('V03')

if __name__ == '__main__': unittest.main()
