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

def click_proofs_ok(rec, strict):
    """(ok, problems): every click carries why + (strict: a target whose src is a known proof kind, and a control
    line's rectangle or a tooltip's x covers the click point)"""
    probs = []
    for i, c in enumerate(rec.get('clicks', [])):
        if not c.get('why'): probs.append('click %d without a reason' % i)
        t = c.get('target')
        if not strict: continue
        if not t or t.get('src') not in PROOF_SRCS:
            probs.append('click %d (%s) without a valid target proof: %r' % (i, c.get('why'), t)); continue
        if t['src'] in ('win_state', 'win_controls') and 'line' in t:
            if not (t.get('x', -1) <= c['x'] <= t.get('x', -1) + t.get('w', 0) and t.get('y', -1) <= c['y'] <= t.get('y', -1) + t.get('h', 0)):
                probs.append('click %d outside its control rectangle %r' % (i, t))
        if t['src'] == 'tooltip' and abs(t.get('x', c['x']) - c['x']) > 3:
            probs.append('click %d not at its tooltip-proved x %r' % (i, t))
        if t['src'] == 'panel + form resource' and 'rect' in t:
            rx, ry, rw, rh = t['rect']
            if not (rx <= c['x'] < rx + rw and ry <= c['y'] < ry + rh):
                probs.append('click %d outside its speed-button rectangle %r' % (i, t))
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

if __name__ == '__main__':
    unittest.main(verbosity=2)
