# Naval battles between two fleets at war: instant, decided by strength, the loser sinks whole, the winner loses one fraction of ships and condition

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task T2 of `docs/proposals/fleet-battles-and-storms.md` (the first live naval battles; no army aboard, calm sea, **war already declared**), on the fixture of `findings/2026-10-02-fleets-sail-and-drift.md`. **50 battles**, 10 seeds in each of five cells, two fleets of one pair of nations.

**Answer.**
- **A naval battle is instant:** clicking an adjacent enemy fleet with your fleet selected, at war, opens **no window and no box**; the news of the next turn says "Carthage sinks fleet of Ptolemaic."
- **The loser always sinks whole** (50 of 50 battles); **the winner lives and loses one fraction of both its ships and its condition**: in all 50 battles the two fractions agree within 0.013 (for example 18 of 90 ships and 14 of 74 condition points).
- **The stronger fleet by `ships × condition / 10` won 48 of 50 battles.** At strength ratios of 0.66, 1.51 and 1.17 (attacker over defender) it won every time; at 1.007 the attacker won 9 of 10 and at 0.84 the defender won 9 of 10, one upset each way. The outcome follows the ratio sharply, with no chance of the weaker side winning at ratios of 1.5 or 1.17 and a rare one at parity; **which model of the random term fits is not settled.**
- **The winner's fraction of loss rises as the loser was closer in strength:** about 0.12 to 0.16 (loser/winner strength 0.66), about 0.20 to 0.25 (0.84 to 0.85), about 0.27 (0.99).
- **The attacker spends all its moves** (23 → 0); a defender that wins keeps its moves.

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb. One fresh process per trial, `SEED.TXT` = the trial's seed 1 to 10 (the random generator is seeded at program start, `findings/2026-09-29-loading-a-save-does-not-reseed.md`).
- **Fixtures:** `FIX_P` is `saves/fleets-adjacent-at-sea-0723.SAV` (Ptolemaic's turn at 0723): Ptolemaic fleet 1, **70 ships, condition 63**, at (111,73), and Carthage fleet 0, **90 ships, condition 74**, at (110,73), war (relation 3). `FIX_C` (`stage_cells.py`) is the same turn at **Carthage's** seat: Ptolemaic ended its turn without acting; the autosave of Carthage's turn start has the same fleets in the same places. It reproduced byte for byte on a second run.
- **Cells** (attacker versus defender; "strength" is the research formula `ships × condition / 10`, before its random 0–30 %):

| cell | fixture | attacker | defender | strength | ratio |
|---|---|---|---|---|---|
| P | FIX_P | Ptolemaic 70 × 63 | Carthage 90 × 74 | 441 v 666 | 0.66 |
| C | FIX_C | Carthage 90 × 74 | Ptolemaic 70 × 63 | 666 v 441 | 1.51 |
| C70 | FIX_C | Carthage, 20 ships split off first: 70 × 74 | Ptolemaic 70 × 63 | 518 v 441 | 1.17 |
| C60 | FIX_C | Carthage, 30 split off: 60 × 74 | Ptolemaic 70 × 63 | 444 v 441 | 1.007 |
| C50 | FIX_C | Carthage, 40 split off: 50 × 74 | Ptolemaic 70 × 63 | 370 v 441 | 0.84 |

- **Driver:** `Game.attack_fleet(own, enemy)` (select the fleet, click the adjacent enemy fleet; with a peace prompt it can capture or answer it) and `Game.fleet_state(i)`, which reads a fleet's record (x, y, owner, moves, supplies, money, ships, condition, carried army) from the game's memory; an owner of −1 is a destroyed fleet. Script `runs/experiments/fleet-battles/trials.py`: load a fixture with the seed, (split), read both fleets, attack, read both fleets again; the first seed of each cell also saves. `probe_attack.py` was the first look, with nothing auto-answered.

## Observations

Saves, the probe and `trials.json` are in release `run-exp-naval-battle`.

**The first battle** (`probe_attack.py`, seed 12345, from FIX_P; `PROBE_START.SAV` → `PROBE_AFTER.SAV`): after the click no window or box appeared in 20 seconds of watching, the battle flag stayed 0, and the selection cleared. The save shows Ptolemaic's fleet gone and Carthage's at 80 ships, condition 66 (from 90 and 74), moves 23, supplies 0; the news ends "Week 7 Spring 270BC / Carthage sinks fleet of Ptolemaic."

**The 50 trials** (`trials.json`; `NB_<cell>_seed1.SAV` per cell):

| cell | ratio | attacker wins | defender wins | winner's ships lost (fraction) | winner's condition lost (fraction) |
|---|---|---|---|---|---|
| P | 0.66 | 0 / 10 | 10 / 10 | 11–21 of 90 (0.122–0.233, mean 0.162) | 9–18 of 74 (0.122–0.243) |
| C | 1.51 | 10 / 10 | 0 / 10 | 7–15 of 90 (0.078–0.167, mean 0.122) | 6–12 of 74 (0.081–0.162) |
| C70 | 1.17 | 10 / 10 | 0 / 10 | 9–19 of 70 (0.129–0.271, mean 0.203) | 10–20 of 74 (0.135–0.270) |
| C60 | 1.007 | **9 / 10** | 1 / 10 (seed 10) | 11–19 of 60 when the attacker won, 19 of 70 when the defender did (0.183–0.317, mean 0.272) | 14–24 of 74 when the attacker won, 17 of 63 when the defender did (0.189–0.324) |
| C50 | 0.84 | 1 / 10 (seed 8) | **9 / 10** | 13–22 of 70 when the defender won, 13 of 50 when the attacker did (0.186–0.314, mean 0.245) | 12–20 of 63 when the defender won, 20 of 74 when the attacker did (0.190–0.317) |

In every one of the 50 battles the loser's fleet was destroyed (owner −1) and the winner's ships and condition fell **by the same fraction** (largest difference between the two fractions 0.013). No box appeared in any trial (they were at war). The attacker, when it wins, ends with moves 0; a winning defender's moves were unchanged (23).

**Against a model.** If each side's strength is multiplied by `1 + U(0, 0.3)` independently (the research formula read literally), the expected attacker win rates are 0.000, 0.926, 0.525, 0.055 and 1.000 for P, C70, C60, C50 and C; observed 0, 10/10, 9/10, 1/10, 10/10. Four cells fit; **C60 is an outlier** (9 or more of 10 has about a 1.7 % probability under 0.525). If only the attacker has a random term the expected rates are 0, 1.0, 1.0, 0.361, 1.0: C60 fits and C50 does not fit well (1 or fewer of 10 has about a 7 % probability under 0.361).

**Also seen** (staging, `stage_cells.json`): the End turn box listed several fleet and army warnings in one box: "An army of yours needs supplies. An army of yours cannot afford to pay its mercenary units. A fleet of yours needs repairing. One of your fleets is not docked at its own city. A fleet of yours needs supplies. If you have not finished your turn click MAKE MORE MOVES. If you are finished moving this turn click END TURN." (so "One of your fleets is not docked at its own city", listed as unseen in `coverage.md`, was seen).

## Inferences

- The research formula's strength term is **the** driver of the result: a ratio of 1.17 or more (or 0.66) never lost in 30 battles, and an attacker 16 % weaker won once in 10.
- **Damage is proportional:** one fraction applies to both ships and condition, and it grows with the loser's relative strength (a close fight costs the winner about a quarter of its fleet, a lopsided one about an eighth to a sixth).
- Whether the random term is the research's "0–30 %" on both sides, an attacker advantage, or a smaller term is **not settled**: the parity cell (C60) leans to an attacker advantage or a small random term, the other cells to the symmetric model. More seeds at parity and the roles swapped (Ptolemaic attacking an equal Carthaginian fleet) would decide it.
- The loser is destroyed outright and the winner pays a fraction: after a war of such battles the fleets that survive are worn (here the winners end at condition 43 to 68, all below 70, the threshold of the moves formula), which links this to the storm and repair findings.

## What this does not establish

- **Armies aboard** (T3), **rough sea**, **storms and losses at sea** (T4): not tested. All fleets here carried nothing, on calm sea.
- **The peace prompt for a fleet** ("Are you sure you want to attack this fleet ?", and the war declaration on Yes): not tested (they were at war), and so is "You cannot attack a fleet docked at its own city !".
- **The random term:** see above; 10 seeds per cell cannot separate 50 % from 60 %, and only one cell is at parity. Whether seeds that give equal damage across cells (several seeds gave the same ship loss in two cells) share a draw was not checked.
- **One pair of fleets, one fixture turn,** both fleets worn and unsupplied (supplies 0); equal conditions and well-supplied fleets were not staged. Whether supplies or the seat matter is untested.
- **The attacker's side:** the cells swap the attacker only between P and C (and in C70, C60, C50 Carthage always attacks); no cell has the weaker-by-condition fleet attacking at parity.
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 -m tests.make_fleet_battle_fixture                       # about 20 minutes: the fixture (or use saves/fleets-adjacent-at-sea-0723.SAV)
python3 runs/experiments/fleet-battles/stage_cells.py            # FIX_C
python3 runs/experiments/fleet-battles/trials.py                 # all five cells, 10 seeds each, about 40 minutes
```
