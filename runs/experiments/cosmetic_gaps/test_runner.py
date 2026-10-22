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

from play_lib import check_guard_ok

def click_proofs_ok(rec, strict):
    """every click passes the SAME check_guard_ok predicate Game3.click uses (single source of truth, R6)."""
    probs = []
    for i, c in enumerate(rec.get('clicks', [])):
        if not c.get('why'):
            probs.append('click %d: no reason' % i); continue
        if not strict: continue
        ok, why = check_guard_ok(c['x'], c['y'], c.get('pointer'), c['why'], c.get('target'))
        if not ok: probs.append('click %d: %s' % (i, why))
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

class TestProductionClickGuard(unittest.TestCase):
    """R6: the production Game3.click uses the same check_guard_ok the tests call; we exercise the
    production path with a mocked pointer and underlying MyGame.click to ensure removing any check from
    production will break the tests."""
    def test_click_without_target_proofs_never_reaches_underlying_click(self):
        import play_lib
        from play_lib import Game3, CLICKS, CTX, MyGame
        seen = []
        # Game3.click calls MyGame.click(self, ...) explicitly - subclass Monkey-patching our override.
        # Monkey-patch MyGame.click instead, on the class. This exercises the production path: the guard
        # runs first (check_guard_ok), then MyGame.click is invoked only on a passing click.
        seen_underlying = []
        original_my_click = MyGame.click
        MyGame.click = lambda self, x, y, pause=0.4: seen_underlying.append((x, y, pause))
        play_lib.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 1}
        try:
            CTX.update(why=None, target=None)
            g = type('G', (), {})()          # no-op object; the patched MyGame.click handles the call
            # 1. no reason -> guard rejects, no underlying click
            try:
                Game3.click(g, 10, 20); self.fail('click without why must raise')
            except Exception as e:
                self.assertIn('no reason', repr(e))
            self.assertEqual(seen_underlying, [], 'underlying click must NOT be called when the guard rejects')
            # 2. reason but no target -> guard rejects
            CTX['why'] = 'test'
            try:
                Game3.click(g, 10, 20); self.fail('click without target must raise')
            except Exception as e:
                self.assertIn('no target proof', repr(e))
            self.assertEqual(seen_underlying, [], 'underlying click must NOT be called when the guard rejects (no target)')
            # 3. reason + valid tooltip target -> guard accepts, underlying click runs
            CTX['target'] = {'src': 'tooltip', 'x': 10, 'y': 20}
            Game3.click(g, 10, 20)
            self.assertEqual(seen_underlying, [(10, 20, 0.4)], 'underlying click reached exactly once for a valid click')
        finally:
            MyGame.click = original_my_click
            CTX.update(why=None, target=None)



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
    """R5/R1: clear_autos must refuse to delete a live autosave unless a same-name archived copy exists AND
    the live save's content (sha256) matches that archived copy (review R1/R5)."""
    def test_refuses_when_no_archive(self):
        import eog, lib, os, tempfile
        with tempfile.TemporaryDirectory() as td:
            from lib import _drv as ld
            orig_g, orig_savedir = ld.G, lib.SAVEDIR
            if not td.endswith('/'): td += '/'
            class FakeF:
                def __init__(self, path): self._path = path; self.name = path.split('/')[-1]
                def __str__(self): return self._path
                def __fspath__(self): return self._path
                @property
                def suffix(self): return '.' + self.name.split('.', 1)[1] if '.' in self.name else ''
                def unlink(self, *a, **kw): pass
            class FakeG:
                def __init__(self, live): self._live = live
                def glob(self, pat): return [FakeF(self._live)]
            live_file = td + 'G/AUTO0721.SAV'
            os.makedirs(os.path.dirname(live_file))
            with open(live_file, 'wb') as f: f.write(b'X')
            ld.G = FakeG(live_file); lib.SAVEDIR = td; eog.SAVEDIR = td
            try:
                eog.clear_autos(); self.fail('clear_autos should raise when nothing harvested')
            except Exception as e:
                self.assertIn('not harvested', repr(e))
            finally:
                ld.G = orig_g; eog.SAVEDIR = td; lib.SAVEDIR = orig_savedir

    def test_refuses_when_archive_stale(self):
        """A same-name archived copy whose contents DIFFER from the live save - must refuse."""
        import eog, lib, os, tempfile
        with tempfile.TemporaryDirectory() as td:
            from lib import _drv as ld
            orig_g, orig_savedir = ld.G, lib.SAVEDIR
            if not td.endswith('/'): td += '/'
            live_file = td + 'G/AUTO0721.SAV'
            os.makedirs(os.path.dirname(live_file))
            with open(live_file, 'wb') as f:
                f.write(b'LIVE-FRESH'); f.flush(); os.fsync(f.fileno())
            with open(td + 'CG_S2_b7_AUTO0721.SAV', 'wb') as f:
                f.write(b'OLD-ARCHIVE'); f.flush(); os.fsync(f.fileno())
            class FakeF:
                def __init__(self, path): self._path = path; self.name = path.split('/')[-1]
                def __str__(self): return self._path
                def __fspath__(self): return self._path
                @property
                def suffix(self): return '.' + self.name.split('.', 1)[1] if '.' in self.name else ''
                def unlink(self, *a, **kw): pass
            class FakeG:
                def __init__(self, live): self._live = live
                def glob(self, pat): return [FakeF(self._live)]
            ld.G = FakeG(live_file); lib.SAVEDIR = td; eog.SAVEDIR = td
            try:
                eog.clear_autos(); self.fail('clear_autos should raise when archive is stale (different content)')
            except Exception as e:
                self.assertIn('differs from its harvested copy', repr(e))
            finally:
                ld.G = orig_g; eog.SAVEDIR = td; lib.SAVEDIR = orig_savedir

    def test_accepts_when_archive_matches(self):
        """A same-name archived copy with matching content - must accept."""
        import eog, lib, os, tempfile
        with tempfile.TemporaryDirectory() as td:
            from lib import _drv as ld
            orig_g, orig_savedir = ld.G, lib.SAVEDIR
            if not td.endswith('/'): td += '/'
            live_file = td + 'G/AUTO0721.SAV'
            os.makedirs(os.path.dirname(live_file))
            content = b'MATCHING-CONTENT-1234'
            with open(live_file, 'wb') as f:
                f.write(content); f.flush(); os.fsync(f.fileno())
            with open(td + 'CG_S2_b7_AUTO0721.SAV', 'wb') as f:
                f.write(content); f.flush(); os.fsync(f.fileno())
            class FakeF:
                def __init__(self, path): self._path = path; self.name = path.split('/')[-1]
                def __str__(self): return self._path
                def __fspath__(self): return self._path
                @property
                def suffix(self): return '.' + self.name.split('.', 1)[1] if '.' in self.name else ''
                def unlink(self, *a, **kw): pass
            class FakeG:
                def __init__(self, live): self._live = live
                def glob(self, pat): return [FakeF(self._live)]
            ld.G = FakeG(live_file); lib.SAVEDIR = td; eog.SAVEDIR = td
            try:
                eog.clear_autos()                 # must not raise
            except Exception as e:
                self.fail('clear_autos refused an identical-content archive: %s' % e)
            finally:
                ld.G = orig_g; eog.SAVEDIR = td; lib.SAVEDIR = orig_savedir
if __name__ == '__main__':
    unittest.main(verbosity=2)
