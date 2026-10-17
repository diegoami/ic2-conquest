"""Offline integrity/coverage validation; not an original-compatibility test."""
from pathlib import Path
import argparse,csv,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];data=root/'runs/experiments/data/run-exp-sav-export37'
load=lambda name:json.loads((data/name).read_text())
public=load('public-scalar-audit-initial.json');assert len(public['records'])==14
for r in public['records']:
 assert hashlib.sha256((root/'saves'/r['file']).read_bytes()).hexdigest()==r['sha256']
 assert len(r['nations'])==16
 for n in r['nations']:
  assert n['active_matches_owned'] and n['active_ASCII_sorted'] and n['non_minusone_after_count']==0
  assert n['unknown_450_46a_unique']==[0] and n['unknown_46d']==0 and n['unknown_491_493']==[0,0,0]
profile=load('dat-profile-initial.json');assert len(profile['records'])==16 and profile['public_nation_baseline_matches']==224
controls=load('x86-controls-v2.json');assert len(controls['records'])==10 and all(r['status']=='pass' for r in controls['records'])
by={r['case']:r for r in controls['records']};assert by['new-army-residue']['retained_synthetic_bytes']==560 and by['new-fleet-residue']['retained_synthetic_bytes']==16
assert by['army-relocation']['full_record_copy'] and by['army-relocation']['fleet_army_reference_after']==0
assert by['strategic-finder-order']['first_live_match']==0 and by['strategic-finder-order']['after_first_tombstoned']==1
with (data/'nation-matrix-v2.csv').open() as f:matrix=list(csv.DictReader(f))
coverage=[]
for r in matrix:
 first,last=int(r['first'],16),int(r['last'],16);assert last-first+1==int(r['bytes']);coverage+=list(range(first,last+1))
 assert '?' not in r['evidence']
assert coverage==list(range(1172)) and len(matrix)==33
unknown=[r for r in matrix if r['policy'].startswith('UNKNOWN')];assert [(r['first'],r['last']) for r in unknown]==[('450','46A'),('46D','46D'),('491','493')]
assert sum(int(r['bytes']) for r in unknown)==31 and all(r['policy']=='UNKNOWN_REJECT_CHANGED_STATE' for r in unknown)
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt');raw=source.read_bytes();lines=raw.decode().splitlines();inventory=load('source-inventory-addresses-v2.json')
assert hashlib.sha256(raw).hexdigest()==inventory['source_sha256']=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
assert len(inventory['functions'])==247 and len(inventory['references'])==2040
for line in (data/'source-focused-v1.txt').read_text().splitlines():
 number,text=line.split(': ',1);assert lines[int(number)-1]==text
provenance=load('input-provenance-initial.json')
for r in provenance['inputs']:
 if r.get('copy'):assert hashlib.sha256((data/r['copy']).read_bytes()).hexdigest()==r['sha256']
result=dict(provenance='Offline retained-packet validation only; no game/Windows run, owner-private data or exporter test.',public_saves=14,nation_records=224,source_functions=247,references=2040,focused_source_lines=1111,original_x86_controls=10,nation_regions=33,nation_bytes=1172,unknown_reject_bytes=31,Windows_output_round_trips=0,changed_state_export_readiness=False)
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
