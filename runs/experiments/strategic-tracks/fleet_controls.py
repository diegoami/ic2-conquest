"""Remaining174: original provider, cargo and stored-route lifetime controls.

Generated exact inputs, no battle resolution, original helper instructions only.
"""
from original_support import *
import argparse
p=argparse.ArgumentParser();p.add_argument("--version",required=True);p.add_argument("--cargo-only",action="store_true");p.add_argument("--multi-unit",action="store_true");options=p.parse_args()
source=(ROOT/'artifacts/run-exp-fleet-actions174/inputs-v1/cargo-positive/input.ram').read_bytes()
f=0x49c26c;army=0x47c1ec;na=0x474670+1172
base=bytearray(source)
# Remove all army/fleet occupancy, then keep exactly one launched own fleet.
for i in range(short(base,0x4a0324)):
 a=army+i*656;x,y=xy(base,a);covered=short(base,a+8)
 if covered>=0:put(base,0x45e870+2*(x*140+y),covered)
for i in range(short(base,0x4a0326)):
 a=f+i*26;x,y=xy(base,a)
 if short(base,a+10)<0:put(base,0x45e870+2*(x*140+y),short(base,a+24))
put(base,0x4a0324,0);put(base,0x4a0326,1);put(base,0x4a0320,1)
cap=short(base,na+1092);city=0x479590+cap*34;cx,cy=xy(base,city+14)
def distance(p,q):return max(abs(p[0]-q[0]),abs(p[1]-q[1]))
def position(r,p):
 old=xy(r,f)
 if 0<=old[0]<320 and 0<=old[1]<140 and cell(r,*old)>=300:put(r,0x45e870+2*(old[0]*140+old[1]),short(r,f+24))
 covered=cell(r,*p)
 for off,value in [(0,p[0]),(2,p[1]),(24,covered)]:put(r,f+off,value)
 put(r,0x45e870+2*(p[0]*140+p[1]),301)
for off,value in [(4,-1),(6,-1),(8,1),(10,-1),(12,20),(14,20),(16,100),(18,10),(20,100),(22,-1)]:put(base,f+off,value)
struct.pack_into('<i',base,na+1080-RAM_BASE,1000)
# Keep distant providers unchanged; exact eligible provider sets are logged below.
cases=[]
def provider(name,dist=1,owner=1,stock=100,money=100,treasury=1000,condition=100,supply=20,relation=0):
 r=bytearray(base);p=min((x,y) for x in range(max(0,cx-dist),min(319,cx+dist)+1) for y in range(max(0,cy-dist),min(139,cy+dist)+1) if distance((x,y),(cx,cy))==dist and cell(r,x,y)<2)
 position(r,p);put(r,city+18,owner);put(r,city+24,stock);put(r,f+16,money);put(r,f+14,supply);put(r,f+20,condition);struct.pack_into('<i',r,na+1080-RAM_BASE,treasury)
 if owner!=1:
  put(r,0x474670+1172+0x26+2*owner,relation);put(r,0x474670+owner*1172+0x26+2,relation)
 cases.append((dict(caseName=name,kind='provider',entry=0x44e5dc,eax=0,edx=0,city=cap,distance=dist),bytes(r)))
for stock in [0,1,100]:provider('own-stock-'+str(stock),stock=stock)
for stock in [0,1,100]:provider('foreign-stock-'+str(stock),owner=3,stock=stock)
for money in [0,1,4,5]:provider('foreign-money-'+str(money),owner=3,money=money)
for dist in [3,4]:provider('own-distance-'+str(dist),dist=dist)
for rel in [0,1,2,3]:provider('foreign-relation-'+str(rel),owner=3,relation=rel)
for treasury in [100,101]:provider('own-treasury-'+str(treasury),money=99,treasury=treasury)
for condition in [94,95]:provider('own-condition-'+str(condition),condition=condition)
for supply in [79,80,81]:provider('own-capacity-'+str(supply),supply=supply)
# Select a real unoccupied coastal neighborhood with at least two legal land cells.
sea=next((x,y) for x in range(40,300) for y in range(25,120) if cell(base,x,y)<2 and sum(2<=cell(base,x+dx,y+dy)<=11 for dx in [-1,0,1] for dy in [-1,0,1])>=2)
lands=[(sea[0]+dx,sea[1]+dy) for dx in [-1,0,1] for dy in [-1,0,1] if 2<=cell(base,sea[0]+dx,sea[1]+dy)<=11]
def cargo_raw(embarked,troops):
 r=bytearray(base);position(r,sea);put(r,0x4a0324,1);r[army-RAM_BASE:army-RAM_BASE+656]=read(source,army+3*656,656)
 for off,value in [(0,sea[0] if embarked else lands[0][0]),(2,sea[1] if embarked else lands[0][1]),(4,1),(6,8),(8,-1 if embarked else cell(r,*lands[0]))]:put(r,army+off,value)
 for i in range(20):put(r,army+16+32*i+4,troops if i==0 else 0)
 for off,value in [(16,0),(18,0),(22,short(source,army+3*656+22))]:put(r,army+off,value)
 if not embarked:put(r,0x45e870+2*(lands[0][0]*140+lands[0][1]),201)
 put(r,f+22,0 if embarked else -1);return bytes(r)
