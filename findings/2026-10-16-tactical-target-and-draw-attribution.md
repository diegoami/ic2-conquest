# Tactical AI: immutable replay inventory and original target-rule discrepancies

**Status:** `[confirmed, partial]` for research issue #25 / build #1107. The 318-log rerun and inventory reconciliation are complete. Local original-rule discrepancies have minimal reproductions; whole-battle causal attribution remains open where indicated below. This finding proposes no gameplay patch, draw rebaseline, fixture edit or expected-failure change.

**Provenance:** original logs/SAVs are the existing **Wine** battle-lab observations, not native Windows confirmation. New `[x86]` evidence executes pinned original instructions under Unicorn 2.1.4. Inputs to local probes are labelled synthetic or contemporaneous **model** state. A local probe does not recover the original process's missing runtime claims or establish an entire original battle path.

**Pins:** build `257f2d2cd7510451d229a983553a54b89065b06c` (T175 control correction, PR1156, merged after MiniMax review); fixtures `6319802a75067e7730e4f6a27dce3b4e296ddd9b`; original EXE `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`; DAT `94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd`. Source decompile SHA256 `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`. The build worktree remained clean throughout. A fresh pinned full suite passed Data248 / Engine7366, with three Windows platform skips.

## Evidence and reconstruction limits

The original hook/save corpus is published in [run-exp-battle-hook](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-battle-hook). No new binary artifacts were produced.

All text is under `runs/experiments/data/run-exp-tactical25/`. Canonical captures:

- `production-20261016-174818/summary.json`: unchanged `GoldenReplay.Run` and `DrawComparison.First` over all 318 hook pairings; all model draws,36 residual contexts, fixture hashes.
- `phases-20261016-180932/`: first differing movement phase in all 36 cases; `phases-20261016-180904/`: phase containing the first differing **model** draw (state-only case uses its first differing phase). Both observers reproduce the entire production state **and event log**, using the same private unit methods, with no substituted rules. Their manifests pin both runner source hashes and the clean build/fixture revisions. Claims in these captures are model claims at the stated instant.
- `original-threat-20261016-180959.json`: full original pure threat helper on30 contemporaneous model actor inputs; original Pass2 on108 model stage inputs (84 completed,24 stopped before a shot). No shot/UI path is stubbed to manufacture an answer. Four synthetic source-rule reproductions are split between this file, `original-repros-20261016-180225.json` and `phases-20261016-180932/model-repros.json`.
- `inventory-20261016-181249.json`: all 36 residuals, exact first state difference, first draw with site/seq/seed/range/result/actor/target, model pass and claims, original field availability, historical/current registry case IDs, original start save and parsed turn.
- `historical-survey-reconciliation.json`, raw636-row TSV and both historical registry snapshots: exact old-inventory recovery. `correction-6208282/` retains the prerequisite's test/TRX and registry transition evidence.

The first failed capture (`production-20261016-174652`) contains **no trial**: its generated runner was outside the build root required by asset discovery. Intermediate successful phase/probe captures are retained as experiment history; use the canonical names above. No save or measurement was deleted or overwritten.

Original actors are recovered from shot-entry AX/DX, or the two rout-entry AX arguments after a four-draw melee exchange. High register halves are not actor IDs. The hook's `side` is sampled after End toggles sides before melee; actor side comes from the slot. All35 first draw divergences have original and model actor/target evidence. Legacy claims are **not serialized** in either hook logs or SAVs. The general pass of an original shot is also not recorded. These fields remain explicitly unknown; an x86 probe on model input cannot fill them.

## Inventory: 42, 57/41, 63/48 and the corrected comparison

The recovered local T129 survey has636 rows:318 with emulation flag false,318 true. That flag identifies the old experimental mode, **not whether the trial passed**. In true mode276 completed and42 did not. Its42 series contain all41 series represented by the57 issue1107 test cases in registry commit `9664936e`; the missing42nd series is **hi-ar-three_s3_r5_hook**. Counts of test cases and distinct battle series are different units.

