#!/usr/bin/env python3
"""Write the tracked code extract of the refusal finding: every function that contains a message-box call (FUN_0042d750) plus the helpers the conditions call,
each with the line numbers of all_app_functions.txt in the first column (a cited line is checked against this file). Never overwrites (next free version)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sites
from common import write_new, DATA
L = sites.load(); fn = sites.functions(L)
names = []
for (name, i, k, txt) in sites.sites(L):
    if name not in names: names.append(name)
HELPERS = ['FUN_0042d750', 'FUN_0042d770', 'FUN_0044a66c', 'FUN_0044a698', 'FUN_004494e4', 'FUN_004492a0', 'FUN_00449018', 'FUN_00449d64', 'FUN_00449dd8', 'FUN_00449d08',
           'FUN_00449cd8', 'FUN_004499c0', 'FUN_004497cc', 'FUN_004496e0', 'FUN_004496bc', 'FUN_0044a4e0', 'TArmyToArmy_InitializeForm', 'TChangeArmyUnits_InitializeForm', 'FUN_00449f08', 'FUN_0044a120']
out = ['# Code extract (message-box call sites and the helpers of their conditions) from %s; the first column is that file\'s line number' % os.path.basename(sites.DUMP)]
for n in names + [h for h in HELPERS if h not in names]:
    v = fn[n]
    out.append('\n'.join('%d\t%s' % (j + 1, L[j]) for j in range(v[0], v[-1] + 1)))
print(write_new(os.path.join(DATA, 'code_extract_refusals.txt'), '\n'.join(out) + '\n'))
