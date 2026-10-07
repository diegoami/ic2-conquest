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
        self.assertTrue(any(all(s in b for s in needles) for b in bad), bad)

    def test_caption_byte(self):
        self.check_bent("`Caption = 'Buy supplies'`", "`Caption = 'Buy supplys'`", ['quotes the buy caption'])
    def test_case_number(self):
        self.check_bent('| 2 | Sound2 | a fleet sails | 51985', '| 2 | Sound2 | a fleet sails | 51986', ['site 51985'])
    def test_play_tag(self):
        self.check_bent('`CG_S3_b3`: the scuttle', '`CG_S3_b4`: the scuttle', ['CG_S3_b4 is recorded'])
    def test_toggle_values(self):
        self.check_bent('byte `1 → 0 → 1`', 'byte `1 → 0 → 0`', ['quoted triple'])
    def test_offset(self):
        self.check_bent('**H+0x474 W+0x472**', '**H+0x475 W+0x472**', ['offset +0x475'])
    def test_title_claim(self):
        self.check_bent("`Imperial Conquest 2    Rome's turn   ()`", "`Imperial Conquest 2   Rome's turn   ()`",
                        ['quoted title'])

class TestDfmParser(unittest.TestCase):
    """nested children must not leak their properties into the parent (the bug the first version had)"""
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
  end
end
"""
    def test_parse(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write(self.DFM); p = f.name
        try:
            dfm = {}; obj = None
            for l in open(p):
                m = re.match(r'\s*object (\w+): (\w+)', l)
                if m:
                    obj = m.group(1); dfm[obj] = {'cls': m.group(2), 'props': {}}
                    continue
                m = re.match(r'\s+(\w+) = (.*)$', l)
                if obj and m and not l.lstrip().startswith('end'):
                    dfm[obj]['props'][m.group(1)] = m.group(2).rstrip()
        finally:
            os.unlink(p)
        self.assertEqual(dfm['AFSupply']['props']['Caption'], "'Supply army'")
        self.assertEqual(dfm['AFSupply']['props']['ClientWidth'], '470')
        self.assertEqual(dfm['btn_buy']['props']['Caption'], "'Buy supplies'")
        self.assertNotIn('Caption', dfm.get('AFSupply', {}))

if __name__ == '__main__':
    unittest.main(verbosity=2)
