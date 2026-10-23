"""Reuse unchanged compiled replay helpers; vary only the engine under test."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
ART=ROOT/'artifacts/run-exp-battle-residual157'
SOURCE=ART/'corpus-cached-live-v1/build/bin/Corpus/debug'
variants={
    'baseline':ROOT/'artifacts/run-exp-faithful-general157/engine-build-v2/bin/IC2.Engine/debug',
    'cached-only':ART/'engine-cached-only-v1/bin/IC2.Engine/debug',
}
for label,engine in variants.items():
    harness=ART/('corpus-'+label+'-v1');harness.mkdir(exist_ok=False)
    (harness/'data').symlink_to('/home/diego/projects/imperial_conquest_2/data',target_is_directory=True)
    with (harness/'IC2.sln').open('x') as f:f.write('# Read-only asset-discovery marker only\n')
    bundle=harness/'bin';shutil.copytree(SOURCE,bundle)
    replaced=[]
    for name in ['IC2.Engine.dll','IC2.Data.dll']:
        target=bundle/name
        old=hashlib.sha256(target.read_bytes()).hexdigest()
        # New bundle is not a measured run yet; replace dependencies before execution.
        shutil.copy2(engine/name,target)
        replaced.append(dict(file=name,before=old,after=hashlib.sha256(target.read_bytes()).hexdigest()))
    assert (bundle/'IC2.Engine.Tests.dll').read_bytes()==(SOURCE/'IC2.Engine.Tests.dll').read_bytes()
    args=['/home/diego/.dotnet/dotnet',str(bundle/'Corpus.dll'),str(DATA/('corpus-'+label+'-v1.jsonl')),str(DATA/('corpus-'+label+'-v1.json'))]
    env=dict(os.environ,IC2_FIXTURES_DIR=str(ART/'full-fixtures-v1'))
    r=subprocess.run(args,env=env,capture_output=True,text=True)
    with (DATA/('corpus-'+label+'-execution-v1.json')).open('x') as f:
        json.dump(dict(argv=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,engine_dependencies=replaced,
                       helper_assembly_unchanged=True,registry_exemptions=False),f,indent=2);f.write('\n')
    print(label,r.returncode,r.stdout[-3500:],r.stderr[-700:],flush=True)