The TSV hash is `41f71b7061b5034576731f79c5b18297b7d7704c3e705b90ff9b31c37dab19e0`. It is a recovered local working artifact consistent with the historical counts, not authenticated as the exact originally published survey. Its experimental C# was only hashed, never run or added to the comparison harness.

By baseline `5ca9c3f`, issue1107 had63 cases/48 series. Relative to the42 survey series, that registry still omitted hi-ar-three_s3 and added seven others: ar-hi-one seeds1/2/3; ar-hi-three seed1; ar-lc-three seed3; li-hi-three-half seed2; li-hi-three-one seed2 (all `_r5_hook`). The JSON lists every name and case ID.

T175 reduced the **whole** strict registry633→94 (545removals, six expressly approved exposed cases). Of94,90 point to1107 and four to1106. Those 90 include non-hook/resume comparisons and must not be equated with the318-hook inventory or the36 residual series here.

The official comparison now has **282 complete exact /36 residual**, **283 exact draw sequences**, and all 318 hook pairings valid. Thirty-five series first differ in draws:30 at0x439557, four at0x439188, one at0x4395ce. These are **original** call sites; the model may already be in a different action. The state-only case is **ar-hi-three_s3_r5_hook**, BATTLE19, slot2 y: port3/original4, with218 identical draws. Every residual start save parses to turn0743.

## Mix-rg_s1: the requested starting case

`starts/FLD-RG_0743_rome_army0_at_86_28.SAV`, turn0743; `hook/mix-rg_s1_r5_hook_BATTLE06.SAV`; source hook SHA256 `693ce0d821e5fe183317cf7971833d8428e29996521fe3947fb7824d8e6c539b`.

The first differing draw is zero-based24, half-round6, original0x439557: **Random(1085)=357**, port **Random(172)=56**. Original melee is **Gaul23→Rome2**; model melee is **Gaul22→Rome1**. Earlier in that movement phase, original slot22 ends at(4,5), target−1; port slot22 at(5,5), target1. Slot23 ends at(3,5), target2 in the original, versus(4,5), target−1 in the model. This is not evidence that1085should replace172 in the same exchange: the actors and targets differ.

On the model's exact input immediately before slot22's threat move, original FUN0043A718 returns aim **(5,3)**, while the port chooses **(6,4)**. Original threat order begins4,8,5,2,1; model order1,5,4,8,2. Slot22 is LI with shots; the original evaluates ordinary enemy strengths, whereas the port gives enemy archers negative shooting keys. The original pure helper, including its line/box routines, runs without stubs. This establishes a **local threat-rule discrepancy** in the relevant phase. It does not prove that every preceding original runtime value equals the model input, or that this one change alone resolves the complete battle. Original runtime claims remain unknown.

## Cause-attributed local reproductions and exact source rules

### A. Pass2 weighted strength and eligibility `[code][x86]`

FUN0043A544 (original lines39860–39939, products39899–39926) uses
`S(u,v)=((troops[u]*quality[u]) div100)*morale[u]*M[type[u]][type[v]]`, with32-bit wrapping and signed division. For **each adjacent candidate**, it computes `adjusted=S(enemy,actor)−focus* S(enemy,actor)`, tests `(2*adjusted) div3 < S(actor,enemy)`, then retains the strict minimum adjusted strength below initial100000000. Eligibility is candidate-specific. Focus counts all20 own target words, including dead slots. Shooting happens first; the routine does not recheck moves before its melee scan.

The port's `GeneralPassTwo` uses **troops alone**, selects a global minimum and then tests that one candidate. Minimal synthetic actorHI3000/q5/m70 at(5,5), enemyLI4000/q1/m50 at(5,6), enemyHI2000/q9/m90 at(6,5), no shots, one actor move: original choosesLI20; port choosesHI21. Original values are own-v-LI630000 / LI8000, own-v-HI52500 / HI81000; HI fails the original54000<52500 test.

