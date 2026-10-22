#!/usr/bin/env python3
"""For each form class: find its VMT in the exe and every code/data reference to it (a form is created or shown
only through its VMT address). Read only. Usage: form_xrefs.py <exe> <forms.json> <out.tsv>"""
import sys, json, struct, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new
exe, forms, out = sys.argv[1:4]
d = open(exe, 'rb').read()
CODE_FILE0, CODE_VA0 = 0x400, 0x401000
def va(o): return o - CODE_FILE0 + CODE_VA0   # valid for the CODE section only
def off(v): return v - CODE_VA0 + CODE_FILE0
CODE_END = 0x5b900
def fmt(v): return '0x%08x' % v
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
from harness import decompile
decompile.check()
dump = open(decompile.DUMP, encoding='latin-1').read()
heads = [(int(m.group(2), 16), m.group(1), m.start()) for m in re.finditer(r'// ==== (\S+) @ ([0-9a-f]+) ====', dump)]
def owner(addr):
    best = None
    for a, n, _ in heads:
        if a <= addr: best = (a, n)
        else: break
    return best[1] if best else '?'
rows = []
for f in json.load(open(forms)):
    cls = f['class']
    pat = bytes([len(cls)]) + cls.encode()
    refs = []
    for m in re.finditer(re.escape(pat) + b'\x00?', d[:CODE_END]):
        s = m.start()
        if s < 0x20000: continue
        sva = va(s)
        for m2 in re.finditer(re.escape(struct.pack('<I', sva)), d):
            slot = m2.start()
            vmt = va(slot) + 28 if slot < CODE_END else None
            if vmt is None: continue
            # candidate VMT: [VMT-44] is the name pointer; count references to VMT itself
            users = [m3.start() for m3 in re.finditer(re.escape(struct.pack('<I', vmt)), d[:CODE_END]) if m3.start() != slot]
            refs.append((vmt, users))
    for vmt, users in refs:
        # a reference from inside the VMT/typeinfo area is not use; keep those in code (below 0x5a000 file) and name the function
        use = []
        for u in users:
            a = va(u)
            use.append('%s@%s' % (owner(a), fmt(a)))
        rows.append((cls, fmt(vmt), len(use), ';'.join(use[:8])))
    if not refs: rows.append((cls, '', 0, ''))
out = write_new(out, 'form\tvmt\tn_refs\treferencing_functions\n' + ''.join('\t'.join(str(x) for x in r) + '\n' for r in rows))
print(len(rows), 'rows')
