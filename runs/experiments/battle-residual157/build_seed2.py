"""Same validated semantic observer, changing only the fixed lab seed to2."""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'runs/experiments/battle-parity157'))
import semantic_observer as O

DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
ART=ROOT/'artifacts/run-exp-battle-residual157'
DATA.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
old=ROOT/'artifacts/run-exp-battle-parity157/semantic-observer-v1.exe'
old_info=json.loads((ROOT/'runs/experiments/data/run-exp-battle-parity157/semantic-build-v1.json').read_text())
assert hashlib.sha256(old.read_bytes()).hexdigest()==old_info['exe_sha256']
assert hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest()==old_info['source_sha256']
raw=Path('/home/diego/ic2-work/build/Imperial Conquest 2 lab s2.exe').read_bytes()
# The existing apply wrapper has a historical seed1 default. Override only that
# argument, retaining the exact same snapshot/cave code and guarded patch sites.
base_apply=O.H.apply
def seeded_apply(b,seed,lab):
    assert seed==1
    return base_apply(b,2,lab)
O.H.apply=seeded_apply
b=bytearray(raw);info=O.apply(b)
before=old.read_bytes();assert len(before)==len(b)
differences=[dict(offset=i,before=x,after=y) for i,(x,y) in enumerate(zip(before,b,strict=True)) if x!=y]
assert len(differences)==2 and all(r['before']==1 and r['after']==2 for r in differences),differences
out=ART/'semantic-seed2-v1.exe'
with out.open('xb') as f:f.write(b)
report=dict(seed=2,exe_sha256=hashlib.sha256(b).hexdigest(),base_lab_sha256=hashlib.sha256(raw).hexdigest(),
            observer_source_sha256=old_info['source_sha256'],seed1_exe_sha256=old_info['exe_sha256'],
            only_differences_from_validated_seed1= differences,info=info,
            scope='Identical semantic observation code; only two seed immediates differ. Seed2 live golden gate still required.')
with (DATA/'observer-build-v1.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print('Seed2 observer built; only two 1-to-2 seed bytes differ from validated seed1',flush=True)
