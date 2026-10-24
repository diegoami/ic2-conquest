"""FINAL retained-owner conditional; output only already-public scalar audit.

Owner input hashes, RAM, projections and complete traces stay PRIVATE.
"""
import json
from core import *
import model as M
source=ROOT/'artifacts/run-exp-seleucid1388/private/hook-seed1-v2/defender-prewalk-ram.bin'
raw=source.read_bytes();assert xy(raw,0x47c1ec+4*656)==[219,93]
out=PRIVATE/'owner-regression-v1';out.mkdir()
origin=(219,93);target=(191,95)
assert classify(raw,origin)==M.geographic(origin)==(-1,1) and classify(raw,target)==M.geographic(target)==(-1,1)
eligible=bool(run(0x44cab4,4,point(target),ram=raw)['eax']&255);direct=bool(run(0x44cb40,point(origin),point(target),ram=raw)['eax']&255)
choice=M.waypoint(raw,1,origin,target);actual=run(0x44db38,point(origin),point(target),0x80a000,(0x80b000,),ram=raw)
assert eligible and not direct and choice['point']==(189,104) and actual['out']==[189,104]
score=run(0x44ee60,4,0x80a000,0x80a004,(0x80a008,),ram=raw)
assert score['words'][0]==24 and score['words'][2]==828 and score['words'][4]==28
v=run(0x44dba8,4,point(target),ram=raw,readonly=False);assert xy(v['ram'],0x47c1ec+4*656)==[212,96] and short(v['ram'],0x47c1ec+4*656+6)==0
with (out/'trace.json').open('x') as f:json.dump({k:x for k,x in v.items() if k!='ram'},f,indent=2)
# Private diagnostic SAV container from retained before-End save metadata.
template=next((ROOT/'artifacts/run-exp-battle1355/private-v1/original-end-acceptance-20261024b').glob('*-BEFORE-END.SAV')).read_bytes();s=sav.parse(template)
na,nf=short(raw,0x4a0324),short(raw,0x4a0326)
b=read(raw,0x45e870,89600)+read(raw,0x479590,11356)+struct.pack('<h',na)+read(raw,0x47c1ec,na*656)
b+=struct.pack('<h',nf)+read(raw,0x49c26c,nf*26)+read(raw,0x474670,18752)+read(raw,0x49da10,600)
news=100958+len(s['armies'])*656+2+len(s['fleets'])*26+18752+600;tail=bytearray(template[s['tail_off']:s['tail_off']+55])
tail[:32]=read(raw,0x49efe8,32)
for offset,address in [(36,0x4a0320),(38,0x4a0322),(40,0x4a0330),(42,0x4a0332),(44,0x4a032e)]:struct.pack_into('<h',tail,offset,short(raw,address))
tail[54]=0;b+=template[news:s['tail_off']]+tail
with (out/'before.SAV').open('xb') as f:f.write(b)
with (out/'before.json').open('x') as f:json.dump(sav.parse(b),f)
with (out/'input.ram').open('xb') as f:f.write(raw)
with (out/'after.ram').open('xb') as f:f.write(v['ram'])
with (DATA/'private-regression-audit-v1.json').open('x') as f:json.dump(dict(scope='final private conditional, not a whole End-turn match or fresh game',
 original_geo_model_equal=True,eligible=eligible,direct=direct,waypoint=list(choice['point']),selected_target=24,score=828,distance=28,
 original_endpoint=[212,96],moves_after=0,owner_hashes_or_full_states_published=False),f,indent=2)
print('PASS final private conditional: eligibility, scores, selected target, waypoint and wrapper endpoint; no private hashes emitted')
