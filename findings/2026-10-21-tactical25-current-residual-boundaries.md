# Tactical25: current HR7 residual boundaries and original shot attribution

**Status:** bounded read-only followup for research25/build1107, not full replay
or cause closure. Current registry and immutable original hook rows are inspected;
no original/port game execution, fixture/range/registry edits or fallback model.

## Current revision and units

Build main at this check: a39bdfc2e2d7e39653360641a9fcee3d57c2b775.
Earlier prerequisite corrections1103/1105/1104 and later1164/1165/1166/1167
are closed/merged; the old control blocker is superseded. T188/T189/T190/T191
merge pins are62fc9f0b877c1106b23c5efaf54e1ba05c6669a5,
976037b9dd276dc32bccef68919e39756ec728af,
8c72d1724387d7d4109f54064115405e3c4b2e96,
8aae26cad0940d5fbb24b8d029a3028bec97031c.

Pinned KnownFailures.json has14 assertions:4 grid1106 and10 target/draw/peace
1107. Ten assertions are not10 independent battles; the current target cases
concern mix-rg seeds1/2 and their gate2 resume counterparts. The historical
318-hook282complete/283draw/36residual result belongs to its old comparison
revision and is not restated as a new current replay. Neither are the older
94 assertions current. The recovered42-series survey is already covered by
the promoted research report and is not re-reconciled here.

## Exact current draw and state boundaries

| Series | Current registered first original draw | Port registered comparison | First saved-state field |
|---|---|---|---|
|mix-rg_s1_r5_hook|zero-based60,HR7,439188,Random153=118|Random58=44|BATTLE07 slot24 troops:port3910/original3822|
|mix-rg_s2_r5_hook|zero-based67,HR7,439188,Random175=173|Random481=477|BATTLE07 slot23 troops:port10614/original10785|

These are first registered comparison boundaries, not complete per-operation
histories. Research40 owns the four separate crafted grid cases; no inference
about normal tactical targeting follows from normalizing them.

## Original actor/target recovered from the exact immutable hook

[Checker](../runs/experiments/tactical25-current/attribute_registry.py) fetches
the registry at the explicit build SHA, retains its Git blob/hash and exact rows,
then indexes ONLY random rows by the registry's zero-based draw index. It
compares original site/bound/result/counter exactly and finds the preceding
shot-entry marker43910C. Actor is lowWORD(EAX), target lowWORD(EDX), not a
high register half. It independently cross-checks the existing exchange row.

[Retained result](../runs/experiments/data/run-exp-tactical25-current/registry-attribution-v1.json)
contains full raw marker/random rows, source paths/hashes and the unchanged
registry. Both original first differing draws are **Rome slot5 archers shooting
Gaul slot24 light infantry**:

- s1 original hook seq106 is random draw60; preceding shot markerseq105,
  EAX3211269 (lowWORD5),EDX24; source RNG before368896245. Existing exchange
  row says actor troops3317,target4557,bound153,draws118/75,loss193.
- s2 original hook seq113 is draw67; preceding shot markerseq112,
  EAX3211269 (lowWORD5),EDX24; source RNG before 1788744665. Existing exchange
  row says actor troops3317,target6238,bound175,draws173/118,loss291.

The richer exchange troop/loss figures are retained prior attribution, not a
new instruction trace. New direct checks cover raw original boundary identity
and marker actor/target. Legacy original runtime claims and shot-general-pass
are NOT stored by these logs; no value is filled in from the current model.

## Next bounded comparison and exact blockers

The earlier HR6 actor-versus-enemy archer condition is now a merged correction;
repeating the old draw24/Random1085-vs172 cause does not explain this HR7 shot.
Before choosing any next fix, obtain the CURRENT production comparison phase
immediately before draw60/67 on this integrated pin: port actor,target,slot/grid,
claim/pass/iteration, original inputs actually available and first state
divergence. Do not infer equal actors from a matching draw index or force the
port bound to153/175. The first saved troop mismatch can follow an earlier
target/position divergence in that same half-round.

No full318-log rerun is claimed here: that needs the integrated production
comparator and complete pinned fixture corpus in an authorized comparison
workspace. This session may not write the remake repo, and its mounted private
battle directory is inaccessible even outside sandbox; no current port phase
capture is present in the registry. Existing original snapshots must be checked
for coverage through the needed HR7 point before requesting fresh original
instrumentation. Missing original claims/pass remain a separate evidence gap.

Research main/build can supply the current read-only comparison packet; original
native/Wine execution remains separately coordinated. All14 assertions remain
strict and unchanged. No range substitution, new expected failure, tolerance,
fixture repair, research25 closure or whole-battle cause claim follows.
