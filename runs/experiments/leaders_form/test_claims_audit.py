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
    def edit(self, tag, fn):
        for f in glob.glob(self.data + 'plays_*.jsonl'):
            if tag in open(f).read(): rewrite(f, lambda r: fn(r) if r.get('tag') == tag else None); return
        raise AssertionError(tag)
    def recs(self): return [json.loads(l) for f in sorted(glob.glob(self.data + 'plays_*.jsonl')) for l in open(f) if l.strip()]
    def remove_rows(self, ids):
        lines = open(self.finding, encoding='utf-8').read().split('\n')
        s = '\n'.join(l for l in lines if not any(l.startswith('| %s |' % i) for i in ids))
        for i in ids: s = re.sub(r'(\| [^|]*)\b%s, ' % i, r'\1', s); s = re.sub(r', %s\b' % i, '', s); s = re.sub(r'(\| )%s(?= \|)' % i, r'\1-', s)
        open(self.finding, 'w', encoding='utf-8').write(s)
    def rehash(self, path):
        """a doctored artifact whose hash is rewritten everywhere (SAVES.sha256, the manifests): only the claims can catch it"""
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest(); name = os.path.basename(path)
        sf = self.latest('SAVES.sha256'); open(sf, 'a').write('%s  %s\n' % (h, name))
        for m in glob.glob(self.data + 'MANIFEST-*.txt'):
            t = open(m).read()
            if 'member:saves/' + name in t: open(m, 'w').write(re.sub(r'[0-9a-f]{64}(  member:saves/%s)' % re.escape(name), h + r'\1', t))
        return h
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
    """R1: every number and operation word of a claim lies in a phrase whose check DERIVES it from a source (operand, operation and direction); a number bound elsewhere in the row, a reversed word and a source-free check each fail"""
    def test_a_changed_number_in_the_prose_fails(self):
        self.edit_finding("The name box limit is 25 characters", "The name box limit is 26 characters"); self.fails('N01', 'the phrase is in the prose of the row')
    def test_a_changed_hex_number_in_the_prose_fails(self):
        self.edit_finding("at most 0x1a bytes, so 25 characters", "at most 0x1b bytes, so 25 characters"); self.fails('O03', '0x1b')
    def test_at_least_450_changed_to_25_a_number_bound_elsewhere_in_the_row_fails(self):
        self.edit_finding("word becomes at least 450 (the larger", "word becomes at least 25 (the larger"); self.fails('O03', 'at least')
    def test_the_phrase_and_the_prose_changed_together_still_fail_against_the_floor_the_code_has(self):
        self.edit_finding("word becomes at least 450 (the larger", "word becomes at least 25 (the larger")
        self.edit_finding('says "+0x440 word becomes at least 450" :: code floor 56949-56951 field 0x440 min 450 fn FUN_00448fd8', 'says "+0x440 word becomes at least 25" :: code floor 56949-56951 field 0x440 min 450 fn FUN_00448fd8')
        self.fails('O03', 'every number of the phrase is vouched for')
    def test_the_larger_changed_to_the_smaller_in_the_prose_fails(self):
        self.edit_finding("(the larger of its value and 450)", "(the smaller of its value and 450)"); self.fails('O03')
    def test_the_larger_changed_to_the_smaller_in_the_prose_and_the_phrase_fails_on_the_operation(self):
        self.edit_finding("(the larger of its value and 450)", "(the smaller of its value and 450)")
        self.edit_finding('says "the larger of its value and 450"', 'says "the smaller of its value and 450"'); self.fails('O03', 'says an operation')
    def test_a_floor_check_of_the_wrong_kind_under_an_operation_word_fails(self):
        self.edit_finding('says "+0x440 word becomes at least 450" :: code floor 56949-56951 field 0x440 min 450 fn FUN_00448fd8', 'says "+0x440 word becomes at least 450" :: code 56949 has 0x1c2'); self.fails('O03', 'says an operation')
    def test_a_source_free_calc_is_refused_as_evidence(self):
        self.edit_finding('says "25 characters" :: calc {0x1a@56954} - 1 == 25', 'says "25 characters" :: calc 25 == 25'); self.fails('O03', 'has a sourced operand')
    def test_a_new_prose_number_bound_by_a_tautology_fails(self):
        self.edit_finding("including the NUL (the running", "including the NUL, 26 in all (the running"); self.edit_finding('says "resource says 25" ::', 'says "26 in all" :: calc 26 == 26 ;; says "resource says 25" ::'); self.fails('N01', 'has a sourced operand')
    def test_a_calc_operand_that_is_not_in_its_source_fails(self):
        self.edit_finding('calc {0x1a@56954} - 1 == 25', 'calc {0x1b@56954} - 1 == 26'); self.fails('O03', 'is found in its source')
    def test_a_count_changed_in_the_answer_fails(self):
        self.edit_finding("cuts a longer text to 25 characters", "cuts a longer text to 26 characters"); self.fails('section "Answer"', 'the number 26')
    def test_a_number_bound_in_another_cited_row_but_not_for_this_claim_fails_in_the_answer(self):
        self.edit_finding("cuts a longer text to 25 characters", "cuts a longer text to 450 characters"); self.fails('section "Answer"', 'the number 450')
    def test_at_most_changed_to_at_least_in_the_answer_fails(self):
        self.edit_finding("OK reads at most 0x1a bytes including the NUL), and **OK**", "OK reads at least 0x1a bytes including the NUL), and **OK**"); self.fails('section "Answer"', 'at least')
    def test_a_changed_number_in_a_clone_row_fails(self):
        self.edit_finding("The name box limit is 25 characters;", "The name box limit is 24 characters;"); self.fails('clone row X03')
    def test_a_clone_word_that_reverses_a_rule_fails_the_verbatim_fragment(self):
        self.edit_finding("the first to play is the first human in the order;", "the first to play is the last human in the order;"); self.fails('clone row X07', 'verbatim piece')
    def test_a_changed_count_in_a_fact_fails(self):
        self.edit_finding("lie between 532 (Greece, the lowest) and 838", "lie between 531 (Greece, the lowest) and 838"); self.fails('V01')
    def test_the_lowest_changed_to_the_highest_in_a_fact_fails(self):
        self.edit_finding("532 (Greece, the lowest)", "532 (Greece, the highest)"); self.fails('V01')
    def test_a_spelled_number_changed_fails(self):
        self.edit_finding("Six humans and sixteen humans are accepted too", "Seven humans and sixteen humans are accepted too"); self.fails('T06')
        self.setUp(); self.edit_finding("Two humans (Carthage, Ptolemaic): the flags", "Three humans (Carthage, Ptolemaic): the flags"); self.fails('T05', 'spelled number')

    def test_r1_the_minimum_changed_to_the_field_address_in_prose_and_phrase_together_fails(self):
        """round-3 R1: 450 -> 1088 (= 0x440, the field address read as a decimal) in the prose and the phrase; the check still verifies a floor of 450"""
        self.edit_finding("word becomes at least 450 (the larger", "word becomes at least 1088 (the larger")
        self.edit_finding('says "+0x440 word becomes at least 450" :: code floor', 'says "+0x440 word becomes at least 1088" :: code floor')
        self.fails('O03', 'is in the role min of the floor')
    def test_r1_the_field_address_replaced_by_the_minimum_in_the_phrase_fails(self):
        self.edit_finding("the nation's `+0x440` word becomes at least 450", "the nation's `+0x1c2` word becomes at least 450")
        self.edit_finding('says "+0x440 word becomes at least 450" :: code floor', 'says "+0x1c2 word becomes at least 450" :: code floor'); self.fails('O03', 'is in the role field of the floor')
    def test_r1_a_calc_operand_claimed_in_place_of_its_result_fails(self):
        """the check calc {0x1a} - 1 == 25 vouches for the result 25, not for the operand 0x1a"""
        self.edit_finding("so 25 characters and a NUL", "so 0x1a characters and a NUL"); self.edit_finding('says "25 characters" :: calc {0x1a@56954} - 1 == 25', 'says "0x1a characters" :: calc {0x1a@56954} - 1 == 25'); self.fails('O03', 'every number of the phrase is vouched for')
    def test_r2_six_humans_changed_to_seven_in_the_prose_the_phrase_and_the_clone_fragment_together_fails(self):
        """round-3 R2: 'Seven' was not a number to the audit"""
        self.edit_finding("Six humans and sixteen humans are accepted too", "Seven humans and sixteen humans are accepted too", count=2)
        self.edit_finding('says "Six humans" ::', 'says "Seven humans" ::'); self.fails('T06', 'every number of the phrase is vouched for')
    def test_r2_every_spelled_number_is_a_number(self):
        for w, v in (('zero', 0), ('one human', 1), ('seven', 7), ('nine', 9), ('eleven', 11), ('thirteen', 13), ('fourteen', 14), ('fifteen', 15), ('seventeen', 17), ('twenty', 20), ('a dozen', 12), ('Sixty', 60)):
            self.assertIn(('d', v), claims_audit.spelled(w), w)
        self.assertEqual(claims_audit.spelled('one OK, when one matches'), set())
    def test_the_order_of_two_steps_swapped_in_the_prose_fails(self):
        self.edit_finding("New Game calls the DAT loader, then the setup", "New Game calls the setup, then the DAT loader"); self.fails('D01')
    def test_a_code_order_claim_with_the_lines_in_the_wrong_order_fails(self):
        self.edit_finding('code order nl:20 < nl:37', 'code order nl:37 < nl:20'); self.fails('W03', 'must be in one function, the first before the second')
    def test_a_floor_claimed_for_another_field_fails(self):
        self.edit_finding('says "+0x440 word becomes at least 450" :: code floor 56949-56951 field 0x440 min 450', 'says "+0x440 word becomes at least 450" :: code floor 56949-56951 field 0x442 min 450'); self.fails('O03')
    def test_a_then_word_not_covered_by_an_order_check_fails(self):
        self.edit_finding('says "then, when no human is left" :: code order 47790 < 47792', 'says "then, when no human is left" :: code 47790 has FUN_0040284c(0xc)'); self.fails('W04', 'says an operation')

