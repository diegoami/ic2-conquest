# Original classical-world navigation rule for T212

This is a bounded rule/specification, not a production patch. Evidence and
addresses: run-exp-navigation187. A route is **not** a shortest-path search.
Use the published interpreted tables and original signed 16-bit/packed coordinates.

## Static data

| Object | RAM | DAT | Shape |
|---|---|---|---|
| Valid points1..58 | 4790AC | 1F3EA | 58 pairs of signed 16-bit (X,Y),4 bytes each |
| Route sequences | 479194 | 1F4D2 | 3 groups × 7 rows × 8 signed 16-bit point IDs |
| Geographic boxes | 4794E8 | 1F81E | 8(Xmin,Xmax,Ymin,Ymax) signed 16-bit tuples |
| Coordinate splits | 479528 | 1F85E | 6 signed 16-bit (Xlimit,Ylimit) pairs |

Point lookup base 4790A8 is indexed by ID; index 0 overlaps the preceding AI type
table/padding and is NOT a valid point. Route padding is−1. Group 0 uses points
1..25/hub 9(sea); group 1 points26..39/hub 32; group 2 points40..54/hub 43;
group 3 points55..58(islands) has no route matrix/hub. Lower IDs/earlier rows win
equal scores. Route rows are ordered sequences, not an adjacency matrix.
Read offsets as hex. Loader explicitly reads 232/336/64/24 bytes respectively;
the SAV format has no navigation section. These blocks equal unique DAT slices
and all 30 retained generated live snapshots. They are static original-world
data, not saved army waypoints or mutable occupancy.

## Geographic classification and eligibility

```text
region = -1
for boxes in table order:
    if xmin < x < xmax and ymin < y < ymax:
        region = boxIndex                 # last match, strict edges
side = 1
for (xx, yy) in split table:
    if x < xx and y < yy: side = 0
group = 3 if region >= 0 else (2 if side == 0 else 1)
```

The historical "coast flag" is this coordinate-side bit. It is NOT a test for
water adjacency or distance to a coast. CA30 returns(region,side); DA88 also
returns the routing group. Source region boxes and routing groups differ.

```text
targetEligible(army, destination) =
    exists fleet in all live records with fleet.owner == army.owner
    OR geo(army.position) == geo(destination)
```

CAB4 does NOT check direct line, budget, fleet launch/moves/cargo/adjacency or a
real ferry route. It can accept a target which cannot actually be reached.
EE60 first limits candidates to owner>=0, coveredCell>=0, relation==3, then
CAB4 and its scoring rules. Do not substitute a million-move native walk or
"any physically reachable target" for this eligibility rule.

## Direct-line predicate CB40

Define medium(code)=sea if code<2 or code>=300; otherwise land. Thus army and
city markers count as land, fleets as sea. Their occupancy/hostility does not
block this predicate. The low-level walker/contact resolver is separate.

Walk the integer major/minor line using the source-shaped rule in model.py:
minor steps occur while error>=0, then a major step. Compare the source medium
at each sampled point **except the final point**. An adjacent destination always
passes this predicate, even if its medium differs. It is not full movement
legality, pathfinding or a contact check. No bound clamp is present here;
inputs must be valid original map coordinates.

Coincident standalone arguments read an uninitialized step word and can return
false/true with stack residue. In D174's actual sequence the origin test runs
before the target test at the same depth; when target==node and origin!=node,
the preceding nonzero line test leaves a positive counter, making target-node
visibility true. Origin-node distance 0 is excluded from candidate selection.
Do not promote isolated coincidence to a universal no-op rule.

## D174: choose the intermediate destination

For routing group g, scan its point-ID interval ascending:

1. Compute d=Chebyshev(origin,point).
2. Add the point to origin-visible entries when CB40 (origin,point) and d>0.
3. For target-visible points, keep the one with smallest **origin distance** d>0
   as targetSideNode. This is not nearest to the target.
4. Among points visible from both, keep smallest origin distance d>0.

All improvements are strict `<`, initialized at 1000. If a common point exists,
return it. Otherwise, if origin-visible entries and targetSideNode exist,
run D010:

```text
primary = secondary = absent; primaryCost = secondaryCost = 1000
for originEntry in ascending candidate order:
    for row 0..6 of routeGroup:
        if originEntry not in row: continue
        if targetSideNode in row:
            cost = abs(position(originEntry)-position(targetSideNode))
            if cost < primaryCost: primary=originEntry; primaryCost=cost
        if hub in row:
            cost = abs(position(originEntry)-position(hub))
            if cost < secondaryCost: secondary=originEntry; secondaryCost=cost
return point(primary if present else secondary)
```

Positions are last matching slot positions if duplicates exist. Static valid
rows have no duplicate positive IDs. A primary result always beats the hub
fallback, regardless of the secondary's numeric cost. This measures sequence
index separation, not geometric distance or total path cost.

