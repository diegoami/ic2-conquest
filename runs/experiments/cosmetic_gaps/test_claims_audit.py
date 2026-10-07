#!/usr/bin/env python3
"""Tests of claims_audit.py. The real finding must audit with 0 mismatches; a finding with ONE claim bent (a caption
byte, a sound case, a play tag, an offset) must produce mismatches - so the audit cannot pass on a wrong finding.
usage: python3 test_claims_audit.py"""
import os, re, sys, shutil, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
import claims_audit as CA

FINDING = os.path.join(paths.ROOT, 'findings', '2026-10-06-cosmetic-gaps.md')
DATA = os.path.join(paths.ROOT, 'runs', 'experiments', 'data', 'run-exp-cosmetic-gaps')
ART = os.path.join(paths.ROOT, 'artifacts', 'run-exp-cosmetic-gaps')

def audit_text(text):
    """run() on a temp copy of `text`; returns (checks, mismatches)"""
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as f:
        f.write(text); p = f.name
    try:
        n, bad = CA.run(p, DATA, ART)
        return n, bad
    finally:
        os.unlink(p)

class TestTheRealFinding(unittest.TestCase):
    def test_zero_mismatches(self):
        n, bad = CA.run(FINDING, DATA, ART)
        self.assertEqual(bad, [], '%d checks' % n)
        self.assertGreater(n, 100)

class TestOneBentClaim(unittest.TestCase):
    """each single edit of the finding must be caught (the audit binds claims to sources, not to itself)"""
    def setUp(self):
        self.base = open(FINDING, encoding='utf-8').read()
    def bent(self, old, new):
        self.assertIn(old, self.base)
        return self.base.replace(old, new, 1)
    def check_bent(self, old, new, needles):
        n, bad = audit_text(self.bent(old, new))
        self.assertTrue(bad, 'no mismatch after bending %r' % old)
        self.assertTrue(all(any(s in b for b in bad) for s in needles), bad)   # each needle in some mismatch

    def test_caption_byte(self):
        self.check_bent("`Caption = 'Buy supplies'`", "`Caption = 'Buy supplys'`", ['quotes the buy caption'])
    def test_case_number(self):
        self.check_bent('| 2 | Sound2 | a fleet sails | 51985', '| 2 | Sound2 | a fleet sails | 51986', ['site 51985'])
    def test_play_tag(self):
        self.check_bent('`CG_S3_b7`: the scuttle', '`CG_S3_b4`: the scuttle', ['CG_S3_b4'])
    def test_toggle_values(self):
        self.check_bent('byte `1 → 0 → 1`', 'byte `1 → 0 → 0`', ['quoted triple'])
    def test_offset(self):
        self.check_bent('**H+0x472 W+0x474**', '**H+0x475 W+0x474**', ['offset +0x475'])
    def test_wrong_but_existing_tag(self):
        self.check_bent('`CG_S3_b7`: the scuttle', '`CG_S1_b7`: the scuttle', ['m06 CG_S1_b7 opened Sound8'])
    def test_swapped_offsets(self):
        self.check_bent('**H+0x472 W+0x474**', '**H+0x474 W+0x472**', ['finding claims area H at +0x472', 'finding claims area W at +0x474'])
    def test_title_claim(self):
        self.check_bent("`Imperial Conquest 2    Rome's turn   ()`", "`Imperial Conquest 2   Rome's turn   ()`",
                        ['quoted title'])

class TestProductionDfmParser(unittest.TestCase):
    """the parser claims_audit.py itself uses (review R10: a copied parser could pass while production broke)"""
    DFM = """# header
object AFSupply: TAFSupply
  Caption = 'Supply army'
  ClientWidth = 470
  object btn_ok: TButton
    Caption = 'OK'
  end
  object btn_buy: TButton
    Left = 320
    Caption = 'Buy supplies'
    object nested: TBevel
      Caption = 'never leaks'
    end
    Top = 136
  end
end
"""
    def test_parse(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write(self.DFM); p = f.name
        try:
            dfm = CA.parse_dfm(p)
        finally:
            os.unlink(p)
        self.assertEqual(dfm['AFSupply']['props']['Caption'], "'Supply army'")
        self.assertEqual(dfam := dfm['AFSupply']['props'], dfam)  # noqa: F841 (readability)
        self.assertNotIn('Left', dfm['AFSupply']['props'])
        self.assertEqual(dfm['btn_buy']['props']['Caption'], "'Buy supplies'")
        self.assertEqual(dfm['nested']['props']['Caption'], "'never leaks'")
        self.assertNotIn('Caption', dfm['nested']['props'].get('Top', {}))

if __name__ == '__main__':
    unittest.main(verbosity=2)
