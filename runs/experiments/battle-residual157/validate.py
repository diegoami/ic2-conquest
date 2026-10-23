"""Strict seed2 recorder gate and source-identity checks; never rebaseline."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
ART=ROOT/'artifacts/run-exp-battle-residual157'
RUN=ROOT/'runs/experiments/data/run-exp-battle-parity157/seed2-residual-v1'
GAME=ROOT/'artifacts/run-exp-battle-parity157/public/seed2-residual-v1/runtime/prefix/drive_c/IC2'
REF=ART/'fixtures-v1/battles'
result=json.loads((RUN/'result.json').read_text())
hook=json.loads((RUN/'hook-after-writeback.json').read_text())
ctl=hook['control']
assert result['complete'] and result['reopen_save']['byte_equal']
assert ctl['magic_ok'] and not any(ctl[k] for k in ['overflow','reentered','busy','truncated_reader'])
assert not hook['chain_breaks'] and not hook['result_misses']
fields=['site','eax','seed_before','seed_after','result','counter','side','flag']
with (REF/'hook/hooklog-mix-rg_s2_r5_hook.csv').open() as f:
    baseline=[{k:int(r[k],0) for k in fields} for r in csv.DictReader(f) if r['kind']=='random']
fresh=[{k:r[k] for k in fields} for r in hook['records'] if r['kind']=='random']
saves=[]
for i in range(1,19):
    a=(REF/f'hook/mix-rg_s2_r5_hook_BATTLE{i:02d}.SAV').read_bytes()
    b=(GAME/f'BATTLE{i:02d}.SAV').read_bytes()
    saves.append(dict(counter=i,byte_equal=a==b,baseline_sha256=hashlib.sha256(a).hexdigest(),fresh_sha256=hashlib.sha256(b).hexdigest()))
report=dict(original_draws=len(baseline),fresh_draws=len(fresh),draws_equal=baseline==fresh,
            first_draw_difference=next((dict(index=i,baseline=a,fresh=b) for i,(a,b) in enumerate(zip(baseline,fresh)) if a!=b),None),
            boundary_saves=saves,save_reopen_byte_equal=result['reopen_save']['byte_equal'],
            recorder_clean=True,scope='Fresh expanded observer on immutable seed2 original trajectory; all draw tuples and whole18SAVs required.')
report['pass']=report['draws_equal'] and all(s['byte_equal'] for s in saves)
with (DATA/'original-gate-v1.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print('Original gate',report['pass'],len(baseline),'draws',sum(s['byte_equal'] for s in saves),'/18 whole saves')
assert report['pass'],'Do not use a non-identical fresh trace for attribution'
