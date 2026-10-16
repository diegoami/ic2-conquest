"""Run the pinned production comparison; append unique evidence, never edit fixtures/rules."""
import argparse, datetime, hashlib, json, os, subprocess
from pathlib import Path
from xml.sax.saxutils import escape
p=argparse.ArgumentParser();p.add_argument('--build-root',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--draw-phases',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[3];build=a.build_root.resolve();fixtures=a.fixtures.resolve()
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
assert git(build,'rev-parse','HEAD')=='257f2d2cd7510451d229a983553a54b89065b06c'
assert git(build,'status','--porcelain')=='', 'comparison source must be clean'
assert git(fixtures,'rev-parse','HEAD')=='6319802a75067e7730e4f6a27dce3b4e296ddd9b'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
out=root/'runs/experiments/data/run-exp-tactical25'/('phases-'+stamp);out_parent=out.parent
runner=build/'rendered'/('tactical25-phases-'+stamp);runner.mkdir(parents=True)
project=runner/'Observe.csproj';code=Path(__file__).with_name('Observe.cs')
project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><ProjectReference Include="'+escape(str(build/'tests/IC2.Engine.Tests/IC2.Engine.Tests.csproj'))+'"/><Compile Include="'+escape(str(code))+'"/></ItemGroup></Project>')
env=dict(os.environ,IC2_FIXTURES_DIR=str(fixtures),PATH='/tmp/ic2-dotnet:/tmp/ic2-pwsh:'+os.environ['PATH'])
if a.draw_phases:env['IC2_OBSERVE_FIRST_DRAW']='1'
log=out_parent/('phases-'+stamp+'.log')
meta={'build_head':git(build,'rev-parse','HEAD'),'fixtures_head':git(fixtures,'rev-parse','HEAD'),'capture_source_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':out.name,'draw_phases':a.draw_phases,'no_fixture_or_rule_edits':True}
with log.open('x') as f:rc=subprocess.run(['dotnet','run','--project',str(project),'--',str(root/'runs/experiments/data/run-exp-tactical25/production-20261016-174818/summary.json'),str(out)],cwd=build,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
meta['exit']=rc;meta['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
meta['source_clean_after']=git(build,'status','--porcelain')==''
with (out_parent/('phases-'+stamp+'-manifest.json')).open('x') as f:json.dump(meta,f,indent=2);f.write('\n')
print(json.dumps(meta,indent=2));raise SystemExit(rc)
