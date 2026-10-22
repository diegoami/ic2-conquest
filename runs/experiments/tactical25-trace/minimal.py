"""Keep the smallest shared-input goal/claims witness without altering full captures."""
import argparse,hashlib,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--attribution',type=Path,required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace';rec=json.loads(a.attribution.read_text());assert rec['first_observed_goal_difference']['shared_input']
states=json.loads((DATA/'states-20261016-191329-1302174.json').read_text())['records'];phases=DATA/rec['model_phases'];model=json.loads((phases/'mix-rg_s1_r5_hook-hr6.json').read_text());unit=next(x for x in model['stages'][2]['units'] if x['slot']==22)
proof=dict(attribution=a.attribution.name,attribution_sha256=hashlib.sha256(a.attribution.read_bytes()).hexdigest(),provenance='NEW Wine seq125/126 observed input/goal; seq127 next actor input shows post-Walk result; model state/log validated against unchanged production',wine=[x for x in states if x['seq'] in [125,126,127]],model_unit=unit,model_previous_stages=model['stages'][:2],first_goal=rec['first_observed_goal_difference'],threat_comparison=next(x for x in rec['threats'] if x['counter']==6 and x['actor']==22))
out=DATA/('minimal-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print(out)
