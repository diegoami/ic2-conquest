# Tactical25: fresh original trace isolates mix-rg_s1's first differing movement order

**Status:** `[confirmed, partial]`, research #25 / build #1107. The first differing **chosen threat goal** is now established on common, directly observed original inputs: half-round 6, Gaul slot 22, original **(5,3)** versus port **(6,4)**. The threat-key condition tests the wrong unit in the port. Earlier computed threat rankings already differ at half-round 4, while their chosen goals agree. This distinction matters when saying “first divergence.”

This is a new original-side trace, following the [inventory and local reproductions](2026-10-16-tactical-target-and-draw-attribution.md), promoted in research main `93bee8965e5d0d05017deb3b31d5289f7af263c0`. It does not implement a correction or establish that a corrected port would match the entire battle. All 36 full battle-path investigations remain open; other cases are unchanged.

**Provenance:** `[Wine]` is a new run of the original fixed-seed battle lab under Wine; `[x86]` executes original pure helper instructions under Unicorn2.1.4 on the new Wine inputs; `[port]` calls the unchanged pinned production methods. There is **no native Windows confirmation**. Missing runtime fields in legacy logs/SAVs remain missing. New runtime claims and pass observations have their own files and sequence IDs; they are never inserted into old records.

## Inputs and inertness gate

Original start: `FLD-RG_0743_rome_army0_at_86_28.SAV`, copied byte-for-byte as `MIX-RG_start.SAV`, SHA256 `39edecd1fa74776ef7ed817794b2f2bea951b6b2b36ef09ab42813208095f0ad`, turn **0743**, seed **1**, Rome army0 against Gaul army10. No unit, nation, flag, fixture, expected draw or gameplay edit was made.

Pins:

| Input | Pin |
|---|---|
| Immutable fixture repository | `6319802a75067e7730e4f6a27dce3b4e296ddd9b` |
| Unchanged port | `257f2d2cd7510451d229a983553a54b89065b06c` |
| Original source/x86 EXE | `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f` |
| Existing unhooked seed1 lab | `06bc469dff70ae8c83438e82ef4266a584bab7796752024521d00f8d8d46ec40` |
| Standard observer | `58c683daf7dd25a10d6c3467d85c4ccc903a21f0364768cbf975fc575ac234db` |
| New state observer | `dae453466e5fd61fe4376192ac669ae5f3703433c65e3e93d9398b45bc00c3ec` |
| DAT | `94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd` |
| Legacy hook CSV | `693ce0d821e5fe183317cf7971833d8428e29996521fe3947fb7824d8e6c539b` |

Both independent fresh runs passed a stronger gate than the requested prefix through half-round 6:

| Fresh run | Draw tuples | Full SAV files |
|---|---:|---:|
| Standard observer, `20261016-190528-1258374` | all 325 identical | all 15 byte-identical |
| New state observer, `20261016-191329-1302174` | all 325 identical | all 15 byte-identical |

Draw comparison covers original site, bound, seed before/after, result, counter, side and battle flag. Neither log overflows or re-enters; both pass seed-chain/formula checks. The SAV check compares **whole files**, not selected battle fields. In particular `20261016-191329-1302174-BATTLE06.SAV` equals legacy `mix-rg_s1_r5_hook_BATTLE06.SAV`, SHA256 `de69151203cd4bb20c34a136b32a1ce68110ddc9fb2e0e685940a06eeb082ae9`, turn 0743. Save/EXE/raw-buffer assets are in [run-exp-tactical25-trace](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-tactical25-trace); `SAVES.sha256` identifies local artifact filenames. GitHub changes spaces in EXE asset names to dots; SAV names are unchanged.

## Observer and validation

`runs/experiments/tactical25-trace/observer.py` extends the existing tested48-byte observer. Added markers are target-choice helper `0x439e08`, engage `0x43a160`, Pass2 `0x43a544`, Pass3 `0x43abb4`, threat helper `0x43a718` and Walk `0x438d24`. Return addresses distinguish the outer and nested passes. Target-choice helper's actor is decoded from the caller's saved local at original ESP+6, checked against the subsequent engage actor and unit type; `actor-stack-decode-20261016-1933.txt` preserves the caller instructions.

