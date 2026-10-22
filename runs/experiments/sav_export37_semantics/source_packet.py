"""Exact original lines encoded in JSON so source whitespace stays unchanged."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt');raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
lines=raw.decode().splitlines();starts=[(i,m.group(1),m.group(2)) for i,s in enumerate(lines) if (m:=re.search(r'// ==== (.+?) @ ([0-9a-fA-F]+) ====',s))]
names={'TChangeTax_InitializeForm','TChangeTax_PrintNewNumbers','TChangeTax_SetNewTax','TChangeTax_OK','TPremierForm_RefreshForms','TUnitMap_PaintForm','TUnitMap_SelectUnit','TUnitMap_InitializeForm','TPremierForm_StartTurn','TPremierForm_StoreFormPositions','TInformation_ShowNationStatus','TInformation_PrintInfo','TInformation_PaintForm','TAreaMap_UnitMapCursor','TRenameArmyUnit_OK','TChangeArmyUnits_InitializeForm','TChangeArmyUnits_OK','TChangeArmyUnits_RenameUnit','TUnitMap_UpdateUMSelection','TUnitMap_ChangeUnitDetails','FUN_00405b54','FUN_00405b88','FUN_00403634','FUN_0042313c','FUN_00416360','FUN_0041633c','FUN_00449f08','FUN_0044a004','FUN_0044a050','FUN_0044a218','FUN_0044a66c','FUN_0044a698','FUN_0044d9a8','FUN_004484d0','TUnitMap_PrintMapSquare','TUnitMap_AreaMapClicked'}
records=[]
for k,(i,name,at) in enumerate(starts):
 if name in names:
  end=starts[k+1][0] if k+1<len(starts) else len(lines)
  records.append(dict(name=name,address=at,first_line=i+1,last_line=end,lines=[dict(number=n+1,text=lines[n]) for n in range(i,end)]))
assert {r['name'] for r in records}==names
with a.output.open('x') as f:json.dump(dict(source_sha256=hashlib.sha256(raw).hexdigest(),method='Exact source lines as JSON string values; no stripping or source changes.',records=records),f,indent=2);f.write('\n')
print(json.dumps(dict(functions=len(records),lines=sum(len(r['lines']) for r in records))))
