# Recheck on remake v0.10.2 (`d4a12c21`): 37 sampled rows fixed in play (the six read ones by T282's per-army support); one new rule row, a knock-on of the new walk-end support tail

**Tag:** [confirmed: anchored remake replays against stored original games, plus a 20-seed sweep per changed row on
both pins]. The original side is the stored Wine games: no new Wine run.
**Status:** promoted 2026-11-09 into imperial-conquest-2-research (research PR #228, by ic2-research, from `173214b4`); this draft is kept for history, the research repo is canonical. Research recounted the rows, sweep classes, stays, the six AI-log diffs and the t102 error from the receipts; the replays, the sweep and the registry were not re-run. Its three narrowings are carried below (marked "research PR #228").
**Task:** owner 2026-11-09: recheck on v0.10.2. The remake's T282 (#1782, `4816a301`) fixes five #195 items, X1/#1771,
X2/#1772, B03/#1773, D05/#1774 and C23/#1775, and asks for "correction commits for researcher rechecks". This is
that recheck.

**Pins.**
- **New:** tag `v0.10.2` = `d4a12c21` (T284, 2026-11-07), 21 commits after v0.9.4 = `168dbc04`, the previous
  recheck's pin.
- **Old:** `168dbc04`.
- **Builds:** `python3 -m difftest.pin build v0.10.2` (`artifacts/diffpin-d4a12c21-build`). The AI-log runs use the
  same CLI build with conquest main's adapter, which has the opt-in `ailog` (`artifacts/diffpin-d4a12c21-ailog-build`).
- **The anchored replays** ran with the adapter of branch `long-games` (`e0f07d29`), whose difftest differs from main
  only by that opt-in option and one probe file.

## 1. Anchored replays of every stored game

**Runs.** 27 games, 1,648 turns, all `--turn-seed 12345 --out anchored-d4a12c21-ts`, with the runner
`runs/experiments/longrun-v090/recheck_pin.sh` (`PIN=d4a12c21`):
- the 19 games of the 168dbc04 recheck: sixteen 40-turn games, and Rome, Rome-h1 and Carthage to 264 BC;
- the 8 later long games: three observer games (Ptolemaic, Seleucid, Macedonia), Ptolemaic rulebot-2 and its h1,
  Seleucid rulebot-2 and its h1 and h2.

The 168dbc04 baseline for each game is `anchored-168dbc04-ts`, or for the eight later games `anchored-turnseed`
(played on 168dbc04 by `runs/experiments/longgames/run_queue.sh`).

**Totals** (`pin_diff.py`, `pin-diff-168dbc04-vs-d4a12c21-v1.txt`). Position rows go from **1,327 to 1,121**: 225
rows gone, 19 new. There is one remake error, the same on both pins (below).

| games | rows 168dbc04 → d4a12c21 |
|---|---|
| the sixteen 40-turn games | 305 → 291 |
| Rome / Rome-h1 / Carthage (264 BC) | 28 → 26 / 58 → 55 / 194 → 166 |
| observers: Ptolemaic / Seleucid / Macedonia | 147 → 107 / 113 → 65 / 104 → 59 |
| Ptolemaic rulebot-2 / h1 | 5 → 5 / 190 → 172 |
| Seleucid rulebot-2 / h1 / h2 | 14 → 14 / 92 → 89 / 77 → 72 |

**The error row** (Seleucid observer t102, both pins): the remake refuses to import the original's t101 end save,
`Relation matrix is not symmetric: [3][6] = -6 but [6][3] = 0` (`SaveNationTable.ValidateRelations`). The original
wrote an asymmetric relation pair between Ptolemaic (3) and Gaul (6), and the importer rejects it. This is not new in
v0.10.2.

**Stays** (`stays.py`, `stays-168dbc04-v1.jsonl` → `stays-d4a12c21-v1.jsonl`): 178 → 156, 31 gone and 9 new.
- **Army own-capital stays:** 76 → 56.
- **The nine #195 diplomacy-draw stays** (`R/2026-11-05-audit195-final-hooks.md` §2) are all still present, as
  expected. The 10th own-capital row, Greece t21, is X2's, and it is gone.

## 2. Which changes are rules and which are draws: a 20-seed sweep per row on both pins

**Why a sweep.** An anchored replay is one seed per turn. A pin that consumes draws in a different order (T282 moves
the support pass and the diplomacy phase) changes that seed's outcome even where no rule changed. In the first case
read, Gaul t1, the "new" Carthage rows came from a post-battle peace suit (`Random(5)`): it fires on 6 of 20 seeds on
**both** pins, and the anchored seed hit on 168dbc04 and missed on d4a12c21.

**Method.** `runs/experiments/recheck-v0102/row_sweep.py` replays the anchored turn from the original's own start, on
seeds 5001–5020 and on both pins. It counts the seeds where the row's nation ends with the original's armies (x, y,
troops) or launched fleets (x, y, ships). The rows swept:
- all 19 new rows;
- every gone row of the 40-turn games and of Rome/Rome-h1;
- for the long games, the first gone row of each (game, nation) cluster: 40 samples covering 196 gone rows.

Results: `sweep-batch1/`, `sweep-batch2/` (`rows.jsonl`, `summary.json`); classes: `sweep-classes-v1.txt`.

| class | gone rows | new rows |
|---|---|---|
| **rule fixed** (≤ 4/20 on 168dbc04, ≥ 16/20 on d4a12c21) | **37** | — |
| rate improved (+5 or more) | 7 | — |
| same rate (± 4): the anchored seed's luck, or a draw | 25 | 18 |
| **rule regressed** (≥ 16 → ≤ 4) | — | **1** |

- **The 37 rule-fixed rows include** Greece t21/23/26/32 Seleucid (X2's own row, t21, plus three more turns of the
  same army), Bithynia t26 (Carthage and Ptolemaic, armies and fleets), Rome-h1 t33/35/44 Ptolemaic, Carthage t23
  Bithynia, and Gaul t25 Seleucid. In the long games: Carthage game t23, t45 (Media), t104, t124, t126, t147;
  Macedonia observer t67, t74, t77, t97; Ptolemaic observer t23, t47, t50, t70, t71, t145; and others
  (`sweep-classes-v1.txt` lists the rest).
- **"Same rate" gone rows** are rows the remake still gets wrong on most seeds (0–4 of 20) on both pins. Their
  anchored seed happened to match on d4a12c21. They are **not** fixes.
- **"Same rate" new rows** match on 17–20 of 20 seeds on both pins (Gaul t1: 6/20 and 0/20 on both), so they are
  not rule changes.

**Attribution of the fixed rows (X2)** `[derived: the remake's own AI log, both pins, anchored seed;
ailog-diffs/]`. Six rows were read:

| row | 168dbc04 | d4a12c21 |
|---|---|---|
| Bithynia t26, Carthage army-3 | carried-army landing (82,79) | carried-army landing (93,78) |
| Rome-h1 t33, Ptolemaic army-3 | resupply city (138,97) | resupply city (124,105) |
| Carthage t23, Bithynia army-9 | resupply city (202,24) | resupply city (209,22) |
| Gaul t25, Seleucid army-4 | resupply city (220,59) | resupply city (213,45) |
| Greece t23, Seleucid army-9 | resupply city (234,60) | resupply city (234,66) |
| Greece t32, Seleucid army-2 | garrison fallback (220,54) | mercenary run (208,57) |

In each, the other log difference is where the support/hire pass runs: up front on 168dbc04, per army on
d4a12c21. One exception (research PR #228): in Bithynia t26 Ptolemaic's log the fleet-1 branch also changes, from
hunt (hunt score 242) to stored-route (hunt −10000), so for that log the support pass is not the only other difference.
So X2's per-army support timing (#1772) changes the target choice in these six rows, and the new choice matches the
original in 18–20 of 20 seeds. **The other 31 rule-fixed rows are not attributed** (research PR #228): T282 also moved
the diplomacy phase, and the pin spans 21 commits, so "X2 fixed in play" holds for the six read rows, and the 37 are
not all shown to be X2. The rate-improved rows (Greece t21
fleets 0 → 15; Thracia t38 Carthage, Ptolemaic ×2 5 → 10; Carthage game t70 Seleucid fleets 0 → 12 and t98
Ptolemaic fleets 0 → 15; Seleucid observer t20 Bithynia 0 → 11) were not read.

## 3. The one new rule row: Ptolemaic observer t123, Seleucid's fleet at (219,55)

**What changes** `[confirmed: replays]`. The original and 168dbc04 keep the 43-ship fleet at (219,55), next to Issus
(220,54), on 20 of 20 seeds. On d4a12c21 it ends elsewhere on 17 of 20 seeds; at the anchored seed it sails to (220,65), next to Aradus. Both pins log the
same branch, "fleet-4 port, support 1": the port the branch picks changed, not the branch.

**Why, as far as it was traced** `[derived: end saves and AI log at the anchored seed 12468]`:
- **The port rule:** `OriginalFleetPort.Pick` takes the nearest own port city with more than 20 tons; Issus at
  distance 1 scores −1 when the fleet has supplies. Neither `OriginalFleetPort.cs` nor `OriginalFleetPhase.cs`
  changed between the pins.
- **The army, an old difference:** Seleucid's army-13 starts at (221,60) and is sent to "the resupply city (220,54)",
  Issus, on both pins. It ends at (220,55); the original's army ends at (225,54). This army difference is
  pre-existing.
- **The supplies, new in d4a12c21:** only on d4a12c21 does that army end with 509 tons, against 414 in the original
  and on 168dbc04, while Issus ends with 106 (143 in both others) and Aradus with 50 (100 in both others).
- **The reading:** the extra tons and the drained Issus fit T282's new walk-end support tail (C23/#1775,
  `OriginalArmyWalkContact.Resupply`, called on each D734 leg in `MoveArmyCommandHandler`). It services the army at
  its walk-end city Issus, so Issus is at or below 20 tons when the fleet phase picks a port. The original's army
  never ends that walk at Issus, so its tail draws on no city there.
- **So the new row is a knock-on:** a pre-existing army-walk difference plus the newly added tail. It is not shown to
  be a wrong tail rule.

**Not established:**
- the tail's transfer itself: it has no log line, and Issus's stock at fleet-phase time was not read;
- why the army walks to Issus at all, a difference older than v0.10.2.

## 4. Registry recheck (orders, stats, campaigns)

`python3 -m difftest.recheck d4a12c21 --tiers orders stats campaigns --version v1`
(`runs/experiments/data/run-exp-recheck-d4a12c21/`).
- **Against v0.8.4:** 113 unchanged, 11 FIXED, 11 REGRESSED, 4 CHANGED, exactly as at 168dbc04.
- **Against 168dbc04:** each of the 139 tests (100 orders, 22 stats, 17 campaigns) has **the same verdict**. Nothing
  in v0.10.1–v0.10.2 moved a registered order or statistic test.

## 5. What this means for the #195 inventory

| row | before | now |
|---|---|---|
| **X2 / C-row "support and hire timing" (#1772)** | remake gap (up-front support pass) | **fixed in play for the six read rows**, attributed to the per-army pass; 37 sampled gone rows now match on ≥ 16/20 seeds, the other 31 unattributed (research PR #228) |
| X1 (#1771) | remake gap | **not confirmed** (research PR #228): X1's own rows (Rome t29, Macedonia t27, Armenia t36) are gone at the anchored seed but same-rate on 20 seeds (0 → 2, 0 → 1, 0 → 2). The war is a 1-in-10 roll, so a seed sweep may not show X1 at all; a sweep with the war forced would |
| B03 (#1773), D05 (#1774) | remake gaps | corrected in code; not separately seen in the sampled rows; not contradicted |
| C23 (#1775) | MISSING, no measured effect | **implemented**. One stored turn shows an effect (§3): the tail resupplies an army at a walk end the original does not reach |
| the 9 diplomacy-draw stays | draws, measured | unchanged (still present, as expected) |

## Does not establish

- That every one of the 225 gone rows is fixed. 196 long-game gone rows were sampled once per (game, nation): 40 rows.
- That X1, B03 or D05 changed any stored row. No read row showed them; X1's own rows are same-rate (research PR #228).
- That the 31 unread rule-fixed rows are X2's.
- That the remake's import check is right to reject the t102 save. The asymmetric relation pair was written by the
  original itself, so the importer's symmetry check is stricter than the original's data: a remake-side issue candidate
  (research PR #228), not filed from here (rule 2).
- Draw parity. The sweep compares the remake on both pins against one stored original outcome; it does not sample
  the original.
- Native Windows behaviour. Everything original is Wine.

## Evidence

- **Data:** `runs/experiments/data/run-exp-recheck0102/`.
  - the position diff `pin-diff-168dbc04-vs-d4a12c21-v1.txt`;
  - the stays rows `stays-*-v1.jsonl`;
  - the sweep `sweep-rows-v1.txt`, `sweep-batch1/`, `sweep-batch2/`, `sweep-classes-v1.txt`;
  - the AI logs `ailog-diffs/`.
- **Per-game anchored turns:** `runs/experiments/data/run-exp-longrun-v09*/<game>/anchored-d4a12c21-ts/` and
  `run-exp-longgames/<game>/anchored-d4a12c21-ts/`.
- **Registry:** `runs/experiments/data/run-exp-recheck-d4a12c21/`.
- **Scripts:** `runs/experiments/recheck-v0102/row_sweep.py`, `ailog_turn.py`, `ailog_diff.sh`.
- **Saves:** release `run-exp-recheck-d4a12c21`, three files: `recheck-d4a12c21-anchored-saves.tar.gz`,
  `recheck-d4a12c21-registry-saves.tar.gz` and `recheck-d4a12c21-sweep-saves.tar.gz`. Their hashes are in each
  data folder's `SAVES.sha256`.
- **Cited turns:**
  - Ptolemaic observer game t123: start `original/t122-*` end checkpoint, original end `t123-*`;
  - Gaul game t1;
  - Bithynia game t26;
  - Rome-h1 t33;
  - Greece game t21–t32.
