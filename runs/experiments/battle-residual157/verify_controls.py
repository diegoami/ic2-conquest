"""Replay recorded original inputs on the actual patched production assembly.

No new original game runs. New outputs only; owner traces/hashes stay private.
Preserve all measurements, including failures. Never delete or overwrite saves.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157/control-replay-v1'
DATA.mkdir(exist_ok=False)
ART=ROOT/'artifacts/run-exp-battle-residual157'
OLD_DATA=ROOT/'runs/experiments/data/run-exp-battle-parity157'
OLD_ART=ROOT/'artifacts/run-exp-battle-parity157'
DLL=ART/'replay-cached-live-v1/Replay.dll'
sys.path.insert(0,str(ROOT/'runs/experiments/battle-parity157'))
from audit_owner import BB,compare

def read(path):return json.loads(path.read_text())
rows=[]
cases=[(c['label'],OLD_DATA/c['label'],OLD_ART/'public'/c['label'],False) for c in read(OLD_DATA/'pilot-manifest-v1.json')['cases']]
cases.append(('reference',OLD_DATA/'reference-semantic-v1',OLD_ART/'public/reference-semantic-v1',False))
cases.append(('owner',OLD_ART/'private/owner-seed1-semantic-v1',OLD_ART/'private/owner-seed1-semantic-v1',True))
for label,source,original_art,private in cases:
    out=(ART/'private'/label if private else DATA/label)
    out.mkdir(parents=True,exist_ok=False)
    original=read(source/'result.json')
    assert original['complete'] and original['reopen_save']['byte_equal']
    args=['/home/diego/.dotnet/dotnet',str(DLL),str(source/'result.json'),'/home/diego/projects/imperial_conquest_2',str(out/'replay-v1.json')]
    r=subprocess.run(args,capture_output=True,text=True)
    with (out/'execution-v1.json').open('x') as f:json.dump(dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2);f.write('\n')
    if r.returncode:raise RuntimeError(label+' replay failed; inspect retained receipt')
    native=read(out/'replay-v1.json')['fullBattles'][0]
    import struct
    raw=bytes.fromhex(original['terminal_slots_hex'])
    terminal=dict(slots=[BB.parse_slot(raw[i*44:(i+1)*44],i) for i in range(40)],grid=list(struct.unpack_from('<168h',raw,1760)))
    hook=read(source/'hook-after-writeback.json')
    assert not hook['chain_breaks'] and not hook['result_misses']
    draws=[e for e in hook['records'] if e['kind']=='random' and e['site'] not in [0x4592bd,0x45951c]]
    begin=next(i for i,e in enumerate(draws) if e['seed_before']==original['entry_seed'])
    draws=draws[begin:]
    modeled=[(e['data']['Bound'],e['data']['Value']) for e in native['events'] if e['type']=='TacticalDrawEvent']
    game=original_art/'runtime/prefix/drive_c/IC2'
    boundaries=[]
    for path in sorted(game.glob('BATTLE*.SAV')):
        counter=int(path.stem[6:])
        if counter<original['entry']['half_round']:continue
        phases=[p for p in native['phases'] if p['Counter']==counter]
        boundaries.append(dict(counter=counter,differences=compare(phases[0],BB.block_of_save(path.read_bytes())) if len(phases)==1 else None))
    row=dict(label=label,original_draws=len(draws),native_draws=len(modeled),draws_equal=[(e['eax'],e['result']) for e in draws]==modeled,
             counter_equal=original['terminal_counter']==native['Counter'],terminal_rng_equal=original['terminal_seed']==native['RandSeed'],
             terminal_differences=compare(native,terminal),boundaries=boundaries,
             selected_provided='entry_selected' in original,controller='Actual compiled ComputerGeneral',private_trace=private)
    row['pass']=row['draws_equal'] and row['counter_equal'] and row['terminal_rng_equal'] and row['terminal_differences']==0 and all(b['differences']==0 for b in boundaries)
    if (source/'semantic-actions-v1.jsonl').exists():
        args=[sys.executable,str(ROOT/'runs/experiments/battle-parity157/compare_semantic.py'),'--original',str(source),'--native',str(out/'replay-v1.json'),'--output',str(out/'semantic-comparison-v1.json')]
        r=subprocess.run(args,capture_output=True,text=True)
        with (out/'semantic-execution-v1.json').open('x') as f:json.dump(dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2);f.write('\n')
        assert r.returncode==0
        semantic=read(out/'semantic-comparison-v1.json')['variants'][0]
        row['semantic_actions_equal']=semantic['all_equal']
        row['semantic_counts']={c['kind']:c['original_count'] for c in semantic['checks']}
        row['pass'] &= semantic['all_equal']
    rows.append(row)
    with (DATA/(label+'-audit-v1.json')).open('x') as f:json.dump(row,f,indent=2);f.write('\n')
    print(label,row['pass'],len(draws),'draws',len(boundaries),'boundaries',flush=True)
    assert row['pass'],label+' differs; no silent tolerance or rebaseline'

# Historical data is an explicit assumption control, never promoted to observation.
source=OLD_ART/'private/historical-entry-assumption-control-v1'
out=ART/'private/historical';out.mkdir(parents=True,exist_ok=False)
r=subprocess.run(['/home/diego/.dotnet/dotnet',str(DLL),str(source/'entry-assumptions.json'),'/home/diego/projects/imperial_conquest_2',str(out/'replay-v1.json')],capture_output=True,text=True)
with (out/'execution-v1.json').open('x') as f:json.dump(dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),f,indent=2)
assert r.returncode==0
h=read(out/'replay-v1.json')['fullBattles'][0]
assert h['Counter']==21 and h['troops']==[48969,0]
report=dict(all_passed=all(r['pass'] for r in rows),cases=rows,
            historical=dict(counter=h['Counter'],troops=h['troops'],assumptions_retained=True,exact_historical_event_equality_not_claimed=True),
            engine_sha256=hashlib.sha256((DLL.parent/'IC2.Engine.dll').read_bytes()).hexdigest(),
            scope='Recorded original tactical entries on actual compiled source correction; no diagnostic controller or new Wine run. Full318 corpus and native Windows not run.')
with (DATA/'verification-v1.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print('All recorded controls passed; historical survivor/counter recovered',flush=True)
