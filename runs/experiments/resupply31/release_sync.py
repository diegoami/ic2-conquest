"""Upload immutable probe artifacts; a refused release write stops, without fallback."""
import hashlib
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-resupply31'
TAG='run-exp-resupply31'
ART=Path('/tmp/ic2r31-artifacts')
ENV=os.environ.copy()
# The release-specific token is passed only to release commands, never printed.
if ENV.get('IC2_RELEASE_TOKEN'):
    ENV['GH_TOKEN']=ENV['IC2_RELEASE_TOKEN']


def run(args):
    return subprocess.run(args,cwd=ROOT,env=ENV,capture_output=True,text=True)


have=run(['gh','release','view',TAG,'--json','assets'])
exists=have.returncode==0
if not exists and 'not found' not in have.stderr.lower():
    raise SystemExit('Release inventory could not be read; no write attempted: '+have.stderr[-500:])
held={x['name']:x for x in json.loads(have.stdout)['assets']} if exists else {}
pending=[]
# GitHub normalized spaces to dots in the already published EXE names. Verify
# matching bytes rather than retry those existing assets. No replacement/clobber.
for path in sorted(p for p in ART.iterdir() if p.is_file()):
    name=path.name.replace(' ','.')
    if name not in held:pending.append(path);continue
    expected='sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
    if held[name].get('digest')!=expected:
        raise SystemExit('Published asset has a different digest; no overwrite attempted: '+name)

rec=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pending=[p.name for p in pending],uploaded=[],refused=None)
for index in range(0,len(pending),30):
    chunk=pending[index:index+30]
    if exists:
        cmd=['gh','release','upload',TAG]+list(map(str,chunk))
    else:
        cmd=['gh','release','create',TAG,'--target','research/foreign-resupply31','--title',TAG,
             '--notes','Immutable research31 foreign-provider staged saves; hashes and logs in runs/experiments/data/run-exp-resupply31. Wine only; not native confirmation.']+list(map(str,chunk))
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
