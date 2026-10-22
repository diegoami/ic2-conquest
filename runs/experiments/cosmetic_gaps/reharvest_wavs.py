#!/usr/bin/env python3
"""Re-harvest the WAV opens of ALREADY-RECORDED plays (no game runs): read each play's strace log from the artifacts
folder and its step marks from the recording, attribute by the line's START offset (scenarios.attribute_wavs; review
R6: the first harvest used each line's END offset, so a line ending exactly at a mark was pulled into the step whose
mark was taken while the line was still being written), and write a NEW versioned wav_opens file beside the old one
(rule 6: the old files stay). The finding cites the new files.
usage: reharvest_wavs.py [BATCH ...]   (default: every batch with strace recordings)"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenarios as S
from paths import ART, DATA
from common import write_new

batches = sys.argv[1:] or sorted({os.path.basename(f)[6:-6] for f in glob.glob(DATA + 'plays_*.jsonl')})
for batch in batches:
    for l in open(DATA + 'plays_%s.jsonl' % batch):
        if not l.strip(): continue
        r = json.loads(l)
        if not r.get('strace_log') or not r.get('strace_marks'): continue
        logp = None
        for root, _, fs in os.walk(ART):
            if r['strace_log'] in fs: logp = os.path.join(root, r['strace_log'])
        if not logp:
            print('MISSING log %s (%s)' % (r['strace_log'], r.get('tag'))); continue
        out = S.attribute_wavs(logp, r['strace_marks'], r['tag'])
        p = write_new(os.path.join(DATA, 'wav_opens_%s.txt' % r['tag']), '\n'.join(out) + '\n')
        print(p)
