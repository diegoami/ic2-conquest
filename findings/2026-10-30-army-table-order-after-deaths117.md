# Army-table order after deaths: the original reorders by swap-remove, the remake keeps order; per-nation AI picks depend on it

**Tag:** [confirmed] for the orders: the original's autosaves in play, and the remake v0.8.4's End turn run from the same
pre-End-turn saves. [confirmed] in emulation for the order dependence of the AI merge. In the observed turns the reorders
never touched two armies of one nation.
**Task:** research [#117](https://github.com/diegoami/imperial-conquest-2-research/issues/117), raised during the main
project's evaluation of #1439 and delegated to conquest on 2026-10-30.
**Background:** `2026-10-30-all-ashore-army-order1439.md` (the sweep `FUN_0044adb0` → `FUN_0044abe0`, swap-remove).

## Answer

1. **The orders diverge whenever armies die.**
   - **Data:** the #232 bot campaigns give 64 End-turn transitions of the original (seed 12345, 16 nations as the human seat);
     19 of them lose live armies (battles, sieges, AI merges).
   - **Original:** the survivors keep their relative order in only **2 of the 19**.
   - **Remake:** its End turn, run from the **original's own pre-End-turn saves** of the same 19 turns, keeps the survivors in
     order in **19 of 19**. Its own deaths there are 1–3 per turn.
   - **The remake's own campaigns** had no army death or merge at all in 80 End turns.
2. **The original's order is the sweep's swap-remove.**
   - The sweep runs before AI seats, so deaths in different seats are removed in different sweeps.
   - Trying every ordered grouping of the deaths into successive sweeps (each top-index-first, the last record into the freed
     slot) reproduces the observed survivor order **exactly in 18 of 19** turns.
   - The 19th (Macedonia turn 2) has a human Join and a battle-mauled army that the identity match cannot pair; it is not a
     different mechanism.
   - Typical patterns:
     - two deaths at records 9 and 10 of 14 give `…, 8, 13, 12, 11`;
     - the death of record 0 brings the table's last record to the front.
3. **An exported SAV's record order differs accordingly.**
   - The original's SAV is the raw table: post-sweep, in swap-remove order.
   - The remake's export is its filtered, in-order list.
   - The original's SAV can also hold **dead records** (owner −1). Three autosaves (`bithynia-rulebot1-5t` t02-a00 and t03-a00,
     `carthage-rulebot1-5t-r2` t03-a00) carry one. In each, the dead record was created during the human's own turn (it first
     appears in a mid-turn save) and survived the End turn. Not every path sweeps before the next autosave; which one does not
     was not traced.
   - The remake never exports a dead record.
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
   - **In the observed death turns no decision could have changed:** **0 of 19** reorders inverted two surviving armies of the
     **same** nation. These early-game nations have one or two armies each, so every reorder was between different nations, and
     the per-nation picks never see that.

## What this does not establish

- **Later game.** With several armies per nation, a death can invert a same-nation pair, and then the merge choice (as
  controlled) and the army phase's visit order differ between the games. No such turn was observed in these 5-turn campaigns.
- **Cross-nation loops.** Tie-breaks by table order across nations (an enemy target chosen as the first at the minimal
  distance, interception scans) were not read; those could depend on the order even when no same-nation pair is inverted.
- **Which paths skip the sweep before an autosave** (the three dead records that survived an End turn); the mechanism is not
  traced.
- **The remake's handling of an imported dead record** (imports were of saves without one in the 19 runs).

## Evidence

- Scripts (`runs/experiments/armyorder117/`):
  - `order_in_play.py`: identity tracking over the original's saves; v1 matched on unit names only and is kept, v2 adds type,
    quality, troops and distance;
  - `sweep_model.py`: ordered sweep groupings;
  - `remake_order.py`: the remake's own campaigns;
  - `remake_same_turns.py`: the remake's End turn from the original's pre-saves;
  - `same_nation.py`;
  - `visit_order.py`: Unicorn F31C in both orders, and the merge control.
- Data (`runs/experiments/data/run-exp-armyorder117/`):
  - `order-in-play-v1/v2.json`, `sweep-model-v1/v2.json`;
  - `remake-order-v1.json`, `remake-same-turns-v1.json`, `same-nation-v1.json`;
  - `visit-order-v1.json`: the F31C swaps;
  - `visit-order-v3.json`: the F31C swaps plus the merge control. v2 was produced with a staging bug that shifted records,
    and was discarded before use.
- Saves:
  - the original's campaign saves `artifacts/run-exp-diff084-campaign/<campaign>/original/tNN-aKK.SAV`
    (release `run-exp-diff084-campaign`);
  - the remake runs in `artifacts/run-exp-armyorder117/remake-v1/<campaign>-tNN/` (release `run-exp-armyorder117`).
- RAM: the #187 snapshot (private).
- Decompile `all_app_functions.txt` (SHA-256 `2018c205…`): ABE0 :49396, ADB0 :49537, 509F0 :53964 (called at :53573),
  F31C :52899.
