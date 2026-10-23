"""Isolate capture lifetime and missing live-target guard in local source copies."""
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'runs/experiments/data/run-exp-battle-residual157'
ART=ROOT/'artifacts/run-exp-battle-residual157'
SOURCE=Path('/home/diego/projects/imperial_conquest_2')
REL='src/IC2.Engine/Battle/Tactical/TacticalMovement.cs'
PIN='ea575e04e9d96f9e3dc6410c1b6edbb0f01b000b'
item=json.loads(subprocess.check_output(['gh','api',f'repos/diegoami/imperial_conquest_2/contents/{REL}?ref={PIN}']))
raw=(SOURCE/REL).read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['sha']
old=raw.decode('latin1')
anchor='''        var start = board.Slots[slot];
        var dx = x - start.X;'''
assert old.count(anchor)==1
header='''    private static bool ComputerChecks(TacticalBoard board, int slot, int x, int y)
    {
        var context = board.Context;
        while (true)
        {
            // #1324: the enemy is looked up only when the stored cell holds a unit code. The original
            // (FUN_00438D24) captures it once per walk; replaying that here matches three #1107 battles
            // but breaks two lc-ar-three trials, so the per-check lookup stays until research settles it.
            var enemy = CaptureDestinationEnemy(board, slot, x, y);'''
assert old.count(header)==1
rows=[]
for variant in ['cached-only','cached-live']:
    text=old.replace(anchor,'        var capturedEnemy = computer ? CaptureDestinationEnemy(board, slot, x, y) : -1;\n'+anchor)
    text=text.replace('ComputerChecks(board, slot, x, y)','ComputerChecks(board, slot, capturedEnemy)')
    text=text.replace(header,'''    private static bool ComputerChecks(TacticalBoard board, int slot, int enemy)
    {
        var context = board.Context;
        while (true)
        {''')
    if variant=='cached-live':
        line='if (distance <= context.RangeOf(unit.Type) && unit.Moves > 0 && unit.Shots > 0 && unit.Target < 0)'
        assert text.count(line)==1
        text=text.replace(line,'// FUN_00438D24, 0x438ED1: a captured target is fired on only while live.\n            '+line[:-1]+' && board.IsLive(enemy))')
    changed=text.encode('latin1')
    folder=ART/('source-'+variant+'-v1');folder.mkdir(parents=True,exist_ok=False)
    with (folder/'TacticalMovement.cs').open('xb') as f:f.write(changed)
    patch=b''.join(difflib.diff_bytes(difflib.unified_diff,raw.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile=('a/'+REL).encode(),tofile=('b/'+REL).encode()))
    with (DATA/('movement-'+variant+'.patch')).open('xb') as f:f.write(patch)
    targets=f'''<Project>
  <Import Project="{ROOT}/runs/experiments/data/run-exp-faithful-general157/overlay-v2.targets" />
  <Target Name="UseResidualMovementSource" BeforeTargets="CoreCompile">
    <ItemGroup Condition="'$(MSBuildProjectName)' == 'IC2.Engine'">
      <Compile Remove="Battle/Tactical/TacticalMovement.cs" />
      <Compile Include="{folder}/TacticalMovement.cs" />
    </ItemGroup>
  </Target>
</Project>
'''
    with (DATA/('overlay-'+variant+'-v1.targets')).open('x') as f:f.write(targets)
    rows.append(dict(variant=variant,source_sha256=hashlib.sha256(changed).hexdigest(),capture_once_per_walk=True,explicit_live_guard=variant=='cached-live'))
with (DATA/'variant-sources-v1.json').open('x') as f:json.dump(dict(main_pr_source_pin=PIN,original_git_blob=item['sha'],original_sha256=hashlib.sha256(raw).hexdigest(),variants=rows,other_checkout_written=False),f,indent=2);f.write('\n')
print('Prepared separate cached-only and cached+live-guard source controls',flush=True)
