"""Validate authoritative logs against immutable saves and write bounded tables.

Explicit input selections keep superseded exploratory runs separate. No source
evidence is changed, and output files use exclusive creation with a fresh stamp.
"""
import collections
import hashlib
import json
import re
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from state import sav,battle_block as BB,hook_log
DATA=Path(__file__).resolve().parent
ART=ROOT/'artifacts/run-exp-ai-oct16'
STAMP=time.strftime('%Y%m%d-%H%M%S')
SUPPLY=['probe-20261016-145017-521550.jsonl','probe-20261016-145549-528200.jsonl','probe-20261016-150546-540049.jsonl']
REGION=['probe-20261016-150204-535849.jsonl','probe-20261016-151025-546199.jsonl']
GENERAL=['probe-20261016-150636-540904.jsonl','probe-20261016-150939-545243.jsonl','probe-20261016-152304-549608.jsonl']


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def events(names):
    for name in names:
        for line_number,line in enumerate((DATA/name).read_text().splitlines(),1):
            r=json.loads(line)
            yield name,line_number,r


def verify_save(name):
    path=ART/name
    assert path.is_file(),name
    return sav.load(path)


def verify_post(r):
    parsed=verify_save(r['post'])
    snapshot=r['snapshot']
    assert parsed['turn']==snapshot['turn'] and parsed['current_nation']==snapshot['current']
    # GUI view fields may differ; rule-bearing subject fields must match exactly.
    for field in ('x','y','owner','moves','cell','supplies','money','morale','troops','units'):
        assert parsed['armies'][0][field]==snapshot['armies'][0][field],(r.get('case'),field)
    for field in ('x','y','owner','moves','supplies','money','ships','condition','army'):
        assert parsed['fleets'][2][field]==snapshot['fleets'][2][field],(r.get('case'),field)
    assert parsed['cities'][89]['supplies']==snapshot['cities'][89]['supplies']
    assert parsed['nations'][0]['treasury']==snapshot['nations'][0]['treasury']


hashes={}
for line in (DATA/'SAVES.sha256').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert name not in hashes or hashes[name]==digest,('conflicting hash',name)
    hashes[name]=digest
for name,digest in hashes.items():assert sha(ART/name)==digest,('bad artifact hash',name)

supply=[];before={}
for source,line,r in events(SUPPLY):
    if r['event']=='before':before[(source,r['case'])]=r
    if r['event']!='after':continue
    verify_post(r)
    initial=before[(source,r['case'])]['snapshot'];final=r['snapshot']
    assert initial['turn']==final['turn']==734 and initial['current']==13 and final['current']==11
    row=dict(case=r['case'],log=source,line=line,input=r['input'],autosave=r['autosave'],post=r['post'],
             turn=734,city_stock=[initial['cities'][89]['supplies'],final['cities'][89]['supplies']],
             treasury=[initial['nations'][0]['treasury'],final['nations'][0]['treasury']],
             army={key:[initial['armies'][0][key],final['armies'][0][key]] for key in ('x','y','cell','supplies','money','troops')},
             fleet={key:[initial['fleets'][2][key],final['fleets'][2][key]] for key in ('x','y','supplies','money','condition','army','ships')},
             city_changes=r['deltas']['cities_changed'])
    supply.append(row)
assert len(supply)==28

regions=[]
for source,line,r in events(REGION):
    if r['event']!='region_after':continue
    verify_post(r)
    regions.append(dict(case=r['case'],mode=r['mode'],log=source,line=line,input=r['input'],post=r['post'],
                        turn=r['snapshot']['turn'],scores=r['scores'],
                        final_army=r['snapshot']['armies'][0],seed=r['snapshot']['seed']))
region_comparisons=[]
for case in sorted({r['case'] for r in regions}):
    p,o=[next(r for r in regions if r['case']==case and r['mode']==mode) for mode in ('plain','observed')]
    assert p['input']==o['input'] and p['seed']==o['seed'] and p['final_army']==o['final_army']
    equal=(ART/p['post']).read_bytes()==(ART/o['post']).read_bytes()
    assert equal,(case,'plain/observer save bytes differ')
    score=next(s for s in o['scores'] if s['site']=='army_score' and s['army']==0)
    region_comparisons.append(dict(case=case,input=p['input'],plain_post=p['post'],observed_post=o['post'],
                                   post_byte_identical=equal,score=score,log=o['log'],line=o['line']))
assert len(region_comparisons)==7

