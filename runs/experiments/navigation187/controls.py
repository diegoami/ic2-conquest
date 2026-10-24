"""Declared minimal controls; raw RAM/traces private, public scalar rows only."""
import json,random,struct
from core import *
import model as M
OUT=PRIVATE/'controls-v1';OUT.mkdir(exist_ok=False);rows=[]
def publish(name,inputs,result,extra=None):
 row=dict(case=name,inputs=inputs,result=result)
 if extra:row.update(extra)
 rows.append(row)
def keep(name,r,trace):
 folder=OUT/name;folder.mkdir()
 with (folder/'input.ram').open('xb') as f:f.write(r)
 with (folder/'trace.json').open('x') as f:json.dump({k:v for k,v in trace.items() if k!='ram'},f,indent=2)
 with (folder/'after.ram').open('xb') as f:f.write(trace['ram'])
# Manifest precedes all controls. Enumerated classifier edges use fixed tables;
# random samples use a fixed harness seed and are not new original game draws.
manifest=dict(classifier='all8strict box edges,6split thresholds,100fixed random coordinates',line='80fixed random pairs plus one-variable medium/marker/end changes',
 eligibility='same/different geographic pairs; fleet owner/launch/cargo/moves',routes='defined real-world pairs and nested route index/hub/tie controls',
 undefined='coincident CB40; direct-walk continuation local_e; group3graph fallback',
 fleet='no usable/adjacent/distant empty own fleet',contact='hostile/friendly final army/city dispatch, stop before resolver',
 owner='final private conditional only after public controls')
