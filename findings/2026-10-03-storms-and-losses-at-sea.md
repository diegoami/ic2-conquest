# Storms: the research formula reproduces a fleet's damage exactly on rough sea, calm sea, next to a city and in winter; a fleet at condition 45 is lost at sea, and an army aboard dies with it or survives as one shrunken unit

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task T4 of `docs/proposals/fleet-battles-and-storms.md`. One fleet (Carthage, 90 ships, the two-human start of `findings/2026-10-02-two-human-seats.md`, seed set 1 to 10) gets **one storm** per trial; 90 trials in twelve cells. **Evidence classes are kept apart:** cells marked *natural* are the start save as it is; cells marked *synthetic* are an edit of the save (condition, season or cargo, `runs/experiments/storms/t4_stage.py`), which tests the formula, not play. **One natural loss at sea was observed** (the idle run below, seed 1: Ptolemaic's fleet, 0727); every other loss below is in a condition-edited cell.

**Answer.**
- **The storm formula of the code reports reproduces every trial at condition 85 exactly** (there the random draw is constant, `Random(15)/10` giving damage 1, so these cells test the branches and the arithmetic; the random draw is tested by the condition-45 cells, which are synthetic, and by the natural Ptolemaic sample below) (natural cells: rough sea, calm sea away from a city, next to a city; edited-season cells: the same in Winter). Example: on rough sea at condition 85, Spring, **90 ships and condition 85 → 65 ships and condition 60 or 61, in 5 of 5 seeds** (ships −25, condition −24 or −25), news "A fleet belonging to Carthage is damaged in a storm."
- **Winter and rough sea compose as the formula says, winter first:** rough sea in Winter at condition 85 gives ships −23 and condition −21 or −22 (5 of 5), the value for damage 13 (`min(5, 2·1) = 2`, then `min(8, 3·2) = 6`, then `2·6 + 1`); rough sea alone gives damage 7.
- **Next to an own city the damage is halved to nothing at condition 85** (condition −0 or −1, only the out-of-supply term) and away from cities it is `2·dmg + 1` (condition −3 or −4 in Spring, −5 or −6 in Winter).
- **A fleet at condition 45 in open water is lost at sea** ("A fleet belonging to Carthage is lost at sea.", the fleet gone from the table, any army aboard gone): **10 of 10 on rough sea** (Spring, Winter, and with an army aboard), **6 of 10 on calm sea away from cities in Spring and 7 of 10 in Winter** (the formula expects about 4.5 and 6.5), **0 of 10 next to an own city**.
- **A natural loss at sea:** with nothing edited, both humans only ending their turns (seed 1), the fleets drifted down on calm sea (Carthage 85 → 60 in six turns, Ptolemaic 75 → 52) until at 0727 **"A fleet belonging to Ptolemaic is lost at sea."** (condition 52, 70 ships; the same storm cost Carthage's fleet 25 ships and took it from 60 to 42: "damaged in a storm"); saves `NAT_seed1_11_0726_seat02.SAV` (Ptolemaic's turn start at 0726, before) and `NAT_seed1_13_0727_seat02.SAV` (after).
- **The loss test comes before the out-of-supply decrement:** two fleets ended at condition 39 and survived (the formula's "condition below 40" is tested on the storm damage alone).
- **An army aboard a fleet that survives a large storm is cut to one shrunken unit or to nothing:** the mixed 11,000-man army aboard on rough sea at condition 85 ended as **a single unit of 312 to 850 men** in 4 of 5 seeds and **gone** in the fifth (the five types: light and heavy infantry, archers, light and heavy cavalry), the "whole units lost when `d > 70`" rule. In the 10 trials where the fleet was lost the army was lost with it (no army left aboard).

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb; one fresh process per trial, `SEED.TXT` = the seed 1 to 10 (shared by every cell, so cells with the same seed share their draws).
- **Start:** `T1_0720_s13_Carthage.SAV` (Carthage's turn at 0720, Spring): Carthage fleet 0 at (49,62), 90 ships, condition 85, supplies 80 (burnt to 0 at the first tick); Ptolemaic fleet 1 at (164,66), 70 ships, condition 75, supplies 80. **Rough tiles are read from the save's map** (code 1; the paint is replaced entirely every turn: 112 tiles at 0720, none kept the next turn). The nearest is (38,74); the fleet sails 17 moves there (`planner/sea.py`, cost 3 on rough sea) and its record's **covered-terrain field (offset 24) reads 1**. A fleet's map cell holds its marker (333), so the covered field is how a fleet "on rough sea" is recognised.
- **One trial:** load the fixture with the seed; sail to the cell's place (rough tile; or stay at (49,62), two tiles from Akra Leuke and away from any own city; or sail to (48,64) next to Akra Leuke); End turn once; the next autosave (Ptolemaic's turn start, after the weather tick and the AI seats) is the result. `t4_trials.py`; every low-condition and every first-seed trial's autosave is kept.
- **Cells.** *Natural:* R85s (rough), K85s (calm, away), H85s (next to a city), 5 seeds each. *Season edited to Winter (the save's season field):* R85w, K85w (5 each). *Condition edited to 45:* R45s, K45s, H45s (Spring), R45w, K45w (Winter), 10 seeds each. *Cargo edited aboard* (`put_cargo` of the T3 finding, the mixed 11,000-man army): R85sA (5), R45sA (10, condition 45). The edit tool is round-trip tested (`t4_stage.py`: with nothing changed the file is identical; each edit changes only its field).
- **The formula** (`t4_analysis.py`, a literal simulation): `dmg = max(1, Random(100 − condition)/10)`; Winter: `min(5, 2·dmg)`; rough: `min(8, 3·dmg)`; away from cities `2·dmg + 1` (Winter: a 1-in-20 spike to 30), next to one `dmg/2`; `dmg < 6`: condition −= dmg; otherwise ships and condition lose `d/300` of themselves with `d = (10000/(dmg+100))²/100` in integer steps; condition below 40 after the damage: lost; then out of supplies: condition −= Random(2).

## Observations

Saves, fixtures, `t4_trials.json` and the logs are in release `run-exp-storms`; the autosave of each trial's result is `ST_<cell>_seed<k>_AUTO0721.SAV` (kept for every first seed, every low-condition cell and every loss; for example `ST_R85s_seed1_AUTO0721.SAV`, `ST_R45s_seed1_AUTO0721.SAV`, `ST_K45s_seed2_AUTO0721.SAV`, the fixture `FIX_T4_K45s.SAV`), turn 0721 (Ptolemaic's seat, after the tick); ships/condition are lost, as (ships, condition).

| cell | place, season | trials | observed | the formula expects |
|---|---|---|---|---|
| R85s *natural* | rough, Spring | 5 | (25, 25) × 3, (25, 24) × 2 | (25, 24) 0.50, (25, 25) 0.50 |
| K85s *natural* | calm, away | 5 | (0, 4) × 3, (0, 3) × 2 | (0, 3) 0.50, (0, 4) 0.50 |
| H85s *natural* | next to a city | 5 | (0, 1) × 3, (0, 0) × 2 | (0, 0) 0.50, (0, 1) 0.50 |
| R85w *season edited* | rough, Winter | 5 | (23, 21) × 4, (23, 22) × 1 | (23, 22) 0.48, (23, 21) 0.47, spike 0.05 |
| K85w *season edited* | calm, away, Winter | 5 | (0, 5) × 4, (0, 6) × 1 | (0, 5) 0.47, (0, 6) 0.48, spike 0.05 |
| R85sA *cargo edited* | rough, Spring, army aboard | 5 | (25, 25) × 4, (25, 24) × 1, army below | as R85s |
| R45s *condition edited* | rough, Spring | 10 | lost × 10 | lost 1.0 |
| R45w *condition + season* | rough, Winter | 10 | lost × 10 | lost 1.0 |
| R45sA *condition + cargo* | rough, Spring, army aboard | 10 | lost × 10 (army gone with it) | lost 1.0 |
| K45s *condition edited* | calm, away | 10 | lost × 6; (0, 3), (0, 4), (0, 5), (0, 6) one each | lost 0.45; (0, 3) 0.18, (0, 4) 0.19, (0, 5) 0.09, (0, 6) 0.09 |
| K45w *condition + season* | calm, away, Winter | 10 | lost × 7; (0, 6) × 3 | lost 0.65; (0, 5) 0.18, (0, 6) 0.17 |
| H45s *condition edited* | next to a city | 10 | (0, 3) × 4, (0, 1) × 3, (0, 2) × 2, (0, 0) × 1 | (0, 1) 0.37, (0, 2) 0.31, (0, 0) 0.19, (0, 3) 0.14 |

**The covered field.** On rough sea the record read 1 before End turn and 0 afterwards (the paint is gone at the next tick); the storm used the state at the tick. **News:** a hit that costs ships says "A fleet belonging to X is damaged in a storm."; a loss says "A fleet belonging to X is lost at sea." (all 43 losses of Carthage's fleet, in R45s, R45w, R45sA, K45s and K45w).

**The loss threshold.** Four survivors ended at condition 39 (K45s seed 3: damage 5 and a supply drop of 1; the three K45w survivors: damage 5 and a drop of 1) and one at 40 (K45s seed 1): the fleet is lost when the condition after the storm damage is below 40, **before** the out-of-supply term is taken off.

**The army in R85sA** (the mixed army, 11,000 men: 4,000 light infantry, 3,000 heavy infantry, 2,000 archers, 1,000 light and 1,000 heavy cavalry, aboard fleet 0 of 90 ships): after the storm that cost 25 ships, the army record is **one unit** in seeds 1, 2, 3, 5: 678 heavy infantry, 312 heavy cavalry, 850 heavy infantry, 312 heavy cavalry, and **gone** (fleet's carried-army field −1, the record removed from the table) in seed 4. The fleet kept the field (army 2) when anything survived. That fits "an army aboard takes casualties, and if `d > 70` loses whole units" (`d` was 86 here): units are lost whole until one remains, and the remainder is a fraction of its size (22.6 % to 31.2 % in these three cases).

**Ptolemaic's fleet** (70 ships, condition 75, supplies 80, calm sea away from cities: a free sample in every trial; the same seeds in every cell give the same draw, so the **independent** samples are the 10 seeds, not the 90 trials): in Spring, condition −3 in 7 or 8 seeds and −5 in 2 or 3 (the formula's 0.8 and 0.2); in **Winter** −5 in 4 seeds, (ships −19, condition −20) in 5, and the 30-spike (ships −13, condition −14) in 1. The damage-9 outcomes are more frequent than the formula's 0.19 expects (5 of 10: about 3 % chance of 5 or more); see Inferences.

**The natural idle run** (`t4_natural.py 1`, nothing edited; seed 1; both fleets stay, calm sea, away from their cities, supplies 0 from 0721):

| turn start | Carthage (90 ships): condition | Ptolemaic (70 ships): condition | save |
|---|---|---|---|
| 0720 | 85 | 75 | `T1_0720_s13_Carthage.SAV` |
| 0721 | 82 | 72 | `NAT_seed1_01_0721_seat02.SAV` |
| 0722 | 78 | 69 | `NAT_seed1_03_0722_seat02.SAV` |
| 0723 | 74 | 64 | `NAT_seed1_05_0723_seat02.SAV` |
| 0724 | 69 | 59 | `NAT_seed1_07_0724_seat02.SAV` |
| 0725 | 64 | 56 | `NAT_seed1_09_0725_seat02.SAV` |
| 0726 | 60 | 52 | `NAT_seed1_11_0726_seat02.SAV` |
| 0727 | **65 ships, 42** ("damaged in a storm") | **lost at sea** | `NAT_seed1_13_0727_seat02.SAV` |

The drift is the calm-sea branch (3 to 5 points a turn). At 0727 both drew a large hit: Carthage at condition 60 took damage 7 (ships −25, condition −17, and −1 for supplies, the same `d = 86` as the rough-sea cells), and Ptolemaic at 52 took damage 9 (`d = 82`: condition −14 would leave 38, below 40) and was lost. The formula's own draws (`Random(100 − condition)/10` of 3 and 4 at those conditions) explain both. One run, one seed.

## Inferences

- **The storm formula of the research reports, read from code, describes the live game:** its three branches (the condition drop below damage 6, the `d/300` loss above it, the loss below 40), the Winter doubling, the rough-sea tripling and their order, the halving next to a city, the doubling and +1 away from cities, the integer arithmetic of `d`, and the zero-supply term, with no unexplained residual in 12 cells (the two small deviations below are the only misses).
- **Rough sea is the dangerous place:** a healthy fleet (85) loses 28 % of its ships and 25 condition points in one storm there, and a fleet at 45 is lost with certainty, while the same fleet on calm sea loses 3 or 4 points; and next to a city a storm costs nothing. For play: park a worn fleet at a city, never in a rough patch; an army aboard a fleet on rough sea is a gamble with the whole army.
- **Rough tiles last one turn** (none kept between consecutive saves), so a fleet is only at risk on the turn it is on one at the tick; whether the rough set of the coming tick can be known from the autosave in advance is not tested (a fleet that stayed on calm sea was never reported on rough sea afterwards).
- **Low condition compounds:** the loss probability on calm sea at condition 45 is 0.45 to 0.65 in one storm; a fleet that drifts below about 50 in open water is likely to be lost within a couple of turns, as the weekly drift of T1 (3 to 5 points) suggests.

## What this does not establish

- **More than one natural loss:** one natural loss (seed 1) meets the plan's "at least one" with its saves before and after; its timing (the 13th End turn) is one draw, and the 43 other losses are in cells with the condition edited to 45. Whether a winter run or other seeds lose fleets earlier or later was not run.
- **The 5,000 and 15,000-man cargo cells and the casualty distribution of `dmg ≥ 6` below `d = 70`:** only the one mixed 11,000-man army was aboard, and only at `d = 86`. Whether a smaller `dmg` (a smaller `d` above 70, or `d < 70`) leaves more units is not tested (the formula has the branch; no cell reached it).
- **The Winter spike and the weather's frequency:** the Ptolemaic fleet's 10 Winter draws show one spike (ships −13, condition −14), and Carthage's Winter cells at condition 85 had no spike in 10 trials (expected 0.5); the 1-in-20 spike is neither confirmed nor excluded. The weather's own rolls (20 region centres, Winter 1/5) were not measured; the cells place the fleet on a tile that is rough now.
- **Two small deviations:** the **Ptolemaic fleet in Winter** (large damage in 6 of 10 seeds against 0.24 expected, p about 0.02) and **H45s** (four of ten at condition −3 against 1.4 expected, p about 0.05) are unexplained; with twelve cells and twelve comparisons one or two such misses are expected by chance, and neither is claimed.
- **Exactly one fixture and one fleet size** (90 ships; Ptolemaic's 70 as a side sample): the ship loss `ships × d / 300` was checked at two values of `d` (86 and 77); other damage values are not tested. Supplies are zero in every Carthage cell at the tick; the supplied case (no −Random(2), no −3 moves) is seen only in the Ptolemaic sample.
- **Item 4.6 of the plan** (a fleet in rough sea with its moves spent: whether it can leave, cost 3 per tile): not run. **The cell values for the 45 edits are synthetic.** **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 -m tests.make_fleet_battle_fixture                  # the T1 fixture saves (or use artifacts of run-exp-fleet-battles)
python3 runs/experiments/storms/t4_stage.py                 # the edit tool's round-trip test
python3 runs/experiments/storms/t4_probe.py 1 2 3 4 5       # the first probe: rough sea at condition 85
python3 runs/experiments/storms/t4_trials.py                # 90 trials in 12 cells, about 3.5 hours
python3 runs/experiments/storms/t4_natural.py 1             # the natural idle run to a loss at sea (about 40 minutes)
python3 runs/experiments/storms/t4_analysis.py              # observed against the formula
```
