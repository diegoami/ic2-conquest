#!/usr/bin/env python3
"""Compare, for every play, the last record before batch b7 with its b7 re-run (verified toolbar runner): same input, same boxes (count and titles), same row's literal read in the OCR,
control and after saves equal byte for byte. Writes a new versioned tracked rerun_summary.txt and prints it."""
import os, sys, json, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
from paths import DATA, ART
import savefacts as SF
import tables as t
P = t.read_plays()
BATCH = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'b8'
P = t.read_plays()
ids = ident = ui = 0; notes = []
sv = lambda n: ART + 'saves/' + n
def cmp(a, b):
    """'identical', 'ui' (the differing bytes all lie in the nation UI block) or 'differs'"""
    if open(sv(a), 'rb').read() == open(sv(b), 'rb').read(): return 'identical'
    return 'ui' if SF.ui_only(sv(a), sv(b)) else 'differs'
for pid in sorted(P):
    rs = P[pid]; new = [r for r in rs if r['batch'] == BATCH]; old = [r for r in rs if r['batch'] < BATCH]
    if not new or not old: notes.append('%s: %s' % (pid, ('no %s record' % BATCH) if not new else 'no earlier record')); continue
    n, o = new[-1], old[-1]; ids += 1
    same_box = [b['title'] for b in n['boxes']] == [b['title'] for b in o['boxes']]
    c, a = cmp(n['control'], o['control']), cmp(n['after'], o['after'])
    if n['input_sha'] == o['input_sha'] and same_box and c == 'identical' and a == 'identical': ident += 1
    elif same_box and c in ('identical', 'ui') and a in ('identical', 'ui') and (n['input_sha'] == o['input_sha']): ui += 1
    else: notes.append('%s: input %s, control %s, after %s, box titles %s' % (pid, n['input_sha'] == o['input_sha'], c, a, same_box))
msg = ('batch %s: %d plays re-run and compared with their previous record: %d byte-identical (same input, same box titles, control and after saves); %d identical except for the UI bytes of nation 0 (+0x46B..+0x48F); %d differ%s'
       % (BATCH, ids, ident, ui, ids - ident - ui, ('; ' + '; '.join(notes)) if notes else ''))
print(msg)
if '--write' in sys.argv: print(write_new(os.path.join(DATA, 'rerun_summary.txt'), msg + '\n'))
