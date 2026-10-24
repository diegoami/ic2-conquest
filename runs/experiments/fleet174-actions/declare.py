"""Declare all synthetic inputs before movement; never overwrite old evidence."""
import json,struct
from common import *
OUT=BASE/'inputs-v1';OUT.mkdir(parents=True,exist_ok=False)
cases=[]
for path in sorted(OLD.iterdir()):
 if (path/'input.ram').exists():cases.append((dict(name='phase-'+path.name,kind='phase',source=path.name),bytearray((path/'input.ram').read_bytes())))
raw=(OLD/'stored-a/input.ram').read_bytes()
def base_case(name,moves=25,cargo=False,rough=None,human=False,stored=True):
 r=bytearray(raw)
 # Move the other fleet to a valid construction record, removing its blocker.
 f=0x49c26c+26;x,y=xy(r,f);put(r,0x45e870+2*(x*140+y),short(r,f+24))
 for off,v in [(0,0),(2,0),(10,5),(12,0),(20,short(r,0x474670+3*1172+0x444)),(24,0)]:put(r,f+off,v)
 put(r,0x49c26c+12,moves)
 goal=[48,66]
 if rough is not None:
  goal=[49,63];put(r,0x45e870+2*(49*140+63),1)
 if stored:
  put(r,0x49c26c+4,goal[0]);put(r,0x49c26c+6,goal[1])
 else:put(r,0x49c26c+4,-1);put(r,0x49c26c+6,-1)
 if human:r[0x474670+1172+0x490-RAM_BASE]=1
 if cargo:
  a=0x47c1ec+3*656;x,y=xy(r,a);put(r,0x45e870+2*(x*140+y),short(r,a+8))
  put(r,a,49);put(r,a+2,62);put(r,a+8,-1);put(r,0x49c26c+22,3)
 return dict(name=name,kind='human-walk' if human else 'phase',source='stored-a',goal=goal,cargo=cargo,rough=rough,moves=moves),r
for args in [dict(name='stored-zero',moves=0),dict(name='stored-one',moves=1),
 dict(name='rough-ai-one',moves=1,rough=True),dict(name='rough-ai-three',moves=3,rough=True),
 dict(name='rough-human-one',moves=1,rough=True,human=True),dict(name='cargo-positive',cargo=True),dict(name='cargo-zero',moves=0,cargo=True)]:cases.append(base_case(**args))
def port_case(protected):
 r=bytearray(raw);cap=short(r,0x474670+3*1172+0x444);cx,cy=xy(r,0x479590+cap*34+14)
 own=[xy(r,0x479590+i*34+14) for i in range(334) if short(r,0x479590+i*34+18)==3]
 def distance(p,q):return max(abs(p[0]-q[0]),abs(p[1]-q[1]))
 target=min((x,y) for x in range(cx-2,cx+3) for y in range(cy-2,cy+3) if cell(r,x,y)<2 and distance((x,y),(cx,cy))==(1 if protected else 2) and (protected or min(distance((x,y),c) for c in own)>=2))
 actor=min((x,y) for x in range(target[0]-3,target[0]+4) for y in range(target[1]-3,target[1]+4) if cell(r,x,y)<2 and distance((x,y),target)==3)
 for i in (0,1):
  f=0x49c26c+i*26;x,y=xy(r,f);put(r,0x45e870+2*(x*140+y),short(r,f+24))
 for i,pos,ships,owner in [(0,actor,90,1),(1,target,10,3)]:
  f=0x49c26c+i*26;covered=cell(r,*pos)
  for off,v in [(0,pos[0]),(2,pos[1]),(4,-1),(6,-1),(12,25),(18,ships),(24,covered)]:put(r,f+off,v)
  put(r,0x45e870+2*(pos[0]*140+pos[1]),owner+(300 if ships<25 else 316 if ships<50 else 332))
 for n,j in [(1,3),(3,1)]:put(r,0x474670+n*1172+0x26+2*j,3)
 return dict(name='port-protected' if protected else 'port-unprotected',kind='phase',source='stored-a',actor=actor,target=target,port_city=cap),r
cases.extend([port_case(True),port_case(False)])
assert len(cases)==23
for spec,r in cases:
 folder=OUT/spec['name'];folder.mkdir()
 with (folder/'input.ram').open('xb') as f:f.write(r)
 with (folder/'input.SAV').open('xb') as f:f.write(project(r))
with (DATA/'case-manifest-v1.json').open('x') as f:json.dump(dict(cases=[s for s,r in cases],scope='synthetic complete fleet-phase/low-level controls; no game run yet',stop_before_naval_combat=True),f,indent=2)
print('Declared23new synthetic movement inputs before execution')
