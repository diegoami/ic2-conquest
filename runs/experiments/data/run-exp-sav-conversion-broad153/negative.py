"""Converter/input refusals and explicitly synthetic format-4 migration."""
import copy,hashlib,json,sys
from offline import ART,HERE,ROOT,DOTNET,CLI,PROBE,REMAKE,TEMPLATE,run,convert

source=json.loads((ART/'native-v1/S00-rome.json').read_text())
folder=ART/'negative-v1';folder.mkdir()
cases=[]
def case(name,mutate):
    doc=copy.deepcopy(source);mutate(doc)
    src=folder/(name+'.json');dst=folder/(name+'.SAV')
    with src.open('x') as f:json.dump(doc,f)
    before=hashlib.sha256(src.read_bytes()).hexdigest()
    result=run('refusal-'+name+'-v1',[DOTNET,CLI,'--export-sav',src,'--output',dst,'--template',TEMPLATE])
    cases.append(dict(name=name,returncode=result.returncode,output_written=dst.exists(),input_unchanged=hashlib.sha256(src.read_bytes()).hexdigest()==before,
                      stderr=result.stderr))
case('N00-improved',lambda d:(d['save'].__setitem__('rulesetId','improved'),d['save']['state'].__setitem__('rulesetId','improved')))
case('N01-name24',lambda d:d['save']['state']['armies'][0]['units'][0].__setitem__('name','N'*24))
case('N02-nonlatin',lambda d:d['save']['state']['armies'][0]['units'][0].__setitem__('name','Unit \U0001f600'))
case('N03-int16-money',lambda d:d['save']['state']['armies'][0].__setitem__('money',40000))
case('N04-missing-allegiance',lambda d:d['save']['state']['cities'][0].__setitem__('allegiance',None))
case('N05-unknown-reference',lambda d:d['save']['state']['nations'][0].__setitem__('recruitmentSlots',[dict(targetCityId='atlantis',unitTypeId='archers',troops=1000,stateCode=0)]))
case('N06-other-scenario',lambda d:(d['save'].__setitem__('scenarioId','other-scenario'),d['save']['state'].__setitem__('scenarioId','other-scenario')))
case('N07-dangling-cargo',lambda d:d['save']['state']['armies'][0].__setitem__('aboardFleetId','absent-fleet'))
case('N08-future-version',lambda d:d.__setitem__('saveFormatVersion',999))
open_save=folder/'N09-open-battle.json'
result=run('generate-open-battle-v1',[DOTNET,PROBE,'open-battle',REMAKE,open_save])
if result.returncode==0:
    dst=folder/'N09-open-battle.SAV'
    result=run('refusal-N09-open-battle-v1',[DOTNET,CLI,'--export-sav',open_save,'--output',dst,'--template',TEMPLATE])
    cases.append(dict(name='N09-open-battle',returncode=result.returncode,output_written=dst.exists(),stderr=result.stderr))
existing=ART/'exports-v1/S00-rome.SAV'
before=hashlib.sha256(existing.read_bytes()).hexdigest()
result=run('refusal-N10-overwrite-v1',[DOTNET,CLI,'--export-sav',ART/'native-v1/S00-rome.json','--output',existing,'--template',TEMPLATE])
cases.append(dict(name='N10-overwrite',returncode=result.returncode,input_unchanged=hashlib.sha256(existing.read_bytes()).hexdigest()==before,stderr=result.stderr))
with (HERE/'negative-summary-v1.json').open('x') as f:json.dump(cases,f,indent=2);f.write('\n')

# Synthetic v4-shaped input: exercise real migrations; not an owner legacy save.
legacy=copy.deepcopy(source);legacy['saveFormatVersion']=4
legacy['save']['state'].pop('roughSeaCells',None)
for city in legacy['save']['state']['cities']:city['underSiege']=False
name='M00-format4';path=ART/'native-v1'/(name+'.json')
with path.open('x') as f:json.dump(legacy,f)
record=json.loads((ART/'native-v1/manifest.jsonl').read_text().splitlines()[0])
record.update(name=name,category='migration',provenance='synthetic v4-shaped JSON derived from S00, roughSeaCells removed and old underSiege fields added; actual SaveManager v4->v7 migration')
with (ART/'native-v1/manifest.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
convert(record)
