#!/usr/bin/env python3
"""OPTIONAL: compare every tracked code extract with the Ghidra dump (all_app_functions.txt, not in git). Needs IC2_DUMP (or the default in paths.py).
The claims audit does not need it: its rule inputs are the tracked extracts."""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DUMP, DATA
src = open(DUMP, errors='replace').read().split('\n'); bad = n = 0
for f in sorted(glob.glob(DATA + 'code_extract_*.txt')):
    for l in open(f, errors='replace').read().split('\n')[1:]:
        m = re.match(r'(\d+)\t(.*)$', l)
        if m: n += 1; bad += src[int(m.group(1)) - 1] != m.group(2)
print('%d extract lines, %d differ from the dump %s' % (n, bad, DUMP)); sys.exit(1 if bad else 0)
