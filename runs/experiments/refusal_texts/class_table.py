#!/usr/bin/env python3
"""For every class of delphi_symbols.tsv (the methods the decompile names): how many methods it has and how many message-box calls (FUN_0042d750) they hold. New versioned
tracked class_sites.tsv. Unnamed FUN_ functions that hold a call are listed under (unnamed)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sites
from common import write_new
from paths import DATA
from harness import decompile  # repo root is on sys.path through paths
SYM = decompile.SYMBOLS


def main():
    decompile.check(SYM)
    L = sites.load(); S = sites.sites(L)
    cls = {}
    for l in open(SYM, encoding='utf-8', errors='replace'):
        f = l.rstrip('\n').split('\t')
        if len(f) >= 2 and '_' in f[1]:
            c = f[1].split('_')[0]; cls.setdefault(c, [0, 0])[0] += 1
    for (name, i, k, txt) in S:
        c = name.split('_')[0] if re.match(r'T[A-Z]\w*_', name) else '(unnamed)'
        cls.setdefault(c, [0, 0])[1] += 1
    rows = ['class\tmethods named in delphi_symbols.tsv\tmessage-box calls']
    for c in sorted(cls): rows.append('%s\t%d\t%d' % (c, cls[c][0], cls[c][1]))
    print(write_new(os.path.join(DATA, 'class_sites.tsv'), '\n'.join(rows) + '\n'))


if __name__ == '__main__':
    main()
