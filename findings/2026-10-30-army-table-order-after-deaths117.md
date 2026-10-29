# Army-table order after deaths: the original reorders by swap-remove, the remake keeps order; per-nation AI picks depend on it

**Tag:** [confirmed] for the orders: the original's autosaves in play, and the remake v0.8.4's End turn run from the same
End-turn-click saves. [confirmed] in emulation for the order dependence of the AI merge. In the observed turns the reorders
never touched two armies of one nation.
**Task:** research [#117](https://github.com/diegoami/imperial-conquest-2-research/issues/117), raised during the main
project's evaluation of #1439 and delegated to conquest on 2026-10-30.
**Background:** `2026-10-30-all-ashore-army-order1439.md` (the sweep `FUN_0044adb0` → `FUN_0044abe0`, swap-remove).

## Answer

1. **The orders diverge whenever armies die.** (Numbers corrected 2026-10-30, see the correction below.)
   - **Data:** the #232 bot campaigns give **80 End turns** of the original (seed 12345, 16 nations as the human seat), each
     paired from the campaign receipt: the state at the End-turn click against that End turn's autosave. The autosave is
     written just before the human's `StartTurn`, after every AI seat (`imp_conquest_fixtures/patch_exe.py`, hook at
     0x45217A). **43** of them lose live armies (battles, sieges, AI merges).
   - **Original:** the survivors keep their relative order in only **4 of the 43**.
   - **Remake:** its End turn, run from the **original's own End-turn-click saves** of the same 43 turns, loses armies in 37
     and keeps the survivors in order in **37 of 37**.
   - **The remake's own campaigns:** 44 death turns of 80, order kept in **44 of 44**.
