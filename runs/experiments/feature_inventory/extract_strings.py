#!/usr/bin/env python3
"""List the Delphi AnsiString literals (refcount -1, length, text, NUL) and other NUL-terminated
printable runs (>= 3 chars, containing a letter) in the exe's CODE section. Read only.
Usage: extract_strings.py <exe> <out.tsv>"""
import sys, re, struct
exe, out = sys.argv[1:3]
d = open(exe, 'rb').read()
CODE_END = 0x5b900   # CODE section ends before the first TPF0 (0x5b984 is data); checked in README of the data folder
hdr = {}
for m in re.finditer(rb'\xff\xff\xff\xff', d[:CODE_END]):
    p = m.start() + 4
    n = struct.unpack_from('<I', d, p)[0]
    if 2 <= n <= 300 and p + 4 + n < len(d) and d[p+4+n] == 0:
        t = d[p+4:p+4+n]
        if all(0x20 <= c < 0x7f or c in (9, 10) for c in t):
            hdr[p+4] = t.decode('latin-1')
rows = []
for off, t in sorted(hdr.items()): rows.append((off, 'ansistring', t))
for m in re.finditer(rb'[\x20-\x7e]{3,}\x00', d[:CODE_END]):
    s = m.start()
    if s in hdr or any(h <= s < h + len(t) for h, t in ()):
        continue
    t = m.group()[:-1].decode('latin-1')
    if re.search('[A-Za-z]', t): rows.append((s, 'cstring', t))
rows.sort()
with open(out, 'w') as f:
    f.write('file_offset\tkind\ttext\n')
    for off, k, t in rows: f.write('0x%06x\t%s\t%s\n' % (off, k, t.replace('\t', ' ')))
print(len(hdr), 'ansistring literals;', len(rows) - len(hdr), 'other runs')