If no origin entries exist, use localFallback(origin). If entries exist but no
targetSideNode, use localFallback(target); if the returned point exists and is
not directly visible from origin, recurse D174 toward that point. No original
recursion-limit rule is claimed; the diagnostic model raises at a guard limit.

Group 3 has no legal D010 table. Complete enumeration of 329 static classical
land/land-marker cells in the eight regions finds visible island-node unions
of size 0 or 1 per region. Thus same-region land pairs either share that one node
or take local fallback: graph fallback is unreachable in this domain. Forced
group 3 graph controls read terrain-name words and an uninitialized temporary,
returning stack-dependent invalid/non-nav points. Do NOT invent a fourth table
or apply this classical-world contract to arbitrary edited/other scenario maps.

## Local fallback CEC8

Scan dx=−1..1 outer, dy=−1..1 inner, excluding (0,0). Test the three cells at
origin+n(dx,dy), n=1..3, independently clamped to x 0..319 / y 0..139. Army mode
(global4A0340=0) requires the same medium on all three. Successful directions
overwrite the output; the **last** successful direction's third cell wins.
No success returns X=−1(Y is not meaningful). Occupied land markers still pass
this medium test; the later walker can fail to enter them. Fleet-mode overrides
are outside this army-mode fallback contract.

## DB38 and ferry protocol

If origin/target geographic pairs match, call D174 with the origin's group.
Otherwise D9A8 chooses the nearest own/current-nation fleet which is launched,
has no cargo and moves>0. Strict distance improvement gives first-record ties.
This is narrower than CAB4's any-own-fleet eligibility.

- No usable fleet: output X=−1, no routing move.
- Fleet distance 1: B79C embarks immediately, removes the army marker, links cargo,
  sets both moves 0 and army coordinates to fleet, trims oversized AI cargo to
  ships×500 if needed; output X=−1 also. Negative output therefore need not mean
  failure. The tested control fits capacity; trimming is source evidence only.
- More distant fleet: CD08 scans the line from army to ship until medium changes.
  Army intermediate is last land cell; fleet stored destination is first sea
  cell. The army caller's requested goal is changed to that intermediate.
  Already at the coast can yield army X=−1 while still writing a ferry request.

An already embarked army bypasses DB38: locate fleet at its coordinates, scan
from the requested land target toward that ship, store the last land approach
as the fleet destination, subtract 2 army moves, without immediately moving the
fleet. CD08 also has the exact496 BCcoordinate exception (x>=248 or x>=214 and
y>=99); do not rename that predicate "coastal". Its special-area extension is
source-defined but not isolated by this batch's ferry controls.

## DBA8 execution and contact contract

Unembarked: CB40 true selects the direct target; false calls DB38 and walks its
nonnegative intermediate. Preserve successful embark/ferry-request results even
when the intermediate Xis−1. Low-level D734 handles contact after its walk:
adjacent hostile army with moves > 0 dispatches AEE4; hostile city with moves>0
dispatches B27C; non-war city dispatches F6D8 supply. The controls stop before
these resolvers and assert dispatch, not battle/siege/supply outcomes.

After no moves were spent, the wrapper may choose CEC8 and spend one additional
move; it recurses while goal distance>1, budget>0 and its intermediate/goal-X
guards allow. There is a required caller-context qualification:

**The direct branch does not initialize local_e.** For the actual F31C target-tree
call, the slot reuses the upper 16 bits of EE60's stack-output pointer. On this
non-large-address-aware 32-bit executable's valid user stack it is nonnegative.
Recursive calls reuse D734 goal X(0..319), also nonnegative. Three filled-stack
full caller controls at the diagnostic stack address produce the same entry
sequence 128,103,110,103,110 and
the same endpoint/budget. This establishes the tested target-tree contract.

At a standalone DBA8 entry, seeding only that inherited word negative versus
nonnegative changes a friendly-marker-blocked direct request from no movement/
8 moves to fallback-recursion/(100,41)/0 moves. Do not initialize a universal
wrapper value by guess for every caller. Other garrison/mercenary/homeland
caller histories are not universally proved here. If T212 needs that broader
cleanup contract, **stop that branch** and run the smallest next original test:
the generated three-friendly-marker wall, entry ESP−14capture at EC7D/ECD6 and
E913, plus actual ensuing positions/moves. No new owner save is needed.

The package specifies the reusable eligibility/first-destination rule and the
tested F31C execution context. It does not authorize silently copying undefined
stack behavior, changing the low-level walker or removing T212's blocked label.

For groups 0–2, each valid point occurs in a row containing its hub. Thus a
nonempty origin-entry list always supplies a secondary route in this static data.

The requested EBE8/E84C caller controls are now in
`findings/2026-10-24-garrison-mercenary-caller-guards187.md`, pending separate
Research promotion. They establish specific full-F31C zero/negative carry
histories, not a universal standalone initialization. Preserve the original
packet's narrower scope when reading the contract above.