class ExtractLines(Base):
    def mutate(self, old, new): p = self.latest('code_extract_leaders.txt'); self.edit_file(p, old, new)
    def test_a_doctored_extract_line_fails(self):
        self.mutate("if (puVar6[0x490] != '\\0') {", "if (puVar6[0x490] == '\\0') {"); self.fails('O02')
    def test_a_message_box_call_added_to_ok_fails(self):
        self.mutate("    puVar6[0x490] = 0;", "    FUN_0042d750(0); puVar6[0x490] = 0;"); self.fails('O01')
    def test_a_second_return_in_ok_fails(self):
        self.mutate("    puVar6[0x490] = 0;", "    return; puVar6[0x490] = 0;"); self.fails('O01')
    def test_the_maximum_changed_to_a_minimum_fails_every_rule_that_uses_it(self):
        self.mutate("if ((short)param_1 <= (short)param_2) {", "if ((short)param_1 >= (short)param_2) {"); self.fails('O02', 'O03', 'O09')
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
        self.edit_finding('TPickLeaders_OK:56930, TPickLeaders_OK:56931', 'TPickLeaders_OK:56930, TPickLeaders_OK:56960'); self.fails('is read by a check of the row')
    def test_a_doctored_loader_read_changes_the_pool_offset(self):
        self.mutate('(piVar2,&DAT_0045e870,0x15e00)', '(piVar2,&DAT_0045e870,0x15e01)'); self.fails('pool offset')
    def test_a_doctored_pool_name_fails(self):
        self.edit_file(self.latest('dat_leader_pool.tsv'), '\t3\tAppius Claudius', '\t3\tAppius Claudia'); self.fails('draws row P01')
    def test_the_sixteen_leader_loop_cited_at_the_wrong_loop_fails(self):
        self.edit_finding('code nl:71 has while (sVar5 != 0x10)', 'code nl:78 has while (sVar1 != 0x10)'); self.fails('D01')

