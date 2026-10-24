"""Fresh recovery, verify every member, rerun retained compiled native tools."""
import argparse,hashlib,json,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument("--version",required=True);a=p.parse_args()
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];B=ROOT/'artifacts/run-exp-strategic-tracks';D=ROOT/'runs/experiments/data/run-exp-strategic-tracks';out=B/('recovery-'+a.version);out.mkdir(exist_ok=False)
with tarfile.open(B/'strategic-tracks-batch01.tar.gz') as tar:
 for item in tar.getmembers():
  p=Path(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 tar.extractall(out,filter='data')
manifest=json.loads((out/'manifest.json').read_text())
for row in manifest:assert hashlib.sha256((out/row['name']).read_bytes()).hexdigest()==row['sha256']
dotnet='/home/diego/.dotnet/dotnet';rows=[]
for tool,source,ledger,expected,label in [('Tracks.dll','phase-replay-v1','phase-facts-v1.json','native-phases-v2.json','phases'),('FleetChecks.dll','fleet-controls-v3','fleet-original-v3.json','fleet-native-v3.json','fleet')]:
 target=out/('replayed-'+label+'.json')
 subprocess.run([dotnet,str(out/'tools'/tool),str(out),str(out/source),str(out/'data-text'/ledger),str(out/('states-'+label)),str(target)],check=True)
 assert target.read_bytes()==(D/expected).read_bytes(),label+' differed'
 rows.append(dict(tool=tool,rows=len(json.loads(target.read_text())),result_byte_equal=True))
with (D/('recovery-verification-'+a.version+'.json')).open('x') as f:json.dump(dict(all_member_hashes_verified=len(manifest),compiled_native_replays=rows,no_original_or_owner_assets_used=True),f,indent=2)
print('PASS fresh recovery hashes and retained compiled native result identity')
