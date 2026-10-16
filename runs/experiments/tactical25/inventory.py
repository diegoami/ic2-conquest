"""Generate a new, fully linked residual inventory from immutable captures."""
import datetime,json,sys
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument("--fixtures",type=Path,required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state.sav import load
R=ROOT/'runs/experiments/data/run-exp-tactical25';P=R/'production-20261016-174818';PH=R/'phases-20261016-180932'
summary=json.loads((P/'summary.json').read_text());registry=json.loads((R/'correction-6208282/strict-registry-after.json').read_text());old=json.loads((R/'registry-t129-9664936e.json').read_text());local=json.loads((R/'original-threat-20261016-180959.json').read_text())
rows=[]
for row in summary['rows']:
 if row['exact']:continue
 name=row['trial'];phase=json.loads((PH/(name+'.json')).read_text());ctx=json.loads((P/(name+'-context.json')).read_text());drawphase=json.loads((R/'phases-20261016-180904'/(name+'.json')).read_text());fd=row['first_divergence'];obs=None
 model_pass=None;model_claims=None
 if fd:
  if fd['model_actor']['pass'].startswith('melee'):
   model_pass='melee after movement';model_claims=ctx['model_snapshot_after_movement']['claim_counts']
  else:
   # All pre-movement draws have null snapshots and precede the tagged general calls.
   enddraws=sum(d['before'] is None for d in drawphase['draws'])
   prefix=sum(e['kind']=='draw' for e in drawphase['initial']['log'])-enddraws
   n=fd['draw_index']-prefix
   obs=drawphase['draws'][n];assert obs['bound']==fd['model']['bound'] and obs['value']==fd['model']['value']
   model_pass=obs['stage'];model_claims=obs['before']['state']['claims']
 pass2local=[r for r in local['pass_two'] if r['trial']==name and r.get('differences')]
 first_state_counter=phase['counter'];difflocal=[r for r in local['rows'] if r['trial']==name and r['aim_differs']]
 bucket='local-threat-key/order discrepancy; whole-trial attribution open' if difflocal else 'unexplained whole-trial first divergence'
 if pass2local:bucket='local weighted pass2 discrepancy; whole-trial attribution open'
 if name.startswith('ar-hi-three') and difflocal:bucket='local exhausted-archer threat-box radius discrepancy; whole-trial attribution open'
 def cases(reg):return [x['Case'] for x in reg if x['Case'].endswith(':'+name) or x['FirstDifference'].startswith(name+':')]
 rows.append(dict(trial=name,turn=load(a.fixtures/'battles'/row['start'])['turn'],start=row['start'],first_state_counter=first_state_counter,first_state_difference=row['block_difference'],first_draw=fd,model_general_pass=model_pass,model_claims_at_first_draw=model_claims,original_runtime_claims=None,original_claims_status='Not recorded in legacy hooks or SAV; local x86 probes do not recover original runtime state',local_probe_discrepancies=difflocal,local_pass2_discrepancies=pass2local,cause_status=bucket,current_registry_cases=cases(registry),historical_registry_cases=cases(old)))
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S');out=R/('inventory-'+stamp+'.json')
with out.open('x') as f:json.dump(dict(production=P.name,phases=PH.name,local_probe='original-threat-20261016-180959.json',rows=rows),f,indent=2);f.write('\n')
md=['| Trial (all `_r5_hook`) | First state HR | First draw index; HR original/port; site | Original → port range=result | Actor→target original / port | Local probe status |','|---|---:|---|---|---|---|']
for r in rows:
 d=r['first_draw'];ix='none (state only)' if d is None else f"{d['draw_index']}; {d['original']['counter']}/{d['model']['counter']}; {d['source_site']}"
 rr='identical draw sequence' if d is None else f"{d['original']['eax']}={d['original']['result']} → {d['model']['bound']}={d['model']['value']}"
 aa='—' if d is None else f"{d['original_actor']['unit']}→{d['original_actor']['target']} / {d['model_actor']['unit']}→{d['model_actor']['target']}"
 status='pass2 + threat' if r['local_pass2_discrepancies'] and r['local_probe_discrepancies'] else 'pass2' if r['local_pass2_discrepancies'] else 'radius' if r['cause_status'].startswith('local exhausted') else 'threat key/order' if r['local_probe_discrepancies'] else 'open'
 md.append(f"| {r['trial'].replace('_r5_hook','')} | {r['first_state_counter']} | {ix} | {rr} | {aa} | {status} |")
with (R/('inventory-'+stamp+'.md')).open('x') as f:f.write('\n'.join(md)+'\n')
print(out)
