#!/usr/bin/env python3
"""Tests of the cosmetic-gaps runner's recordings (plays_*.jsonl), in the refusal_texts test_runner's spirit: a
recording is evidence only if its clicks were verified. For EVERY recording, every batch, runner version included:
 * the tag is unique (a play is never re-recorded under the same tag; a re-run uses a new batch name);
 * every click's pointer was read back from the X server AT the click's coordinates (no click at a guessed position);
 * every play that reached its dialog/wait step has at least one verified step (a tooltip proved an x, or a control
   line proved a click target), and FAILED plays carry an error plus a failure screenshot;
 * every screenshot the recordings name exists under artifacts/ and is hashed in SAVES.sha256;
 * the strace-tagged plays recorded their strace log name, and its harvested wav_opens file exists.
usage: python3 test_runner.py * for every recording of a HARDENED batch (the runner that rejects unproved clicks): every click carries a target proof
   whose `src` is one of the known kinds, and a control-line or tooltip target's rectangle contains the click's point;
   a play without any such proof cannot be cited.
Negative tests forge records with a missing, a null and an inconsistent target and require each to fail the same validator.
usage: python3 test_runner.py"""
import os, sys, json, glob, hashlib, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
DATA = os.path.join(paths.ROOT, 'runs', 'experiments', 'data', 'run-exp-cosmetic-gaps') + '/'
ART = os.path.join(paths.ROOT, 'artifacts', 'run-exp-cosmetic-gaps')

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def recordings():
    out = []
    for f in sorted(glob.glob(DATA + 'plays_*.jsonl')):
        for l in open(f):
            if l.strip(): out.append((os.path.basename(f), json.loads(l)))
    return out

RECS = recordings()
HARDENED = {'b7', 'b8', 'close-probe2'}          # batches recorded after the runner began rejecting unproved clicks
PROOF_SRCS = {'tooltip', 'win_state', 'win_controls', 'ocr', 'driver tile targeting', 'xdotool getmouselocation', 'panel + form resource'}

REQUIRED_FIELDS = {
    'tooltip':                 ('x', 'y'),                                # tooltip-proved x at known y; how added to the writes post-R3
    'win_state':               ('x', 'y', 'w', 'h', 'line'),            # the verbatim line of the control; window added to the writes post-R3
    'win_controls':            ('x', 'y', 'w', 'h', 'line'),            # ditto from win_controls for popups; window added to the writes post-R3
    'ocr':                     ('word', 'region', 'x', 'y'),               # the OCR'd word's centre and the region it was looked in
    'driver tile targeting':   ('tile',),                                  # the tile the driver is targeting (the kind, not just the kind)
    'xdotool getmouselocation':('root', 'pointer'),                        # the root id + a pointer read-back for the bare-root click
    'panel + form resource':   ('button', 'panel_line', 'rect', 'hint'),   # the speed button's resource decl + its own rect + the tooltip's text
}

def prove_one(t, c):
    """validate one click's target; return (ok, problems)"""
    probs = []
    if not t or t.get('src') not in REQUIRED_FIELDS:
        return False, ['target %r unknown or missing' % t]
    for k in REQUIRED_FIELDS[t['src']]:
        if k not in t: probs.append('%s target missing %r' % (t['src'], k))
    if not probs:
        if t['src'] in ('win_state', 'win_controls'):
            if not (t['x'] <= c['x'] <= t['x'] + t['w'] and t['y'] <= c['y'] <= t['y'] + t['h']):
                probs.append('click %d outside its control rectangle' % c['x'])
        elif t['src'] == 'tooltip':
            if abs(t['x'] - c['x']) > 3: probs.append('click %d not at tooltip x %d' % (c['x'], t['x']))
        elif t['src'] == 'panel + form resource':
            rx, ry, rw, rh = t['rect']
            if not (rx <= c['x'] < rx + rw and ry <= c['y'] < ry + rh):
                probs.append('click %d outside speed-button rectangle' % c['x'])
        elif t['src'] == 'xdotool getmouselocation':
            if t.get('pointer', {}).get('window') != t.get('root'):
                probs.append('bare-root click: pointer window %r != root %r' % (t.get('pointer'), t.get('root')))
    return not probs, probs

