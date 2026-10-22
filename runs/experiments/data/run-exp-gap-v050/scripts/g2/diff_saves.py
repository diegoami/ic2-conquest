#!/usr/bin/env python3
"""Diff two remake JSON saves (state only): python3 diff_saves.py a.sav b.sav  -> lines 'path: old -> new'."""
import json, sys
def load(p): return json.load(open(p))['save']['state']
def idx(lst):
    out = {}
    for i, x in enumerate(lst):
        k = x.get('id') if isinstance(x, dict) and 'id' in x else (x.get('slotIndex') if isinstance(x, dict) and 'slotIndex' in x else i)
        out[k] = x
    return out
def walk(a, b, p, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f'{p}/{k}: (absent) -> {json.dumps(b[k])[:160]}')
            elif k not in b: out.append(f'{p}/{k}: {json.dumps(a[k])[:160]} -> (absent)')
            else: walk(a[k], b[k], f'{p}/{k}', out)
    elif isinstance(a, list) and isinstance(b, list) and a and isinstance(a[0], dict) and any(('id' in x or 'slotIndex' in x) for x in a + b if isinstance(x, dict)):
        ia, ib = idx(a), idx(b)
        for k in list(ia) + [k for k in ib if k not in ia]:
            if k not in ia: out.append(f'{p}[{k}]: (absent) -> {json.dumps(ib[k])[:200]}')
            elif k not in ib: out.append(f'{p}[{k}]: removed (was {json.dumps(ia[k])[:200]})')
            else: walk(ia[k], ib[k], f'{p}[{k}]', out)
    elif a != b:
        out.append(f'{p}: {json.dumps(a)[:160]} -> {json.dumps(b)[:160]}')
a, b = load(sys.argv[1]), load(sys.argv[2])
out = []
walk(a, b, '', out)
print('\n'.join(l for l in out if '/newsLog' not in l and '/randomSeed' not in l) or '(no state difference)')
