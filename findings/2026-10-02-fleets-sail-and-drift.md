# Two fleets sailing toward each other: moves, supplies and condition per turn against the research formulas

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task T1 of `docs/proposals/fleet-battles-and-storms.md`, run on the two-human setup of `findings/2026-10-02-two-human-seats.md` (Carthage and Ptolemaic human, seed 12345). It is a **staging run**, not an experiment on storms or battles; the numbers are a by-product, **three rounds of two fleets** (8 turn-start readings), and they agree with the code reports they are compared with except for one unexplained first turn.

**Answer.**
- **A staging fixture:** the fleets of Carthage (90 ships) and Ptolemaic (70 ships) sailed 140 tiles toward each other along a computed sea path and were **adjacent at the start of Ptolemaic's turn at 0723**, at war (relation 3): `saves/fleets-adjacent-at-sea-0723.SAV`. It took three rounds, 25 + 25, 28 + 23 and 25 + 13 tiles.
- **Moves per turn follow `30 − (ships − 50)/10`, minus 3 at zero supplies and `(70 − condition) >> 2` below condition 70, in 6 of 6 readings after the first turn** (Carthage 23, 23, 23; Ptolemaic 28, 25, 24). On the first turn both fleets had **25**, where the formula gives 26 and 28: unexplained.
- **Supplies burn `ships` tons a turn:** Carthage (90 ships) 80 → 0, Ptolemaic (70 ships) 80 → 10 → 0.
- **Condition fell 3 to 5 points a turn** on calm sea away from any own city, as the storm formula predicts (damage `2·dmg + 1`, plus up to 1 more at zero supplies): Carthage 85 → 81 → 78 → 74, Ptolemaic 75 → 72 → 67 → 63.

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb, `SEED.TXT` = 12345. Script `tests/make_fleet_battle_fixture.py`; the path planner `planner/sea.py` (calm sea cost 1, rough 3; `tests/test_sea_path.py`); driver `harness/driver.py`.
- **Procedure:** New Game with rows 1 and 3 human. Each seat's turn: copy the autosave at once (the second human's overwrites the first's), read the state, sail its fleet along the cheapest sea path to a tile next to the other fleet as far as its moves go (one tile per click, `Game.move_fleet`), End turn. Carthage set war toward Ptolemaic in its first turn (`Game.relation`). The run stops when the fleets are adjacent at the start of a seat's turn.
- **Readings:** from each seat-start autosave (`state/sav.py`): position, ships, condition, moves, supplies, money, per fleet. The turn-start readings are the four seat-2 saves (Ptolemaic's turn starts, 0720-0723) × the two fleets: at a seat-2 start both fleets have their full moves, while at a seat-13 start Ptolemaic's are already spent.

## Observations

Saves are in release `run-exp-fleet-battles`; the fixture is in git.

| turn | fleet | position | ships | condition | moves | supplies (t) | money | formula moves |
|---|---|---|---|---|---|---|---|---|
| 720 | Ptolemaic | (189,89) | 70 | 75 | **25** | 80 | 200 | 28 |
| 720 | Carthage | (49,62) | 90 | 85 | **25** | 80 | 1000 | 26 |
| 721 | Ptolemaic | (164,66) | 70 | 72 | 28 | 10 | 200 | 28 |
| 721 | Carthage | (74,52) | 90 | 81 | 23 | 0 | 1000 | 26 − 3 = 23 |
| 722 | Ptolemaic | (136,65) | 70 | 67 | 25 | 0 | 200 | 28 − 3 − 0 = 25 |
| 722 | Carthage | (97,64) | 90 | 78 | 23 | 0 | 1000 | 26 − 3 = 23 |
| 723 | Ptolemaic | (111,73) | 70 | 63 | 24 | 0 | 200 | 28 − 3 − 1 = 24 |
| 723 | Carthage | (110,73) | 90 | 74 | 23 | 0 | 1000 | 26 − 3 = 23 |

(All eight rows are from the saves `T1_0720_s02_Ptolemaic.SAV` … `T1_0723_s02_Ptolemaic.SAV`, the turn start of Ptolemaic's seat.) After sailing, `moves_after` was 0 except Carthage's last leg (10 left: it stopped adjacent), so the formula column is compared with the turn-start value only.

**Route.** The planned path from (49,62) to a tile next to (190,93) is 140 tiles, cost 140, all calm sea (`tests/test_sea_path.py`). Positions per seat: Ptolemaic (189,89) → (164,66) → (136,65) → (111,73); Carthage (49,62) → (74,52) → (97,64) → (110,73). The game accepted every one-tile click along the path and stopped nowhere early.

**Supplies.** 80 tons each at the start, `ships` tons burnt a turn: Carthage 80 − 90 → 0 (at 0 from turn 721), Ptolemaic 80 − 70 = 10 (turn 721), then 0 (722).
**Condition.** Carthage 85, 81, 78, 74 (−4, −3, −4); Ptolemaic 75, 72, 67, 63 (−3, −5, −4). For condition 85 the storm formula's `max(1, Random(100 − condition)/10)` is 1, so damage `2·1 + 1 = 3` away from a city, plus `Random(2)` at zero supplies (the −4 turns); for condition 75 it is 1 or 2, so 3 or 5. The observed drops are all among those values.
**Money aboard:** Carthage's fleet 1,000 talents, Ptolemaic's 200, both unchanged.
**The first turn.** Both fleets showed **25** moves at 0720 (seat 2 and 13 starts) although their supplies were 80 tons (no penalty) and their condition ≥ 70: the formula gives 26 (90 ships) and 28 (70 ships). `docs/rules-digest.md` §10 notes moves 8 in the start state becoming 9 after the first tick for armies ("the session-start effect"); a similar start-of-game effect for fleets is a guess, not tested.

**War.** Carthage's war order in its first turn: the relation Carthage–Ptolemaic is 3 in every later save (`T1_0721_s02_Ptolemaic.SAV` onward), as in the T0 finding.

## Inferences

- The fleet formulas in the research reports hold on every reading after the first turn, including the zero-supply and low-condition terms, and the supply burn and the condition drift fit the storm and supply formulas; this is a confirmation of the code reports, small (8 readings, one seed, calm sea, no rough water, no army aboard).
- Fleets of 90 and 70 ships close 140 tiles in about three rounds when both sail (≈ 25 each a turn), with the second mover able to stop adjacent: the staging works without surprises from the AI, the weather or the other human.
- The two fleets arrive with **condition 74 and 63 and zero supplies**: any battle from this fixture is between worn, unsupplied fleets. For the plan's equal-condition cells, supply and repair must be part of the staging; for the "condition term" cells, the natural difference (74 v 63) is a free pair.

## What this does not establish

- **Any battle:** this is staging; the fleets were not attacked or attacking. **Storms, rough water and loss at sea:** not tested; every tile of the route was calm and the damage observed is the ordinary kind.
- **The first-turn deviation** (25 against 26 and 28): unexplained, two readings.
- **The condition formula's randomness:** three drops per fleet cannot show a distribution; "consistent with" is all that is claimed.
- **Other seeds, other nations, an army aboard** (the formula's cargo term): not tested. **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 -m tests.test_sea_path               # the planner, pure logic
python3 -m tests.make_fleet_battle_fixture   # about 20 minutes; writes artifacts/run-exp-fleet-battles/
```
