"""Target-side fallback and separated score/destination/step controls."""
import json
from core import *
import model as M
out=PRIVATE/'advanced-v1';out.mkdir();rows=[]
def save(name,r,v,row):
 folder=out/name;folder.mkdir()
 with (folder/'input.ram').open('xb') as f:f.write(r)
 with (folder/'result.json').open('x') as f:json.dump({k:x for k,x in v.items() if k!='ram'},f,indent=2)
 with (folder/'after.ram').open('xb') as f:f.write(v['ram'])
 rows.append(dict(case=name,**row))
origin=(221,94);target=(230,100)
for success in [False,True]:
 r=fresh_map(0);setcell(r,origin,2)
 for p in M.line(origin,M.POINTS[33]):setcell(r,p,2)
 radius=4 if success else 1
 for x in range(target[0]-radius,target[0]+radius+1):
  for y in range(target[1]-radius,target[1]+radius+1):setcell(r,(x,y),2)
 if success:
  for p in M.line(origin,(233,103)):setcell(r,p,2)
 expected=M.waypoint(r,1,origin,target);v=run(0x44d174,1,point(origin),point(target),(0x80a000,),ram=r)
 assert expected['kind']=='target-local-fallback'
 assert (v['out'][0]==-1 if expected['point'] is None else v['out']==list(expected['point']))
 save('target-fallback-'+str(success),r,v,dict(origin=origin,target=target,point=expected['point'],branch=expected['kind'],model_equal=True))
for blocked in [False,True]:
 r=fresh_map();origin=(230,80);target=(240,90);place_army(r,2,origin,1);place_army(r,6,target,3);place_army(r,0,(220,82),0)
 for actor,troops,typ in [(6,7000,0),(0,31565,1)]:
  for k in range(20):put(r,0x47c1ec+actor*656+16+32*k+4,troops if k==0 else 0)
  put(r,0x47c1ec+actor*656+16+2,typ)
 for n,j in [(1,3),(3,1),(1,0),(0,1)]:put(r,0x474670+n*1172+0x26+2*j,3)
 put(r,0x47c1ec+2*656+6,8)
 if blocked:setcell(r,(235,85),0)
 score=run(0x44ee60,2,0x80a000,0x80a004,(0x80a008,),ram=r);selected=score['words'][0];value=score['words'][2];dist=score['words'][4];assert selected==6
 direct=M.direct(r,origin,target)
 waypoint=None if direct else M.waypoint(r,1,origin,target)['point']
 v=run(0x44dba8,2,point(target),ram=r,local_e=0,readonly=False,stop=(0x44aee4,0x44b27c))
 stores=[s for s in v['coordinate_stores'] if s['actor']==2]
 save('score-vs-route-'+str(blocked),r,v,dict(origin=origin,target=target,changed_cell=None if not blocked else [235,85,0],selected_army=selected,score=value,distance=dist,
   direct=direct,waypoint=waypoint,entered_steps=len(stores)//2,terminal=xy(v['ram'],0x47c1ec+2*656),remaining=short(v['ram'],0x47c1ec+2*656+6),
   continuation_guard='seeded nonnegative to model the proven F31C caller context; budget exhaustion makes residue immaterial here'))
assert rows[2]['score']==rows[3]['score'] and rows[2]['selected_army']==rows[3]['selected_army'] and rows[2]['direct'] is True and rows[3]['direct'] is False
with (DATA/'advanced-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(rows))
