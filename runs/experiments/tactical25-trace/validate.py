"""Compare a fresh run to immutable legacy draws/full SAV bytes; report failures, never rebaseline."""
import argparse,csv,hashlib,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace';ART=ROOT/'artifacts/run-exp-tactical25-trace'
rows=[json.loads(s) for s in a.run.read_text().splitlines()];hook=next(x for x in rows if x['event']=='hook');saves=next(x for x in rows if x['event']=='saves')['files'];oldlog=a.fixtures/'battles/hook/hooklog-mix-rg_s1_r5_hook.csv';newlog=DATA/hook['file']
def read(p):return list(csv.DictReader(p.open()))
old=[x for x in read(oldlog) if x['kind']=='random'];new=[x for x in read(newlog) if x['kind']=='random'];fields=['site','eax','seed_before','seed_after','result','counter','side','flag']
def integers(row):return tuple(int(row[k],0) for k in fields)
first=next((dict(index=i,original=o,new=n) for i,(o,n) in enumerate(zip(old,new)) if integers(o)!=integers(n)),None)
pairs=[]
for f in saves:
 name=f['name'].split('-')[-1];baseline=a.fixtures/'battles/hook'/('mix-rg_s1_r5_hook_'+name);fresh=ART/f['name'];ob=baseline.read_bytes();nb=fresh.read_bytes()
 pairs.append(dict(save=name,baseline_sha256=hashlib.sha256(ob).hexdigest(),fresh_name=f['name'],fresh_sha256=hashlib.sha256(nb).hexdigest(),byte_equal=ob==nb,first_byte_difference=next((i for i,(x,y) in enumerate(zip(ob,nb)) if x!=y),None)))
rec=dict(run=a.run.name,legacy_log_sha256=hashlib.sha256(oldlog.read_bytes()).hexdigest(),new_log_sha256=hashlib.sha256(newlog.read_bytes()).hexdigest(),draw_fields=fields,legacy_draws=len(old),new_draws=len(new),first_draw_difference=first,draws_equal=first is None and len(old)==len(new),legacy_expected_saves=15,saves=pairs,control_ok=hook['control']['magic_ok'] and not any(hook['control'][k] for k in ['overflow','reentered','busy','truncated_reader']),chain_breaks=hook['chain_breaks'],result_misses=hook['result_misses'])
rec['pass']=rec['draws_equal'] and len(pairs)==15 and all(x['byte_equal'] for x in pairs) and rec['control_ok'] and not rec['chain_breaks'] and not rec['result_misses']
out=DATA/('validation-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out,rec['pass']);raise SystemExit(0 if rec['pass'] else 1)
