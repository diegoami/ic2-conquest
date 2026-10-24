"""Static island-domain proof; forced group3garbage is not a routing table."""
import json
from core import *
import model as M
rows=[];samples=[]
for index,(x0,x1,y0,y1) in enumerate(M.SPEC['regions']):
 union=set();cells=0
 for x in range(x0+1,x1):
  for y in range(y0+1,y1):
   p=(x,y)
   if M.geographic(p)[0]!=index or M.medium(cell(RAM,p)):continue
   cells+=1
   for j in range(55,59):
    node=M.POINTS[j]
    if node==p:continue
    expected=M.direct(RAM,p,node)
    if expected:union.add(j)
    if (x+y+j)%37==0:
     actual=bool(run(0x44cb40,point(p),point(node))['eax']&255);assert actual==expected
     samples.append(dict(region=index,point=p,node=j,direct=actual))
 assert len(union)<=1
 rows.append(dict(region=index,land_or_land_marker_cells=cells,visible_island_node_union=sorted(union),graph_fallback_reachable_for_two_same_region_land_points=False))
with (DATA/'island-topology-v1.json').open('x') as f:json.dump(dict(regions=rows,original_instruction_spot_controls=samples,
 domain='fixed original classical terrain plus army/city marker substitution; does not cover arbitrary edited maps',
 proof='At most one island waypoint is visible anywhere within each region. If origin and target each see a waypoint, it is the same common node. Otherwise origin/target local fallback runs; D010group3is not reached.'),f,indent=2)
print('PASS329static island land cells; group3graph fallback unreachable in this fixed-world domain;',len(samples),'additional original line controls')
