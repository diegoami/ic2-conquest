"""Check production reachability of each originally selected target."""
import json
import argparse
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['eligibility','from-scores'],default='eligibility');p.add_argument('--manifest',default='case-manifest-v2.json');p.add_argument('--case');a=p.parse_args()
for case in json.loads((DATA/a.manifest).read_text())['cases']:
    if a.case and case['label']!=a.case:continue
    label=case['label']+'-hook-v1';out=DATA/label/('original-target-'+a.mode+'-v1.jsonl')
    with (DATA/(a.mode+'-'+case['label']+'-v1.log')).open('x') as f:
        r=subprocess.run(['/home/diego/.dotnet/dotnet',str(ROOT/'runs/experiments/strategic-fidelity/bin/Debug/net10.0/Probe.dll'),
            a.mode,str(BASE/'source-v1'),str(BASE/'projections'/(label+'-v1')),str(out)],stdout=f,stderr=subprocess.STDOUT)
    print(label,r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