Original full Pass2 completed on84of108stage inputs;24were explicitly stopped before their first shot. Six completed stages differ in targets: ar-hc-three_s1 (slot20→2 versus−1), hc-ar-three_s3 (22→−1 versus2), hc-hc-three_s2 (1→21 versus22), hc-hi-three_s3 (20→0 versus2), hi-ar-three_s1 nestedPass2 (2→22 versus21), hi-lc-three_s1 (0→20 versus21). These are local probes on model stage inputs; the supplied JSON retains all successful and stopped runs.

### B. Threat key subject and exhausted-archer radius `[code][x86]`

FUN0043A718 (39940onward) sets `ranged = actor.Type==archers && actor.Shots>0`. For **every enemy**, ranged actors use `−ShotBound(actor,enemy)`; other actors use enemy weighted strength `troops*quality*morale*M[enemy][actor] div10000`. The same actor condition selects box radius2 versus1. The port tests **enemy** archer/shots for its negative key, reverses shot arguments, and uses an actor-type-only radius even after archers run out of shots.

Minimal synthetic LI actor3000/q1/m100 at(5,5), archer enemy20 with3000/q1/m100 and one shot at(5,6), LI enemy21 with1000/q1/m100 at(6,6): original keys300and150 put21first and aim(6,6); port puts20first. The source condition, not a guessed range correction, explains this rule difference.

The original helper returns different aims on15actor inputs in15residual series. Two are exhausted-archer radius reproductions: **ar-hi-three_s2 slot2**, original(9,3)/port(10,3), and **ar-hi-three_s3 slot2**, original(8,4)/port(8,3). In both, the actor is an archer with **zero shots** and the complete live enemy order is identical in both routines. The other13have changed threat order. The inventory retains each input, original sorted keys/order/aim and port order/aim; whole-battle attribution remains open.

### C. Exact selection sort and dead entries `[code][x86]`

The original fills **all20 enemy entries**, giving dead units key1000000, finds the first strict minimum in the remaining suffix, and performs **one swap** after scanning the suffix. It stops considering keys above999999. The port filters dead slots and swaps immediately for each smaller candidate. This is a different tie rule.

Four synthetic identical-type enemies with troops3000,2000,2000,1000 produce original order **23,21,22,20** and port **23,22,21,20**. Both are actual routine outputs. This proves the tie defect; no residual battle is assigned to this defect alone without a complete shared-input path proof. Dead-entry filtering and the1000000sentinel also require preservation, rather than a library-sort replacement.

### D. Flank vertical equality `[code][x86]`

FUN0043AA60 (40108–40190) adds1for an enemy **strictly below**, otherwise subtracts1, so **equal-Y enemies count with above**, then uses+1only for a positive balance. The port ignores equal-Y enemies.

Synthetic HI actor(5,5), two moves; four live enemies at(8,6),(9,6),(8,5),(9,5), empty grid, seed1, captured horizontal flag false: original's first Walk destination is **(3,3)**; port ends at **(3,7)**. The x86 probe stops before Walk and captures its actual arguments; it does not stub movement. Original balance0becomes−1; port balance2becomes+1. This is a minimal local defect, not an attribution of any entire residual trial. No first draw mismatch is at the flank Random(3) site.

### E. Iteration, claims and remaining flank details `[code; attribution open]`

Only Pass1 FUN0043A31C uses type order `[HI,HC,LC,LI,Ar]` (table0x4790a0), then ascending slot. Pass2 FUN0043A544 and the threat/flank loops in FUN0043ABB4 iterate **ascending own slot** directly. The port reuses type order in every pass. A mixed unsorted army can therefore differ; a type-sorted army cannot establish this cause. No trial is assigned to this alone here.

Original claims at0x45e6b0 are40 signed actor→target words, reset−1. Target-choice records a chosen target in the actor's word; FUN00439DE8 counts matching words. Focus FUN00438420 counts matching target words in the20 own slots. The port stores claim counts by target. These representations are equivalent during an uninterrupted once-per-actor Pass1; representation alone is **not** a proved defect. Interrupt/re-enable streams are separate inputs and are not mixed into the318 recorded-run comparison.

