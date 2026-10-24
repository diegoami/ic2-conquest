"""Public synthetic score-fed original branch boundaries, no owner data."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'));import core as C
sys.path.insert(0,str(ROOT/'runs/experiments/fleet174-actions'));from common import project
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args();D=ROOT/'runs/experiments/data/run-exp-city-army187';out=ROOT/'artifacts/run-exp-city-army187/private'/('branch-grid-'+a.version);out.mkdir(exist_ok=False)
base=C.fresh_map();C.place_army(base,4,(100,40),1)
for off,value in [(6,7),(10,0),(14,80)]:C.put(base,0x47c1ec+4*656+off,value)
C.place_army(base,6,(128,40),3)
for city,pos in [(0,(128,40)),(1,(90,50))]:
 for off,value in [(14,pos[0]),(16,pos[1])]:C.put(base,0x479590+city*34+off,value)
order=struct.unpack('<16h',C.read(base,0x49efe8,32));C.put(base,0x4a0322,order.index(1))
container=bytearray(project(base));tail=C.sav.parse(container)['tail_off'];container[tail:tail+32]=C.read(base,0x49efe8,32)
with (out/'generated-before.SAV').open('xb') as f:f.write(container)
spec=[dict(army_score=army,city_score=city,city_distance=dist,army_distance=28,moves=7,supplies=0,morale=80) for army in [99,100,101,828] for city in [99,100,101,495] for dist in [6,28]]
with (D/('branch-grid-manifest-'+a.version+'.json')).open('x') as f:json.dump(dict(scope='score-fed branch boundary controls only, not naturally reached scorer outputs or complete games',cases=spec),f,indent=2)
rows=[]
for case in spec:
 r=bytearray(base);C.put(r,0x479590+14,100+case['city_distance'])
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
 for va,rp,rs in C.SECTIONS:
  if rs:u.mem_write(va,C.EXE[rp:rp+rs])
 u.mem_write(C.ORIGIN,bytes(r));u.mem_write(0x80f000,struct.pack('<7h',1,0,6,case['army_score'],case['city_score'],28,case['city_distance']))
 for reg,value in [(UC_X86_REG_ESP,0x80f000),(UC_X86_REG_EBX,0x47c1ec+4*656),(UC_X86_REG_ESI,4)]:u.reg_write(reg,value)
 result={};rng=[]
 def hook(uc,address,size,user):
  if address==0x40284c:rng.append(address);uc.emu_stop()
  if address in [0x44dba8,0x44e84c]:
   site=struct.unpack('<I',uc.mem_read(uc.reg_read(UC_X86_REG_ESP),4))[0]-5
   result.update(kind={0x44f409:'AttackArmy',0x44f43f:'AttackCity',0x44f47c:'MoveToResupplyCity',0x44f485:'MercenaryRun'}[site],site=hex(site));uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44f3b8,0x44f4cc,count=100000)
 assert result and not rng and bytes(u.mem_read(C.ORIGIN,C.SIZE))==bytes(r)
 rows.append(dict(**case,original_branch=result['kind'],original_call_site=result['site'],game_RAM_unchanged=True,original_RNG_calls=0))
with (D/('branch-grid-original-'+a.version+'.json')).open('x') as f:json.dump(rows,f,indent=2)
print('PASS32 original public score-fed branch controls at99/100/101 and positive controls')