Each added parallel snapshot records the original pre-call 40 slots, grid,40 actor→target claim words, control flags, active slot bounds/nation, registers already present in the base record and live stack words. The added state-copy instructions write only their observer section; original calls retain the base observer’s tested stack convention. Snapshots stop after counter 6; all random/boundary records continue through the full battle. There are **152 snapshots**, with state overflow0. A snapshot's copied Random header is pre-call, so its result/seed-after fields are not completed draws; authoritative results come from the joined base CSV.

The existing private-stack guard restores registers, ESP, live stack and EFLAGS, including DF. `cpu-20261016-191210.json` retains100 random-call,900 marker-entry,132 flag,132 reseed comparisons,20 re-entry batches, nested-entry and overflow controls, the existing broken-cave sensitivity check, and18 active payload/DF/counter/capacity cases. Counters are deliberately forced into0..6 during normal comparisons so the copy code actually runs. The expanded image required relocating only the emulator's test stack. `byte-audit-20261016-194904.json` verifies the original threat body and its pure line/box/min/max/swap/distance helper bytes agree in the source EXE, standard lab and observed EXE, apart from the checked entry detour.

The unmodified port was observed in `model-phases-20261016-192217/`: placement control plus movement phases3–6. Each reconstructed movement phase calls the same production unit methods, then asserts **entire state and event-log equality** with the authoritative `GoldenReplay` snapshot. No production rule or known-failure entry changes. Original and model decoded slot fields/names, grid and claim counts are then compared at corresponding decisions. End toggles the original's side before melee, so the final pre-melee comparison deliberately compares slots/grid/claims rather than pretending those header sides are simultaneous.

## Earliest output difference on shared original state

`attribution-20261016-192641.json` contains115 state comparisons, all 28Pass1chosen targets and23 Pass 1Walk goals. All preceding Pass1 inputs, claims, choices and movement goals agree. The first Pass2's output also agrees before Pass3 in every captured movement phase, including6.

The five actual original threat helper calls are:

| HR | Actor | Original goal `[Wine]` | Port goal | Original chosen enemy `[x86]` / port | Shared input? |
|---:|---:|---|---|---|---|
|4|24|(6,4)|(6,4)|0 /0|yes|
|5|3|(3,8)|(3,8)|23 /23|yes|
|6|22|**(5,3)**|**(6,4)**|**5 /1**|**yes**|
|6|23|(3,4)|(4,4)|2 /5|no; slot 22 already differs|
|6|24|(10,4)|(10,4)|8 /8|no; earlier units differ|

Original sorted keys and selected enemy are separately labelled x86 evidence: executing the unchanged pure helper on each new Wine input reproduces **all five directly observed Wine Walk goals**, without a UI/shot stub. The port keys and journal are measured from unchanged production. `minimal-20261016-193117.json` contains the key original snapshots and their model counterpart; the full input remains in the state capture.

The decisive new Wine sequence is:

1. **125**: threat helper entry for slot 22, half-round 6, side1. All40 decoded slots/names, all 168grid cells and all 40claim counts equal the port before the corresponding unit call.
2. **126**: original Walk entry, actor22, packed destination **(5,3)**. Its gameplay input still equals that same port input. The port's production journal requests **(6,4)**.
3. **127**: next threat helper entry, actor23, after original slot 22's walk. Original 22 is at(4,5), moves0, target−1; port 22 is at(5,5), moves1, target1. The boards now differ. The later slot 23 comparison no longer has shared input and is not treated as a second independent cause proof.

At125/126the original's claims are exactly20→0,21→0,22→4,23→4,24→4, with every other actor claim−1. Equivalent model claim counts are target 0=2, target 4=3, all others0. Original control bytes are `[1,0,0,0]`: attacker general enabled, defender general disabled, battle-end and human-interruption bytes0. Claims or an interrupted/re-enabled general therefore do not explain this first goal difference.

## Cause: the archer condition reads the enemy instead of the moving unit

Original `FUN_0043A718`, pinned original lines39940onward in the prior finding's `target-routines-static-20261016-170424.txt`, defines:

```text
ranged = actor.Type == archers AND actor.Shots > 0
key(enemy) = -ShotBound(actor,enemy)                 if ranged
             enemy.troops*quality*morale*M[enemy][actor] div10000 otherwise
```

Slot22is **LI**, with 7 shots. The original therefore uses ordinary weighted strength for every enemy. The port's `GeneralPassThree.Threat` instead tests whether **the enemy** is an archer with shots, and calls the shot bound with reversed arguments. On this common input, that gives three enemy archers negative keys:

