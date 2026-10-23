"""Two explicit native-array permutation/cargo-index controls, no SAV patching."""
import copy,json
from offline import ART,HERE,REMAKE,convert
base=json.loads((ART/'native-v1/F28-disembark.json').read_text())
plans=[json.loads(l) for l in (ART/'native-v1/manifest.jsonl').read_text().splitlines()]
source=next(p for p in plans if p['name']=='F28-disembark')
world=json.loads((REMAKE/'data/worlds/classical-mediterranean.json').read_text())
antium=next(c for c in world['cities'] if c['id']=='antium')
for which in (54,55):
 doc=copy.deepcopy(base);s=doc['save']['state'];s['armies'].reverse();s['fleets'].reverse()
 cargo=next(i for i,a in enumerate(s['armies']) if a['aboardFleetId'] is not None)
 carrier=next(i for i,f in enumerate(s['fleets']) if f['carriedArmyId'] is not None)
 record=copy.deepcopy(source)
 if which==54:
  name='F54-reordered-cargo';record['originalAction']=dict(kind='disembark',army=cargo,fleet=carrier,x=101,y=45)
  record['remakeCommand']=f'disembark-army army-{cargo} 101 45'
  origin='synthetic native army/fleet arrays reversed, stable native IDs unchanged; cargo pointer must use last army/new carrier ordinal'
 else:
  empty=next(i for i,f in enumerate(s['fleets']) if f['carriedArmyId'] is None)
  f=s['fleets'][empty];f.update(nation='rome',x=antium['x'],y=antium['y'],ships=30,conditionPercent=90,constructionTicksRemaining=None,buildCityId=None,moves=25)
  name='F55-compact-before-carrier';record['originalAction']=dict(kind='scuttle',fleet=empty)
  record['remakeCommand']=f'scuttle-fleet fleet-{empty}'
  origin='synthetic reversed native arrays, empty fleet before the cargo carrier staged at own port; scuttle tests index compaction with live cargo'
 doc['save'].update(id=name,label=name)
 path=ART/'native-v1'/(name+'.json')
 with path.open('x') as f:json.dump(doc,f)
 record.update(name=name,category='feature',provenance=origin)
 with (ART/'native-v1/manifest.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 convert(record)
