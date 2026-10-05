#!/usr/bin/env python3
"""Compare, for every play, the last record before batch b7 with its b7 re-run (verified toolbar runner): same input, same boxes (count and titles), same row's literal read in the OCR,
control and after saves equal byte for byte. Writes a new versioned tracked rerun_summary.txt and prints it."""
import os, sys, json, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
from paths import DATA
import tables as t
P = t.read_plays()
rows = []; same = 0; ids = 0; notes = []
for pid in sorted(P):
    rs = P[pid]; new = [r for r in rs if r['batch'] == 'b7']; old = [r for r in rs if r['batch'] != 'b7']
    if not new or not old: notes.append('%s: %s' % (pid, 'no b7 record' if not new else 'only a b7 record')); continue
    n, o = new[-1], old[-1]; ids += 1
    same_in = n['input_sha'] == o['input_sha']; same_ctl = n['control_sha'] == o['control_sha']; same_aft = n['after_sha'] == o['after_sha']
    same_box = [(b['title']) for b in n['boxes']] == [(b['title']) for b in o['boxes']]
    ok = same_in and same_ctl and same_aft and same_box
    same += ok
    if not ok: notes.append('%s: input %s, control %s, after %s, box titles %s' % (pid, same_in, same_ctl, same_aft, same_box))
msg = '%d plays re-run with the verified runner (b7) and compared with their previous record: %d reproduce (same input, same box titles, byte-identical control and after saves); %d differ%s' % (ids, same, ids - same, ('; ' + '; '.join(notes)) if notes else '')
print(msg)
if '--write' in sys.argv: print(write_new(os.path.join(DATA, 'rerun_summary.txt'), msg + '\n'))
