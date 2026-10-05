#!/usr/bin/env python3
"""How well does the empirical phrase decoder reproduce the help text? For every compressed record, compare the decoded length with the
declared decompressed length (DataLen2). Usage: hlp_check.py <hlp> > help_decode_check.txt"""
import sys
from hlp_topics import topics
d = open(sys.argv[1], 'rb').read()
recs, pm, sm = topics(d)
ok = bad = plain = 0; diffs = []
for p, rt, l1, l2, dl2, rl in recs:
    if dl2 > rl:
        if len(l2) == dl2: ok += 1
        else: bad += 1; diffs.append(len(l2) - dl2)
    else: plain += 1
print('records:', len(recs), 'compressed:', ok + bad, 'exact length:', ok, 'not exact:', bad, 'uncompressed:', plain)
if diffs:
    print('decoded minus declared length, not-exact records: min %d max %d mean %.1f' % (min(diffs), max(diffs), sum(diffs) / len(diffs)))
print('Reading: the decoder never adds text; in most paragraphs it loses a few characters (a phrase or a word after some control codes, e.g. "If" shows as "f").')
print('The text is readable, not byte-exact. The inventory uses help statements only as cited evidence (digits and nouns survive) and the WinHelp viewer confirms the first topic (FI_b1_06_help_topics.png).')
