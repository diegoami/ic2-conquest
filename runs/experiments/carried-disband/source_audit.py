"""Record exact original caller sites and bounded selection-writer inventory.
No full original source/bytes/private hashes published. Unique version mandatory.
"""
from pathlib import Path
import argparse,re,json,hashlib,sys
R=Path(__file__).resolve().parents[3];D=R/'runs/experiments/data/run-exp-carried-disband';A=R/'artifacts/run-exp-carried-disband'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args()
raw=(R/'artifacts/cloud-migration-20261021/ic2-research-inputs-20261021/decompile/all_app_functions.txt').read_bytes();lines=raw.decode('latin1').splitlines()
assert hashlib.sha256(raw).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
heads=[(i+1,m[1],m[2]) for i,line in enumerate(lines) if (m:=re.match(r'// ==== (.*?) @ ([0-9a-fA-F]+) ====',line))]
names=['TUnitMap_PaintForm','TUnitMap_SelectUnit','TUnitMap_UnitMapClick','TUnitMap_AreaMapClicked','TUnitMap_CancelSelection','TUnitMap_KeyPressed','TUnitMap_EndUMSelection','TUnitMap_UpdateUMSelection','TUnitMap_DisbandArmy','TUnitMap_SupplyArmy','TUnitMap_RecruitMercenaries','TUnitMap_ChangeUnitDetails','TUnitMap_ArmyToArmyTransfer','TUnitMap_SplitArmy','TPremierForm_UnitMapAction','TPremierForm_KeyPressed','TInformation_KeyPressed','TInformation_ShowFleetUnits','TChangeArmyUnits_InitializeForm','TChangeArmyUnits_Disband','TChangeArmyUnits_RemoveUnit','TChangeArmyUnits_OK','TChangeArmyUnits_Cancel','TArmyToArmy_OK','TArmyToArmy_Cancel','FUN_0044ab90']
sites=[]
for n in names:
 hits=[(j,h)for j,h in enumerate(heads)if h[1]==n];assert len(hits)==1,n
 j,h=hits[0];sites.append(dict(function=n,address=h[2],first_line=h[0],last_line=heads[j+1][0]-1))
# Syntactic candidates only, not whole-program pointer/indirect-store absence proof.
refs=[]
for i,line in enumerate(lines,1):
 if not ('0x220' in line or '0x88' in line):continue
 if not re.search(r'\)\s*=(?!=)|\]\s*=(?!=)',line):continue
 head=next((h for h in reversed(heads)if h[0]<=i),None)
 if head and (head[1].startswith('TUnitMap_')or head[1]=='TArmyToArmy_OK'):
  refs.append(dict(line=i,function=head[1],address=head[2],kind='syntactic store candidate, aliases/context manually reviewed'))
obj=dict(original_listing_identity_verified=True,sites=sites,selection_store_candidates=refs,limits=['bounded named-handler audit; not exhaustive indirect-pointer/VCL reentrancy proof','disband last-unit in Change units vs Army transfer are distinct commit/cleanup paths','no new Original run by this static audit'])
with (D/f'source-sites-{q.version}.json').open('x')as f:json.dump(obj,f,indent=2)
with (A/f'private-source-identity-{q.version}.json').open('x')as f:json.dump(dict(listing_sha256=hashlib.sha256(raw).hexdigest()),f,indent=2)
print('located',len(sites),'sites;',len(refs),'store candidates')
