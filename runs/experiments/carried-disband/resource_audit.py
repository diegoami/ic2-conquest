from pathlib import Path
import sys,re,json,argparse
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args()
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'runs/experiments/feature_inventory'));import extract_forms as ef
b=(R/'artifacts/run-exp-restrictions85/work-v1/prefix/drive_c/IC2/Imperial Conquest 2.exe').read_bytes();out=[]
for match in re.finditer(b'TPF0',b):
 try:o=ef.obj(ef.P(b,match.start()+4))
 except Exception:continue
 if o['class']not in ['TPremierForm','TUnitMap','TInformation','TChangeArmyUnits']:continue
 def visit(obj,path):
  props=obj['props'];events={k:v for k,v in props.items()if k.startswith('On')}
  if events or obj['class']=='TMenuItem' and ('Disband' in props.get('Caption','')or props.get('ShortCut',0)):
   out.append(dict(form=o['class'],control=obj['name'],cls=obj['class'],path=path,caption=props.get('Caption'),shortcut=props.get('ShortCut'),events=events))
  for c in obj['children']:visit(c,path+[obj['name']])
 visit(o,[])
p=R/'runs/experiments/data/run-exp-carried-disband/resource-callbacks-v1.json'
with p.open('x')as f:json.dump(out,f,indent=2)
print('bounded resources:',len(out),'event/shortcut rows')
for row in out:
 if row['form']=='TInformation'or row['caption']=='Disband army':print(row)
