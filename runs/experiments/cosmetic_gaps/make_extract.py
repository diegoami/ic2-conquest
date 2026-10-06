#!/usr/bin/env python3
"""Write the tracked code extract of the cosmetic-gaps finding: the decompiled functions the finding cites (title, sounds,
window positions, toggle, supply dialog) and, under CALLSITES, the enclosing function of every MakeSound / SetTurnTitle /
StoreFormPositions call with three lines of context, each line prefixed with its line number in the dump it comes from
(all_app_functions.txt). A cited line is checked against this file by claims_audit.py. Never overwrites (next free version).
usage: make_extract.py"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
RT = os.environ.get('IC2_RETOOLS', '/mnt/c/Users/diego/AppData/Local/ReTools')
FILE = 'all_app_functions.txt'
FUNCS = ['0043ddac',                                    # TAreaMap_InitializeForm
         '0043de0c',                                    # TAreaMap_PaintForm
         '0043dfd4',                                    # TAreaMap_ToggleMap
         '0043ff98',                                    # TAFSupply_TransferSupply
         '004484d0',                                    # the save writer's trailer
         '0045aad4',                                    # TPremierForm_OpenGameFile
         '0045ab84',                                    # TPremierForm_SaveGameFile
         '0045ac5c',                                    # TPremierForm_StartTurn
         '0045bb1c',                                    # TPremierForm_StoreFormPositions
         '0045bf28',                                    # TPremierForm_MakeSound
         '0045c084',                                    # TPremierForm_SetTurnTitle
         '0044fa20',                                    # FUN_0044fa20 (SetTurnTitle caller)
         ]
CALLS = ['MakeSound', 'SetTurnTitle', 'StoreFormPositions']
lines = open(os.path.join(RT, FILE), errors='replace').read().split('\n')
heads = []
for i, l in enumerate(lines):
    m = re.match(r'// (?:==== (\S+) @ ([0-9a-f]+) ====|FUNCTION (\S+) @ ([0-9a-f]+))', l)
    if m: heads.append((i, m.group(1) or m.group(3), m.group(2) or m.group(4)))
out = ['# Code extract of the cosmetic-gaps finding. Sections: FUNCS then CALLSITES; the first column is %s\'s line number' % FILE,
       '# FILE %s' % FILE]
for a in FUNCS:
    s = next(i for i, nm, ad in heads if ad == a)
    e = next((i for i, nm, ad in heads if i > s), len(lines))
    out.append('\n'.join('%d\t%s' % (j + 1, lines[j]) for j in range(s, e)).rstrip())
out.append('# CALLSITES (enclosing function, call line and three lines before it)')
for i, l in enumerate(lines):
    if any('TPremierForm_%s(' % c in l for c in CALLS):
        s = max(0, i - 3)
        f = next((nm for j, nm, ad in heads if j <= i), '?')
        out.append('---- in %s ----' % f)
        out.append('\n'.join('%d\t%s' % (j + 1, lines[j]) for j in range(s, i + 1)).rstrip())
print(write_new(os.path.join(DATA, 'code_extract_cosmetic.txt'), '\n'.join(out) + '\n'))