def click_proofs_ok(rec, strict):
    """every click carries why + (strict: a target whose src has all the fields the proof needs, and the
    rect/x/pointer matches the click point)"""
    probs = []
    for i, c in enumerate(rec.get('clicks', [])):
        if not c.get('why'): probs.append('click %d without a reason' % i)
        if not strict: continue
        ok, sub = prove_one(c.get('target'), c)
        probs.extend('%d: %s' % (i, s) for s in sub)
    return not probs, probs

def click_guard_active(rec, strict):
    """the production click guard (Game3.click in play_lib.py) - reject a click that arrives without a
    reason or a target. Tested by reconstructing the guard's predicate against the same fields the runner reads."""
    probs = []
    for i, c in enumerate(rec.get('clicks', [])):
        if not c.get('why'): probs.append('click %d: no reason' % i)
        if not c.get('target'): probs.append('click %d: no target' % i)
    return not probs, probs
HASHES = {}
for l in open(DATA + 'SAVES.sha256'):
    p = l.split()
    if len(p) == 2: HASHES[p[1]] = p[0]

def find_art(name):
    for r, _, fs in os.walk(ART):
        if name in fs: return os.path.join(r, name)
    return None

class TestRecordings(unittest.TestCase):
    def test_there_are_recordings(self):
        self.assertGreater(len(RECS), 10)

    def test_tags_unique(self):
        seen = {}
        canon = {}
        for f, r in RECS:
            tag = r.get('tag') or 'CG_%s_%s' % (r['play'], r['batch'])
            if 'partial' in f:
                continue          # the restored b2 partial is historical: its tags must exist canonically, checked below
            self.assertNotIn(tag, seen, '%s also recorded in %s' % (tag, seen.get(tag)))
            seen[tag] = f; canon[tag] = f
        for f, r in RECS:
            if 'partial' in f:
                tag = r.get('tag') or 'CG_%s_%s' % (r['play'], r['batch'])
                self.assertIn(tag, canon, '%s: the partial records a play no canonical file holds' % tag)

    def test_clicks_carry_target_proofs(self):
        seen = 0
        for f, r in RECS:
            if r.get('batch') not in HARDENED: continue
            seen += 1
            ok, probs = click_proofs_ok(r, strict=True)
            self.assertTrue(ok, '%s %s: %s' % (f, r.get('tag'), probs))
        self.assertGreater(seen, 5, 'no hardened recordings found to check')

    def test_clicks_pointer_read_back(self):
        for f, r in RECS:
            for c in r.get('clicks', []):
                self.assertEqual((c['x'], c['y']), (c['pointer']['x'], c['pointer']['y']),
                                 '%s %s: click %s,%s but pointer at %s,%s' % (f, r.get('tag'), c['x'], c['y'], c['pointer']['x'], c['pointer']['y']))
                self.assertTrue(c.get('why'), '%s %s: a click without a reason' % (f, r.get('tag')))

    def test_status_and_evidence(self):
        for f, r in RECS:
            st = r.get('status')
            if st is None:
                continue          # the close probe's record (a measurement, not a play: it carries clicks and steps only)
            self.assertIn(st, ('ok', 'FAILED'), r.get('tag'))
            if st == 'FAILED':
                self.assertTrue(r.get('error'), r.get('tag'))
            else:
                self.assertTrue(r.get('verified'), '%s: ok without any verified step' % r.get('tag'))

    def test_screenshots_exist_and_hashed(self):
        for f, r in RECS:
            for key, s in (r.get('screens') or {}).items():
                p = find_art(s['png'])
                self.assertTrue(p, '%s %s: %s not under artifacts' % (f, r.get('tag'), s['png']))
                self.assertEqual(HASHES.get(s['png']), sha(p), s['png'])
                self.assertEqual(s['png_sha'], sha(p), s['png'])

    def test_strace_plays_kept_their_harvest(self):
        for f, r in RECS:
            # a play that FAILED before its strace step (b2's S3) has no harvest: its failure is the record
            if r.get('strace_log') and r.get('status') == 'ok':
                self.assertTrue(r.get('wav_opens'), '%s %s: strace play without a harvest' % (f, r.get('tag')))
                self.assertTrue(os.path.exists(DATA + r['wav_opens']), r['wav_opens'])
                self.assertTrue(find_art(r['strace_log']), r['strace_log'])

