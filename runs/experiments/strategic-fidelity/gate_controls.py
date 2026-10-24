"""The projection gate must reject mismatching expected troops/relations."""
import json
import resource
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
source=BASE/'projections/N-rome-hook-v1-v1';out=BASE/'negative-gates-v1';out.mkdir()
rows=[]
for name in ['troops','relations']:
    folder=out/name;folder.mkdir();shutil.copy2(source/'000.SAV',folder/'000.SAV');shutil.copy2(source/'manifest.json',folder/'manifest.json')
    expected=json.loads((source/'000.json').read_text())
    if name=='troops':expected['armies'][0]['units'][0]['troops']+=1
    else:expected['nations'][0]['relations']['Carthage']+=1
    with (folder/'000.json').open('x') as f:json.dump(expected,f)
    output=folder/'must-not-exist.jsonl'
    with (DATA/('negative-gate-'+name+'-v1.log')).open('x') as f:
        run=subprocess.run(['/home/diego/.dotnet/dotnet',str(ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0/Probe.dll'),
            'decisions',str(BASE/'source-v1'),str(folder),str(output)],stdout=f,stderr=subprocess.STDOUT,
            preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
    assert run.returncode!=0 and not output.exists()
    rows.append(dict(mutation=name,rejected=True,output_created=False,returncode=run.returncode))
with (DATA/'negative-gates-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print('PASS troop and relation mismatch gates reject before emitting comparable rows')
