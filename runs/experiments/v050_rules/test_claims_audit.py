"""Tests of the claims audit: it passes on the real inputs, and a doctored expected value (a save field, a DAT price, a tracked screen reading,
a code-extract line) makes it fail. Run: python3 -m unittest runs/experiments/v050_rules/test_claims_audit.py  (needs the archive extracted, see fetch_archive.py)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claims_audit as A

def bad(ctx): return [c for c in A.run(ctx) if not c[2]]

class T(unittest.TestCase):
    def test_clean(self): self.assertEqual(bad(A.Ctx()), [])
    def doctored(self, key, fn, expect_q):
        ctx = A.Ctx(); ctx.doctor[key] = fn
        b = bad(ctx); self.assertTrue(b, 'doctoring %r was not caught' % (key,)); self.assertTrue(any(c[0] == expect_q for c in b), [c[0] for c in b])
    def test_save_purse(self): self.doctored(('save', 'Q1_06_after_join'), lambda d: [a.__setitem__('money', 1999) for a in d['armies'] if a['id'] == 1], 'Q1')
    def test_save_mobilisation(self): self.doctored(('save', 'Q3_02_after_disband_hi4000'), lambda d: d['nations'][0].__setitem__('mobilization', 27), 'Q3')
    def test_save_relation(self): self.doctored(('save', 'Q6_05_after_zero_move_click'), lambda d: d['nations'][6]['relations'].__setitem__('Greece', 3), 'Q6')
    def test_save_merc_flag(self): self.doctored(('save', 'Q5B_01_after_disband_merc'), lambda d: d['nations'][0].__setitem__('mobilization', 27), 'Q5')
    def test_dat_price(self): self.doctored(('tsv', 'dat_unit_prices'), lambda r: [x[:3] + ['5'] if x[0] == 'hc' else x for x in r], 'Q4')
    def test_displayed_reading(self): self.doctored(('tsv', 'q4_displayed_cost'), lambda r: [[x[0], '35'] if 'thurii' in x[0] else x for x in r], 'Q4')
    def test_panel_reading(self): self.doctored(('tsv', 'q4_panel_pay'), lambda r: [x[:2] + ['64'] if 'thurii' in x[1] else x for x in r], 'Q4')
    def test_balance_reading(self): self.doctored(('tsv', 'q2_balance_values'), lambda r: [x[:2] + ['633'] if x[1] == 'Tribute' else x for x in r], 'Q2')
    def test_extract_line(self): self.doctored(('line', 54751), 'sVar1 = (psVar8[2] / 100) * price;', 'Q4')

class RowAudit(unittest.TestCase):
    def test_clean(self):
        import row_source_audit as R
        out, fail = R.run(); self.assertEqual(fail, 0)
    def test_doctored_row_fails(self):
        import row_source_audit as R
        out, fail = R.run(doctor=lambda rid, ok: False if rid == 'R413' else ok); self.assertEqual(fail, 1)
    def test_missing_key_fails(self):
        import row_source_audit as R, tempfile, shutil, os
        d = tempfile.mkdtemp(); 
        for f in os.listdir(R.DATA):
            if f.startswith('code_extract_') or f == 'row_source_audit.psv': shutil.copy(R.DATA + f, d)
        p = d + '/row_source_audit.psv'; t = open(p).read().replace('|`troops div 500 ≤ the fleet\'s ship-count word`|', '|a phrase the finding does not contain|'); open(p, 'w').write(t)
        out, fail = R.run(data=d + '/'); self.assertGreaterEqual(fail, 1)

if __name__ == '__main__': unittest.main()
