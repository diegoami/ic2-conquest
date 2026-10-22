#!/usr/bin/env python3
"""Apply the predicate audit's catalogue corrections (issue #58) to the refusal-texts finding.

The corrections file (corrections.json under runs/experiments/data/run-exp-refusal-audit58/) lists, per row, the exact old text of a
cell (or part of it), the new text, the mismatch kinds it answers and why. The old text stays in that tracked file, so every
correction can be read side by side. Each old text must occur exactly once in its row's line and in the named column's cell;
otherwise nothing is written. usage: apply_corrections.py [--corrections C] [--finding F] [--check]  (--check: verify only)"""
import argparse, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import latest
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-refusal-audit58')
FINDING = os.path.join(ROOT, 'findings', '2026-10-05-refusal-texts-and-conditions.md')


def apply(text, corrections):
    lines = text.split('\n'); errs = []; headers = {}
    hdr = None
    for i, l in enumerate(lines):
        if l.startswith('| id |'): hdr = [c.strip() for c in re.split(r'(?<!\\)\|', l.strip())[1:-1]]
        m = re.match(r'\| (\w+) \|', l)
        if m and hdr: headers[m.group(1)] = (i, hdr)
    for c in corrections:
        if c['id'] not in headers: errs.append('%s: no row' % c['id']); continue
        i, hdr = headers[c['id']]
        cells = re.split(r'(?<!\\)\|', lines[i])
        if c['column'] not in hdr: errs.append('%s: no column %s' % (c['id'], c['column'])); continue
        k = hdr.index(c['column']) + 1
        if cells[k].count(c['old']) != 1:
            errs.append('%s %s: the old text occurs %d times in the cell' % (c['id'], c['column'], cells[k].count(c['old']))); continue
        cells[k] = cells[k].replace(c['old'], c['new'])
        lines[i] = '|'.join(cells)
    return '\n'.join(lines), errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corrections', default=None); ap.add_argument('--finding', default=FINDING); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    cp = a.corrections or latest(os.path.join(DATA, 'corrections.json'))
    corr = json.load(open(cp, encoding='utf-8'))['corrections']
    text = open(a.finding, encoding='utf-8').read()
    new, errs = apply(text, corr)
    for e in errs: print('ERROR', e)
    if errs: sys.exit(1)
    print('%d corrections apply cleanly' % len(corr))
    if not a.check:
        open(a.finding, 'w', encoding='utf-8').write(new)
        print('written', os.path.relpath(a.finding, ROOT))


if __name__ == '__main__':
    main()
