"""Ferry/contact/stack-residue controls. Full traces and bytes remain private."""
import json,struct
from core import *
import model as M
OUT=PRIVATE/'branches-v1';OUT.mkdir(exist_ok=False);rows=[]
def keep(name,r,v,public):
 folder=OUT/name;folder.mkdir()
 for file,body in [('before.ram',bytes(r)),('after.ram',v['ram'])]:
  with (folder/file).open('xb') as f:f.write(body)
 with (folder/'trace.json').open('x') as f:json.dump({k:x for k,x in v.items() if k!='ram'},f,indent=2)
 rows.append(dict(case=name,**public))
def ferry(src=(100,40),fleet=(101,40),owner=1,moves=25,countdown=-1,cargo=-1,aboard=False):
 r=fresh_map()
 for x in range(101,160):
  for y in range(140):setcell(r,(x,y),0)
 place_army(r,2,src,1);put(r,0x4a0326,1)
 for off,value in [(0,fleet[0]),(2,fleet[1]),(4,-1),(6,-1),(8,owner),(10,countdown),(12,moves),(18,90),(20,100),(22,cargo),(24,0)]:put(r,0x49c26c+off,value)
 setcell(r,fleet,332+owner)
 if aboard:
  a=0x47c1ec+2*656;setcell(r,src,2);put(r,a,fleet[0]);put(r,a+2,fleet[1]);put(r,a+8,-1);put(r,0x49c282,2)
 return r
for name,kw in [('foreign',dict(owner=3)),('building',dict(countdown=5)),('loaded',dict(cargo=3)),('zero',dict(moves=0)),
 ('adjacent',dict()),('distant-coast',dict(fleet=(105,40))),('distant-inland',dict(src=(98,40),fleet=(105,40)))]:
 r=ferry(**kw);src=tuple(xy(r,0x47c1ec+2*656));dst=(230,90)
 v=run(0x44db38,point(src),point(dst),0x80a000,(0x80b000,),ram=r,readonly=False)
 keep('ferry-'+name,r,v,dict(origin=src,target=dst,fleet_conditions=kw,waypoint_x=v['out'][0],waypoint=None if v['out'][0]<0 else v['out'],
   fleet_stored=xy(v['ram'],0x49c270),fleet_moves=short(v['ram'],0x49c278),fleet_cargo=short(v['ram'],0x49c282),
   army_position=xy(v['ram'],0x47c1ec+2*656),army_moves=short(v['ram'],0x47c1ec+2*656+6),army_covered=short(v['ram'],0x47c1ec+2*656+8),caller_goal_after=v['frame_goal_after'],calls=[t['function'] for t in v['trace']]))
r=ferry(src=(100,40),fleet=(105,40),aboard=True)
v=run(0x44dba8,2,point((230,90)),ram=r,readonly=False)
keep('already-aboard',r,v,dict(fleet_stored=xy(v['ram'],0x49c270),army_position=xy(v['ram'],0x47c1ec+2*656),army_moves=short(v['ram'],0x47c1ec+2*656+6),calls=[t['function'] for t in v['trace']]))
# Two fleets at equal distance: helper keeps first eligible table entry.
r=ferry(fleet=(105,40));put(r,0x4a0326,2)
for off,value in [(0,100),(2,45),(8,1),(10,-1),(12,25),(18,90),(20,100),(22,-1),(24,0)]:put(r,0x49c26c+26+off,value)
setcell(r,(100,45),333)
v=run(0x44db38,point((100,40)),point((230,90)),0x80a000,(0x80b000,),ram=r,readonly=False)
keep('ferry-tie',r,v,dict(first_fleet_stored=xy(v['ram'],0x49c270),second_fleet_stored=xy(v['ram'],0x49c26c+26+4),calls=[t['function'] for t in v['trace']]))
# Direct continuation residue: seed ONLY the wrapper's uninitialized local_e.
for residue in [-1,0,123]:
 r=fresh_map();place_army(r,2,(100,40),1)
 for i,p in zip([0,1,3],[(101,39),(101,40),(101,41)]):place_army(r,i,p,1)
 put(r,0x47c1ec+2*656+6,8)
 v=run(0x44dba8,2,point((110,40)),ram=r,local_e=residue,readonly=False)
 keep('direct-residue-'+str(residue),r,v,dict(residue=residue,direct=M.direct(r,(100,40),(110,40)),final=xy(v['ram'],0x47c1ec+2*656),moves=short(v['ram'],0x47c1ec+2*656+6),calls=[t['function'] for t in v['trace']]))
# Do not hide group3out-of-table reads/uninitialized secondary output.
for fill in [0,1,0xff]:
 setup=[(-2,1,2),(-0x2a,55,2),(-0x2c,3,2),(-0x2e,56,2),(8,0x80a000,4)]
 v=run(0x44d010,args=(0x80b000,),frame_setup=setup,fill=fill)
 keep('island-undefined-'+str(fill),RAM,v,dict(stack_fill=fill,point=v['out'],scope='forced nested group3branch; no route table/hub exists'))
# Actual final-destination contact dispatch, stopped BEFORE game resolution.
for name,typ,rel,moves in [('enemy-army','army',3,8),('peace-army','army',0,8),('enemy-zero','army',3,0),('enemy-city','city',3,8),('peace-city','city',0,8)]:
 r=fresh_map();place_army(r,2,(100,40),1);put(r,0x47c1ec+2*656+6,moves)
 if typ=='army':place_army(r,6,(101,40),3)
 else:
  for off,val in [(14,101),(16,40),(18,3)]:put(r,0x479590+off,val)
  setcell(r,(101,40),23)
 for n,j in [(1,3),(3,1)]:put(r,0x474670+n*1172+0x26+2*j,rel)
 v=run(0x44d734,2,point((101,40)),ram=r,readonly=False,stop=(0x44aee4,0x44b27c,0x44f6d8))
 keep('contact-'+name,r,v,dict(kind=typ,relation=rel,moves=moves,dispatch=v['stop'],final=xy(v['ram'],0x47c1ec+2*656),remaining=short(v['ram'],0x47c1ec+2*656+6)))
with (DATA/'branch-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(cases=len(rows),ferry=[r for r in rows if r['case'].startswith('ferry-')],residue=[r for r in rows if r['case'].startswith('direct-residue')],contacts=[r for r in rows if r['case'].startswith('contact')]),separators=(',',':')))
