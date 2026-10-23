"""Keep the refused city overlap; add the intended valid sea compaction case."""
import copy,json
from offline import ART,HERE,convert,entries
doc=json.loads((ART/'native-v1/F55-compact-before-carrier.json').read_text())
name='F56-compact-sea-before-carrier';doc['save'].update(id=name,label=name)
doc['save']['state']['fleets'][0].update(x=101,y=47,coveredTileCode=0)
record=copy.deepcopy(next(x for x in entries() if x['name']=='F55-compact-before-carrier'))
record.update(name=name,provenance='synthetic reverse-array cargo compaction: empty fleet moved to SEA101,47 adjacent Antium102,46; original city-tile overlap retained as refused F55')
with (ART/'native-v1'/(name+'.json')).open('x') as f:json.dump(doc,f)
with (ART/'native-v1/manifest.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
convert(record)
with (HERE/'lineage-F55-disposition-v1.json').open('x') as f:
 json.dump(dict(case='F55-compact-before-carrier',disposition='converter refusal, original not executed',
  evidence='export-F55-compact-before-carrier-v1.json: exit2 POLICY_VIOLATION city[89]:city_marker; no output',
  cause='Synthetic fleet placed on Antium city tile; strict city-marker policy refuses that overlay',
  original_acceptance='UNTESTED; do not assert native validity implies original support',
  replacement_control=name,orchestration_error='Original runner tried missing input after failed asynchronous export; FileNotFound record retained; no original process started for F55'),f,indent=2)
