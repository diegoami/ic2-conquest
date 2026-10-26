"""Publish bounded classifications; private exact comparison projections remain private."""
from original import *
from collections import Counter
import argparse
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args();native={r['id']:r for r in json.load(open(D/'native-v2.json'))};rows=[]
for spec in json.load(open(D/'original-v1-plan.json')):
 id=spec['id'];o=json.load(open(D/('original-v1_'+id+'.json')));n=native[id];folder=A/'private-original-v1'/id;s=json.load(open(folder/'expected.json'));before=json.load(open(folder/'before.json'))
 # Exact import/projection comparisons use shapes, not reimported expected SAVs.
 expected=json.load(open(folder/'expected-shape-v2.json'));actualfile=A/'private-native-v2'/(id+'-projection.json')
 diffs=[]
 if actualfile.exists():
  actual=json.load(open(actualfile));key=lambda a:json.dumps(a,separators=(',',':'),ensure_ascii=False)
  eo=Counter(key(a)for a in expected['armies']);na=Counter(key(a)for a in actual['armies'])
  for name,counter in [('original_only',eo-na),('native_only',na-eo)]:
   for value,count in counter.items():
    row=json.loads(value);diffs.append(dict(side=name,copies=count,owner=row[0],x=row[1],y=row[2],moves=row[3],money=row[5],supply=row[6],units=[u[2]for u in row[9]]))
 if spec.get('helper_no_land'):classification='helper-only diagnostic; not natural adjacent-embark evidence'
 elif spec.get('not_gui_equivalent'):classification='non-equivalent human helper/command boundary; preserve human policy'
 elif spec.get('tombstone'):classification='raw-table versus model-live-count boundary policy; not automatic correction'
 elif not n['accepted']:classification='owner-approved atomic refusal; original destructive/corrupt branch not copied'
 elif n['projection_equal']:classification='exact measured projection match'
 else:classification='accepted success receiver-context/moves discrepancy; correction candidate'
 if n.get('accepted')is False:assert n['full_state_unchanged']
 calls=o['calls'];assert 'random'not in calls and 'compactarmy'not in calls
 if o['negative_index_writes']:assert o['negative_index_writes']==[dict(city_id=315,city_offset=0,size=2,synthetic_value=30),dict(city_id=315,city_offset=2,size=2,synthetic_value=33)]
 receiver=[dict(id=a['id'],x=a['x'],y=a['y'],moves=a['moves'],troops=a['troops'],money=a['money'],supply=a['supplies'])for a in s['armies']if a['id']>=len(before['armies'])and a['owner']>=0 and a['troops']>0]
 if receiver and 'post_placement'in n:assert n['post_placement']==[receiver[0]['x'],receiver[0]['y']],id
 rows.append(dict(id=id,classification=classification,original_before=o['before'],original_after=o['after'],original_new_receiver=receiver,native=n,army_projection_differences=diffs,negative_index_writes=o['negative_index_writes'],raw_compaction_called=False))
counts=Counter(r['classification']for r in rows)
write(D/('comparison-'+q.version+'.json'),dict(original_controls=len(rows),native_commands=15,input_projection_gates_passed=15,counts=dict(counts),rows=rows))
print(json.dumps(dict(counts),indent=2))
