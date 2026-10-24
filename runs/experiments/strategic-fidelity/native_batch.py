"""Ordinary native End-turn observations for all declared inputs; no overwrites."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
cases=json.loads((DATA/'case-manifest-v1.json').read_text())['cases']
for case in cases:
    label=case['label'];log=DATA/('native-end-'+label+'-v1.log')
    assert not log.exists()
    with log.open('x') as f:
        result=subprocess.run(['/home/diego/.dotnet/dotnet',str(ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0/Probe.dll'),
            'end',str(BASE/'source-v1'),str(BASE/'inputs-v1'/(label+'.SAV')),str(BASE/'native'/(label+'-v1'))],stdout=f,stderr=subprocess.STDOUT)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