class Obligations(Base):
    """R3: the obligations come from the code (every branch arm and statement of the form's handlers) and from the recordings, not from the finding: a derived behaviour removed consistently still fails"""
    def test_the_already_human_name_edit_row_removed_consistently_fails_on_its_branch_arms(self):
        self.remove_rows(['O04']); self.fails('branch arm TPickLeaders_OK:56929 implicit-else')
    def test_every_rule_row_removed_consistently_fails(self):
        ids = re.findall(r'^\| ([A-Z]\d\d) \| \d \|', open(FINDING, encoding='utf-8').read(), re.M); self.assertGreater(len(ids), 50)
        survivors = []
        for i in ids:
            shutil.copy(FINDING, self.finding); self.remove_rows([i]); n, bad = self.audit()
            if not bad: survivors.append(i)
        self.assertEqual(survivors, [], 'removing these rows consistently left the audit passing')
    def test_a_range_that_names_an_absent_id_fails_in_the_answer(self):
        self.edit_finding('(H01-H04)', '(H01-H05)'); self.fails('the cited id H05 exists')
    def test_a_branch_claim_for_an_arm_the_code_does_not_have_fails(self):
        self.edit_finding('branch TPickLeaders_OK:56930 implicit-else', 'branch TPickLeaders_OK:56930 else'); self.fails('the code has this branch arm')
    def test_a_branch_arm_added_to_the_code_without_a_row_fails(self):
        self.edit_file(self.latest('code_extract_leaders.txt'), '56892\t  else {', '56892\t  else if (iVar2 == 7) {\n  }\n  else {'); self.fails('branch arm TPickLeaders_HumanOrComputer')
    def test_a_statement_added_inside_a_covered_range_fails(self):
        self.edit_file(self.latest('code_extract_leaders.txt'), "    puVar6[0x490] = 0;", "    puVar6[0x491] = 1; puVar6[0x490] = 0;"); self.fails('O02')
    def test_the_name_lands_obligation_comes_from_the_recordings(self):
        self.remove_rows(['N09']); self.fails('the name lands in the nation record')
    def test_the_default_form_obligation_comes_from_the_recordings(self):
        self.remove_rows(['D03']); self.fails('the default form has every tick clear')

