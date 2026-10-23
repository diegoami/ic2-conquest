"""Resume retained matrix after reviewing every first-pass failure.

No completed case is rerun. Reviewed driver failures get distinct v2 files;
LI4800 becomes an explicit original-refusal control, not a success claim.
"""
import copy,json
import live

reviewed={
 'F04-unit-split':'Original R41 refuses LI4800 below6000; known findings/g2. Retest as refusal, preserve v1 wrong-expectation result.',
 'F07-army-supply':'Outdated fixed OK coordinates. Control diagnostic-v2 proves actual OK control closes the dialog.',
 'F08-army-money':'Same outdated supply dialog coordinates; actual spinner and OK geometry now derived from controls.',
 'F21-fleet-split':'Session checkpoint interrupted before any saved/game order; restart only this case with a new attempt name.',
}
for n,label in [(11,'recruit-li'),(12,'recruit-hi'),(13,'recruit-ar'),(14,'recruit-lc'),(15,'recruit-hc'),(16,'mobilize-quality4'),(17,'recruit-disband'),(18,'recruit-cap40')]:
 reviewed[f'F{n:02d}-{label}']='ANSI list-caption helper returned only first UTF16 character. Retained diagnostic; Unicode helper now verifies full ROME caption.'
with (live.HERE/'reviewed-recovery-plan-v1.json').open('x') as f:
 json.dump({'reviewed_failures':reviewed,'diagnostic':'control-diagnostic-v2.json',
            'unexecuted_relation_controls':'F42/F43 correctly expected to refuse based on native predicate and original R41/peace research; positive controls F52/F53 separate.'},f,indent=2)
cases=[json.loads(l) for l in (live.ART/'native-v1/manifest.jsonl').read_text().splitlines()]
priority={'feature':0,'migration':1,'progressed':2,'nation-start':3}
try:
 for index,source in sorted(enumerate(cases),key=lambda p:(priority[p[1]['category']],p[0])):
  name=source['name'];old=live.HERE/f'live-{name}-v1.json'
  attempt='v1'
  if old.exists():
   result=json.loads(old.read_text())
   if result['complete']:continue
   if name not in reviewed:
    print('Unreviewed failure preserved, no retry:',name,flush=True);continue
   attempt='v2'
  case=copy.deepcopy(source)
  if name in ('F04-unit-split','F42-alliance','F43-peace'):case['originalAction']['expect_unchanged']=True
  print('RESUME',name,attempt,case['originalAction']['kind'],flush=True)
  live.run_case(case,index,attempt)
finally:
 if live.display is not None:live.display.terminate();live.display.wait(timeout=10)
