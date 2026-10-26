"""Verify archived public remake sources against exact GitHub tree; exclusive receipt."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[3];pin='4d70275aac4e155c0370a3ee23525cf34450a908'
t=json.loads(subprocess.check_output(['gh','api',f'repos/diegoami/imperial_conquest_2/git/trees/{pin}?recursive=1']))
assert not t['truncated'];blobs={x['path']:x['sha'] for x in t['tree'] if x['type']=='blob'}
paths=['godot/UI/Dialogs/SupplyDialogModel.cs','godot/UI/Dialogs/ArmyDialogModels.cs','godot/UI/Dialogs/FleetCityDialogModels.cs','godot/UI/Dialogs/StrategyDialogModels.cs','godot/Screens/TacticalBattleViewModel.cs','src/IC2.Engine/Armies/Commands/ArmyTransferCommandHandler.cs','src/IC2.Engine/Naval/Commands/EmbarkArmyCommandHandler.cs','src/IC2.Engine/Recruitment/Commands/HireMercenaryCommandHandler.cs','src/IC2.Engine/Economy/Commands/TransferMoneyCommandHandler.cs','src/IC2.Engine/Naval/Commands/FleetToFleetTransferCommandHandler.cs','src/IC2.Engine/Armies/Commands/DisbandArmyCommandHandler.cs','src/IC2.Engine/Economy/QuarterlyEconomySystem.cs','data/rulesets/classical-faithful.json']
rows=[]
for path in paths:
 b=(R/'artifacts/run-exp-restrictions85/remake4d70275a'/path).read_bytes();sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert sha==blobs[path],path
 rows.append(dict(path=path,git_blob=sha))
with (R/'runs/experiments/data/run-exp-restrictions85/native-source-verified-v1.json').open('x') as f:json.dump(dict(pin=pin,authoritative_tree_verified=True,rows=rows),f,indent=2)
print('verified',len(rows),'public source blobs')
