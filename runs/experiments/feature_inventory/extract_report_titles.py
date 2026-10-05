#!/usr/bin/env python3
"""List the research repository's reports (file name and first heading) so the sweep for player-facing rules runs on a tracked extract.
Read only on the research repo. Usage: extract_report_titles.py <reports dir> <out.tsv>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
d, out = sys.argv[1:3]
rows = ['file\ttitle\n']
for f in sorted(os.listdir(d)):
    if f.endswith('.md'):
        t = next((l.lstrip('# ').strip() for l in open(os.path.join(d, f), encoding='utf-8') if l.startswith('#')), '')
        rows.append('%s\t%s\n' % (f, t.replace('\t', ' ')))
print(write_new(out, ''.join(rows)), len(rows) - 1, 'reports')
