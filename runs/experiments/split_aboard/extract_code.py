#!/usr/bin/env python3
"""Write the decompiled functions a finding cites to a tracked code extract (never overwrites: next free version).
usage: extract_code.py NAME ADDR [ADDR ...]   -> runs/experiments/data/run-exp-split-aboard/code_extract_NAME.txt
Each function keeps the line numbers of all_app_functions.txt (the first column), so a cited line can be checked against the extract."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
sys.argv, args = sys.argv[:1], sys.argv[1:]
import importlib.util
spec = importlib.util.spec_from_file_location('fn', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fn.py'))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fn.py')).read()
ns = {}
exec(src.split("if sys.argv[1]=='-g'")[0], ns)
name, addrs = args[0], args[1:]
out = ['# Code extract %s from %s (line numbers are that file\'s)\n' % (name, ns['F'])]
for a in addrs:
    s, b = ns['body'](a.lower().lstrip('0x').zfill(8))
    out.append('\n'.join('%d\t%s' % (s + k + 1, l) for k, l in enumerate(b)))
print(write_new(os.path.join(DATA, 'code_extract_%s.txt' % name), '\n'.join(out) + '\n'))
