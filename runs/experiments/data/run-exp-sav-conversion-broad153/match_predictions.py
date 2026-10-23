"""Match GUI-selected quantities/ports, retaining the original predictions.

The original recruit helper increments from the dialog's per-type default;
its argument is not an absolute troop request. The build-fleet GUI chooses its
own port. These companion native commands align those actual inputs.
"""
import json
from offline import ART,HERE,ROOT,DOTNET,PROBE,REMAKE,run,entries
from compare import prior

world=json.loads((REMAKE/'data/worlds/classical-mediterranean.json').read_text())
plans={r['name']:r for r in entries()}
chosen={}
for p in sorted(HERE.glob('live-*-v*.json')):
 r=json.loads(p.read_text())
 if r['complete']:chosen[r['name']]=r
for name,live in chosen.items():
 case=plans[name];kind=case['originalAction']['kind']
 if kind not in ('recruit','build-fleet') or case['originalAction'].get('expect_unchanged'):continue
 receipt=HERE/f'predict-matched-{name}-v1.json'
 if receipt.exists():continue
 before=prior.sav.load(ART/live['files']['immediate']['file']);after=prior.sav.load(ART/live['files']['order']['file'])
 if kind=='recruit':
  me=before['current_nation'];old=before['nations'][me]['recruit_slots'];new=after['nations'][me]['recruit_slots']
  if len(new)!=len(old)+1:continue
  slot=new[-1];types={'li':'light_infantry','hi':'heavy_infantry','ar':'archers','lc':'light_cavalry','hc':'heavy_cavalry'}
  city=world['cities'][slot['city']]['id'];command=f"recruit-standing {city} {types[slot['type']]} {slot['troops']}"
  evidence=dict(original_requested_increment=case['originalAction'],observed_new_slot=slot)
 else:
  if len(after['fleets'])!=len(before['fleets'])+1:continue
  f=after['fleets'][-1];city=world['cities'][f['build_city']]['id'];command=f"order-fleet {city} {f['ships']} broad-built"
  evidence=dict(original_gui_selected_city=city,observed_fleet=f)
 if command==case['remakeCommand']:continue
 source=ART/'exports-v1'/(name+'-imported.json');out=ART/'exports-v1'/(name+'-matched-predicted.json')
 result=run(f'predict-matched-{name}-v1',[DOTNET,PROBE,'action',REMAKE,source,out,command])
 with (HERE/f'prediction-input-alignment-{name}-v1.json').open('x') as f:
  json.dump(dict(case=name,original_prediction=case['remakeCommand'],matched_prediction=command,
      reason='Compare the same GUI-selected quantity/port, not a different native order',evidence=evidence,returncode=result.returncode),f,indent=2)
