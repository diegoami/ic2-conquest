"""Integrity and evidence consistency only; no original game/export validation."""
import argparse, hashlib, json, re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];data=root/'runs/experiments/data/run-exp-sav-export37-closure';prior=root/'runs/experiments/data/run-exp-sav-export37'
load=lambda name:json.loads((data/name).read_text())
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt').read_bytes();lines=source.decode().splitlines()
digest=hashlib.sha256(source).hexdigest();assert digest=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
inventory=load('source-alias-leads-v2.json');assert inventory['source_sha256']==digest
assert len(inventory['functions'])==156 and len(inventory['absolute_references'])==680
assert inventory['unknown_start_references']==inventory['relative_unknown_constant_leads']==inventory['added_functions']==[]
for f in inventory['functions']:
 assert f['name'] in lines[f['first_line']-1]
 for r in f['absolute_references']:
  assert lines[r['line']-1]==r['text'];at=int(r['address'],16)
  assert 0x474670<=at<0x474670+16*1172
  n,o=divmod(at-0x474670,1172);assert (n,hex(o))==(r['nation'],r['offset'])
extract=(data/'source-controls-and-history-v1.txt').read_text().splitlines();functions=[]
for s in extract:
 n,text=s.split(': ',1);assert lines[int(n)-1]==text
 if text.startswith('// ==== '):functions.append(text)
assert len(functions)==8
assert not (data/'source-added-functions-v1.txt').read_bytes()
controls=load('x86-path-controls-v2.json');rows=controls['records'];assert len(rows)==6 and all(r['status']=='pass' for r in rows)
assert controls['public_save_sha256']==hashlib.sha256((root/'saves'/controls['public_save']).read_bytes()).hexdigest()
assert controls['exe_sha256']==hashlib.sha256(Path(controls['exe_path']).read_bytes()).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
for r in rows[:4]:assert r['unknown_canaries']==496 and r['all_canaries_preserved'] and r['unknown_reads_writes']==[]
assert rows[0]['historical_baselines_preserved']
for r in rows[2:4]:assert r['inactive_last_retains_origin_type_quality_and_text'] and r['inactive_last_changed_offsets']==[4,5]
assert rows[4]['buffers_differ_after_same_rename'] and rows[4]['trailing_bytes_retained']==21
positive=rows[5]['unknown_reads_writes'];assert {e['access'] for e in positive}=={16,17}
assert {int(e['address'],16) for e in positive if e['access']==17}=={0x474f54,0x474f55}
assert all(e['size']==1 and e['unknown_bytes'] for e in positive)
provenance=json.loads((prior/'input-provenance-initial.json').read_text())
for r in provenance['inputs']:
 if r.get('copy'):assert hashlib.sha256((prior/r['copy']).read_bytes()).hexdigest()==r['sha256']
 if r['source'].endswith('.dat'):assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['sha256']
for script in Path(__file__).parent.glob('*.py'):compile(script.read_text(),str(script),'exec')
record=dict(method='Offline pinned-artifact integrity and bounded-control result consistency, not a game/export test.',source_sha256=digest,source_functions=156,absolute_lexical_references=680,additional_functions=0,source_extract_functions=8,source_extract_lines=len(extract),original_x86_controls=6,negative_unknown_paths=4,unknown_canaries_per_path=496,positive_guest_access_types=[16,17],Windows_round_trips=0,changed_state_export_readiness=False,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.iterdir()) if p.is_file()})
with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k!='files'}))
