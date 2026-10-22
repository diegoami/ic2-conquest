"""Check retained evidence/pins and strict candidate projection, no game/export file writes."""
import argparse,hashlib,importlib.util,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];data=root/'runs/experiments/data/run-exp-sav-export37-semantics';load=lambda n:json.loads((data/n).read_text())
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt').read_bytes();assert hashlib.sha256(source).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
lines=source.decode().splitlines();packet=load('source-command-consumers-v1.json');assert len(packet['records'])==36
assert sum(len(r['lines']) for r in packet['records'])==1800
for r in packet['records']:
 for l in r['lines']:assert lines[l['number']-1]==l['text']
binary=load('x86-cfg-alias-leads-v1.json');assert binary['decoded_instructions']==74750 and binary['covered_code_bytes']==232148 and binary['executable_virtual_bytes']==375252
assert len(binary['indirect_edges'])==812 and len(binary['nation_operand_leads'])==408 and len(binary['nation_relocations'])==411
assert binary['decode_failures']==binary['overlapping_targets']==[]
assert {r['pc'] for r in binary['unknown_operand_starts']}=={'0x445b61','0x445d96','0x4462c4'}
assert all(r['text'].startswith('lea ') and r['offset']=='0x450' for r in binary['unknown_operand_starts'])
assert {r['resource']:r['value'] for r in binary['resources']}=={'TCHANGETAX':40,'TRENAMEARMYUNIT':23}
rejected=load('x86-cfg-alias-leads-v2.json');assert len(rejected['decode_failures'])==266 and len(rejected['overlapping_targets'])==2514
proof=load('transition-projection-v3.json');assert proof['tax_cases']==len(proof['tax_records'])==656
assert {(r['nation'],r['tax']) for r in proof['tax_records']}=={(n,t) for n in range(16) for t in range(41)}
for r in proof['tax_records']:
 assert len(r['serialized_write_events'])==1
 assert int(r['serialized_write_events'][0]['address'],16)==0x474670+1172*r['nation']+0x44a
assert len(proof['viewport_cases'])==4 and len(proof['rename_cases'])==4 and not proof['full_UI_callbacks_executed'] and proof['Windows_round_trips']==0
for r in proof['rename_cases']:assert r['whole_army_copy_bytes']==656 and r['changed_allowed_name_prefix_only']
assert len(proof['profile_cases'])==6 and len(proof['rejected_profile_cases'])==3
spec=importlib.util.spec_from_file_location('transition',Path(__file__).with_name('transition_proof.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for r in proof['profile_cases']:
 raw=(root/'saves'/r['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['source_sha256'];*_,no,news,last,tail=module.layout(raw)
 n=r['nation'];ui=tuple(module.i16(raw,no+n*1172+o) for o in [0x47c,0x47a,0x488,0x486])
 out=module.tax_projection(raw,n,r['tax'],*ui);assert hashlib.sha256(out).hexdigest()==r['output_sha256']
 assert [i for i,(x,y) in enumerate(zip(raw,out)) if x!=y]==r['changed_byte_offsets']
 assert set(r['changed_byte_offsets'])<=set(range(no+n*1172+0x44a,no+n*1172+0x44c))
 assert not r['save_written']
for r in json.loads((root/'runs/experiments/data/run-exp-sav-export37/input-provenance-initial.json').read_text())['inputs']:
 if r.get('copy'):assert hashlib.sha256((root/'runs/experiments/data/run-exp-sav-export37'/r['copy']).read_bytes()).hexdigest()==r['sha256']
 if r['source'].endswith('.exe') or r['source'].endswith('.dat'):assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['sha256']
for script in Path(__file__).parent.glob('*.py'):compile(script.read_text(),str(script),'exec')
base='ed1a411ac3ac47fa07d3dc179511515bd6cdc04c';cmd=['git','diff','--check',base,'--','.'];r=subprocess.run(cmd,cwd=root,capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
record=dict(method='Offline retained evidence/pin/source/profile consistency; no original GUI or Windows execution.',tax_instruction_cases=656,viewport_cases=4,rename_commit_cases=4,public_in_memory_projections=6,source_functions=36,exact_source_lines=1800,full_UI_callbacks_executed=False,Windows_round_trips=0,export_readiness=False,whitespace_check=dict(argv=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.iterdir()) if p.is_file()})
with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k!='files'}))