| Enemy slot | Original key | Port key |
|---:|---:|---:|
|4|378|−45|
|8|745|745|
|5|1413|−153|
|2|1716|1716|
|1|1719|−186|
|6|4443|4443|
|0|4824|4824|
|3|5809|5809|
|7|8875|8875|

Original order is **4,8,5,2,1,6,0,3,7**. The first two candidates have no usable route; candidate 5 yields(5,3). The port starts **1,5,4,8,2,6,0,3,7** and takes the clear line to 1 at(6,4). All original live keys are distinct and below the dead-entry sentinel1000000. Consequently the previously documented tie-sort/dead-entry discrepancy cannot explain this order difference. The actor is not an archer, so exhausted-archer radius is also not the cause here. The active Gaul units are already in type/slot order, so later-pass iteration differences do not select another first actor.

Computed threat order already differs atHR 4slot 24, but both routines choose enemy 0 and(6,4); atHR 5slot3both choose enemy 23 and(3,8). Thus the first **ranking-rule** discrepancy precedes the first **observed selected-goal/state** discrepancy. The report does not collapse those two claims.

There are no original shooting-entry markers and no flank Random(3)calls throughHR 6. The separately promoted source-only correction to Pass2's shooting divisor is not exercised by a shot in this prefix. This trace does not validate that divisor with new shot execution.

## Relation to the original draw24 mismatch

The completed original CSV's zero-based draw 24 is fresh sequence 146, site 0x439557, counter 6, side 0 after End's toggle: Random(1085)=357, seed698472713→1415176494. It exactly matches the immutable legacy draw. The validated port baseline still draws Random(172)=56 at that index, with the exchange actors Gaul 22→Rome 1 rather than original Gaul 23→Rome 2. The fresh actor pair is independently recovered from the two rout-entry AX arguments following the four melee draws; the linked proof is retained in `draw-link-20261016-193659.json`. The original pre-melee snapshot retains slot 22 target −1 and slot 23 target 2; the model retains slot 22 target 1 and slot 23 target −1.

The trace now locates a concrete earlier cause of the board/order divergence: the different threat goal on shared original input. It does **not** establish that changing one condition makes every later order, draw, rout and post-battle result match. Other independently identified defects may become visible after a correction. No expected range is substituted and no combined emulation is added to the comparison harness.

## Canonical evidence and reproducibility

All tracked text is under `runs/experiments/data/run-exp-tactical25-trace/`:

- `validation-20261016-190814.json`: fresh standard control versus immutable legacy.
- `validation-20261016-191525.json`: new observer versus immutable legacy, all 325 draws/all 15 full saves.
- `states-20261016-191329-1302174.json`, matching hook CSV/run JSONL, `build-20261016-191329.json` and `cpu-20261016-191210.json`.
- `model-phases-20261016-192217/` and manifest: authoritative complete-state/log checks and production threat keys.
- `pure-original-20261016-192034.json`: five original helper executions on the fresh inputs, each matching its Wine goal.
- `attribution-20261016-192641.json` and `minimal-20261016-193117.json`: linked shared-input proof and first goal difference.
- Earlier failed UI/build/emulator attempts and earlier successful analyses are retained, not overwritten. The first UI attempt stopped before battle because the generic driver used13columns; the B11 runner's existing29×27map configuration resolved it. An initially oversized marker layout was rejected before any EXE/run. No measured save was deleted.

`prepare.py` makes a private prefix/game folder and unchanged standard observer; `run.py` requires that private workspace/display, refuses existing BATTLE files and preserves every result under a unique artifact name. `build.py` requires the matching CPU evidence, retains the standard game folder and builds a fresh state-observer folder. `validate.py` gates attribution on full identity; `port_phases.py`, `probe_original.py`, `analyze.py` and `minimal.py` preserve separate port/x86/derived results. Source/data hashes accompany the packet.

Publication initially succeeded for 20 assets; the second batch stopped before uploading because the helper did not recognize GitHub's space-to-dot EXE naming. The failed command is retained. Duplicate detection was corrected to verify existing normalized names **and SHA256digests**, then the same `gh release upload` route published the remaining 20 assets. No overwrite, alternate API or credential route was used.

Research intake/build evaluation can now use the actual common-input threat-rule reproduction. Research #25 and build #1107 remain open; complete battle-path verification and all other residual cases require their own evidence and separately reviewed implementation work.
