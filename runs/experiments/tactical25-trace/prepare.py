"""Prepare a private prefix/game folder; no original files or old measurements are written."""
import hashlib,json,shutil,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'));import battle_hook as H
work=Path(sys.argv[1]);prefix=work/'prefix';source=Path('/tmp/ic2-ai-general-work/prefix')
assert str(work).startswith('/tmp/ic2-tactical25-trace-')
work.mkdir(exist_ok=False)
def ignore(path,names):return ['IC2'] if Path(path)==source/'drive_c' else []
shutil.copytree(source,prefix,symlinks=True,ignore=ignore)
g=prefix/'drive_c/IC2';g.mkdir()
assets=Path('/home/diego/ic2-work/prefix/drive_c/IC2')
for p in assets.iterdir():
 if p.is_file() and p.suffix.lower() in ('.dat','.hlp','.cnt','.ini','.dll','.bmp'):shutil.copy2(p,g/p.name)
 if p.name.upper()=='WAVS':shutil.copytree(p,g/p.name)
plain=Path('/home/diego/ic2-work/build/Imperial Conquest 2 lab s1.exe');raw=plain.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='06bc469dff70ae8c83438e82ef4266a584bab7796752024521d00f8d8d46ec40'
(g/plain.name).write_bytes(raw);b=bytearray(raw)
info=H.apply(b,1,SimpleNamespace(BATTLE_START_CALL=0x45c1ae,SEED_CAVE=0x564400,TBATTLE_START=0x436fb4))
(g/'Imperial Conquest 2 tactical25 standard.exe').write_bytes(b)
source_save=Path('/tmp/ic2-build-fixtures/battles/starts/FLD-RG_0743_rome_army0_at_86_28.SAV');shutil.copy2(source_save,g/'MIX-RG_start.SAV')
(g/'SEED.TXT').write_text('1\n')
rec=dict(work=str(work),source_prefix=str(source),source_save_sha256=hashlib.sha256(source_save.read_bytes()).hexdigest(),plain_sha256=hashlib.sha256(raw).hexdigest(),hook_sha256=hashlib.sha256(b).hexdigest(),info=info,game_files=sorted(p.name for p in g.iterdir()))
stamp=time.strftime('%Y%m%d-%H%M%S');out=ROOT/'runs/experiments/data/run-exp-tactical25-trace'/('prepare-'+stamp+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out)