with (DATA/'control-manifest-v1.json').open('x') as f:json.dump(manifest,f,indent=2)
positions=[]
for x0,x1,y0,y1 in M.SPEC['regions']:
 positions.extend([(x0,(y0+y1)//2),(x0+1,(y0+y1)//2),(x1-1,(y0+y1)//2),(x1,(y0+y1)//2),((x0+x1)//2,y0),((x0+x1)//2,y0+1),((x0+x1)//2,y1-1),((x0+x1)//2,y1)])
for x,y in M.SPEC['coordinate_splits']:positions.extend([(x-1,y-1),(x,y-1),(x-1,y),(x,y)])
rng=random.Random(187);positions.extend([(rng.randrange(1,319),rng.randrange(1,139)) for _ in range(100)])
for i,p in enumerate(positions):
 actual=classify(RAM,p);expected=M.geographic(p);assert actual==expected,(p,actual,expected)
 publish(f'geo-{i:03}',dict(point=p),dict(region=actual[0],coordinate_side=actual[1],model_equal=True))
base=fresh_map();origin=(230,80);target=(240,90)
for name,change in [('clear',None),('sea-intermediate',((235,85),0)),('rough-intermediate',((235,85),1)),('army-intermediate',((235,85),203)),('city-intermediate',((235,85),23)),('fleet-intermediate',((235,85),303)),('sea-final',(target,0))]:
 r=bytearray(base)
 if change:setcell(r,*change)
 result=run(0x44cb40,point(origin),point(target),ram=r);value=bool(result['eax']&255);assert value==M.direct(r,origin,target)
 publish('line-'+name,dict(origin=origin,target=target,change=change),dict(direct=value,model_equal=True))
for i in range(80):
 a=(rng.randrange(2,318),rng.randrange(2,138));b=(rng.randrange(2,318),rng.randrange(2,138))
 if a==b:continue
 value=bool(run(0x44cb40,point(a),point(b))['eax']&255);assert value==M.direct(RAM,a,b),(a,b,value)
 publish(f'line-world-{i:03}',dict(origin=a,target=b),dict(direct=value,model_equal=True))
for fill in [0,1,0xff]:
 value=bool(run(0x44cb40,point(origin),point(origin),fill=fill)['eax']&255)
 publish('line-coincident-'+str(fill),dict(point=origin,stack_fill=fill),dict(direct=value,scope='isolated uninitialized-step control, not a universal no-op rule'))
for name,src,dst,fleet in [
 ('same-clear',(230,80),(240,90),None),('same-blocked',(230,80),(240,90),None),
 ('cross-none',(100,40),(230,90),None),('cross-foreign',(100,40),(230,90),dict(owner=3)),
 ('cross-own-building',(100,40),(230,90),dict(owner=1,countdown=5)),
 ('cross-own-loaded',(100,40),(230,90),dict(owner=1,cargo=3)),
 ('cross-own-zero',(100,40),(230,90),dict(owner=1,moves=0)),
 ('cross-own-empty',(100,40),(230,90),dict(owner=1)),
 ('different-island',(86,56),(108,66),None)]:
 r=fresh_map();place_army(r,2,src,1)
 if name=='same-blocked':setcell(r,(235,85),0)
 if fleet:
  put(r,0x4a0326,1)
  for off,value in [(8,fleet['owner']),(10,fleet.get('countdown',-1)),(12,fleet.get('moves',25)),(22,fleet.get('cargo',-1))]:put(r,0x49c26c+off,value)
 actual=bool(run(0x44cab4,2,point(dst),ram=r)['eax']&255)
 expected=M.geographic(src)==M.geographic(dst) or bool(fleet and fleet['owner']==1);assert actual==expected
 publish('eligible-'+name,dict(origin=src,target=dst,fleet=fleet),dict(eligible=actual,direct=bool(run(0x44cb40,point(src),point(dst),ram=r)['eax']&255),model_equal=True))
# Precise nested route helper contract; static route rows/hubs are exercised
# directly with the actual parent's documented candidate frame.
for i,(g,candidates,tgt) in enumerate([(1,[26,39],36),(1,[26,33],31),(1,[31,33],32),(1,[33,31],32),(2,[40,54],47),(0,[1,6],25)]):
 hub=M.HUBS[g];setup=[(-2,len(candidates),2),(-0x2c,g,2),(-0x2e,tgt,2),(-0x30,hub,2),(8,0x80a000,4)]+[(-0x2a+2*k,v,2) for k,v in enumerate(candidates)]
 value=run(0x44d010,args=(0x80b000,),frame_setup=setup)['out'];pc=sc=1000;primary=secondary=None
 for c in candidates:
  for row in range(7):
   rr=M.ROUTES[g,row]
   if c not in rr:continue
   x=rr.index(c)
   if tgt in rr and abs(x-rr.index(tgt))<pc:pc=abs(x-rr.index(tgt));primary=c
   if hub in rr and abs(x-rr.index(hub))<sc:sc=abs(x-rr.index(hub));secondary=c
 selected=primary if primary is not None else secondary;assert value==list(M.POINTS[selected])
 publish(f'route-frame-{i}',dict(group=g,visible_candidates=candidates,target_side_node=tgt,hub=hub),dict(point=value,node=selected,primary=primary is not None,model_equal=True))
# Deterministic actual-world route samples, covering direct-blocked routing
# rather than deriving a rule from the owner's one recorded origin.
land=[(x,y) for x in range(8,313,8) for y in range(8,133,8) if 2<=cell(RAM,(x,y))<=11]
route_counts={};tested=0
for _ in range(650):
 a=rng.choice(land);b=rng.choice(land)
 if a==b or M.geographic(a)!=M.geographic(b) or M.direct(RAM,a,b):continue
 g=M.group(a)
 try:expected=M.waypoint(RAM,g,a,b)
 except M.OriginalUndefined:continue
 if route_counts.get(expected['kind'],0)>=12:continue
 actual=run(0x44d174,g,point(a),point(b),(0x80a000,))['out'];want=expected['point']
 assert (actual[0]==-1 if want is None else actual==list(want)),(a,b,expected,actual)
 publish(f'world-waypoint-{tested:03}',dict(origin=a,target=b,group=g),dict(point=None if actual[0]==-1 else actual,branch=expected['kind'],model_equal=True))
 route_counts[expected['kind']]=route_counts.get(expected['kind'],0)+1;tested+=1
for name,r in [('no-node',fresh_map(0)),('origin-local',fresh_map(0))]:
 src=(230,80);dst=(240,90)
 for pos in [src,dst]:
  radius=4 if name=='origin-local' else 1
  for x in range(pos[0]-radius,pos[0]+radius+1):
   for y in range(pos[1]-radius,pos[1]+radius+1):setcell(r,(x,y),2)
 actual=run(0x44d174,1,point(src),point(dst),(0x80a000,),ram=r);expected=M.waypoint(r,1,src,dst)
 assert (actual['out'][0]==-1 if expected['point'] is None else actual['out']==list(expected['point']))
 publish('waypoint-'+name,dict(origin=src,target=dst),dict(point=None if actual['out'][0]==-1 else actual['out'],branch=expected['kind'],eligible_looking=M.geographic(src)==M.geographic(dst),model_equal=True));keep(name,r,actual)
with (DATA/'scalar-controls-v1.json').open('x') as f:json.dump(dict(rows=rows,world_route_branches=route_counts),f,indent=2)
print(json.dumps(dict(public_scalar_rows=len(rows),world_route_branches=route_counts,coincident=[r['result']['direct'] for r in rows if r['case'].startswith('line-coincident')])))
