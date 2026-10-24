"""Check retained corpus against pinned archive; only aggregate identity public."""
import argparse,hashlib,json,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'runs/experiments/data/run-exp-battle-current157';B=ROOT/'artifacts/run-exp-battle-current157'
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--version',required=True);a=p.parse_args()
count=0
with tarfile.open(a.archive) as tf:
 for m in tf:
  rel=Path(*Path(m.name).parts[1:])
  if not m.isfile() or not rel.parts or rel.parts[0]!='battles':continue
  assert (a.fixtures/rel).read_bytes()==tf.extractfile(m).read();count+=1
assert count==5862
assert hashlib.sha256((a.fixtures/'Imperial Conquest 2.dat').read_bytes()).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
source=B/'source-v1';registry=json.loads((source/'tests/IC2.Engine.Tests/Battle/Tactical/GoldenMaster/KnownFailures.json').read_text());assert not registry
ns={'t':'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'};tree=ET.parse(B/'private/tactical-tests-v1/tactical.trx');c=tree.find('.//t:ResultSummary/t:Counters',ns);assert c is not None
counters={k:int(v) for k,v in c.attrib.items()};assert counters['total']==counters['passed']==2420 and counters['failed']==counters['notExecuted']==0
r=dict(retained_battle_files_equal_pinned_archive=count,original_DAT_pin_equal=True,expected_failure_registry_entries=len(registry),tactical_test_counts=counters,owner_paths_hashes_traces_published=False,scope='read-only input integrity after tests; no Original/Wine game, fixture edit or Windows acceptance')
with (D/('input-test-gates-'+a.version+'.json')).open('x') as f:json.dump(r,f,indent=2)
print('PASS5862 unchanged retained battle files, original DAT pin, empty registry and2420tactical tests/0skip')
