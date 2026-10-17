"""Read immutable hostile saves, verify published hashes, retain parsed before/after."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
from state import sav
art=root.parent.parent/'resupply31/artifacts'
manifest={n:h for h,n in (line.split(None,1) for line in (root/'runs/experiments/data/run-exp-resupply31/SAVES.sha256').read_text().splitlines())}
rows=[]
for stem in ('land-war-20261017-083008-11228','aboard-war-20261017-084100-17426','fleet-war-20261017-084059-17272'):
 row=dict(stem=stem,provenance='Existing staged Wine observations, redecoded; no new execution',states={})
 for kind in ('input','loaded','post'):
  name=stem+'-'+kind+'.SAV';raw=(art/name).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==manifest[name]
  s=sav.parse(raw);row['states'][kind]=dict(filename=name,sha256=h,parsed=s)
 before=row['states']['loaded']['parsed'];after=row['states']['post']['parsed']
 row['nation_changes']={k:[before['nations'][0][k],after['nations'][0][k]] for k in before['nations'][0] if before['nations'][0][k]!=after['nations'][0][k]}
 assert before['cities']==after['cities']
 assert before['turn']==after['turn']==734
 assert before['current_nation']==13 and after['current_nation']==11
 assert all(row['states']['input']['parsed'][k]==before[k] for k in ('cities','armies','fleets','nations'))
 rows.append(row)
output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True)
with output.open('x') as out:json.dump(dict(rows=rows),out,indent=2);out.write('\n')
print('PASS9 immutable save hashes;3 loaded-state controls;3 unchanged city tables')
