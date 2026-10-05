#!/usr/bin/env python3
"""Write help_topics.tsv (one row per WinHelp topic: order, title, text) and help_contents_entries.tsv (the .cnt tree).
Usage: extract_help.py <hlp> <cnt> <outdir>   (read only on both)"""
import sys, os, re
from hlp_topics import topics
hlp, cnt, out = sys.argv[1:4]
d = open(hlp, 'rb').read()
recs, pm, sm = topics(d)
tops = []
for p, rt, l1, l2, dl2, rl in recs:
    if rt == 2:
        tops.append({'offset': p, 'title': l2.decode('latin-1').strip(), 'text': []})
    elif rt in (0x20, 0x23) and tops:
        tops[-1]['text'].append(l2.decode('latin-1'))
with open(os.path.join(out, 'help_topics.tsv'), 'w') as f:
    f.write('order\toffset\ttitle\ttext\n')
    for i, t in enumerate(tops):
        txt = ' / '.join(x.replace('\x00', ' ').replace('\n', ' ').strip() for x in t['text'] if x.strip())
        f.write('%d\t0x%06x\t%s\t%s\n' % (i, t['offset'], t['title'], txt))
rows = []; path = []
for l in open(cnt, encoding='latin-1'):
    m = re.match(r'(\d) (.*)', l.rstrip('\r\n'))
    if not m: continue
    lvl, rest = int(m.group(1)), m.group(2)
    title, _, ctx = rest.partition('=')
    path = path[:lvl-1] + [title]
    rows.append((len(rows), lvl, ' > '.join(path), title, ctx.split('>')[0] if ctx else '', ctx))
with open(os.path.join(out, 'help_contents_entries.tsv'), 'w') as f:
    f.write('n\tlevel\tpath\ttitle\tcontext\traw_target\n')
    for r in rows: f.write('\t'.join(str(x) for x in r) + '\n')
print(len(tops), 'topics in the .hlp;', len(rows), 'entries in the .cnt')