FUN0043ABB4 captures enemy min/maxX and its horizontal-side flag before threat movement/nestedPass2; its nested flank helper reads that captured flag. The port recomputes bounds per flank actor. Original flank eligibility is no target plus full moves, or one move/counter<10/type!=HI. Its vertical balance and the capture time are distinct issues. Capture-time and iteration effects are source-backed investigation leads; no range mismatch selects a fix for them here.

## All surviving first divergences

Draw indices below are zero-based; first state HR can precede first draw HR. Actor arrows identify **slots**, and original/port actions can differ. `pass2`, `threat key/order` and `radius` mean a reproduced **local rule difference** on that trial's model phase input, not a proof that the whole original trial is explained. The JSON supplies exact claims arrays and action-pass tags; original runtime claims and original shot-general-pass gaps are explicit.

| Trial (all `_r5_hook`) | First state HR | First draw index; HR original/port; site | Original → port range=result | Actor→target original / port | Local probe status |
|---|---:|---|---|---|---|
| ar-hc-three_s1 | 14 | 100; 14/14; 0x439557 | 44=3 → 49=3 | 20→2 / 20→1 | pass2 + threat |
| ar-hi-three_s2 | 19 | 200; 19/20; 0x439557 | 10172=5803 → 1=0 | 2→20 / 20→2 | radius |
| ar-hi-three_s3 | 19 | none (state only) | identical draw sequence | — | radius |
| ar-lc-three_s2 | 8 | 36; 8/8; 0x439557 | 51=14 → 389=110 | 20→1 / 22→1 | threat key/order |
| ar-li-three_s1 | 8 | 28; 8/8; 0x439557 | 90=25 → 101=28 | 22→2 / 22→1 | threat key/order |
| ar-li-three_s2 | 8 | 26; 8/8; 0x439557 | 125=3 → 76=2 | 22→2 / 22→1 | open |
| ar-li-three_s3 | 8 | 28; 8/8; 0x439557 | 96=17 → 103=19 | 22→1 / 22→2 | threat key/order |
| hc-ar-three_s1 | 16 | 161; 17/16; 0x439557 | 13=12 → 1266=1198 | 1→22 / 21→1 | open |
| hc-ar-three_s3 | 20 | 199; 20/20; 0x439557 | 1178=1056 → 1591=1427 | 22→1 / 22→2 | pass2 |
| hc-hc-three_s2 | 11 | 44; 11/11; 0x439557 | 210=89 → 199=84 | 1→21 / 1→22 | pass2 |
| hc-hi-three_s3 | 8 | 21; 8/8; 0x439557 | 291=135 → 329=153 | 20→0 / 20→2 | pass2 |
| hi-ar-three_s1 | 7 | 40; 7/7; 0x439557 | 15=2 → 16=2 | 2→22 / 2→21 | pass2 + threat |
| hi-ar-three_s2 | 7 | 40; 8/7; 0x439188 | 39=5 → 15=2 | 20→0 / 2→22 | threat key/order |
| hi-ar-three_s3 | 7 | 42; 7/7; 0x4395ce | 13454=853 → 13169=835 | 2→21 / 2→22 | threat key/order |
| hi-lc-three_s1 | 7 | 44; 7/7; 0x439557 | 316=3 → 322=3 | 0→20 / 0→21 | pass2 |
| hi-li-three_s3 | 6 | 29; 7/6; 0x439557 | 53=47 → 7063=6266 | 0→21 / 22→1 | open |
| lc-ar-three_s1 | 9 | 64; 9/9; 0x439557 | 30=17 → 32=18 | 2→22 / 2→21 | threat key/order |
| lc-ar-three_s2 | 9 | 64; 9/9; 0x439557 | 55=35 → 61=38 | 0→20 / 0→22 | threat key/order |
| lc-hi-three_s1 | 7 | 46; 7/7; 0x439557 | 845=549 → 897=583 | 1→22 / 1→21 | open |
| lc-hi-three_s2 | 7 | 50; 8/7; 0x439557 | 268=229 → 988=844 | 20→0 / 2→22 | open |
| lc-li-three_s2 | 11 | 140; 11/11; 0x439557 | 134=22 → 139=22 | 1→22 / 1→22 | open |
| lc-li-three_s3 | 8 | 12; 9/8; 0x439188 | 253=96 → 2496=952 | 0→20 / 20→0 | open |
| li-ar-three_s2 | 9 | 52; 9/9; 0x439557 | 101=50 → 112=56 | 2→20 / 2→22 | threat key/order |
| li-hc-three_s1 | 9 | 40; 9/9; 0x439557 | 742=106 → 1267=181 | 1→22 / 0→21 | open |
| li-hc-three_s3 | 11 | 91; 11/11; 0x439557 | 1058=518 → 1238=606 | 1→21 / 0→21 | open |
| li-hi-half-three_s1 | 7 | 12; 8/7; 0x439557 | 36=30 → 8757=7363 | 20→0 / 0→20 | open |
| li-hi-half-three_s3 | 7 | 12; 8/7; 0x439557 | 39=14 → 8085=3083 | 20→0 / 0→20 | open |
| li-hi-one-three_s1 | 7 | 12; 8/7; 0x439557 | 71=59 → 8737=7346 | 20→0 / 0→20 | open |
| li-hi-one-three_s3 | 7 | 12; 8/7; 0x439557 | 76=28 → 8021=3059 | 20→0 / 0→20 | open |
| li-hi-three_s2 | 7 | 36; 8/7; 0x439557 | 46=13 → 7794=2208 | 20→0 / 2→22 | open |
| li-lc-three_s1 | 8 | 24; 8/8; 0x439557 | 225=74 → 197=64 | 20→0 / 21→2 | open |
| li-lc-three_s2 | 10 | 118; 10/10; 0x439557 | 254=83 → 93=30 | 21→1 / 21→2 | open |
| li-lc-three_s3 | 8 | 44; 8/9; 0x439557 | 211=177 → 137=115 | 22→1 / 0→20 | open |
| mix-rg_s1 | 6 | 24; 6/6; 0x439557 | 1085=357 → 172=56 | 23→2 / 22→1 | threat key/order |
| mix-rg_s2 | 6 | 20; 6/6; 0x439188 | 505=500 → 514=509 | 23→8 / 22→8 | threat key/order |
| mix-rg_s3 | 4 | 19; 6/6; 0x439188 | 279=121 → 470=205 | 24→8 / 23→1 | threat key/order |

