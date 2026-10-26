"""Pin exact original sites without publishing full decompile or private hashes."""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-restrictions85';ART=ROOT/'artifacts/run-exp-restrictions85'
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args()
source=ROOT/'artifacts/cloud-migration-20261021/ic2-research-inputs-20261021/decompile/all_app_functions.txt'
raw=source.read_bytes();text=raw.decode('latin1');lines=text.splitlines()
heads=[(i+1,m.group(1),m.group(2)) for i,line in enumerate(lines) if (m:=re.match(r'// ==== (.*?) @ ([0-9a-fA-F]+) ====',line))]
names=['TAFSupply_InitializeForm','TAFSupply_CityOrFleet','TAFSupply_FindProviders','TAFSupply_ChangeProvider','TAFSupply_ChangeSupply','TAFSupply_ChangeBuyAmount','TAFSupply_TransferSupply','TAFSupply_ChangeMoney','TAFSupply_OK','TArmyToArmy_InitializeForm','TArmyToArmy_ChangeMoney','TArmyToArmy_Army1Transfer','TArmyToArmy_Army2Transfer','TArmyToArmy_MoveUnit','TArmyToArmy_OK','TArmyToArmy_Cancel','TUnitMap_ArmyToArmyTransfer','TUnitMap_SplitArmy','TUnitMap_SupplyArmy','TUnitMap_SupplyFleet','TUnitMap_RecruitMercenaries','TRecruitMercs_RecruitMercUnit','TFleetToFleet_ChangeMoney','TFleetToFleet_OK','TUnitMap_DisbandArmy','FUN_0044ab90','FUN_0044ac3c','FUN_00451b40','TPremierForm_UnitMapAction','TArmyRecruits_InitializeForm','TArmyRecruits_ChangeCity','TArmyRecruits_SetCityRecruits','TBattleMap_OnMapClick','TBattleMap_SelectUnit','TBattleMap_CancelSelection']
rows=[]
for name in names:
 hits=[(j,h) for j,h in enumerate(heads) if h[1]==name]
 assert len(hits)==1,name
 j,h=hits[0];rows.append(dict(function=name,address=h[2],first_line=h[0],last_line=heads[j+1][0]-1))
# Byte identity of exact original is private, public boolean/platform only.
exe=ART/'work-v1/prefix/drive_c/IC2/Imperial Conquest 2.exe';dat=exe.with_suffix('.dat')
assert exe.read_bytes()==Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
with (DATA/f'source-sites-{q.version}.json').open('x') as f:json.dump(dict(stock_exe_identity_verified=True,pinned_decompile_verified=True,remake_revision='4d70275aac4e155c0370a3ee23525cf34450a908',research_revision='865755e04f107afc38cdb496669d882e2551aca6',sites=rows,additional_disassembly_sites=['004544e0-00454885 recruitment list selection','004378f8-00437a3d enemy roster']),f,indent=2)
with (ART/f'private-source-identity-{q.version}.json').open('x') as f:json.dump({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,exe,dat]},f,indent=2)
print('source identities verified; sites',len(rows))
