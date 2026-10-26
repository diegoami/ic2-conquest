"""Create isolated stock-original Wine context. Does not launch the game.
Never overwrites an existing context; symlinks are preserved, never followed.
"""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[3]
source=R/'artifacts/run-exp-manual-funding1456/work-v1';dest=R/'artifacts/run-exp-restrictions85/work-v1'
assert not dest.exists()
dest.mkdir(parents=True)
shutil.copytree(source/'prefix',dest/'prefix',symlinks=True,ignore=shutil.ignore_patterns('*.SAV','*.sav','*.png','*.log','*.LOG'))
for name in ['toolbar.json','army_toolbar.json','fleet_toolbar.json','win_controls.exe','funding-controls.exe']:shutil.copy2(source/name,dest/name)
with (dest/'private-identity.json').open('x') as f:
 json.dump({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (dest/'prefix/drive_c/IC2').glob('*.exe')},f,indent=2)
