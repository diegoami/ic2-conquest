#!/usr/bin/env python3
"""Build row_source_audit.tsv from row_audit.cfg: finds each quote's line in its tracked source and checks that the row carries the condition.
Writes a NEW version (rule 6). Usage: build_row_audit.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_check as cc
from common import write_new, DATA
rows = cc.load_rows(); out = ['row\tsource\tline\tquote\tkey\n']; bad = 0
for n, l in enumerate(open(os.path.join(DATA, 'row_audit.cfg'), encoding='utf-8'), 1):
    if l.startswith('#') or not l.strip(): continue
    row, src, quote, key = [x.strip() for x in l.rstrip('\n').split(' :: ')]
    line = '-'
    if not src.startswith('R:'):
        lines = cc.read(src).split('\n')
        hit = [i + 1 for i, t in enumerate(lines) if quote in t]
        if not hit: print('cfg line %d: quote not found in %s: %r' % (n, src, quote)); bad += 1; continue
        line = str(hit[0])
    if not re.search(key, rows[row]['what'] + ' ' + rows[row]['pre'], re.I): print('cfg line %d: row %s lacks key %r' % (n, row, key)); bad += 1
    out.append('%s\t%s\t%s\t%s\t%s\n' % (row, src, line, quote, key))
if bad: sys.exit(1)
print(write_new(os.path.join(DATA, 'row_source_audit.tsv'), ''.join(out)), len(out) - 1, 'conditions')
