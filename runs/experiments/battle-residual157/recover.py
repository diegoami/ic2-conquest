"""Recover the two immutable residual aliases; never overwrite an input."""
import base64
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
DEST=ROOT/'artifacts/run-exp-battle-residual157/fixtures-v1'
REV='6319802a75067e7730e4f6a27dce3b4e296ddd9b'
REPO='diegoami/ic2-test-fixtures'

def api(path):
    return json.loads(subprocess.check_output(['gh','api',path]))

def blob(sha):
    value=api(f'repos/{REPO}/git/blobs/{sha}')
    assert value['encoding']=='base64'
    raw=base64.b64decode(value['content'])
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==sha
    return sha,raw

if __name__=='__main__':
    DATA.mkdir(parents=True,exist_ok=True)
    DEST.mkdir(parents=True,exist_ok=False)
    tree=api(f'repos/{REPO}/git/trees/{REV}?recursive=1')
    assert not tree['truncated']
    entries={e['path']:e for e in tree['tree']}
    names={'battles/starts/FLD-RG_0743_rome_army0_at_86_28.SAV','battles/hook/hooklog-mix-rg_s2_r5_hook.csv'}
    for folder,prefix in [('hook','mix-rg_s2_r5_hook'),('probe','gate2_s2a')]:
        names.update(f'battles/{folder}/{prefix}_BATTLE{i:02d}.SAV' for i in range(1,19))
        names.add(f'battles/{folder}/{prefix}_post.SAV')
    aliases=[]
    for suffix in [f'BATTLE{i:02d}.SAV' for i in range(1,19)]+['post.SAV']:
        a=f'battles/hook/mix-rg_s2_r5_hook_{suffix}'
        b=f'battles/probe/gate2_s2a_{suffix}'
        assert entries[a]['sha']==entries[b]['sha']
        aliases.append(dict(hooked=a,gate=b,git_blob=entries[a]['sha']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        content=dict(pool.map(blob,sorted({entries[n]['sha'] for n in names})))
    rows=[]
    for name in sorted(names):
        e=entries[name];raw=content[e['sha']]
        assert len(raw)==e['size']
        path=DEST/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f:f.write(raw)
        rows.append(dict(path=name,bytes=len(raw),git_blob=e['sha'],sha256=hashlib.sha256(raw).hexdigest()))
    report=dict(revision=REV,files=rows,unique_blobs=len(content),byte_identical_alias_pairs=aliases,
                scope='Two named residual series share all18boundary files andpost exactly. One recorded trajectory, not two independent battles.')
    with (DATA/'fixture-recovery-v1.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print('Recovered',len(rows),'files from',len(content),'verified blobs;19 alias pairs byte-identical',flush=True)
