"""Add a declared shortage case beyond all automatic supply-provider radii."""
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity';BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
m=json.loads((DATA/'case-manifest-v2.json').read_text());source=BASE/'inputs-v1/L-ptolemaic-shortages.SAV'
b=bytearray(source.read_bytes());s=sav.parse(b);army=next(a for a in s['armies'] if a['owner']==3 and not a['embarked'])
cap=s['cities'][s['nations'][3]['capital']]
def distance(p,q):return max(abs(p[0]-q[0]),abs(p[1]-q[1]))
options=[]
for x in range(160,221):
    for y in range(95,126):
        pos=x,y
        if not 2<=sav.cell(s,x,y)<=11 or not 10<=distance(pos,(cap['x'],cap['y']))<=30:continue
        if min(distance(pos,(c['x'],c['y'])) for c in s['cities'])<6:continue
        if min(distance(pos,(a['x'],a['y'])) for a in s['armies'] if a['id']!=army['id'])<8:continue
        options.append(pos)
x,y=min(options,key=lambda p:(distance(p,(cap['x'],cap['y'])),p))
old=army['x'],army['y'];covered=sav.cell(s,x,y);marker=sav.cell(s,*old)
struct.pack_into('<h',b,2*(old[0]*140+old[1]),army['cell']);struct.pack_into('<h',b,2*(x*140+y),marker)
off=100958+army['id']*656;struct.pack_into('<2h',b,off,x,y);struct.pack_into('<h',b,off+8,covered)
label='L-ptolemaic-isolated'
with (BASE/'inputs-v1'/(label+'.SAV')).open('xb') as f:f.write(b)
case=dict(label=label,source='L-ptolemaic-shortages',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    input_sha256=hashlib.sha256(b).hexdigest(),human='Carthage',turn=720,seed=1,focus='isolated-low-supply-decision',
    provenance='synthetic relocation of declared shortage case, no owner input',
    edits=[dict(field='army-position-and-map-overlay',army=army['id'],before=old,after=[x,y],
        minimum_city_distance=min(distance((x,y),(c['x'],c['y'])) for c in s['cities']),supplies=0,money=0)])
m['cases'].append(case);m['coverage_amendment']='The first shortage input is naturally refilled before target choice. Add this isolated input before running it to measure a genuinely depleted decision boundary; preserve all prior cases/results.'
with (DATA/'case-manifest-v3.json').open('x') as f:json.dump(m,f,indent=2)
print(json.dumps(case))
