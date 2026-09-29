# Run 0: Rome pilot (rome-v1, 24 turns): proposal

Status: **awaiting the player's approval** in the run's GitHub issue. No turn is played before it.

## What run 0 is for

The pilot proves the harness, the order driver, the logs and the feedback loop over one game-year. Winning is not its goal (README).

- **Start:** a new game, Rome human, default DAT, **seed 12345**: `AUTO0720.SAV` (270 BC Spring week 1), SHA-256 `050bc354f1cbbe37…`, reproduced byte for byte by two independent new games.
- **Length:** 24 turns, 0720 to 0743; the run ends at the autosave `AUTO0744.SAV` (269 BC Spring week 1).
- **Build:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`).
- **Each turn** is played in a fresh game process: `SEED.TXT` = `12345 + (turn − 720)`, open `AUTOnnnn.SAV`, issue the orders, End turn, wait for `AUTO(n+1).SAV`. Any turn can then be replayed exactly from its save and seed.
- **Per turn, in git:** `runs/0/turns/nnnn.md` (intent, strategy step, orders, expected vs actual, surprises), `metrics.csv`, `armies.csv`, `state/nnnn.json`. **Per turn, as artifacts:** the autosave, a full-screen screenshot after the orders and one at the next turn start, `AUTOSAVE.LOG`, `SEED.LOG`. **Per season:** an ffmpeg recording of the display.
- **Artifacts go to** `artifacts/run-0/<season>/` (gitignored), because the session's GitHub proxy refuses release calls even with `IC2_RELEASE_TOKEN` (probe on 2026-09-29: `POST /repos/diegoami/ic2-conquest/releases` → HTTP 403 "Creating, editing, or deleting releases is not permitted for this session type"). At the end of the run the bot posts the exact `gh release create run-0 …` command for the player.

## Before turn 1: orders still to drive

Driven and tested headless on a save diff: new game, open, save, **move, attack (siege), recruit, end turn** (`tests/results.md`). Needed in the first four turns and built next, each with its own save-diff test before first use: **supply army, hire mercenaries, fortify city, join armies, mobilize**. An order whose test fails is dropped from the turn and recorded as a surprise; the run does not stall on it.

## Turn 1: 0720, 270 BC Spring week 1 (`AUTO0720.SAV`)

Position: treasury 2,200; tax 10 %; mobilization 30. Army 0, 23,700 (HI 16,100) at (100,37) beside Arretium, supplies 170/237, morale 70. Army 1, 22,000 (HI 14,600) at (120,53) beside Heraclea, supplies 176/220, morale 68. Gaul's only army, 40,500 (LI 33,600), at (93,28) beside Brixia. Rome moves 12th of the 16 seats, Gaul 15th.

| # | Order | Why (principle) | Expected on the next save |
|---|---|---|---|
| 1 | **Recruit** at Rome: heavy infantry 6,000 | P4, P1b | new slot HI 6,000, state 0, city 85; treasury −600; mobilization +3 |
| 2 | **Recruit** at Rome: archers 3,500 | P4; bot's proposal (siege ×3, shoots LI) | new slot archers 3,500; treasury −68; mobilization +2 |
| 3 | **Fortify** Arretium +3 points (72 → 75) | P5: purpose = recruit at the front city the combined army will stand beside for the Gallic campaign | treasury −99; Arretium fort 372 (order pending), 75 after the tick; Arretium appears in the recruit list on 0721 |
| 4 | Army 1: **hire mercenaries** at Heraclea: Samnite light infantry 3,868, quality 8 | P6: cost 24 from a purse of 100, pay 30 a quarter from the purse | army 1: 7 units, 25,868 troops, purse 76 |
| 5 | Army 0: **supply** from Arretium, +67 t (to 237/237) | P2 | army 0 supplies 237; Arretium stock 150 → 83 |
| 6 | Army 1: **move** to (113,45) (8 moves, all plain) | P1: bring the armies together | army 1 at (113,45), moves 0 |
| 7 | **End turn** | | `AUTO0721.SAV`; Arretium fort 75 |

Treasury after the turn: about 1,433. Net upkeep added: HI 60, archers 17 a quarter (Rome's estimated net at 10 % tax was +120 a quarter before these).

## Turn 2: 0721, Spring week 3

| # | Order | Why | Expected |
|---|---|---|---|
| 1 | Army 1: **move** (113,45) → (104,36), 9 moves, plain | P1 | army 1 at (104,36) |
| 2 | Army 0: **move** (100,37) → (103,36), 5 moves around the river | P1 | army 0 at (103,36), adjacent to army 1 |
| 3 | **Join armies** 0 and 1 | P1: one field army of about 49,500 (HI 30,700) | one army, about 49,500 troops, 13 units, moves 0; capacity 495 t |
| 4 | **End turn** | | `AUTO0722.SAV` |

Then, as the plan stands (re-planned each turn from the save):
- **0722:** the joined army walks 6 moves to (99,30) beside Felsina and besieges it. Siege strength ≈ 49,500 / 80 × morale ~69 ≈ 42,700 against Felsina's 34,050 (Felsina's loyalty and fortification may have changed). A capture triggers Gaul's defection check (unity 577 − 15 < 650): Taurasia and Modena are candidates.
- **0724:** mobilize HI 4,000 and HC 1,000 at Rome (average quality by then) into a second army, and supply it at once from Rome (a new army has 0 supplies).
- A Gallic attack on the joined army is fought with *Computer general* and logged with both sides' composition, as P1's calibration data.

## Checkpoints (comments in the run's issue)

| Checkpoint | After turn | Save it reports on | Content |
|---|---|---|---|
| End of Spring | 0725 | `AUTO0726.SAV` (Summer week 1) | metrics, milestone status (phase 0), principle violations, Summer's plan |
| End of Summer | 0731 | `AUTO0732.SAV` | same; phase 0 deadline ("combined field army stronger than Gaul's largest by composition, end of 270 BC summer") |
| **Winter check** | 0736 | `AUTO0737.SAV` (Autumn week 11) | P3: for every army, the winter supply its reachable own cities can give vs its winter consumption; the move or split planned for each army |
| End of Autumn | 0737 | `AUTO0738.SAV` | same as the seasonal ones |
| End of Winter = end of run | 0743 | `AUTO0744.SAV` | final metrics, then `runs/0/debrief.md` |

`rome-v1` does not set `pause: true`, so the run continues after each checkpoint unless the player steers in the issue.

## Questions for the player

1. Approve run 0 as above?
2. **Archers** in the recruitment mix (bot's proposal, not in rome-v1)?
3. **Diplomacy** (rome-v1's open question): Rome has one free trade slot. A trade with the Ptolemaic kingdom would pay about 513 talents a quarter (research estimate). Propose it on turn 2?
4. Taxes stay at 10 % in the pilot unless you say otherwise.

## The player's answers (2026-09-29, given in the working session, recorded by the bot)

- **Strategy:** before besieging Felsina, gather the army and **defeat the Gallic army first**, then start taking cities. **Defeating armies always takes priority over taking cities.** If the Gauls cannot be beaten, escape, wait, recruit more and add the recruits to the army.
- **Archers:** yes, they go into the recruitment mix.
- **Trade:** yes, and always try to fill every trade slot.
- **Taxes:** the player usually taxes high. The side effect is lower loyalty, which has seldom mattered when militarily strong. The player does not know exactly what low loyalty does.
- **Findings:** sent to the research session "AUTOSAVE IMPERIAL_CONQUEST".

**Approval:** the run has **not** started. The player asked for the remaining order tests first, then a handover.

### What changes in the plan (bot)

- **Turn 2 (0721)** stays: bring armies 0 and 1 together and join them (≈ 49,500 with the Samnite mercenaries).
- **Turn 3 onward:** the combined army seeks Gaul's field army (40,500 at (93,28) in this game) and attacks it when adjacent. Felsina comes after that battle. The walk to the Gallic army costs about 11–15 moves from Arretium, so the battle is expected on turn 0723–0724. Each battle is fought with *Computer general* and logged with both armies' compositions (P1 calibration).
- **Rule for escaping:** if the joined army's field strength (research formula, or better, measured battle results) is below Gaul's × k, the army falls back beside Arretium or Rome and waits for the 0724/0726/0728 mobilizations.
- **Trade:** in this game Rome trades only with Illyria (Macedonia dropped its trade before Rome's first turn: relation −8). Numidia accepts a trade on turn 1; the third slot is tried every turn against the richest nation that has not refused (a refused nation is retried after a quarter).
- **Tax:** the bot proposes 20 % for the pilot (it is the player's style, and it tests the loyalty side effects). What low loyalty does, from the research (`docs/rules-digest.md` §3, §5):
  - each quarter, a city at tax < 11 gains loyalty with a chance, and any city loses `Random(tax) div 8` with a 1-in-3 chance;
  - loyalty is 150 × loyalty of a city's **siege defence**;
  - below 65, an own city can **defect** to an enemy that captures a city of yours nearby, when your unity is < 650;
  - below 30, a non-capital city **rebels** each quarter to its allegiance nation or to an enemy army nearby. This has never been observed in any save.
  - Unity also falls with tax (`+25 − tax/2 − mob/5` a quarter); a nation dies below 400.
