"""Declare immutable generated strategic cases before launching them.

No owner1355/1388 input is read. Never delete/overwrite a save or measurement.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from state import sav
BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
INPUT=BASE/'inputs-v1';INPUT.mkdir(parents=True,exist_ok=False)
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
SOURCE=ROOT/'artifacts/run-exp-sav-conversion-broad153/exports-v1'
cases=[]
def declare(label,source,edit=None,focus='natural-start'):
    original=(SOURCE/(source+'.SAV')).read_bytes();b=bytearray(original)
    s=sav.parse(b);edits=[]
    if edit:edit(b,s,edits)
    assert len(b)==len(original)
    final=sav.parse(b)
    path=INPUT/(label+'.SAV')
    with path.open('xb') as f:f.write(b)
    cases.append(dict(label=label,source=source,source_sha256=hashlib.sha256(original).hexdigest(),
        input_sha256=hashlib.sha256(b).hexdigest(),human=sav.NATIONS[final['current_nation']],
        turn=final['turn'],seed=1,focus=focus,edits=edits,
        provenance='retained generated gameplay start' if not edits else 'synthetic strategic edits of retained generated start'))

for source in ('S00-rome','S01-carthage','S02-seleucid','S03-ptolemaic','S05-numidia','S06-gaul'):
    declare('N-'+source[4:],source)

def nation_offset(s):return sav.ARMY_OFF+2+len(s['armies'])*656+2+len(s['fleets'])*26
def war(n,m):
    def edit(b,s,edits):
        off=nation_offset(s)
        for i,j in ((n,m),(m,n)):
            p=off+i*1172+0x26+j*2;before=struct.unpack_from('<h',b,p)[0]
            struct.pack_into('<h',b,p,3)
            edits.append(dict(field='relation',nation=i,other=j,before=before,after=3))
    return edit
declare('W-rome-gaul','S05-numidia',war(0,6),'active-war')
declare('W-carthage-numidia','S00-rome',war(1,5),'active-war')
def shortages(b,s,edits):
    for army in s['armies']:
        if army['owner']!=3:continue
        for offset,field in ((10,'supplies'),(12,'money')):
            p=100958+army['id']*656+offset
            before=struct.unpack_from('<h',b,p)[0];struct.pack_into('<h',b,p,0)
            edits.append(dict(field=field,army=army['id'],before=before,after=0))
declare('L-ptolemaic-shortages','S01-carthage',shortages,'supplies-and-money')
def threat(b,s,edits):
    war(1,2)(b,s,edits)
    cap=s['cities'][s['nations'][2]['capital']]
    army=next(a for a in reversed(s['armies']) if a['owner']==1 and not a['embarked'])
    options=[(x,y) for x in range(max(1,cap['x']-16),min(319,cap['x']+16)+1)
        for y in range(max(1,cap['y']-16),min(139,cap['y']+16)+1)
        if max(abs(x-cap['x']),abs(y-cap['y']))==14 and 2<=sav.cell(s,x,y)<=11]
    x,y=min(options,key=lambda p:(abs(p[1]-cap['y']),p[0],p[1]))
    old=(army['x'],army['y']);covered=sav.cell(s,x,y);marker=sav.cell(s,*old)
    struct.pack_into('<h',b,2*(old[0]*140+old[1]),army['cell'])
    struct.pack_into('<h',b,2*(x*140+y),marker)
    p=100958+army['id']*656
    struct.pack_into('<2h',b,p,x,y);struct.pack_into('<h',b,p+8,covered)
    edits.append(dict(field='army-position-and-map-overlay',army=army['id'],before=old,after=[x,y],
        covered_before=army['cell'],covered_after=covered,marker=marker,capital=[cap['x'],cap['y']],distance=14))
declare('H-seleucid-capital','S00-rome',threat,'homeland-threat')
with (DATA/'case-manifest-v1.json').open('x') as f:json.dump(dict(cases=cases,
    live_observer_cases=10,plain_controls=['N-rome','H-seleucid-capital'],
    known_reference='1388 retained private evidence, no new owner run',
    decision_families=['army-target-tree','resupply-destination','army-route','fleet-route'],
    outcome_only_families=['recruitment','economy','diplomacy'],
    scope='one End turn per generated case; local conditional comparisons, not whole-turn RNG parity'),f,indent=2)
print('Declared',len(cases),'cases; two plain recorder controls; all inputs new and immutable')
