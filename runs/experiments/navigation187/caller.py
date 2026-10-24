"""Resolve wrapper residue in its actual target-tree caller before deciding scope."""
import json
from core import *
OUT=PRIVATE/'caller-v1';OUT.mkdir(exist_ok=False);rows=[]
for fill in [0,1,0xff]:
 r=fresh_map();place_army(r,2,(100,40),1);put(r,0x47c1ec+2*656+6,8)
 for i,p in zip([0,1,3],[(101,39),(101,40),(101,41)]):place_army(r,i,p,1);put(r,0x47c1ec+i*656+6,0)
 place_army(r,6,(110,40),3)
 for i in range(20):put(r,0x47c1ec+6*656+16+32*i+4,7000 if i==0 else 0)
 for n,j in [(1,3),(3,1)]:put(r,0x474670+n*1172+0x26+2*j,3)
 try:
  v=run(0x44f31c,ram=r,fill=fill,readonly=False,stop=(0x44dba8,))
  first=v['trace'][-1];assert first['function']=='0x44dba8'
  rows.append(dict(stack_fill=fill,actor=first['eax']&65535,destination=list(struct.unpack('<2h',struct.pack('<I',first['edx']))),entry_local_e=first['entry_local_e'],scope='actual F31C caller stopped before DBA8'))
  with (OUT/f'{fill}-trace.json').open('x') as f:json.dump({k:x for k,x in v.items() if k!='ram'},f,indent=2)
 except Exception as e:rows.append(dict(stack_fill=fill,error=repr(e)))
with (DATA/'caller-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(rows))
