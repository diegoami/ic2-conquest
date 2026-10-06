#!/usr/bin/env python3
"""List every string literal of the program's T*_* functions (the game's own form and unit code, from delphi_symbols names) with a category, to a new versioned
tracked file literals_in_scope.tsv. Categories: `message-box literal` (the first argument of a FUN_0042d750 call), `fragment of a built message` (any other literal in a function
that builds a message-box text at run time: the call-site table lists those functions as `expr` sites), `other` (captions, panel labels, resource names, unit names: not message boxes)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sites
from common import write_new, DATA
L = sites.load(); fn = sites.functions(L); S = sites.sites(L)
msg_lit = set()                                   # (function, 0-based line) of every first-argument literal of a message-box call
built = set()                                     # functions that build a message-box text at run time (first argument not a literal)
for (name, i, k, txt) in S:
    a0 = sites.parse_call(txt)[0]
    if re.fullmatch(r'\(uint \*\)"(?:[^"\\]|\\.)*"', a0):
        for j in range(i, k + 1):
            if a0[len('(uint *)'):] in L[j]: msg_lit.add((name, j)); break
    else: built.add(name)
rows = ['function\tline\tliteral\tcategory']
for name, v in fn.items():
    if not re.match(r'T[A-Z]\w*_', name): continue
    for i in range(v[0], v[-1] + 1):
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', L[i]):
            lit = sites.unescape(m.group(1))
            if len(lit) < 2: continue
            if (name, i) in msg_lit: cat = 'message-box literal'
            elif name in built: cat = 'fragment of a built message'
            else: cat = 'other'
            rows.append('%s\t%d\t%s\t%s' % (name, i + 1, lit.replace('\n', '\\n').replace('\t', '\\t'), cat))
print(write_new(os.path.join(DATA, 'literals_in_scope.tsv'), '\n'.join(rows) + '\n'))
