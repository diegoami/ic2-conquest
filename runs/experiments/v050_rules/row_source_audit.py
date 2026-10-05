#!/usr/bin/env python3
"""Row source audit: every rule statement of the six findings against the code line it rests on. Input: data/row_source_audit.psv (hand-written: rule, source
line, quote, the conditions in the code, the key phrase that states them in the finding, disposition stated|excluded + reason). The check, mechanical:
  - the QUOTE must be on that source line of the tracked code extracts;
  - the KEY must occur in the finding's text (a 'stated' row) ; an 'excluded' row must carry a reason.
Writes row_source_audit_table.tsv (versioned) with the totals and returns the number of failures."""
import sys, os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from paths import ROOT, DATA
from common import write_new
FIND = {'purse': 'army-purse-writes-and-the-1000-cap', 'tribute': 'balance-sheet-tribute-line', 'disband-queue': 'disbanding-a-queued-recruitment',
        'merc': 'mercenary-hire-price-is-a-gate-not-a-charge', 'disband-unit': 'disbanding-a-regular-unit-lowers-mobilisation', 'attack': 'refused-attack-declares-nothing'}
def run(data=DATA, root=ROOT, doctor=None):
    L = {}
    for f in sorted(glob.glob(data + 'code_extract_*.txt')):
        for l in open(f, errors='replace').read().split('\n')[1:]:
            m = re.match(r'(\d+)\t(.*)$', l)
            if m: L[int(m.group(1))] = m.group(2)
    texts = {k: open(glob.glob(root + '/findings/2026-10-05-%s.md' % v)[0]).read() for k, v in FIND.items()}
    rows = [l.split('|') for l in open(data + 'row_source_audit.psv').read().split('\n') if l and not l.startswith('#')]
    out = ['id\tfinding\tsource_line\tquote_on_line\tkey_in_finding\tdisposition\tresult']; fail = 0; stated = excl = 0
    for r in rows:
        rid, fnd, rule, line, quote, cond, key, disp = r[:8]; note = r[8] if len(r) > 8 else ''
        q = quote in L.get(int(line), ''); k = key in texts[fnd]
        ok = q and (k if disp == 'stated' else bool(note))
        if doctor: ok = doctor(rid, ok)
        fail += not ok; stated += disp == 'stated'; excl += disp == 'excluded'
        out.append('%s\t%s\t%s\t%s\t%s\t%s\t%s' % (rid, fnd, line, q, k, disp, 'OK' if ok else 'FAIL'))
    out.insert(0, '# row source audit: %d rows (%d stated, %d excluded with a reason), %d failures' % (len(rows), stated, excl, fail))
    return out, fail
if __name__ == '__main__':
    out, fail = run(); print(write_new(DATA + 'row_source_audit_table.tsv', '\n'.join(out) + '\n')); print(out[0])
    for l in out:
        if l.endswith('FAIL'): print(l)
    sys.exit(1 if fail else 0)