class Inventory(Base):
    """the claims, controls, handlers and plays the task requires must be in the finding, from sources other than the finding"""
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
        self.assertTrue(any('16 human(s) ticked' in b for b in bad))
    def test_the_escape_and_return_claim_removed_consistently_still_fails(self):
        self.remove_rows(['C04']); n, bad = self.audit(); text = '\n'.join(bad)
        self.assertIn('Escape discards the ticks', text)
    def test_the_cancel_handler_removed_from_every_derived_row_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'(, )?TPickLeaders_Cancel:\d+', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        n, bad = self.audit(); self.assertIn('handler TPickLeaders_Cancel of the task is read by a derived rule', '\n'.join(bad))
    def test_a_play_removed_from_the_plays_table_fails(self):
        s = open(self.finding, encoding='utf-8').read(); s = re.sub(r'\n\| P05 \|[^\n]*', '', s); open(self.finding, 'w', encoding='utf-8').write(s)
        self.fails('plays table lists exactly the play ids')
    def test_a_play_with_a_doctored_seed_in_the_plays_table_fails(self):
        self.edit_finding('| 12345 then 777 | ok |', '| 12345 then 778 | ok |'); self.fails('plays table: P09 seed')
    def test_a_confirmed_row_without_a_screenshot_fails(self):
        self.edit_finding('; LF_P06_b8_before_ok_form.png', '', count=1); self.fails('evidence files are exactly')
    def test_a_derived_row_that_cites_a_play_fails(self):
        self.edit_finding('| [derived] | - | dfm PickLeaders.Caption', '| [derived] | P01 | dfm PickLeaders.Caption'); self.fails('derived rows cite no play')
    def test_a_derived_row_that_reads_a_play_fails(self):
        self.edit_finding('dfm PickLeaders.Caption == @literal ;; dfm PickLeaders.ClientWidth', 'dfm PickLeaders.Caption == @literal ;; P01 form.default.limits len== 16 ;; dfm PickLeaders.ClientWidth'); self.fails('F25 derived rows read no play')

class PlaysTable(Base):
    """R2: the `what` column of the plays table is bound, phrase by phrase, to the recording's verified steps and the state it left"""
    def test_all_sixteen_humans_changed_to_zero_humans_and_cancel_fails(self):
        self.edit_finding('| P05 | all sixteen humans; OK |', '| P05 | zero humans; Cancel |'); self.fails('plays table: P05')
    def test_ok_changed_to_cancel_fails(self):
        self.edit_finding('| P02 | zero humans; OK |', '| P02 | zero humans; Cancel |'); self.fails('plays table: P02')
    def test_a_recorded_closer_left_unsaid_fails(self):
        self.edit_finding('| P01 | the form as it opens; tab order of the first 8 presses; nothing ticked; Cancel |', '| P01 | the form as it opens; tab order of the first 8 presses; nothing ticked |'); self.fails('P01 says everything the recording did')
    def test_six_humans_changed_to_two_fails(self):
        self.edit_finding('| P06 | six humans;', '| P06 | two humans;'); self.fails('plays table: P06')
    def test_a_nation_named_that_was_not_ticked_fails(self):
        self.edit_finding('| P04 | two humans (Carthage, Ptolemaic);', '| P04 | two humans (Carthage, Seleucid);'); self.fails('plays table: P04')
    def test_a_phrase_the_audit_does_not_understand_fails(self):
        self.edit_finding('| P02 | zero humans; OK |', '| P02 | zero humans; OK; everything went well |'); self.fails('is a phrase the audit understands')
    def test_the_first_game_step_dropped_from_p09_fails(self):
        self.edit_finding('| P09 | tick Carthage; OK; a second', '| P09 | a second'); self.fails('plays table: P09')