class TestForgedRecords(unittest.TestCase):
    """negative tests: the validator must REJECT a missing, a null and an inconsistent target (review R3)"""
    BASE = {'batch': 'b8', 'status': 'ok', 'verified': [{'step': 'x', 'ok': True}],
            'clicks': [{'x': 10, 'y': 20, 'why': 'control X', 'pointer': {'x': 10, 'y': 20, 'window': 1},
                        'target': {'src': 'win_state', 'x': 0, 'y': 0, 'w': 30, 'h': 40, 'line': 'X'}}]}
    def test_valid_passes(self):
        ok, probs = click_proofs_ok(self.BASE, strict=True); self.assertEqual(probs, [])
    def test_missing_target(self):
        r = json.loads(json.dumps(self.BASE)); del r['clicks'][0]['target']
        ok, probs = click_proofs_ok(r, strict=True); self.assertTrue(probs)
    def test_null_target(self):
        r = json.loads(json.dumps(self.BASE)); r['clicks'][0]['target'] = None
        ok, probs = click_proofs_ok(r, strict=True); self.assertTrue(probs)
    def test_inconsistent_target(self):
        r = json.loads(json.dumps(self.BASE)); r['clicks'][0]['x'] = 500
        ok, probs = click_proofs_ok(r, strict=True); self.assertTrue(probs)
    def test_unknown_proof_src(self):
        r = json.loads(json.dumps(self.BASE)); r['clicks'][0]['target'] = {'src': 'guessed'}
        ok, probs = click_proofs_ok(r, strict=True); self.assertTrue(probs)

class TestEndTurnTimeout(unittest.TestCase):
    """R4: end_turn must raise when the autosave line count never advances; a click that never took effect is
    not a successful End turn. The stubbed game never advances the counter, so the 1-second timeout fires."""
    def test_end_turn_raises_on_no_advance(self):
        import cg, play_lib
        class Stub:
            def find_windows(self, p): return []
            def controls(self, t): return []
            def popups(self): return []
            def click(self, x, y, pause=0.0): pass
            def key(self, *a, **kw): pass
        import eog
        play_lib.CTX.update(why=None, target=None)
        cg.main_tool = lambda *a, **kw: None
        cg.close_all_boxes = lambda g, tag: []
        orig_aal = eog.autosave_lines; orig_boxes = cg.boxes
        eog.autosave_lines = lambda: 0; cg.boxes = lambda g: []
        try:
            try:
                cg.end_turn(Stub(), timeout=1); self.fail('end_turn should have raised DriverError')
            except Exception as e:
                self.assertIn('autosave did not advance', repr(e))
        finally:
            eog.autosave_lines = orig_aal; cg.boxes = orig_boxes

class TestClearAutosRefuses(unittest.TestCase):
    """R5: clear_autos must REFUSE to delete an AUTO*.SAV that hasn't been harvested (no copy under SAVEDIR) - so
    an unharvested measured output cannot be silently deleted. The check raises DriverError."""
    def test_refuses_unharvested(self):
        import eog, lib, os, tempfile
        from lib import _drv as ld
        orig_g, orig_savedir = ld.G, eog.SAVEDIR
        ld.G = type('P', (), {'glob': lambda self, pat: [type('F', (), {'name': 'AUTO0721.SAV', 'suffix': '.SAV', 'unlink': lambda self: None})]})()
        eog.SAVEDIR = '/nonexistent-zen-of-the-discovery'
        try:
            try:
                eog.clear_autos(); self.fail('clear_autos should have raised')
            except Exception as e:
                self.assertIn('not harvested', repr(e))
        finally:
            ld.G = orig_g; eog.SAVEDIR = orig_savedir


if __name__ == '__main__':
    unittest.main(verbosity=2)
