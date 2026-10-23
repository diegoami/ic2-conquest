"""Audit frozen final evidence, never regenerate a game/save or waive a failure."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from offline import HERE,ART,entries
from compare import native,prior

rows=json.loads((HERE/sys.argv[1]).read_text());assert len(rows)==78
groups=Counter(r['case']['category'] for r in rows)
assert groups=={'nation-start':16,'progressed':4,'feature':57,'migration':1},groups
assert len({r['case']['nation'] for r in rows if r['case']['category']=='nation-start'})==16
checks=[];hash_checks=0;unique_sources=set();ui_changes={};mismatches={};random_cases=[]
for row in rows:
 name=row['case']['name']
 if name=='F55-compact-before-carrier':
  refused=json.loads((HERE/'export-F55-compact-before-carrier-v1.json').read_text())
  assert refused['returncode']==2 and 'POLICY_VIOLATION' in refused['stderr'] and 'city_marker' in refused['stderr']
  assert not (ART/'exports-v1'/(name+'.SAV')).exists()
  continue
 assert row['export_success'] and row['policy_pass'] and row['import_success'],name
 assert row['original']['complete'] and row['original']['action_verified'],(name,row['original'])
 assert row['original']['reopen_byte_equal'],name
 assert row['return_success'] and row['return_reexport_success'] and row['return_policy_pass'],name
 continuation=row['return_continuation'];assert continuation['returncode']==0,name
 payload=continuation['payload'];assert payload and payload['changed'],name
 assert not any('rejected (' in line for line in payload['Lines']),(name,payload['Lines'])
 source=ART/'exports-v1'/(name+'.SAV');raw=source.read_bytes();unique_sources.add(hashlib.sha256(raw).hexdigest())
 # Full raw original immediate-save differences may change only UI geometry,
 # view/filter/delay/hint preferences. No ignored gameplay-byte region.
 state=prior.sav.load(source);base=100956+2+656*len(state['armies'])+2+26*len(state['fleets'])
 allowed=set(range(state['tail_off']+46,state['tail_off']+54))
 for n in range(16):allowed.update(range(base+1172*n+0x46E,base+1172*n+0x490))
 comp=row['original_comparisons']['export_immediate']
 assert comp['lengths'][0]==comp['lengths'][1],name
 assert set(comp['differing_offsets'])<=allowed,(name,comp['differing_offsets'])
 assert comp['semantic_differences']==[],(name,comp['semantic_differences'][:5])
 ui_changes[name]=len(comp['differing_offsets'])
 for kind,entry in row['original_files'].items():
  path=ART/entry['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],str(path);hash_checks+=1
 if row.get('action_differential_random'):random_cases.append(name)
 else:
  diff=row.get('input_aligned_differential_differences',row.get('action_differential_differences'))
  assert diff is not None,name
  if diff:mismatches[name]=diff
 # Canonical IDs must remain unambiguous in the chosen comparator.
 for file in [ART/'native-v1'/(name+'.json'),ART/'exports-v1'/(name+'-imported.json')]:
  s,_=native(file)
  for key in ('armies','fleets'):assert len({x['id'] for x in s[key]})==len(s[key]),(name,key)
checks.append('77 case inputs export/check/import; 16 nations represented; all planned categories present')
checks.append('Every selected original case verifies its action/refusal and byte-identical fresh reopen')
checks.append('Every original immediate save differs only in explicitly bounded UI byte regions, no parsed gameplay change')
checks.append('Every selected original result returns/resumes/orders/reexports with policy pass')
negative=json.loads((HERE/'negative-summary-v1.json').read_text());assert len(negative)==11
for row in negative:
 assert row['returncode']==2,row
 assert not row.get('output_written',False),row
 assert row.get('input_unchanged',True),row
assert 'OPEN_BATTLE' in next(r for r in negative if r['name']=='N09-open-battle')['stderr']
checks.append('11 converter/input refusal controls refuse safely; actual saved tactical battle reaches OPEN_BATTLE refusal')
archives=[]
for file in sorted(HERE.glob('batch-*-manifest.json')):
 m=json.loads(file.read_text());assert hashlib.sha256((ART/m['archive']).read_bytes()).hexdigest()==m['sha256']
 for item in m['files']:
  path=ART/item['file'];assert path.stat().st_size==item['bytes'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'];hash_checks+=1
 archives.append(dict(archive=m['archive'],files=len(m['files']),sha256=m['sha256']))
checks.append('All selected artifact hashes and all retained archive/member hashes match')
conq=next(r for r in rows if r['case']['name']=='F36-eliminated-conqueror')
assert any(d['path']=='/nations/14/conqueredBy' and d['before']=='rome' and d['after'] is None for d in conq['source_import_differences'])
checks.append('Known conqueredBy importer loss reproduced explicitly, never counted as full-fidelity equality')
accepted_groups=dict(groups);accepted_groups['feature']-=1
out=dict(passed=True,checks=checks,cases=len(rows)-1,planned_inputs=len(rows),additional_refused_case='F55-compact-before-carrier',
 total_refusal_controls=len(negative)+1,categories=accepted_groups,planned_categories=dict(groups),distinct_exported_SAV_hashes=len(unique_sources),
 artifact_hash_checks=hash_checks,archives=archives,immediate_ui_changed_bytes=ui_changes,
 deterministic_action_differences=mismatches,random_continuation_cases=random_cases,
 limits=['Wine, not native Windows','one selected startup seed per nation; no full seed cross product',
 'synthetic boundary/state cases labelled; not all naturally reached','not owner twelve-save set','not exhaustive gameplay/UI/campaign coverage',
 'not independent model review','native metadata/RNG reset is not full-state equality'])
with (HERE/sys.argv[2]).open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('PASS',len(rows)-1,'roundtrip cases +12 refusal controls;',hash_checks,'hash checks;',len(mismatches),'explicit deterministic mismatch cases')
