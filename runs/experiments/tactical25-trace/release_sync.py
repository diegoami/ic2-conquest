"""Upload immutable probe artifacts; a refused release write stops, without fallback."""
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace'
TAG='run-exp-tactical25-trace'
ART=ROOT/'artifacts'/TAG
ENV=os.environ.copy()
# The release-specific token is passed only to release commands, never printed.
if ENV.get('IC2_RELEASE_TOKEN'):
    ENV['GH_TOKEN']=ENV['IC2_RELEASE_TOKEN']


def run(args):
    return subprocess.run(args,cwd=ROOT,env=ENV,capture_output=True,text=True)


have=run(['gh','release','view',TAG,'--json','assets','--jq','.assets[].name'])
exists=have.returncode==0
if not exists and 'not found' not in have.stderr.lower():
    raise SystemExit('Release inventory could not be read; no write attempted: '+have.stderr[-500:])
held=set(have.stdout.split()) if exists else set()
pending=sorted(p for p in ART.iterdir() if p.is_file() and p.name not in held)
rec=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pending=[p.name for p in pending],uploaded=[],refused=None)
for index in range(0,len(pending),30):
    chunk=pending[index:index+30]
    if exists:
        cmd=['gh','release','upload',TAG]+list(map(str,chunk))
    else:
        cmd=['gh','release','create',TAG,'--target','research/tactical25-original-trace','--title',TAG,
             '--notes','Immutable October 16 original tactical25 runtime traces; SHA-256 and logs in runs/experiments/data/run-exp-ai-oct16. Wine-only unless explicitly marked otherwise.']+list(map(str,chunk))
    result=run(cmd)
    if result.returncode:
        rec['refused']=dict(command=shlex.join(cmd),stderr=result.stderr[-700:])
        print('Release write refused; no alternate route will be tried. Exact command:\n'+shlex.join(cmd))
        break
    exists=True
    rec['uploaded']+= [p.name for p in chunk]
name=f'release-sync-{time.strftime("%Y%m%d-%H%M%S")}-{os.getpid()}.json'
with (DATA/name).open('x') as out:
    json.dump(rec,out,indent=2)
print(json.dumps(dict(record=name,uploaded=len(rec['uploaded']),pending=len(pending),refused=rec['refused'])))
raise SystemExit(3 if rec['refused'] else 0)
