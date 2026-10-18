"""Read-only finite evidence check. Private bytes are never emitted or copied."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from remaining_cases import CASES,SOURCE,CAND,PRIVATE,DATA,layout

def digest(p):return dict(name=p.name,size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main(out):
 assert not out.exists()
 cases={1:dict(source='1.sav',candidate='t184-tax-1-n0-0.SAV',source_sha='d20971d5c73a39c82bb9a6c76413394d1d6fc8174bf5ae857a8161eaba5d7c10',candidate_sha='5e85a985382dc56ae964889ed01d4fda56b0e2414ccaede5e18d03b3bd2a314c'),**CASES}
 files=[];checks=[];inputs=[]
 for case,c in cases.items():
  for role,folder,name,want in [('source',SOURCE,c['source'],c['source_sha']),('candidate',CAND,c['candidate'],c['candidate_sha'])]:
   item=digest(folder/name);assert item['sha256']==want;item.update(case=case,role=role,unchanged=True);inputs.append(item)
  stage={s:PRIVATE/f'N{case}{s}68B2.SAV' for s in 'ILOER'}
  for s,p in stage.items():
   item=digest(p);item.update(case=case,stage=s);files.append(item);layout(p.read_bytes())
  assert stage['I'].read_bytes()==stage['L'].read_bytes()==(CAND/c['candidate']).read_bytes()
  assert stage['E'].read_bytes()==stage['R'].read_bytes()
  assert stage['L'].read_bytes()!=stage['O'].read_bytes()!=stage['E'].read_bytes()
  completion=json.loads((DATA/f'case{case}-completion-v1.json').read_text());assert completion.get('final_active_original_processes',0)==0
  for s in 'BT':files.append(dict(case=case,stage='reference'+s,**digest(PRIVATE/f'C{case}{s}68B2.SAV')))
  if case>1:assert (PRIVATE/f'C{case}T68B2.SAV').read_bytes()==(CAND/c['candidate']).read_bytes()
  checks.append(dict(case=case,load_save_exact_candidate=True,order_changed_save=True,postturn_changed_save=True,fresh_reopen_exact_postturn=True,completion_record=f'case{case}-completion-v1.json'))
 exe=Path('/mnt/c/Users/diego/Documents/imp_conq_original/Imperial Conquest 2.exe');ex=digest(exe);assert ex['sha256']=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
 captures=[digest(p) for p in sorted(PRIVATE.glob('*.PNG')) if p.name.startswith(('N1','N2','N3','C1','C2','C3'))]
 logs=sorted(DATA.glob('*.json'))
 for p in logs:json.loads(p.read_text())
 for p in Path(__file__).parent.glob('*.py'):compile(p.read_text(),str(p),'exec')
 r=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-Command',"@{count=@(Get-Process|Where-Object {$_.ProcessName -like '*Conquest*'}).Count}|ConvertTo-Json -Compress"],capture_output=True,text=True);assert r.returncode==0;count=json.loads(r.stdout)['count'];assert count==0
 # Re-read immutable inputs after all inspection; no before/after race is hidden.
 for c in cases.values():assert digest(SOURCE/c['source'])['sha256']==c['source_sha'] and digest(CAND/c['candidate'])['sha256']==c['candidate_sha']
 assert digest(exe)==ex
 result=dict(method='Read-only private hashes/whole-file identities, authentic full strategic framing, retained metadata parse and script compilation; no UI action/game launch/save creation',native_candidate_sequences_completed=3,required=3,checks=checks,immutable_inputs=inputs,original_EXE=ex,private_files=files,private_captures=captures,parsed_measurement_JSON_files=len(logs),active_original_processes=count,internal_callback_instruction_trace='UNVERIFIED',twelve_native_JSON_conversion_target='UNMET/separate',full_exporter_or_issue_closure=False)
 with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(result='PASS',cases=3,measurement_JSON=len(logs),private_captures=len(captures),active_original_processes=count)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
