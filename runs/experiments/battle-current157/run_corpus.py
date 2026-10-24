"""Fresh current-Main strict replay; full trial/error details remain private."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];B=ROOT/'artifacts/run-exp-battle-current157';D=ROOT/'runs/experiments/data/run-exp-battle-current157'
p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--version',required=True);p.add_argument('--fixed-only',action='store_true');a=p.parse_args()
out=B/'private'/('corpus-'+a.version);out.mkdir(parents=True,exist_ok=False)
harness=B/('harness-'+a.version);harness.mkdir();(harness/'IC2.sln').write_text('# Task-owned asset discovery marker; source/fixtures unchanged\n');(harness/'data').symlink_to(B/'source-v1/data',target_is_directory=True)
shutil.copytree(ROOT/'runs/experiments/battle-current157/bin/Debug/net10.0',harness/'bin')
command=['/home/diego/.dotnet/dotnet',str(harness/'bin/Corpus.dll'),str(out/'rows.jsonl'),str(out/'summary.json')]
if a.fixed_only:command.append('--fixed-only')
with (out/'execution.log').open('x') as f:result=subprocess.run(command,env=dict(os.environ,IC2_FIXTURES_DIR=str(a.fixtures.resolve())),stdout=f,stderr=subprocess.STDOUT)
if (out/'summary.json').exists():
 raw=json.loads((out/'summary.json').read_text());keys=['fixedCases','passed','failed'] if a.fixed_only else ['trials','statePass','drawPass','failed'];counts={k:raw[k] for k in keys}
else:counts=dict(summary_missing=True)
receipt=dict(main_pin='b593c6e28939c1c7154f9a41d0436a8f14f352dc',returncode=result.returncode,counts=counts,registry_exemptions=False,tactical_overlay=False,original_fixtures_changed=False,fresh_engine_and_test_assembly=True,engine_sha256=hashlib.sha256((harness/'bin/IC2.Engine.dll').read_bytes()).hexdigest(),test_helpers_sha256=hashlib.sha256((harness/'bin/IC2.Engine.Tests.dll').read_bytes()).hexdigest(),private_details_published=False,scope='headless recorded tactical replay, not fresh game/strategic copy-in/native Windows or installed-desktop acceptance')
with (D/('corpus-'+a.version+'.json')).open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt));raise SystemExit(result.returncode)
