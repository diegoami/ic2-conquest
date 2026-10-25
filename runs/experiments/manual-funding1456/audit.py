#!/usr/bin/env python3
"""Reparse retained original save pairs; publish only synthetic case scalars.

No mutation of original evidence. Exclusive versioned output. Full file hashes
stay private as required by Main #1456. Not a game/simulator or a formula test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from state import sav
ART=ROOT/'artifacts/run-exp-manual-funding1456'
DATA=ROOT/'runs/experiments/data/run-exp-manual-funding1456'


def blob_sha(path):
    b=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',required=True)
    args=parser.parse_args()
    plan=json.loads((DATA/'all-cases-plan-v1.json').read_text())
    native={r['id']:r for r in json.loads((DATA/'native-v2.json').read_text())}
    rows=[];hashes={}
    for case in plan:
        files=list(DATA.glob('*_'+case['id']+'.json'))
        assert len(files)==1,(case['id'],files)
        row=json.loads(files[0].read_text())
        copies=[]
        for key in ['before_save','after_save']:
            matches=list(ART.glob('private-*/*'+row[key]))
            assert len(matches)==1,(key,matches)
            p=matches[0];b=p.read_bytes();s=sav.parse(b)
            hashes[str(p.relative_to(ART))]=hashlib.sha256(b).hexdigest()
            assert s['turn']==734 and s['battle_flag']==0
            balances=[s['nations'][0]['treasury'],s['armies'][0]['money'] if case['kind']=='army' else s['fleets'][2]['money'],s['fleets'][2 if case['kind']=='army' else 5]['money']]
            assert balances==row['before' if key=='before_save' else 'after']
            # Compare all parsed strategic state, except balances under test
            # and camera position changed by selecting the target.
            s['nations'][0]['treasury']=0
            for n in s['nations']:n['view']=[0,0]
            if case['kind']=='army':s['armies'][0]['money']=0
            else:s['fleets'][2]['money']=0
            s['fleets'][2 if case['kind']=='army' else 5]['money']=0
            copies.append(s)
        assert copies[0]==copies[1],case['id']
        assert row['prediction_match'] and row['control_enabled'] and row['control_visible'] and row['total_conserved']
        assert row['after']==case['expected']
        rows.append(dict(id=case['id'],before=row['before'],after=row['after'],
            enabled=True,visible=True,parsed_state_unchanged_except_balances_and_view=True,
            native_after=native[case['id']]['native_after'],
            native_matches_original=native[case['id']]['native_after']==row['after']))
    identity=json.loads((ART/'private-v1/identity.json').read_text())
    game=ART/'work-v1/prefix/drive_c/IC2'
    assert hashlib.sha256((game/'Imperial Conquest 2.exe').read_bytes()).hexdigest()==identity['exe_sha256']
    assert hashlib.sha256((game/'Imperial Conquest 2.dat').read_bytes()).hexdigest()==identity['dat_sha256']
    # Original asset identity compared privately to the retained unmodified
    # original, never expose its hash in public output.
    assert (game/'Imperial Conquest 2.exe').read_bytes()==Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
    source=ROOT/'artifacts/run-exp-battle-current157/source-v1/src/IC2.Engine/Economy'
    assert blob_sha(source/'TreasuryPurseTransfer.cs')=='884097638b6708f5152ae3a5b53c8d1ca72149bc'
    assert blob_sha(source/'Commands/TransferMoneyCommandHandler.cs')=='9a66af872c31e9ecbb0947e7cf608d20f4fa0362'
    rules=ROOT/'artifacts/run-exp-battle-current157/source-v1/data/rulesets/classical-faithful.json'
    assert blob_sha(rules)=='4e04ca3e72cb1eb5bbe68010eb3280a373ebb93b'
    result=dict(cases=len(rows),original_matches_predictions=len(rows),
        native_matches_original=sum(r['native_matches_original'] for r in rows),
        original_exe_unchanged=True,original_dat_unchanged=True,
        platform='Linux, Wine 10.0 Ubuntu 10.0~repack-12ubuntu1, win32 prefix, Xvfb 1280x1024',
        source_fixture='fleet-split-antium-0734.SAV',turn=734,
        native_scope='Actual helper with source-verified TransferMoneyCommandHandler treasury/via dispatch; no native UI or complete command execution',
        scope='Staged monetary fields only, real original UI clicks; no battle/End turn/native Windows',rows=rows)
    with (DATA/('audit-'+args.version+'.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    with (ART/('audit-private-hashes-'+args.version+'.json')).open('x') as f:json.dump(hashes,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main()
