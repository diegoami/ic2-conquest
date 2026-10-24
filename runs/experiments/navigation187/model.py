"""Source-shaped rule evaluator for the classical static world, not a new AI.

Undefined original stack branches raise explicitly. No invented pathfinder.
"""
import json,struct
from pathlib import Path
DATA=Path(__file__).resolve().parents[3]/'runs/experiments/data/run-exp-navigation187'
def cell(world,p):
 # Public model needs only a cell(x,y) callback. Raw-RAM adapter is retained
 # for the original diagnostic controls; no original binary is imported here.
 if callable(world):return world(*p)
 return struct.unpack_from('<h',world,0x870+2*(p[0]*140+p[1]))[0]
SPEC=json.loads((DATA/'navigation-data-v1.json').read_text())
POINTS={p['index']:(p['x'],p['y']) for p in SPEC['waypoints']}
ROUTES={(r['group'],r['row']):r['points'] for r in SPEC['routes']}
GROUPS={int(k):v for k,v in SPEC['groups'].items()};HUBS={int(k):v for k,v in SPEC['hubs'].items()}
class OriginalUndefined(RuntimeError):pass
def geographic(pos):
 x,y=pos;region=-1;split=1
 for i,(xmin,xmax,ymin,ymax) in enumerate(SPEC['regions']):
  if xmin<x<xmax and ymin<y<ymax:region=i
 for xx,yy in SPEC['coordinate_splits']:
  if x<xx and y<yy:split=0
 return region,split
def group(pos):
 region,split=geographic(pos);return 3 if region>=0 else 2 if split==0 else 1
def medium(code):return int(code<2 or code>=300)
def line(a,b):
 if a==b:raise OriginalUndefined('CB40coincident arguments read an uninitialized step word in isolation')
 x,y=a;dx=abs(b[0]-x);dy=abs(b[1]-y);sx=(b[0]>x)-(b[0]<x);sy=(b[1]>y)-(b[1]<y)
 xmajor=dx>=dy;major=max(dx,dy);minor=min(dx,dy);error=2*minor-major
 for _ in range(major):
  while error>=0:
   if xmajor:y+=sy
   else:x+=sx
   error-=2*major
  if xmajor:x+=sx
  else:y+=sy
  error+=2*minor;yield x,y
def direct(ram,a,b,coincident=False):
 if a==b:
  if coincident:return True
  raise OriginalUndefined('CB40zero-distance isolated call')
 m=medium(cell(ram,a));points=list(line(a,b))
 return all(medium(cell(ram,p))==m for p in points[:-1])
def distance(a,b):return max(abs(a[0]-b[0]),abs(a[1]-b[1]))
def fallback(ram,pos,mode=0):
 chosen=None;m=medium(cell(ram,pos))
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:
   if dx==dy==0:continue
   ray=[(min(319,max(0,pos[0]+dx*n)),min(139,max(0,pos[1]+dy*n))) for n in [1,2,3]]
   if all(medium(cell(ram,p))==m or (mode&medium(cell(ram,p)))!=0 for p in ray):chosen=ray[-1]
 return chosen
def waypoint(ram,g,origin,target,depth=0):
 if depth>12:raise OriginalUndefined('recursive waypoint control did not converge')
 visible=[];closest_target=None;closest_common=None;ct=cc=1000
 for i in range(GROUPS[g][0],GROUPS[g][1]+1):
  p=POINTS[i];d=distance(origin,p)
  # Source calls origin test first, then target test on the same stack. If
  # target==node and d>0, its step residue is positive, so target visibility true.
  source_visible=False if d==0 else direct(ram,origin,p)
  if source_visible and d>0:visible.append(i)
  target_visible=direct(ram,target,p,coincident=True)
  if target_visible and 0<d<ct:closest_target=i;ct=d
  if target_visible and source_visible and 0<d<cc:closest_common=i;cc=d
 if closest_common is not None:return dict(kind='common-visible',point=POINTS[closest_common],node=closest_common)
 if visible and closest_target is not None:
  if g not in HUBS:raise OriginalUndefined('group3has no route matrix or initialized hub; D010reads terrain words/stack')
  primary=secondary=None;pc=sc=1000
  for i in visible:
   for row in range(7):
    r=ROUTES[g,row]
    if i not in r:continue
    a=max(j for j,v in enumerate(r) if v==i)
    if closest_target in r:
     b=max(j for j,v in enumerate(r) if v==closest_target);cost=abs(a-b)
     if cost<pc:primary=i;pc=cost
    if HUBS[g] in r:
     h=max(j for j,v in enumerate(r) if v==HUBS[g]);cost=abs(a-h)
     if cost<sc:secondary=i;sc=cost
  selected=primary if primary is not None else secondary
  if selected is None:raise OriginalUndefined('D010secondary output slot was not initialized')
  return dict(kind='route-row' if primary is not None else 'route-hub',point=POINTS[selected],node=selected)
 if not visible:return dict(kind='origin-local-fallback',point=fallback(ram,origin),node=None)
 point=fallback(ram,target)
 if point is not None and not direct(ram,origin,point):return waypoint(ram,g,origin,point,depth+1)
 return dict(kind='target-local-fallback',point=point,node=None)
