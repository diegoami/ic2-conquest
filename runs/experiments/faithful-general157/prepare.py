"""Prepare a narrow reviewable engine patch without writing another checkout."""
import base64
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path('/home/diego/projects/imperial_conquest_2')
DATA=ROOT/'runs/experiments/data/run-exp-faithful-general157'
ART=ROOT/'artifacts/run-exp-faithful-general157'
OVERLAY=ART/'source-v2'
PIN='8e5f0a35c9dd45a8ec31b38154406843b131013a'
DATA.mkdir(parents=True,exist_ok=True)
OVERLAY.mkdir(parents=True,exist_ok=False)
paths=['GeneralOrders.cs','GeneralPassTwo.cs','GeneralPassThree.cs','ComputerGeneral.cs']
rows=[]
patch=[]
for name in paths:
    rel='src/IC2.Engine/Battle/Tactical/General/'+name
    item=json.loads(subprocess.check_output(['gh','api',f'repos/diegoami/imperial_conquest_2/contents/{rel}?ref={PIN}']))
    blob=json.loads(subprocess.check_output(['gh','api',f'repos/diegoami/imperial_conquest_2/git/blobs/{item["sha"]}']))
    raw=base64.b64decode(blob['content'])
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==item['sha']
    assert raw==(SOURCE/rel).read_bytes(), 'Source differs from pinned main: '+rel
    # Latin1 is a reversible byte mapping; preserve the upstream mixed encodings.
    text=raw.decode('latin1')
    if name=='GeneralOrders.cs':
        text=text.replace("The general's units, in its iteration order:","Pass one's units, in type order:")
        insertion='''
    /// <summary>The later passes visit live units in ascending slot order (FUN_0043A544/FUN_0043ABB4).</summary>
    internal static IEnumerable<int> InSlotOrder(TacticalBoard board)
    {
        var first = board.FirstSlotOf(board.SideToMove);
        for (var slot = first; slot < first + board.SlotsPerSide; slot++)
        {
            if (board.IsOver)
            {
                yield break;
            }

            if (board.IsLive(slot))
            {
                yield return slot;
            }
        }
    }
'''
        text=text.removesuffix('}\n')+insertion+'}\n'
    elif name in ['GeneralPassTwo.cs','GeneralPassThree.cs']:
        expected=1 if name=='GeneralPassTwo.cs' else 4
        assert text.count('GeneralOrders.InOrder(board)')==expected
        text=text.replace('GeneralOrders.InOrder(board)','GeneralOrders.InSlotOrder(board)')
        text=text.replace('For each unit, in the general\'s order,','For each unit, in ascending slot order,')
        text=text.replace("For each of the general's units, in its order,","For each of the general's units, in ascending slot order,")
    else:
        old='pass 2, the flank, pass 2 again), each over all the units in the same order.'
        assert old in text
        text=text.replace(old,'pass 2, the flank, pass 2 again). These later passes visit live units in ascending slot order.')
    changed=text.encode('latin1')
    assert changed!=raw
    with (OVERLAY/name).open('xb') as f:f.write(changed)
    patch.extend(difflib.diff_bytes(difflib.unified_diff,raw.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile=('a/'+rel).encode(),tofile=('b/'+rel).encode()))
    rows.append(dict(path=rel,original_git_blob=item['sha'],original_sha256=hashlib.sha256(raw).hexdigest(),patched_sha256=hashlib.sha256(changed).hexdigest()))
with (DATA/'faithful-general.patch').open('xb') as f:f.write(b''.join(patch))
targets=['<Project>',f'  <Import Project="{ROOT}/runs/experiments/data/run-exp-sav-conversion-broad153/overlay.targets" />',
         '  <Target Name="UseFaithfulGeneralSources" BeforeTargets="CoreCompile">',
         '    <ItemGroup Condition="\'$(MSBuildProjectName)\' == \'IC2.Engine\'">']
for name in paths:
    targets.extend([f'      <Compile Remove="Battle/Tactical/General/{name}" />',f'      <Compile Include="{OVERLAY/name}" />'])
targets.extend(['    </ItemGroup>','  </Target>','</Project>'])
with (DATA/'overlay-v2.targets').open('x') as f:f.write('\n'.join(targets)+'\n')
with (DATA/'source-pin-v2.json').open('x') as f:json.dump(dict(remake_main=PIN,files=rows,other_checkout_written=False,change='First pass remains type order; later passes and their public helper entrypoints use live slot order. No combat rule or setting added.'),f,indent=2);f.write('\n')
print('Prepared guarded four-file faithful patch and compile overlay')
