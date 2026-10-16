"""Build state observer into a NEW game folder; retain the prior game folder and every save."""
import hashlib,json,shutil,sys,time
from pathlib import Path
import observer as O
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace';ART=ROOT/'artifacts/run-exp-tactical25-trace';work=Path(sys.argv[1]);g=work/'prefix/drive_c/IC2'
assert str(work).startswith('/tmp/ic2-tactical25-trace-')
cpu=json.loads(Path(sys.argv[2]).read_text());assert cpu['exit']==0 and cpu['observer_sha256']==hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest() and len(cpu['snapshot_payload_cases'])==18
stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime());archive=g.with_name('IC2-standard-'+stamp)
raw=Path('/home/diego/ic2-work/build/Imperial Conquest 2 lab s1.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()=='06bc469dff70ae8c83438e82ef4266a584bab7796752024521d00f8d8d46ec40'
b=bytearray(raw);info=O.apply(b)
g.rename(archive);g.mkdir()
for p in archive.iterdir():
 if p.is_file() and (p.suffix.lower() in ['.dat','.hlp','.cnt','.ini','.dll','.bmp'] or p.name in ['MIX-RG_start.SAV','SEED.TXT']):shutil.copy2(p,g/p.name)
 if p.name.upper()=='WAVS':shutil.copytree(p,g/p.name)
name='Imperial Conquest 2 tactical25 state.exe'
with (g/name).open('xb') as f:f.write(b)
art=ART/('state-observer-'+stamp+'.exe')
with art.open('xb') as f:f.write(b)
hash_=hashlib.sha256(b).hexdigest()
with (DATA/'SAVES.sha256').open('a') as f:f.write(hash_+'  '+art.name+'\n')
rec=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),exe_sha256=hash_,exe_name=name,artifact=art.name,source_lab_sha256=hashlib.sha256(raw).hexdigest(),observer_sha256=hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest(),info=info,cpu_evidence=str(Path(sys.argv[2]).name),prior_game_folder_retained=str(archive),start_sha256=hashlib.sha256((g/'MIX-RG_start.SAV').read_bytes()).hexdigest(),dat_sha256=hashlib.sha256((g/'Imperial Conquest 2.dat').read_bytes()).hexdigest())
with (DATA/('build-'+stamp+'.json')).open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(json.dumps(dict(exe=name,artifact=art.name,sha256=hash_)))
