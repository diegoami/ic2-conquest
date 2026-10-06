#!/usr/bin/env python3
"""Write the tracked code extract of the leaders-form finding: the decompiled functions the finding cites, each line prefixed with its line number in the dump it comes from
(all_app_functions.txt, and news_log_decomp.txt for the two functions that file holds). A cited line is checked against this file by claims_audit.py. Never overwrites (next free version).
usage: make_extract.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
RT = os.environ.get('IC2_RETOOLS', '/mnt/c/Users/diego/AppData/Local/ReTools')
FILES = {'all_app_functions.txt': ['004571a8', '0045730c', '00457404', '00457590', '0045a9e0', '0045b148', '0045b198', '00449050', '00449078', '0040284c', '00412c44', '00412c6c', '00412cdc',
                                   '0041439c', '00448fd8', '0042313c', '00428d88', '00422f40', '00424608', '004127a0', '004127c0', '00420c58', '00420c84', '00405b00', '00403458'],
         'news_log_decomp.txt': ['00448aa4', '004481a0']}
out = ['# Code extract of the leaders-form finding. Sections: one per dump file; the first column is that file\'s line number']
for fname, addrs in FILES.items():
    lines = open(os.path.join(RT, fname), errors='replace').read().split('\n')
    out.append('# FILE %s' % fname)
    heads = []
    for i, l in enumerate(lines):
        m = re.match(r'// (?:==== (\S+) @ ([0-9a-f]+) ====|FUNCTION (\S+) @ ([0-9a-f]+))', l)
        if m: heads.append((i, (m.group(2) or m.group(4))))
    for a in addrs:
        s = next(i for i, ad in heads if ad == a)
        e = next((i for i, ad in heads if i > s), len(lines))
        if fname == 'news_log_decomp.txt': s += 0                    # the header of this file is a 3-line banner; the function body follows
        out.append('\n'.join('%d\t%s' % (j + 1, lines[j]) for j in range(s, e)).rstrip())
print(write_new(os.path.join(DATA, 'code_extract_leaders.txt'), '\n'.join(out) + '\n'))
