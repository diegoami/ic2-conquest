"""Actual CLI/import/session calls, one immutable receipt per operation."""
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ART=ROOT/'artifacts/run-exp-sav-conversion-broad153'
REMAKE=Path('/home/diego/projects/imperial_conquest_2')
DOTNET='/home/diego/.dotnet/dotnet'
CLI=ART/'build/bin/IC2.Cli/debug/IC2.Cli.dll'
PROBE=ART/'probe-build-v6/bin/BroadProbe/debug/BroadProbe.dll'
TEMPLATE=ROOT/'saves/run0-start-AUTO0720-seed12345.SAV'

def run(name,argv):
    receipt=HERE/(name+'.json')
    if receipt.exists():raise RuntimeError('Refusing existing measurement '+name)
    result=subprocess.run(list(map(str,argv)),capture_output=True,text=True,cwd=ROOT,timeout=240)
    with receipt.open('x') as f:
        json.dump(dict(argv=list(map(str,argv)),returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),f,indent=2);f.write('\n')
    print(name,'exit',result.returncode,flush=True)
    if result.returncode:print(result.stderr[-1800:],flush=True)
    return result

def entries():
    return [json.loads(l) for l in (ART/'native-v1/manifest.jsonl').read_text().splitlines()]

def convert(case):
    name=case['name'];src=ART/'native-v1'/(name+'.json');dst=ART/'exports-v1'/(name+'.SAV')
    if (HERE/('export-'+name+'-v1.json')).exists():
        print('Preserving existing conversion:',name,flush=True);return
    dst.parent.mkdir(exist_ok=True)
    p=run('export-'+name+'-v1',[DOTNET,CLI,'--export-sav',src,'--output',dst,'--template',TEMPLATE])
    if p.returncode:return
    run('policy-'+name+'-v1',[sys.executable,ROOT/'scripts/sav_export_policy_check.py',dst,'--out',HERE/('policy-result-'+name+'-v1.json')])
    imported=ART/'exports-v1'/(name+'-imported.json')
    p=run('import-'+name+'-v1',[DOTNET,PROBE,'import',REMAKE,dst,imported])
    if p.returncode:return
    run('predict-'+name+'-v1',[DOTNET,PROBE,'action',REMAKE,imported,ART/'exports-v1'/(name+'-predicted.json'),case['remakeCommand']])

if __name__=='__main__':
    mode=sys.argv[1]
    if mode in ('starts','progress','features','features-extra','features-more','features-final'):
        ART.mkdir(exist_ok=True,parents=True)
        for n in ('IC2.sln','data'):
            if not (ART/n).exists():(ART/n).symlink_to(REMAKE/n,target_is_directory=(REMAKE/n).is_dir())
        run('generate-'+mode+'-v1',[DOTNET,PROBE,mode,REMAKE,ART/'native-v1'])
        for case in entries():convert(case)
    elif mode=='convert':
        for case in entries():convert(case)
    elif mode=='return':
        if not PROBE.exists():raise SystemExit('Build the selected adapter before running return imports')
        completed={}
        for p in sorted(HERE.glob('live-*-v*.json')):
            r=json.loads(p.read_text());name=r['name']
            if r.get('complete'):completed[name]=r
        for name,r in completed.items():
            version='v1'
            prior=HERE/('return-'+name+'-v1.json')
            if prior.exists():
                old=json.loads(prior.read_text())
                if old['returncode']==0:continue
                if 'specified command or file was not found' not in old['stderr']:
                    print('Review retained return failure before retry:',name,flush=True);continue
                version='v2'
                if (HERE/('return-'+name+'-v2.json')).exists():continue
            final=ART/r['files']['reopen']['file'];folder=final.parent
            suffix='' if version=='v1' else '-'+version
            result=run('return-'+name+'-'+version,[DOTNET,PROBE,'import',REMAKE,final,folder/('returned'+suffix+'.json')])
            if result.returncode:continue
            result=run('continue-'+name+'-'+version,[DOTNET,PROBE,'action',REMAKE,folder/('returned'+suffix+'.json'),folder/('continued'+suffix+'.json'),'set-tax 19'])
            if result.returncode:continue
            target=folder/('REEXPORT'+suffix+'.SAV')
            result=run('reexport-'+name+'-'+version,[DOTNET,CLI,'--export-sav',folder/('continued'+suffix+'.json'),'--output',target,'--template',TEMPLATE])
            if result.returncode==0:
                run('reexport-policy-'+name+'-'+version,[sys.executable,ROOT/'scripts/sav_export_policy_check.py',target,'--out',HERE/('reexport-policy-result-'+name+'-'+version+'.json')])
    else:raise SystemExit('starts/progress/convert/return')
