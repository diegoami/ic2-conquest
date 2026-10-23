"""Fail-closed controls on an actual validated public original trace."""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-parity157'
SOURCE=DATA/'reference-semantic-v1'
OUT=ROOT/'artifacts/run-exp-battle-parity157/semantic-parser-tests-v1'
OUT.mkdir(exist_ok=False)
hook=json.loads((SOURCE/'hook.json').read_text())
states=json.loads((SOURCE/'states.json').read_text())
rows=[]
for name in ['positive','sequence-gap','missing-snapshot','wrong-draw-result','unknown-marker','unbalanced-boundary']:
    h,s=copy.deepcopy(hook),copy.deepcopy(states)
    folder=OUT/name
    folder.mkdir()
    if name=='sequence-gap':
        h['records'][4]['seq_ok']=False
    elif name=='missing-snapshot':
        s['records'].pop(4)
    elif name=='wrong-draw-result':
        next(r for r in h['records'] if r['kind']=='random')['result'] ^= 1
    elif name in ['unknown-marker','unbalanced-boundary']:
        r=next(r for r in h['records'] if r['kind']=='marker' and r['site']==0x438a6c)
        r['site']=0x401234 if name=='unknown-marker' else 0x439968
        next(x for x in s['records'] if x['seq']==r['seq'])['site']=hex(r['site'])
    for filename,value in [('hook.json',h),('states.json',s)]:
        with (folder/filename).open('x') as f:
            json.dump(value,f)
    r=subprocess.run([sys.executable,str(Path(__file__).with_name('semantic_log.py')),str(folder)],capture_output=True,text=True)
    passed=(r.returncode==0)==(name=='positive')
    rows.append(dict(case=name,returncode=r.returncode,expected_success=name=='positive',passed=passed,stdout=r.stdout,stderr=r.stderr))
    print(name,r.returncode,'pass' if passed else 'FAIL',flush=True)
with (DATA/'semantic-parser-controls-v1.json').open('x') as f:
    json.dump(dict(all_passed=all(r['passed'] for r in rows),cases=rows),f,indent=2)
    f.write('\n')
assert all(r['passed'] for r in rows)
