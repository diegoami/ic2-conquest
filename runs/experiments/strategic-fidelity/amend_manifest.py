"""Retain v1's duplicate war declaration; add an explicit peace counterfactual."""
import hashlib
import json
import struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity';BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
m=json.loads((DATA/'case-manifest-v1.json').read_text())
old=next(c for c in m['cases'] if c['label']=='W-rome-gaul')
source=next(c for c in m['cases'] if c['label']=='N-numidia')
assert old['input_sha256']==source['input_sha256']
b=bytearray((BASE/'inputs-v1/N-numidia.SAV').read_bytes())
import sys
sys.path.insert(0,str(ROOT));from state import sav
s=sav.parse(b);off=100958+len(s['armies'])*656+2+len(s['fleets'])*26;edits=[]
for n,j in ((0,6),(6,0)):
    p=off+n*1172+0x26+2*j;before=struct.unpack_from('<h',b,p)[0];assert before==3
    struct.pack_into('<h',b,p,0);edits.append(dict(field='relation',nation=n,other=j,before=3,after=0))
case={**old,'label':'P-rome-gaul-peace','focus':'peace-versus-natural-war',
    'input_sha256':hashlib.sha256(b).hexdigest(),'edits':edits,'provenance':'synthetic peace counterfactual; natural N-numidia already has Rome-Gaul war'}
with (BASE/'inputs-v1/P-rome-gaul-peace.SAV').open('xb') as f:f.write(b)
m['cases']=[c for c in m['cases'] if c['label']!='W-rome-gaul']+[case]
m['superseded_alias']=dict(label='W-rome-gaul',identical_input_to='N-numidia',native_observation_retained=True,original_alias_run_not_needed=True)
m['amendment']='Before focused original runs: v1 war edit was a no-op because the generated start already has war. Preserve v1 and its native output; test peace against natural war instead.'
with (DATA/'case-manifest-v2.json').open('x') as f:json.dump(m,f,indent=2)
print('Manifest v2: ten byte-distinct cases; war/peace comparison explicit; duplicate native observation retained')
