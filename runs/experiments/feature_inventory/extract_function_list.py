#!/usr/bin/env python3
"""List every function of the whole-application Ghidra dump (address, name, Delphi symbol if any, line in the dump). Read only on the dump.
Usage: extract_function_list.py <dump> <symbols.tsv> <out.tsv>"""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
from harness import decompile
dump, syms, out = sys.argv[1:4]
decompile.check(dump, syms)   # dump_line citations are line numbers of the pinned dump
sym = {int(l.split('\t')[0], 16): l.split('\t')[1].strip() for l in open(syms) if '\t' in l}
rows = ['addr\tname\tsymbol\tdump_line\n']
for n, l in enumerate(open(dump, encoding='latin-1'), 1):
    m = re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====', l)
    if m: rows.append('0x%08x\t%s\t%s\t%d\n' % (int(m.group(2), 16), m.group(1), sym.get(int(m.group(2), 16), ''), n))
print(write_new(out, ''.join(rows)), len(rows) - 1, 'functions')
