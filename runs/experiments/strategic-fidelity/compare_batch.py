"""Produce original/native matched-state decision rows for completed labels."""
import argparse
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
p=argparse.ArgumentParser();p.add_argument('labels',nargs='+');a=p.parse_args()
for label in a.labels:
    case=label.removesuffix('-hook-v1')
    projected=BASE/'projections'/(label+'-v1')
    if not projected.exists():
        log=DATA/('projection-'+case+'-v1.log')
        with log.open('x') as f:
            r=subprocess.run(['/home/diego/.local/bin/python3.12',str(Path(__file__).with_name('prepare_decisions.py')),label],stdout=f,stderr=subprocess.STDOUT)
        if r.returncode:raise SystemExit(r.returncode)
    output=DATA/label/'native-decisions-v1.jsonl'
    if output.exists():raise RuntimeError('Existing native decision output; inspect before choosing new version')
    with (DATA/('decision-replay-'+case+'-v1.log')).open('x') as f:
        r=subprocess.run(['/home/diego/.dotnet/dotnet',str(Path(__file__).parent/'bin/Debug/net10.0/Probe.dll'),
            'decisions',str(BASE/'source-v1'),str(projected),str(output)],stdout=f,stderr=subprocess.STDOUT)
    print(label,'exit',r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
