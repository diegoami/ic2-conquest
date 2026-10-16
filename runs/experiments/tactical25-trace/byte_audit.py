"""Read-only byte equality of pure attribution helpers in source/control/observed executables."""
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'));import battle_hook as H
paths=[Path('/home/diego/ic2-work/build/Imperial Conquest 2 fast rollingsave seed.exe'),Path('/home/diego/ic2-work/build/Imperial Conquest 2 lab s1.exe'),ROOT/'artifacts/run-exp-tactical25-trace/state-observer-20261016-191329.exe'];raw=[p.read_bytes() for p in paths]
def get(b,va,n):
 for _,s,v,r,z,_ in H.sections(b):
  if s<=va and va+n<=s+z:return b[r+va-s:r+va-s+n]
 raise ValueError(hex(va))
rows=[]
for label,start,end in [('threat body after displaced prologue',0x43a721,0x43aa60),('line and box pure helpers',0x439f00,0x43a160),('min max swaps distance helpers',0x448fd0,0x449030)]:
 bs=[get(b,start,end-start) for b in raw];assert bs[0]==bs[1]==bs[2];rows.append(dict(label=label,start=hex(start),end_exclusive=hex(end),sha256=hashlib.sha256(bs[0]).hexdigest(),all_three_equal=True))
rec=dict(exe_sha256s=[dict(path=str(p),sha256=hashlib.sha256(b).hexdigest()) for p,b in zip(paths,raw)],ranges=rows,scope='Body equality for source/x86 attribution; entry detour/prologue preserved separately by inertness proof')
out=ROOT/'runs/experiments/data/run-exp-tactical25-trace'/('byte-audit-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out)
