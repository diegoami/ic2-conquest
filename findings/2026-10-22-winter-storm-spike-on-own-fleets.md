# The Winter storm spike to 30, seen on own fleets at sea: 4 of 72 fleet-turns, each loss exactly the code's d = 57 step

2026-10-22. **[confirmed]** (code + play, Wine, staged position). Run `run-exp-manual-gaps`, item B10. Complements
`2026-10-03-storms-and-losses-at-sea.md`, which saw the spike once, on an AI fleet in a season-edited cell.

## Answer

- **Code** (`docs/rules-digest.md` §8): `dmg = max(1, Random(100 − condition)/10)`; Winter `min(5, 2·dmg)`; rough `min(8, 3·dmg)`;
  away from an own city `2·dmg + 1`, **and in Winter 1 in 20 `dmg = 30`**; `dmg < 6`: condition −= dmg; else
  `d = (10000/(dmg+100))²/100` (integer steps) and ships and condition each lose `x·d/300`.
- **Play.** Six Rome fleets of 50 ships, condition 100, supplies 400, on calm open sea 6–9 tiles from any city, Winter week 1,
  270 BC; six End turns (0738 → 0744; the sixth tick still ran as Winter), two seeds (12345 and 1): **72 fleet-turns, every
  one of them matches a code branch** (`b10-table.v1.md`):

  | Outcome | Count | (ships, condition) lost | Code |
  |---|---:|---|---|
  | calm, dmg 5 | 61 | (0, 5) | dmg0 = 1 (always so at condition ≥ 81, `Random(<20)/10` ≤ 1) → Winter 2 → away 5 |
  | calm, dmg 9 | 7 | (13, 20) at 50 ships / cond 75; (11, 17–18) at 41 / 63–68 | dmg0 2 → Winter 4 → away 9, d = 84 |
  | **spike, dmg 30** | **4** | **(9, 17) at cond 90 (twice), (9, 16) at 85, (9, 15) at 80** | d = 76²/100 = 57: 50·57/300 = 9, 90·57/300 = 17, 85 → 16, 80 → 15 |

  - The four spikes: seed 12345 turn 0741 fleet 0; seed 1 turn 0741 fleet 1, turn 0742 fleet 0, turn 0743 fleet 4.
    4 of 72 = 5.6 % against the code's 5 %.
  - **The spike hurts less than the ordinary heavy hit**: −9 ships for dmg 30 against −13 for dmg 9, because `d` falls as dmg
    rises (d = 57 for 30, 84 for 9). At condition ≥ 80 (where the normal Winter hit is only −5 condition) the spike is the only
    way a fleet loses ships on calm sea, so it reads as a sudden loss of about 18 % of the ships.
  - No fleet was lost (lowest condition 46); no weather turned a fleet's tile rough in these runs (covered cell 0 throughout).
  - The End turn box listed "One of your fleets is not docked at its own city" once per fleet away from a city, and
    "A fleet of yours needs repairing." once condition fell low (texts in `b10-storms.jsonl`).

## What this does not establish

- The position is staged (fleets moved, re-owned, given 50 ships and condition 100 by a save edit; `staged-edits.jsonl`); the
  storms themselves are natural. Two seeds only; the 1-in-20 rate is consistent, not measured precisely.
- Rough sea and the next-to-own-city branch were not exercised (the 2026-10-03 finding covers them).

## Evidence

- `runs/experiments/data/run-exp-manual-gaps/`: `b10-storms.jsonl` (fleet records read from memory every turn),
  `b10-table.v1.md` (`b10_analyse.py`, which also reads the sea under each fleet from the autosaves), `staged-edits.jsonl`.
- Saves (Drive `IC2/artifacts/run-exp-manual-gaps/saves/`): `MG_B10_staged_6_rome_fleets_at_sea_winter_270.SAV`
  (`e9f5947dba28…`, from `saves/fleet-split-antium-0734.SAV` `20f38b88cb06…`), the autosaves `MG_B10_seed12345_AUTO0739.SAV` ..
  `AUTO0744.SAV` and `MG_B10_seed1_AUTO0739.SAV` .. `AUTO0744.SAV` (hashes in `SAVES.sha256`); the spike turns are in
  `MG_B10_seed12345_AUTO0741.SAV`, `MG_B10_seed1_AUTO0741.SAV`, `..._AUTO0742.SAV`, `..._AUTO0743.SAV`.
- Seed build `354d8265…`.
