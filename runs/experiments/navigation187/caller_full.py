"""Actual F31C blocked-line caller/recursive context controls, private traces."""
import json
from core import *
out=PRIVATE/'caller-full-v1';out.mkdir();rows=[]
for fill in [0,1,0xff]:
 r=fresh_map();place_army(r,2,(100,40),1);put(r,0x47c1ec+2*656+6,8)
 for i,p in zip([0,1,3],[(101,39),(101,40),(101,41)]):place_army(r,i,p,1);put(r,0x47c1ec+i*656+6,0)
 place_army(r,6,(110,40),3)
 for i in range(20):put(r,0x47c1ec+6*656+16+32*i+4,7000 if i==0 else 0)
 for n,j in [(1,3),(3,1)]:put(r,0x474670+n*1172+0x26+2*j,3)
 v=run(0x44f31c,ram=r,fill=fill,readonly=False,stop=(0x44aee4,0x44b27c),budget=10000000)
 entries=[t for t in v['trace'] if t['function']=='0x44dba8']
 rows.append(dict(stack_fill=fill,entries=[dict(actor=t['eax']&65535,local_e=t['entry_local_e']) for t in entries],final_army=xy(v['ram'],0x47c1ec+2*656),moves=short(v['ram'],0x47c1ec+2*656+6),stopped=v['stop']))
 with (out/f'{fill}-trace.json').open('x') as f:json.dump({k:x for k,x in v.items() if k!='ram'},f,indent=2)
 with (out/f'{fill}-after.ram').open('xb') as f:f.write(v['ram'])
assert all(r['final_army']==rows[0]['final_army'] and r['moves']==rows[0]['moves'] for r in rows)
with (DATA/'caller-full-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(rows))
