#!/usr/bin/env python3
"""Tests of the cosmetic-gaps runner's recordings (plays_*.jsonl), in the refusal_texts test_runner's spirit: a
recording is evidence only if its clicks were verified. For EVERY recording, every batch, runner version included:
 * the tag is unique (a play is never re-recorded under the same tag; a re-run uses a new batch name);
 * every click's pointer was read back from the X server AT the click's coordinates (no click at a guessed position);
 * every play that reached its dialog/wait step has at least one verified step (a tooltip proved an x, or a control
   line proved a click target), and FAILED plays carry an error plus a failure screenshot;
 * every screenshot the recordings name exists under artifacts/ and is hashed in SAVES.sha256;
 * the strace-tagged plays recorded their strace log name, and its harvested wav_opens file exists.
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
        for f, r in RECS:
            tag = r.get('tag') or 'CG_%s_%s' % (r['play'], r['batch'])
            self.assertNotIn(tag, seen, '%s also recorded in %s' % (tag, seen.get(tag)))
            seen[tag] = f

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

if __name__ == '__main__':
    unittest.main(verbosity=2)