class StepPlan(Base):
    """R4: the expected action sequence of a play comes from the play definition (scenarios.py), not from the record's labels; unknown step kinds are refused; others_unchanged is recomputed from the retained before/after output"""
    def test_an_unknown_step_label_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': v['step'] = 'zzz Carthage on'; break
        self.edit('LF_P04_b8', f); self.fails("one of the runner's step kinds", 'prescribes')
    def test_a_step_relabelled_to_another_known_kind_fails_the_play_definition(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': v['step'] = 'tick Carthage off'; break
        self.edit('LF_P04_b8', f); self.fails('prescribes')
    def test_a_step_dropped_from_a_record_fails_the_play_definition(self):
        def f(r): r['verified'] = [v for v in r['verified'] if v['step'] != 'name Carthage']
        self.edit('LF_P04_b8', f); self.fails('prescribes')
    def test_another_row_changed_in_the_retained_output_fails_the_recomputed_flag(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': v['raw_after'] = v['raw_after'].replace('Appius Claudius', 'Appius Claudiux'); break
        self.edit('LF_P04_b8', f); self.fails('recorded rows_after equals what the raw helper output gives', 'the other 15 rows are unchanged')
    def test_a_flag_flipped_while_the_output_is_unchanged_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': v['others_unchanged'] = False; break
        self.edit('LF_P04_b8', f); self.fails('recorded others_unchanged equals what the raw helper output gives')
    def test_a_step_without_the_retained_output_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': del v['raw_before']; break
        self.edit('LF_P04_b8', f); self.fails('retains the raw helper output before and after the step')
    def test_a_seed_that_differs_from_the_play_definition_fails(self):
        def f(r): r['new_games'][0]['seed'] = 999
        self.edit('LF_P01_b8', f); self.fails('the New Games it started have the seeds the play definition prescribes')
    def test_the_play_definition_is_what_the_plan_reads(self):
        import play_plans
        pl = play_plans.plan_of(os.path.join(HERE, 'scenarios.py'), 'P09'); self.assertEqual(pl.seeds, [12345, 777, 777]); self.assertEqual(pl.steps.count('confirm Yes'), 1)
        self.assertEqual(play_plans.plan_of(os.path.join(HERE, 'scenarios.py'), 'P10').steps[-1], 'confirm No')

class RawDumps(Base):
    """R5: every claimed nation field is decoded from the raw nation dump, every form summary and step state from the retained helper output; the JSON copies are only compared"""
    def test_a_treasury_changed_consistently_in_the_finding_and_the_json_still_fails_against_the_dump(self):
        self.edit_finding('P06 mem.nations[1].treasury_0x438 == 11000', 'P06 mem.nations[1].treasury_0x438 == 12000')
        def f(r): r['state']['nations'][1]['treasury_0x438'] = 12000
        self.edit('LF_P06_b8', f); self.fails('O05', 'the recorded JSON equals what the raw dumps decode to')
    def test_the_treasury_in_the_json_only_fails(self):
        def f(r): r['state']['nations'][1]['treasury_0x438'] = 12000
        self.edit('LF_P06_b8', f); self.fails('the recorded JSON equals what the raw dumps decode to')
    def test_a_doctored_dump_with_every_hash_rewritten_fails_its_claims(self):
        r = [x for x in self.recs() if x.get('tag') == 'LF_P04_b8'][0]; name = r['dumps']['state']['nations_bin']; p = self.art + 'saves/' + name
        b = bytearray(open(p, 'rb').read()); i = 1 * 1172 + 0x0B; b[i] = ord('Q'); open(p, 'wb').write(bytes(b)); self.rehash(p)
        def f(rr): rr['dumps']['state']['nations_bin_sha'] = hashlib.sha256(bytes(b)).hexdigest()
        self.edit('LF_P04_b8', f); self.fails('P04', 'the recorded JSON equals what the raw dumps decode to')
    def test_r3_one_byte_after_the_nul_changed_in_the_dump_with_every_hash_and_the_json_rewritten_fails_the_same_bytes_claim(self):
        """round-3 R3: the leader strings still agree, the 26-byte fields no longer do"""
        r = [x for x in self.recs() if x.get('tag') == 'LF_P04_b8'][0]; name = r['dumps']['state']['nations_bin']; p = self.art + 'saves/' + name
        b = bytearray(open(p, 'rb').read()); i = 1 * 1172 + 0x0B + 20; old = b[i]; b[i] = old ^ 0x55; open(p, 'wb').write(bytes(b)); self.rehash(p)
        def f(rr):
            rr['dumps']['state']['nations_bin_sha'] = hashlib.sha256(bytes(b)).hexdigest(); n = rr['state']['nations'][1]
            n['leader_hex'] = bytes(b[1172 + 0x0B:1172 + 0x0B + 26]).hex(); n['sha'] = hashlib.sha256(bytes(b[1172:2 * 1172])).hexdigest()
        self.edit('LF_P04_b8', f); self.fails('N09', 'the same bytes in both')
    def test_a_form_summary_that_differs_from_the_retained_output_fails(self):
        def f(r): r['forms']['default']['rows'][3][4] = 1
        self.edit('LF_P08a_b8', f); self.fails('the recorded rows and focus equal the audit')
    def test_a_doctored_raw_output_fails_against_the_recorded_summary(self):
        def f(r): r['forms']['default']['raw'] = r['forms']['default']['raw'].replace('Antipater', 'Antipatex')
        self.edit('LF_P08a_b8', f); self.fails('the recorded rows and focus equal the audit')
    def test_a_doctored_raw_output_and_summary_together_fail_the_names_in_the_dump_and_the_pool(self):
        def f(r):
            r['forms']['default']['raw'] = r['forms']['default']['raw'].replace('Antipater', 'Antipatex')
            for row in r['forms']['default']['rows']:
                if row[3] == 'Antipater': row[3] = 'Antipatex'
        self.edit('LF_P08a_b8', f); self.fails('P08a')
    def test_the_immediate_post_tick_state_doctored_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'] == 'tick Carthage on': v['post']['sel1'] = 2
        self.edit('LF_P07_b8', f); self.fails('recorded post equals what the raw helper output gives')
    def test_a_missing_memory_dump_fails(self):
        os.remove(self.art + 'saves/LF_P02_b8_after_ok_nations.bin'); self.fails('LF_P02_b8_after_ok_nations.bin exists')
    def test_a_missing_globals_dump_fails(self):
        os.remove(self.art + 'saves/LF_P02_b8_after_ok_globals.bin'); self.fails('LF_P02_b8_after_ok_globals.bin exists')

class StateEvidence(Base):
    """R6: a [confirmed] row cites the precise recorded observation and the state evidence the task requires (a save or a memory dump)"""
    def test_a_confirmed_row_without_a_save_or_a_dump_fails(self):
        s = open(self.finding, encoding='utf-8').read()
        s = s.replace('LF_P01_b8_after_cancel_globals.bin; LF_P01_b8_after_cancel_nations.bin; ', '', 1) if False else s
        self.edit_finding('| P01; LF_P01_b8:forms.default; LF_P01_b8_after_cancel_globals.bin; LF_P01_b8_after_cancel_nations.bin; LF_P01_b8_default_form.png |', '| P01; LF_P01_b8:forms.default; LF_P01_b8_default_form.png |')
        self.fails('confirmed rows cite state evidence the task requires')
    def test_a_confirmed_row_without_the_observation_it_reads_fails(self):
        self.edit_finding('LF_P01_b8:forms.default; ', '', count=1); self.fails('evidence files are exactly')
    def test_a_form_only_confirmed_row_is_refused(self):
        row = '| F30 | 1 | The running name box reports the limit 25 for each of the 16 rows | - | - | [confirmed] | P01; LF_P01_b8:forms.default; LF_P01_b8_default_form.png | P01 form.default.limits len== 16 |\n'
        self.edit_finding('| F31 |', row + '| F31 |'); self.fails('F30 confirmed rows cite state evidence the task requires')
    def test_an_observation_that_does_not_exist_in_the_recording_fails(self):
        self.edit_finding('LF_P01_b8:forms.default;', 'LF_P01_b8:forms.nonexistent;', count=1); self.fails('observation')
    def test_the_form_only_rows_f30_and_f32_are_not_in_the_finding(self):
        s = open(FINDING, encoding='utf-8').read(); self.assertNotIn('| F30 |', s); self.assertNotIn('| F32 |', s)

class Answer(Base):
    """R7: Return and Escape are named only inside the phrases that say what each does"""
    def test_return_said_to_discard_fails(self):
        self.edit_finding('and the Return key what OK does (it commits the current form)', 'and the Return key what Cancel does (it discards the current form)'); self.fails('section "Answer"', 'Return')
    def test_escape_said_to_commit_fails(self):
        self.edit_finding('The Escape key does what Cancel does (it discards', 'The Escape key does what OK does (it commits'); self.fails('section "Answer"', 'Escape')
    def test_both_leave_the_same_world_wording_is_gone(self):
        s = open(FINDING, encoding='utf-8').read(); self.assertNotIn('Both leave the same world', s); self.assertIn('the Return key what OK does (it commits the current form)', s)

class Evidence(Base):
    """a screenshot is bound to the state the check reads; an earlier runner's recording is not evidence"""
    def test_the_before_ok_screenshot_replaced_by_the_default_one_fails(self):
        self.edit_finding('LF_P06_b8_before_ok_form.png', 'LF_P06_b8_default_form.png', count=1)
        n, bad = self.audit(); self.assertTrue(any('evidence files are exactly the files the checks read' in b for b in bad))
    def test_a_screenshot_of_another_play_fails(self):
        self.edit_finding('LF_P06_b8_before_ok_form.png', 'LF_P05_b8_before_ok_form.png', count=1); self.fails('belongs to a cited play')
    def test_a_cited_recording_of_an_earlier_runner_fails(self):
        self.edit_finding('LF_P04_b8_AUTO0720.SAV', 'LF_P04_b6_AUTO0720.SAV', count=1)
        n, bad = self.audit(); self.assertTrue(any('earlier recordings are kept but are not evidence' in b or 'exactly one recording' in b for b in bad))
    def test_an_unused_file_cited_fails(self):
        self.edit_finding('LF_P06_b8_AUTO0720.SAV', 'LF_P06_b8_AUTO0720.SAV; LF_P06_b8_after_ok_screen.png', count=1); self.fails('evidence files are exactly the files the checks read')
    def test_a_missing_screenshot_fails(self):
        os.remove(self.art + 'LF_P04_b8_before_ok_form.png'); self.fails('LF_P04_b8_before_ok_form.png exists')
    def test_a_replaced_screenshot_fails_its_hash(self):
        p = self.art + 'LF_P04_b8_before_ok_form.png'; b = bytearray(open(p, 'rb').read()); b[-20] ^= 0xFF; open(p, 'wb').write(bytes(b)); self.fails('SHA-256 is recorded')
    def test_the_immediate_post_tick_screenshot_missing_fails(self):
        for fn in glob.glob(self.art + 'LF_P07_b8_tick_Carthage_on_post*.png') + glob.glob(self.art + 'saves/LF_P07_b8_tick_Carthage_on_post*.png'): os.remove(fn)
        self.fails('LF_P07_b8_tick_Carthage_on_post.png exists')
    def test_the_post_tick_screenshot_dropped_from_h04_fails(self):
        self.edit_finding('LF_P07_b8_tick_Carthage_on_post.png; ', '', count=1); self.fails('H04 evidence files are exactly')

class Saves(Base):
    def rec(self, play='P04'):
        recs = [json.loads(l) for f in sorted(glob.glob(self.data + 'plays_*.jsonl')) for l in open(f) if l.strip()]
        return [x for x in recs if x['play'] == play and x['status'] == 'ok' and x.get('runner') == 3 and 'autosave_seen' in x][-1]
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
        p, r = self.flip(); h = self.rehash(p); name = os.path.basename(p)
        for rr in glob.glob(self.data + 'plays_b8.jsonl'): rewrite(rr, lambda x: x.update(autosave_sha=h) if x.get('autosave') == name else None)
        self.fails('P04 save.humans', 'the save and the game memory agree')

class Recordings(Base):
    """every recording is kept by its unique tag and audited; the clicks carry an independent pointer and target, and every click and key belongs to a verified step"""
    def test_a_duplicated_recording_fails(self):
        f = self.data + 'plays_b8.jsonl'; lines = open(f).read().splitlines(); open(f, 'w').write('\n'.join(lines + [lines[0]]) + '\n'); self.fails('is unique')
    def test_a_recording_removed_changes_the_counts_and_fails(self):
        f = self.data + 'plays_b1.jsonl'; lines = open(f).read().splitlines(); open(f, 'w').write('\n'.join(lines[:-1]) + '\n'); self.fails('count ')
    def test_a_doctored_count_fails(self):
        self.edit_finding('| successful recordings (all runners) | 64 |', '| successful recordings (all runners) | 15 |'); self.fails('count successful recordings (all runners)')
    def test_unique_play_ids_and_recordings_are_counted_apart(self):
        self.edit_finding('| unique play ids recorded ok | 15 |', '| unique play ids recorded ok | 64 |'); self.fails('count unique play ids recorded ok')
    def test_a_click_without_a_reason_fails(self):
        def f(r): r['clicks'][0]['why'] = None
        self.edit('LF_P04_b8', f); self.fails('every click has a recorded reason')
    def test_a_click_and_its_reason_moved_together_still_fails_against_the_helpers_own_line(self):
        def f(r):
            c = [c for c in r['clicks'] if c['why'].startswith('control TCheckBox')][0]
            c['x'] += 400; c['pointer']['x'] += 400
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
    def test_a_failed_non_menu_step_fails(self):
        def f(r):
            for v in r['verified']:
                if v['step'].startswith('press '): v['ok'] = False; break
        self.edit('LF_P04_b8', f); self.fails('failed attempt of a retried transition')
    def test_a_seed_recorded_for_a_new_game_that_differs_from_the_form_fails(self):
        def f(r): r['new_games'][0]['seed'] = 999
        self.edit('LF_P01_b8', f); self.fails('the New Games it started each record their seed', 'the first New Game used the seed')
    def test_the_draws_table_seed_doctored_fails_for_every_row_even_the_second_new_game(self):
        self.edit_finding('| 777 | P09 |', '| 778 | P09 |'); self.fails('draws row P09: the seed 778')
        self.setUp(); self.edit_finding('| 111 | P08a |', '| 112 | P08a |'); self.fails('draws row P08a: the seed 112')
    def test_a_doctored_slot_fails(self):
        self.edit_finding('`3; 6; 10; 5; 5; 2; 6; 11; 8; 7; 11; 2; 10; 3; 8; 6`', '`3; 6; 10; 5; 5; 2; 6; 11; 8; 7; 11; 2; 10; 3; 8; 7`'); self.fails('draws row P01')
    def test_the_turn_order_of_a_recording_doctored_in_the_json_fails_against_the_dump(self):
        def f(r): r['state']['turn_order'] = list(reversed(r['state']['turn_order']))
        self.edit('LF_P04_b8', f); self.fails('the recorded JSON equals what the raw dumps decode to')
    def test_the_turn_order_in_the_dump_doctored_fails_the_fact_and_the_rule(self):
        r = [x for x in self.recs() if x.get('tag') == 'LF_P04_b8'][0]; p = self.art + 'saves/' + r['dumps']['state']['globals_bin']
        b = bytearray(open(p, 'rb').read()); b[0:2], b[2:4] = b[2:4], b[0:2]; open(p, 'wb').write(bytes(b)); self.rehash(p)
        def f(rr): rr['dumps']['state']['globals_bin_sha'] = hashlib.sha256(bytes(b)).hexdigest()
        self.edit('LF_P04_b8', f); self.fails('W07', 'V02')
    def test_a_nation_score_below_the_floor_in_a_dump_fails_the_fact(self):
        r = [x for x in self.recs() if x.get('tag') == 'LF_P02_b8'][0]; p = self.art + 'saves/' + r['dumps']['state']['nations_bin']
        b = bytearray(open(p, 'rb').read()); struct.pack_into('<h', b, 7 * 1172 + 0x440, 400); open(p, 'wb').write(bytes(b)); self.rehash(p)
        def f(rr): rr['dumps']['state']['nations_bin_sha'] = hashlib.sha256(bytes(b)).hexdigest()
        self.edit('LF_P02_b8', f); self.fails('V01')
    def test_a_default_form_that_is_not_greyed_fails_the_fact(self):
        def f(r):
            r['forms']['default']['rows'][3][4] = 1
            r['forms']['default']['raw'] = r['forms']['default']['raw']
        self.edit('LF_P08a_b8', f); self.fails('the recorded rows and focus equal the audit')

if __name__ == '__main__': unittest.main()
