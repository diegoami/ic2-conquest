"""Coverage and conversion/action comparisons without rerunning a game.

Keep raw differences. Stage-level comparisons do not equate metadata reset on
import with game-field loss. Differential actions canonicalize entity IDs by
owner/location, but preserve unit order and actual unit text.
"""
import copy,importlib.util,json,sys
from pathlib import Path
from offline import HERE,ROOT,ART,entries

spec=importlib.util.spec_from_file_location('first_conversion_compare',HERE.parent/'run-exp-sav-conversion-roundtrip/compare.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
differences=prior.differences

def native(path,for_action=False):
    s=json.loads(Path(path).read_text())['save']['state']
    ids={a['id']:f"army:{a['nation']}:{a['x']}:{a['y']}:{int(a['aboardFleetId'] is not None)}" for a in s['armies']}
    ids.update({f['id']:f"fleet:{f['nation']}:{f['x']}:{f['y']}:{f['buildCityId'] if f['constructionTicksRemaining'] is not None else 'launched'}" for f in s['fleets']})
    def walk(x):
        if isinstance(x,dict):return {k:walk(v) for k,v in x.items()}
        if isinstance(x,list):return [walk(v) for v in x]
        return ids.get(x,x) if isinstance(x,str) else x
    s=walk(s);rng=s.pop('randomSeed')
    s['armies'].sort(key=lambda a:a['id']);s['fleets'].sort(key=lambda f:f['id'])
    for f in s['fleets']:
        if f['constructionTicksRemaining'] is None:f['buildCityId']=None
    for a in s['armies']:
        for u in a['units']:
            label=u['mercenaryLabel']
            if label and u['name']==f'Mercenary unit (label {label})':u['name']=f'Mercenary (label {label})'
    if for_action:
        s['calendar'].pop('turnIndex',None)
        for n in s['nations']:
            for key in ('populationAtStart','treasuryAtStart','cityCountAtStart','population'):n.pop(key,None)
        # Covered cell is derived by exporter/importer, never persistent native authority.
        for a in s['armies']:a.pop('coveredTileCode',None)
        for f in s['fleets']:f.pop('coveredTileCode',None)
    return s,rng

def command(name):
    path=HERE/(name+'.json')
    if not path.exists():return None
    result=json.loads(path.read_text());payload=None
    if result['returncode']==0:
        try:payload=json.loads(result['stdout'])
        except json.JSONDecodeError:pass
    return dict(returncode=result['returncode'],payload=payload,stderr=result['stderr'])

def compare():
    rows=[]
    for case in entries():
        name=case['name'];row=dict(case=case)
        exported=command('export-'+name+'-v1');policy=command('policy-'+name+'-v1');imp=command('import-'+name+'-v1')
        row['export_success']=exported is not None and exported['returncode']==0
        row['policy_pass']=policy is not None and policy['returncode']==0
        row['import_success']=imp is not None and imp['returncode']==0
        row['remake_prediction']=command('predict-'+name+'-v1')
        native_source=ART/'native-v1'/(name+'.json');imported=ART/'exports-v1'/(name+'-imported.json')
        if imported.exists():
            a,ra=native(native_source);b,rb=native(imported)
            row['source_import_differences']=differences(a,b)
            row['source_import_rng']=[ra,rb]
        attempts=sorted(HERE.glob(f'live-{name}-v*.json'))
        successful=[p for p in attempts if json.loads(p.read_text()).get('complete')]
        live=successful[-1] if successful else attempts[-1] if attempts else HERE/f'live-{name}-v1.json'
        row['original_attempts']=[{'receipt':p.name,'complete':json.loads(p.read_text()).get('complete'),
            'error':json.loads(p.read_text()).get('error')} for p in attempts]
        if live.exists():
            r=json.loads(live.read_text());row['original']=dict(complete=r['complete'],action_verified=r.get('action_verified'),
                reopen_byte_equal=r.get('byte_stable_reopen'),error=r.get('error'),exe=r.get('exe'),
                offer_processed_on_load=r.get('offer_processed_on_load'))
            files=r['files'];source=ART/'exports-v1'/(name+'.SAV')
            row['original_comparisons']={}
            if 'immediate' in files:row['original_comparisons']['export_immediate']=prior.savcompare(source,ART/files['immediate']['file'])
            if 'order' in files:row['original_comparisons']['action']=prior.savcompare(ART/files['immediate']['file'],ART/files['order']['file'])
            if 'reopen' in files:row['original_comparisons']['reopen']=prior.savcompare(ART/files['order']['file'],ART/files['reopen']['file'])
            version='v2' if (HERE/('return-'+name+'-v2.json')).exists() else 'v1'
            ret=command('return-'+name+'-'+version);cont=command('continue-'+name+'-'+version);reexport=command('reexport-'+name+'-'+version);rp=command('reexport-policy-'+name+'-'+version)
            row['return_success']=ret is not None and ret['returncode']==0
            row['return_continuation']=cont;row['return_reexport_success']=reexport is not None and reexport['returncode']==0
            row['return_policy_pass']=rp is not None and rp['returncode']==0
            returned=(ART/files['reopen']['file']).parent/('returned'+('' if version=='v1' else '-'+version)+'.json') if 'reopen' in files else ART/'absent.json'
            predicted=ART/'exports-v1'/(name+'-predicted.json')
            if returned.exists() and predicted.exists():
                a,_=native(predicted,True);b,_=native(returned,True)
                row['action_differential_differences']=differences(a,b)
                row['action_differential_random']=case['originalAction']['kind'] in ('end-turn','siege','attack-fleet','field-battle')
        else:row['original']={'complete':False,'not_run':True}
        rows.append(row)
    return rows

if __name__=='__main__':
    rows=compare();target=HERE/sys.argv[1]
    with target.open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
    from collections import Counter
    print('Cases',len(rows),'original complete',sum(r['original']['complete'] for r in rows),'returned',sum(r.get('return_success',False) for r in rows))
    for r in rows:
        if r.get('original',{}).get('error'):print('ORIGINAL ISSUE',r['case']['name'],r['original']['error']['message'])
        if r.get('action_differential_differences') and not r.get('action_differential_random'):
            print('DETERMINISTIC DIFFERENCE',r['case']['name'],len(r['action_differential_differences']))
