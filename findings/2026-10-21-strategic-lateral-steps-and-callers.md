# Strategic lateral steps: exact ties, endpoint exception and callers

**Status:** draft for research #42/build #1012, source and bounded original-x86
controls; no new Wine/native Windows execution or remake/fixture changes.

## Answer

The strategic step selects the cheapest of the line cursor and two alternatives,
but switches away from the line only for a strictly cheaper alternative. Equal
alternatives favor the first candidate AFTER the major-axis swap. If the cursor
is the final destination, the step bypasses alternative selection entirely.
Affordability is tested after selecting the candidate. Human/AI armies share
the army walker/step; fleets have a separate walker/step with parallel selection
and sea-only costs. Caller wrappers and destination interactions differ.

The original-instruction controls reproduce the old far/near endpoint totals
and reveal the corresponding emulator path through (101,33). This is new x86
evidence on the existing source save, not an observed path in the historical
Wine run and not native Windows confirmation.

## Method and exact inputs

Source: all_app_functions.txt SHA-256
2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8.
Static instruction checks used original EXE SHA-256
9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31.
DAT SHA-256 94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd;
the actual12 terrain records atDAT 1F622 are loaded into runtime0x4792E4.
Cost vector is1,3,1,1,2,4,4,4,4,4,4,4.

[Runner](../runs/experiments/terrain42/original_steps.py) executes original
instructions under installed Unicorn, mapping original PE sections without
patching their bytes. It intercepts ONLY map redraw445B38 and sound45BF28
as presentation no-ops; every movement/selection/cost/distance/swap helper
executes original code. The current-nation WORD at 0x4A0320 is set to 0; fleet carried-army index (+0x16) is set to -1 for the isolated fleet controls. Presentation hooks preserve general registers, including EAX, and emulate a no-result register-convention return by advancing ESP/EIP only; they assume no caller-used result or stack-argument cleanup and do not reproduce painting/event timing. Human-success cases and full walks use these explicit
presentation stubs. This is not unstubbed whole-program execution. Synthetic
step inputs include an explicit parent frame and all-land/all-sea maps.

[Retained output](../runs/experiments/data/run-exp-terrain42/original-controls-v1.json)
records 11 successful bounded step assertions and 2 complete army-walker
assertions, actual instruction-coordinate stores, helper-entry states, input
hashes and runner hash. No measured output, source save or original input was
overwritten. Existing Wine evidence remains the canonical g2 report at 1ff54ab.

## Exact candidate and cost rules

LetP be the Bresenham path cursor, U the actor's current position, sx/sy the
walker direction signs and Ymajor=(abs(dy)>abs(dx)). Cursor and actor may differ
after a detour; neither may be replaced with the other in the cost checks.

| Direction | First alternative A | Second alternative B |
|---|---|---|
|sx=0|(Px+1,Py)|(Px-1,Py)|
|sy=0|(Px,Py+1)|(Px,Py-1)|
|sx/sy nonzero, X-major|(Ux+sx,Uy)|(Ux,Uy+sy)|
|sx/sy nonzero, Y-major|(Ux,Uy+sy)|(Ux+sx,Uy)|

IfP==destination, chooseP without this table. Otherwise compute costs cP,cA,cB:
if neither alternative is strictly below cP, chooseP; otherwise chooseB only
when cB<cA, and chooseA on equality. Source 0044D420 lines 51425–51476;
instructions 44D429–44D45B encode endpoint bypass;44D56D–44D575 strict
improvement checks;44D58B–44D59E compare alternatives with first-on-tie.

Army helper0044D31C lines51368–51396 starts at blocked cost10. It requires
0<x<320,0<y<140; stored map code2..11; terrain cost from4792F0+14*code;
Chebyshev distance<=1 to BOTH cursor and current army. Thus marker/occupied
cells are blocked regardless of owner/hostility, and coordinate0 fails this
helper. There is no special enemy-contact branch in the single step.

After selection,0044D420 lines51478–51512 rereads the chosen map cell,
requires land code2..11, terrain cost<=remaining moves, and helper cost<10.
On success restore old covered cell, store new covered terrain, update army
XY, transport map marker and subtract terrain cost. On failure abort the walk
through its frame bounds; only an AI seat facing an unaffordable land tile
also zeroes moves. Humans retain unused moves. There is no automatic cheaper
candidate retry AFTER failed affordability. Selected cheapest-first means
ordinary positive-cost alternatives cannot rescue an unaffordable minimum.

The final-destination bypass means even a forest next to equally reachable
plain alternatives is entered directly when it IS the clicked destination.
It is not safe to generalize the through-forest detour to a one-tile forest click.

## Bounded original-instruction controls

