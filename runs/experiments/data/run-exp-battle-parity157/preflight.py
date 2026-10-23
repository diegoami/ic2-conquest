"""Read-only instrumentation preflight; no game launch or fixture mutation."""
import datetime,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def run(name,args):
 out=HERE/(name+'.json')
 if out.exists():raise RuntimeError('Prior measurement preserved: '+name)
 result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
 with out.open('x') as f:json.dump(dict(argv=args,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr),f,indent=2);f.write('\n')
 print(name,'exit',result.returncode,flush=True)
 print(result.stdout[-1500:],result.stderr[-800:],flush=True)
 return result
if __name__=='__main__':
 run('hook-build-reader-v1',[sys.executable,'-m','tests.test_battle_hook_build'])
 run('hook-register-inertness-v1',[sys.executable,'-m','tests.test_battle_hook_caves'])
 sources=['patches/battle_hook.py','patches/battle_lab.py','state/hook_log.py',
          'runs/experiments/tactical25/original_phase.py','runs/experiments/data/run-exp-battle1355/audit_private.py']
 availability=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  python=sys.version.split()[0],unicorn=importlib.util.find_spec('unicorn') is not None,
  source_hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources},
  fixture_env_configured=bool(os.environ.get('IC2_FIXTURES_DIR')),
  standard_golden_fixture_checkout_exists=Path('/home/diego/projects/ic2-test-fixtures').exists(),
  old_hook_covers='RNG14sites + shot/melee/rout entry markers + start/clear/reseed boundaries',
  missing_exact_log_fields=['all movement/placement entry-exit state','original chosen AI aim/pass/claims at each decision','atomic complete before/after grid for each exchange'],
  owner_baseline='Existing private1355 inputs/traces preserved; no private hashes included',
  latest_remake_main='8e5f0a35c9dd45a8ec31b38154406843b131013a',
  previous_battle_engine='ae614899d63ac721ee46d1e3213191fe1f43a676',
  change_since='PR1356 presentation/readability only; production tactical sources unchanged in compareAPI')
 with (HERE/'tracing-capability-v1.json').open('x') as f:json.dump(availability,f,indent=2);f.write('\n')