for moves in [0,8]:
 for target in lands[:2]:
  r=bytearray(cargo_raw(True,5000));put(r,f+12,moves);put(r,army+6,moves)
  cases.append((dict(caseName=f'land-moves{moves}-{target[0]}-{target[1]}',kind='disembark',entry=0x44b840,eax=0,edx=target[0]|target[1]<<16,target=target),bytes(r)))
for troops in [4999,5000,5001,10000]:cases.append((dict(caseName='embark-troops-'+str(troops),kind='embark',entry=0x44b79c,eax=0,edx=0,troops=troops),cargo_raw(False,troops)))
if options.multi_unit:
 cases=[]
 for units in [[4000,2000],[2000,3000,1000],[5000,1],[3000,2000]]:
  r=bytearray(cargo_raw(False,sum(units)))
  for slot in range(20):
   for off,value in [(0,0),(2,slot%5),(4,units[slot] if slot<len(units) else 0),(6,7)]:put(r,army+16+slot*32+off,value)
  cases.append((dict(caseName='embark-units-'+'-'.join(map(str,units)),kind='embark',entry=0x44b79c,eax=0,edx=0,units=units),bytes(r)))
if options.cargo_only:cases=[(s,r) for s,r in cases if s['kind']!='provider']
write(DATA/('fleet-manifest-'+options.version+'.json'),[s for s,r in cases]);out=BASE/('fleet-controls-'+options.version);out.mkdir(exist_ok=False);rows=[]
for spec,raw in cases:
 u,after,trace=execute(raw,spec['entry'],spec['eax'],spec['edx']);assert not trace['draws'];pair(out/spec['caseName'],raw,after)
 row=dict(**spec,draws=trace['draws'],original_fleet=list(struct.unpack('<13h',read(after,f,26))),original_army=None if short(after,0x4a0324)==0 else list(struct.unpack('<8h',read(after,army,16))))
 if spec['kind']=='provider':row['provider_cities']=[i for i in range(334) if read(raw,0x479590+i*34+24,2)!=read(after,0x479590+i*34+24,2)]
 rows.append(row)
write(DATA/('fleet-original-'+options.version+'.json'),rows);print(f'Preserved {len(rows)} provider/cargo controls, zero original RNG calls')
if options.cargo_only:raise SystemExit(0)
# Two consecutive fleet phases with a synthetic budget refresh only. Keep route
# support separate from native known unsupported stored-destination state.
r=bytearray(base);position(r,sea);goal=next((sea[0]+dx,sea[1]+dy) for dx in [-1,0,1] for dy in [-1,0,1] if (dx or dy) and cell(r,sea[0]+dx,sea[1]+dy)<2)
put(r,f+4,goal[0]);put(r,f+6,goal[1]);route=[]
for step in range(2):
 if step:put(r,f+12,20)
 before=bytes(r);u,after,trace=execute(before,0x44f608);pair(out/f'route-phase-{step}',before,after)
 route.append(dict(step=step,before=xy(before,f),after=xy(after,f),stored_route=xy(after,f+4),moves=short(after,f+12),draws=trace['draws']))
 r=bytearray(after)
write(DATA/('fleet-route-lifetime-'+options.version+'.json'),dict(scope='two synthetic F608 calls, moves reset between them; not two calendar turns or native route support',goal=goal,phases=route))