All synthetic controls start at U(10,10), moves 8 unless specified. A northward
nonterminal cursor is P(10,9),goal (10,5). Ordinary army map is plain 2 and its
marker 200; fleet map is calm sea 0 and marker 300. The named changed cells are
explicit in the runner; no fixtures are altered.

| Control | Original result XY/moves |
|---|---|
|P forest2cost, both laterals plain1cost|(11,9)/7: first lateral wins|
|All three plain1cost|(10,9)/7: line wins equality|
|P mountain4cost,A forest2cost,B plain1cost|(9,9)/7|
|P forest2cost,A occupied marker206,B plain|(9,9)/7|
|P==goal forest2cost, alternatives plain|(10,9)/6: endpoint bypass|
|All candidate costs4,moves3,human|unchanged(10,10)/3|
|Same unaffordable input,AI|unchanged(10,10)/0|
|Diagonal P(11,11)forest, X-major equal alternatives|(11,10)/7|
|Same diagonal with Y-major signs/frame|(10,11)/7|
|Fleet P rough sea3cost, calm alternatives1cost|(11,9)/7|
|Fleet P==goal rough sea3cost|(10,9)/5|

These controls isolate ties, blocked alternatives, endpoint and controller
branches; they do not prove complete strategic AI, routing or every edge cell.

## Existing source-save routes reproduced under original instructions

Unchanged saves/run0-start-AUTO0720-seed12345.SAV SHA-256
050bc354f1cbbe374b6a627f06054f2043b9f91a268f6fbfbc18ed1e7e65574c,
turn 0720, army 0 (100,37), 8 moves. The harness copies its exact map and army0
record into the emulator; no file write or original UI order occurs.

Both walks execute0044D734 with human flag1 and intercept its display/sound:

- Target(100,25): coordinate stores trace(100,36),(100,35),(100,34),
  (101,33),(100,32),(100,31),(100,30),(100,29), ending 0 moves.
- Target(100,32): same first 5 steps,  ending 3 moves at the target.

The endpoints/moves agree with the retained [Wine C4 endpoint log](../runs/experiments/data/run-exp-g2-original-checks/g2_checks-C4-20261011-185907.jsonl): far12 ends at (100,29)/0 and near5 at (100,32)/3. The stepped path is this
emulator run's evidence only. River affordability was isolated synthetically;
the historical staged 11-move river case was not rerun here. No new save-backed
gameplay progress or native compatibility claim follows.

## Caller and termination matrix

| Caller | Route into exact step | Boundary differences |
|---|---|---|
|Human army00446D9C|46728/46733 ->0044D734 ->0044D420 ->0044D31C|Second walk when not at target and moves remain; human residual moves preserved.|
|AI army0044DBA8|51825/51829/51835 ->same army walk/step/helper|Routing before walking and fallback moves accounting; aboard branch routes carrier instead of a land walk.|
|Human fleet00446E24|46761/46766 ->0044E094 ->0044DD70 ->0044DCAC|Separate sea walker; possible second call; fleet moves field+12.|
|AI fleet0044F608|53054/53058/53063 ->0044E1FC ->0044E094 ->same fleet step/helper|Routing/recursive wrapper; adjacent unloading, fleet-city supply and naval contacts stay outside the single step.|

Fleet0044DD70 lines51900–51994 has equivalent terminal/candidate/tie structure,
but0044DCAC prices stored codes<2 through the sea entries, and the commit
checks sea cost<=fleet moves. It is not a call to the army step or permission
to apply land costs to fleets. Fleet helper has no equivalent explicit army
coordinate-range guard in its shown body; this report's fleet controls stay
well inside the board and do not bless out-of-range access. Successful fleet
steps synchronize carried army XY, as the separate research41 handoff covers.

Army walker0044D734 lines51549–51627 advances the cursor independently of
detours and stops when its frame bounds are aborted or the path loop ends.
Afterward, at distance1 from the requested destination, lines51629–51657:
terrain2..11 can recurse only when cost<remaining moves (strict); army-marker
codes200..247 and city-marker codes20..99 enter their own hostility/contact
branches, with positive-move gates for attacks and own/nonwar city supply.
This tail is not proof of a middle-path interaction or research #5 contact-rule
reopening. Human caller's second walk and AI routing wrapper are separate
from the step's own return; endpoint agreement alone cannot identify the path.

## Limits / next acceptance

No current remake behavior was changed, fixtures normalized or expectations
rebaselined. A bounded correction contract should own strategic step/cost
selection and named callers explicitly, preserve contact research #5, and test
normal paths plus the endpoint exception, swapped lateral ties and controller
affordability. Whole human/AI routing and native Windows paths still need their
own acceptance evidence; these synthetic controls do not establish natural
frequency or full original/remake parity. Research #42 remains open pending
independent review/intake and its remaining required validation.