Nineteen series have at least one local discrepancy (six Pass2, fifteen Threat, two overlap); **seventeen have none in these evaluated local probes**. All36 remain open for complete causal-path confirmation. In particular, blocked original shot paths, missing original claims/pass observations and any interactions before these local inputs must be investigated independently. The state-only ar-hi-three_s3 case must remain in the inventory even though a draw-only sweep would miss it.

## Reproduction and intake

`runs/experiments/tactical25/capture.py --build-root <pinned-build> --fixtures <pinned-fixtures>` reruns all 318 through unchanged production. `observe.py` adds validated per-unit phase observations; `--draw-phases` selects the first model draw divergence. `original_repros.py` and `original_phase.py` take explicit pinned EXE/DAT paths; the latter takes `--phases` pointing to a validated state-phase capture. `inventory.py --fixtures <pinned-fixtures>` generates a fresh linked inventory. All outputs use new UTC filenames/directories and refuse existing measurement paths.

The paired minimal reproductions identify original rules suitable for **research intake and build evaluation**, not an implementation contract. Keep original fixtures/draw bounds immutable and maintain strict comparison behavior. A later build task must correct each independently accepted rule, rerun full comparisons, and report which whole-trial divergences actually disappear. Unexplained cases remain open; this finding does not authorize adding expected failures.
