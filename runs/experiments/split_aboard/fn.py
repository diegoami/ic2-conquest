#!/usr/bin/env python3
"""Print decompiled functions from all_app_functions.txt by address (hex), or grep with line numbers.
usage: fn.py 00446f50 [...]   |  fn.py -g REGEX"""
import re,sys
F='/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt'
lines=open(F,errors='replace').read().split('\n')
idx={}
for i,l in enumerate(lines):
    m=re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====',l)
    if m: idx[m.group(2)]=i
starts=sorted(idx.values())
def body(a):
    s=idx[a]; n=next((x for x in starts if x>s),len(lines))
    return s,lines[s:n]
if sys.argv[1]=='-g':
    cur=None
    for i,l in enumerate(lines):
        m=re.match(r'// ==== (\S+) @ ([0-9a-f]+)',l)
        if m: cur=m.group(2)
        if re.search(sys.argv[2],l): print(f'{cur}:{i+1}: {l.strip()}')
else:
    for a in sys.argv[1:]:
        s,b=body(a.lower().lstrip('0x').zfill(8))
        for k,l in enumerate(b): print(f'{s+k+1}\t{l}')