states=[];traces=[];boundaries=[]
for source,line,r in events(GENERAL):
    if r['event']=='general_state':
        b=r['battle']
        live=[] if b is None else [s for s in b['slots'] if s['alive']]
        states.append(dict(mode=r['mode'],label=r['label'],log=source,line=line,flags=r['flags'],
                           counter=None if b is None else b['half_round'],side=None if b is None else b['x2'],
                           phase=None if b is None else b['y1'],seed=r['seed'],
                           active_slots=[dict(slot=s['slot'],type=s['type'],x=s['x'],y=s['y'],moves=s['state'],target=s['target'])
                                         for s in live if (s['slot']<20)==(b['x2']==0)] if b else []))
    if r['event']=='general_boundary':
        path=ART/r['file'];assert sha(path)==r['sha256']
        b=BB.block_of_save(path.read_bytes());assert b==r['battle']
        boundaries.append(dict(mode=r['mode'],log=source,line=line,file=r['file'],sha256=r['sha256'],
                               counter=b['half_round'],side=b['x2'],phase=b['y1'],
                               slots=[dict(slot=s['slot'],type=s['type'],x=s['x'],y=s['y'],moves=s['state'],target=s['target'])
                                      for s in b['slots'] if s['alive']]))
    if r['event']=='general_trace':
        recs=r['records'];assert not hook_log.result_check(recs)
        # A lab StartBattle/Resume deliberately reseeds. Validate each segment;
        # retain the raw cross-start diagnostics rather than treating it as a draw.
        chunks=[];chunk=[]
        for event in recs:
            if event['kind']=='start' and chunk:chunks.append(chunk);chunk=[]
            chunk.append(event)
        if chunk:chunks.append(chunk)
        breaks=[]
        for chunk in chunks:
            # Sequence validation uses absolute record indices, already parsed
            # into seq_ok by hook_log; splitting does not renumber evidence.
            breaks+=hook_log.chain_check(chunk)
        assert not breaks,(r['mode'],breaks)
        control=r['control'];assert control['magic_ok'] and not control['overflow'] and not control['reentered']
        setups=[dict(counter=e['counter'],side=e['side'],flags=[(e['reserved']>>(8*k))&255 for k in range(4)],seed=e['seed_before'])
                for e in recs if e['kind']=='marker' and e['site']==0x439968]
        traces.append(dict(mode=r['mode'],log=source,line=line,records=len(recs),
                           draws=sum(e['kind']=='random' for e in recs),segments=len(chunks),
                           within_segment_chain_breaks=breaks,raw_cross_start_diagnostics=r['chain_breaks'],setups=setups))

plain=[r for r in boundaries if r['mode']=='plain_off']
observed=[r for r in boundaries if r['mode']=='human_off']
assert len(plain)==len(observed)==1 and plain[0]['sha256']==observed[0]['sha256']

result=dict(supply=supply,region=region_comparisons,general_states=states,general_traces=traces,
            general_boundaries=boundaries,plain_general_boundary_byte_identical=True,
            verified_artifact_hashes=len(hashes),authoritative_logs=dict(supply=SUPPLY,region=REGION,general=GENERAL))
out=DATA/f'observations-{STAMP}.json'
with out.open('x') as f:json.dump(result,f,indent=2)
table=DATA/f'observations-{STAMP}.md'
with table.open('x') as f:
    f.write('# Verified observation tables\n\nGenerated by `summarize.py` from the explicit authoritative logs; raw inputs remain unchanged.\n\n')
    f.write('| Case | Army supply | Fleet supply | Fleet money | Condition | City stock | Treasury | Post save |\n|---|---|---|---|---|---|---|---|\n')
    for r in supply:
        fmt=lambda pair:' → '.join(map(str,pair))
        f.write('| '+ ' | '.join([r['case'],fmt(r['army']['supplies']),fmt(r['fleet']['supplies']),fmt(r['fleet']['money']),fmt(r['fleet']['condition']),fmt(r['city_stock']),fmt(r['treasury']),f"`{r['post']}`"])+ ' |\n')
    f.write('\n| Region control | Selected army | Score | Distance | Plain/observer post saves identical |\n|---|---|---|---|---|\n')
    for r in region_comparisons:
        s=r['score'];f.write(f"| {r['case']} | {s['target']} | {s['score']} | {s['distance']} | yes |\n")
    f.write('\n| General mode | State | Flags A/D/end/interrupt | Counter | Side | Phase | First active slot moves |\n|---|---|---|---|---|---|---|\n')
    for r in states:
        f.write(f"| {r['mode']} | {r['label']} | {r['flags']} | {r['counter']} | {r['side']} | {r['phase']} | {[(s['type'],s['moves']) for s in r['active_slots'][:4]]} |\n")
print(json.dumps(dict(output=out.name,table=table.name,supply_cases=len(supply),region_pairs=len(region_comparisons),general_boundaries=len(boundaries),hashes=len(hashes))))
