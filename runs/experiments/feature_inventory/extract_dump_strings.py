#!/usr/bin/env python3
"""For every function in the whole-application Ghidra dump: address, Delphi symbol (if recovered), and the
string literals its decompilation contains. Read only. Usage: extract_dump_strings.py <dump> <symbols.tsv> <out.tsv>"""
import sys, re
dump, syms, out = sys.argv[1:4]
sym = {}
for l in open(syms):
    a, n = l.rstrip('\n').split('\t')[:2]
    sym[int(a, 16)] = n
cur = None; rows = []; nfun = 0
for l in open(dump, encoding='latin-1'):
    m = re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====', l)
    if m:
        cur = (m.group(1), int(m.group(2), 16)); nfun += 1; continue
    if cur:
        for s in re.findall(r'"((?:[^"\\]|\\.)*)"', l):
            if len(s) >= 2 and re.search('[A-Za-z]', s):
                rows.append((cur[1], sym.get(cur[1], ''), cur[0], s))
with open(out, 'w') as f:
    f.write('addr\tsymbol\tfunction\tliteral\n')
    for a, s, fn, lit in rows: f.write('0x%08x\t%s\t%s\t%s\n' % (a, s, fn, lit.replace('\t', ' ')))
print(nfun, 'functions;', len(rows), 'literals;', len({r[0] for r in rows}), 'functions with literals')