2. **The original's order is the sweep's swap-remove.**
   - The sweep runs at the start of the End turn's seat loop and before each AI seat, so deaths in different seats are removed
     in different sweeps. Dead records already in the pre table (left by the previous round's last AI seats) go in the first
     sweep. A death after the last sweep stays in the table as a dead record.
   - Trying every ordered grouping of the deaths into successive sweeps (each top-index-first, the last record into the freed
     slot) reproduces the observed survivor order **exactly in 42 of 43** turns.
   - The 43rd (Macedonia turn 3) has a human Join and a battle-mauled army that the identity match cannot pair; it is not a
     different mechanism.
   - Typical patterns:
     - two deaths at records 9 and 10 of 14 give `…, 8, 13, 12, 11`;
     - the death of record 0 brings the table's last record to the front.
3. **An exported SAV's record order differs accordingly.**
   - The original's SAV is the raw table: post-sweep, in swap-remove order.
   - The remake's export is its filtered, in-order list.
   - The original's SAV can also hold **dead records** (owner −1). **4 End-turn autosaves** carry one: `bithynia-rulebot1-5t`
     t01-a02 and t02-a01, `carthage-rulebot1-5t-r2` t02-a03 and `gaul-rulebot1-5t-r2` t01-a02. Each is a death after the last
     sweep, by an AI seat after the last sweep or the AI merge's donor. That is exactly what the code predicts
     (`2026-10-30-all-ashore-army-order1439.md`): no sweep runs between the last AI seat and the human's turn. The next End
     turn's first sweep removes it.
   - The remake never exports a dead record (0 in 37 + 44 runs).
4. **Does any AI decision depend on the order?**
   - **Yes, within a nation.** `FUN_004509f0`, the AI's small-army merge (economy phase, `FUN_0044ffbc`, before the army phase):
     - the **donor** is the first own army in table order with fewer than 20,000 troops, not aboard;
     - the **receiver** is the first other own army in table order within 18 tiles that has room (units < 20, troops < 80,000);
     - one merge per call (dump :53964–53988).

     **Emulated control** on the #187 RAM snapshot, all helpers unmodified: Carthage's two armies staged with 12,000 troops each
     at (47,62) and (45,63).

     | Order | Donor | Merged 24,000-troop army stands on |
     |---|---|---|
     | as captured | the army at (47,62) | **(45,63)** |
     | the two records swapped | the army at (45,63) | **(47,62)** |

     The surviving army's unit order differs too.
   - **The army phase `F31C` visits own armies in table order** (count snapshot, :52922). Swapping the two armies of nations 0, 1
     and 2 at the game's start changed **nothing**: the armies are far apart and no random number was drawn. Order matters there
     only when same-nation armies interact (a shared target, a contested cell, the shared random stream).
   - **In the observed death turns no decision could have changed:** **0 of 43** reorders inverted two surviving armies of the
     **same** nation. These early-game nations have one or two armies each, so every reorder was between different nations, and
     the per-nation picks never see that.

## Correction (2026-10-30, the same day)

The first version paired each campaign's last checkpoint of turn N with turn N+1's `a00`, and the remake's last checkpoint
of turn N with the next folder's `a000`. Both pairings were wrong:

- **The original's checkpoints are numbered per action, not per End turn.** The End-turn action's checkpoint is the autosave.
  When the next turn has orders, `a00` is the save after its first order. So 27 of the 64 old pairs ended mid-turn and
  contained no AI round; 37 coincided with an End turn; 43 of the 80 End turns were not among the old pairs.
- **A remake folder's `a000` is the imported start of that turn,** identical to the previous folder's end, so the remake
  appeared to have no deaths at all.

Re-paired from the receipts (`order-in-play-v3.json`, `sweep-model-v5.json`, `remake-same-turns-v2.json`,
`remake-order-v2.json`, `same-nation-v2.json`):

| | first version | corrected |
|---|---|---|
| original End turns / with deaths / order kept | 64 / 19 / 2 | **80 / 43 / 4** |
| explained by sweep groupings | 18 of 19 | **42 of 43** (the model now also takes the pre table's old dead records and the never-swept deaths) |
| remake from the same pre states: deaths / order kept | 19 / 19 | **37 / 37** |
| remake's own campaigns | "no deaths in 80" | **44 death turns, order kept 44 of 44** |
| same-nation inversions | 0 of 19 | **0 of 43** |
| dead records in autosaves | 3, "created during the human's own turn" | **4, deaths after the last sweep**, as the code predicts |

The conclusions stand: the orders diverge, the original's order is the sweep's, the merge depends on it, and no same-nation
pair was inverted in these turns. The first version's data files are kept beside the new ones.

## Addendum (2026-10-30): cross-nation tie-breaks also depend on the order

The first open item below ("cross-nation loops") is answered for the two AI routines that scan other nations' armies.

- **`FUN_0044ee60`, the enemy army an AI army goes for** (dump :52715–52776).
  - It scans **every** army of a nation at war with the actor's (relation 3), in table order.
  - Each one scores `min(1000, strength×110 / enemy strength − distance)`, halved by `FUN_0044eb9c`'s test, plus 1,000 when the
    enemy is weaker and within 7 tiles.
  - A candidate replaces the current one only when its score is **strictly** greater, so on a tie the **lowest table index
    wins**.
  - The cap applies before anything else can separate the candidates. So for a strong army **every weak enemy within 7 tiles
    scores exactly 2,000**, whatever its distance, and the target is simply the first of them in table order.
  - **Emulated** (`tiebreak.py`, #187 RAM, unmodified helpers). Carthage's 33,900-troop army 2 at (47,62), at war with Rome,
    with Rome's armies re-placed as 2,000-troop units:

    | Romans at | Records as staged | The two records swapped |
    |---|---|---|
    | (44,62) and (50,62), both 3 away | targets (44,62) | targets **(50,62)** |
    | (44,62) and (51,62), 3 and 4 away | targets (44,62), 3 away | targets **(51,62), 4 away: the farther one** |

- **`FUN_0044efc8`, the capital defence** (dump :52776–52899, read, not emulated). It first lists the enemy armies near the
  capital, other nations', in table order, **at most 10** (`min(9, n + 1)`). Then it gives each own army a threat from that
  list. With more than 10 threats, which ones are listed depends on the order, and the assignment runs in list order.

So a reorder between **different** nations, which the original makes after deaths and the remake does not, can change an AI
army's target and the capital defence's assignments. None of the 43 observed death turns was checked for such a tie.

## What this does not establish

- **Later game.** With several armies per nation, a death can invert a same-nation pair, and then the merge choice (as
  controlled) and the army phase's visit order differ between the games. No such turn was observed in these 5-turn campaigns.
- **Cross-nation loops beyond the two above.** Other AI scans (e.g. `FUN_004502e0`, `FUN_0044ffbc`'s economy decisions) were
  not read for table-order tie-breaks. Whether a tie of `FUN_0044ee60` actually occurred in the 43 death turns was not checked
  (it needs the actor's view at that moment).
- **The remake's handling of an imported dead record** (imports were of saves without one in the 19 runs).

## Evidence

- Scripts (`runs/experiments/armyorder117/`):
  - `order_in_play.py`: identity tracking over the original's saves; v1 matched on unit names only and is kept, v2 adds type,
    quality, troops and distance; v3 pairs each End turn from the receipt (`--pairs receipt`, the default);
  - `sweep_model.py`: ordered sweep groupings;
  - `remake_order.py`: the remake's own campaigns;
  - `remake_same_turns.py`: the remake's End turn from the original's pre-saves;
  - `same_nation.py`;
  - `visit_order.py`: Unicorn F31C in both orders, and the merge control.
- Data (`runs/experiments/data/run-exp-armyorder117/`):
  - corrected: `order-in-play-v3.json`, `sweep-model-v5.json` (v3 and v4 are the intermediate model versions), `remake-order-v2.json`,
    `remake-same-turns-v2.json`, `same-nation-v2.json`;
  - first version, kept: `order-in-play-v1/v2.json`, `sweep-model-v1/v2.json`, `remake-order-v1.json`,
    `remake-same-turns-v1.json`, `same-nation-v1.json`;
  - `visit-order-v1.json`: the F31C swaps;
  - `visit-order-v3.json`: the F31C swaps plus the merge control. v2 was produced with a staging bug that shifted records,
    and was discarded before use.
- Saves:
  - the original's campaign saves `artifacts/run-exp-diff084-campaign/<campaign>/original/tNN-aKK.SAV`
    (release `run-exp-diff084-campaign`);
  - the remake runs in `artifacts/run-exp-armyorder117/remake-v2/<campaign>-tNN/` (corrected) and `remake-v1/` (first
    version), release `run-exp-armyorder117`.
- RAM: the #187 snapshot (private).
- Decompile `all_app_functions.txt` (SHA-256 `2018c205…`): ABE0 :49396, ADB0 :49537, 509F0 :53964 (called at :53573),
  F31C :52899.
