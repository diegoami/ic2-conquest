# Two human seats: the original supports them, plays the AI seats in between, and overwrites the first human's autosave

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task T0 of `docs/proposals/fleet-battles-and-storms.md` (approved by the player 2026-10-02) and builds on `findings/2026-10-02-start-as-each-nation.md` (the turn order and the seat-dependent start). One seed, one pair of nations (Carthage + Ptolemaic), **one and a half rounds**.

**Answer.**
- **Two human seats work.** The New Game form accepts two "human" ticks; the autosave's human flags are exactly the two ticked nations; the title bar and `CUR_NATION` follow whose seat it is.
- **A round is the shared turn order**: the human seats play in their positions (Ptolemaic, seat 2, then Carthage, seat 13), **the AI seats between them play by themselves**, and the calendar advances only at the round tick (week 1 → 3). End turn by one human hands control to the **next human seat**, not to a new round.
- **The two humans' autosaves share a name**: both round-1 saves are `AUTO0720.SAV`, so the second human's turn start **overwrites** the first's. A harness must copy the save after every End turn.
- **War between the humans is one order, symmetric and immediate:** Carthage set war toward Ptolemaic and **both** relation entries became 3 at once, with no refusal and no consent step; it was still 3 at the next round's start.
- **Orders act on the current seat's nation**, and a battle involving a human seat opens the tactical screen **for that human** during the AI phase.

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb, `SEED.TXT` = 12345. Scripts `runs/experiments/two-humans/t0.py` (phase 1: New Game with `rows=[1, 3]`, Carthage and Ptolemaic) and `t0_phase2.py` (phase 2, from Carthage's saved turn: the war order, End turn). Driver `harness/driver.py`.
- **Phase 1:** record the title bar, `CUR_NATION` (`0x4A0320`), the calendar and `AUTOSAVE.LOG`; set Ptolemaic's tax to 15 (`Game.taxation`, which writes the current nation's `+0x44A`); End turn.
- **Phase 2:** load Carthage's turn (`T0_AUTO0720.SAV`), set war toward Ptolemaic with `Game.relation(3, "war")`, read **both** nations' relation entries in memory (`+0x26 + 2·j` of each nation record), End turn.
- A first run of phase 2 failed because `Game.relation` clicked a hardcoded OK button (see Observations); it was rewritten to read the dialog's controls and the phase was run again. All numbers below are from the second run.

## Observations

Saves are in release `run-exp-two-humans`. "Seat" is the position in the turn order (0 first), `seat_index` of the save.

| save | turn | `current_nation` | seat | human flags | relation Carthage→Ptolemaic / back | Ptolemaic tax |
|---|---|---|---|---|---|---|
| `T0_NEWGAME_AUTO0720.SAV` | 720 (week 1) | 3 Ptolemaic | 2 | 1, 3 | 1 / 1 (trade) | 13 |
| `T0_AUTO0720.SAV` | 720 (week 1) | 1 Carthage | 13 | 1, 3 | 1 / 1 | 15 |
| `T0_P2_WAR.SAV` | 720 (week 1) | 1 Carthage | 13 | 1, 3 | **3 / 3** | 15 |
| `T0_P2_AUTO0721.SAV` | 721 (week 3) | 3 Ptolemaic | 2 | 1, 3 | **3 / 3** | 15 |

**The form and the first seat.** With rows 1 and 3 ticked, the first autosave (`T0_NEWGAME_AUTO0720.SAV`) has human flags `[1, 3]`, `seat_index` 2 and `current_nation` 3, the same turn order as every other start of this seed (Illyria, Numidia, **Ptolemaic**, Galatia, Seleucid, Thracia, Greece, Dacia, Macedonia, Media, Armenia, Rome, Bithynia, **Carthage**, Gaul, Celtiberia). Title bar: "Ptolemaic's turn (Thutmose)". Treasuries 11,000 (Carthage) and 4,900 (Ptolemaic), as in each nation's own single-human start.

**Orders act on the current seat.** Taxation 15 in Ptolemaic's turn changed Ptolemaic's tax (13 → 15) and left Carthage's at 5 (`T0_AUTO0720.SAV`).

**End turn.** Ptolemaic's End turn showed the **"End turn ?" box** with "An army of yours cannot afford to pay its mercenary units. If you have not finished your turn click MAKE MORE MOVES. If you are finished moving this turn click END TURN." (a second wording of the box first seen for "needs supplies"), then several Confirm boxes, and then a **battle screen "Seleucid v Ptolemaic, Ptolemaic to place units"**: a battle between Seleucid (an AI seat) and the human Ptolemaic opened during the AI phase, and the human was asked to place units (the driver played it with Computer general; the title does not say who attacked, though the Rome-start news already has "Seleucid destroys army of Ptolemaic"). Control then returned at **Carthage's turn** in the same week: `CUR_NATION` 1, title "Carthage's turn (Agis)", calendar unchanged, and `AUTOSAVE.LOG` gained a **second** line `0720 AUTO0720.SAV OK`.

**The autosave name.** The two round-1 saves differ (`current_nation` 3 / seat 2 against 1 / seat 13; Ptolemaic's tax 13 against 15) yet both lines of the log name `AUTO0720.SAV`; only the second file is left in the game folder. `T0_NEWGAME_AUTO0720.SAV` exists because the script copied it before the End turn.

**Round 2.** After Carthage's End turn the AI seats 14 and 15, the round tick and the AI seats 0 and 1 played, and Ptolemaic's seat came up: `CUR_NATION` 3, week 3, `AUTO0721.SAV` (`T0_P2_AUTO0721.SAV`: `current_nation` 3, seat 2).

**The war.** The International Relations dialog has all 16 nations as rows (the current nation's own row has no choice) and four radio buttons per row, peace, trade, ally and war: **64 radio buttons**, two buttons, OK and Cancel; Carthage's dialog shows Rome peace, Seleucid trade, **Ptolemaic trade**, Numidia ally, Greece trade, Celtiberia war and peace for the rest (`t0_relations_dialog_carthage.png`, produced by `t0_phase2.py`), the same as the save. The Carthage–Ptolemaic relation is **1 (trade)** in this two-human start, where it is **−10** (peace with a cooldown) in the Rome-seat start. One click on the war radio and OK: **both** entries became 3 immediately (`T0_P2_WAR.SAV`), no box appeared, and both were still 3 at the next round's start (`T0_P2_AUTO0721.SAV`).

**Driver bug found on the way.** `Game.relation` clicked a hardcoded OK at (308,217) and radios from a recorded layout; in this Wine layout OK is at (333,232), so the war order did nothing and the dialog stayed open (`DriverError: International Relations did not close`, the first phase-2 run). It now reads the radios and the buttons from the dialog (sorted by position: row = nation index, columns peace, trade, ally, war).

## Inferences

- A two-human game is an ordinary game with two seats flagged human: the original needs nothing special, and the harness needs three things: `new_game(rows=[…])` (done), an End turn that returns at the next human seat (it does), and **a copy of each human seat's autosave right after the End turn that produced it**.
- Since the second human's save carries the first human's finished turn (Ptolemaic's tax 15 in `T0_AUTO0720.SAV`), "the save at the start of a seat" is a fair description of each file, but only the last of the round survives.
- A human–human war needs no agreement and cannot be refused, at least from trade; the cooldown rules that may refuse a war (the −18 value of the plan's pair 2) are not shown here.
- For the fleet-battle plan, pair 1 works as designed in the two-human start: Carthage and Ptolemaic start on trade terms, not at war, and one order makes them enemies.

## What this does not establish

- **Pair 2** (Seleucid + Ptolemaic, which may already be at war and have the cooldown): not run.
- **Anything after the war order:** no fleets, no battle between the two humans, no "Are you sure you want to attack this …" for a human target. In particular whether **both** humans are asked to place units when their units meet, and what the battle does to the seat order, is unknown.
- **The war's side effects:** the news of the following turn ("ends all current trading agreements", the ally cascade) was not read.
- **More than one and a half rounds, one seed, one pair:** the overwrite of the first autosave is two lines of one log; whether a later setting (a rolling save, a different build) changes it is untested.
- Whether the End turn "mercenary pay" box appears for the same reason in every start (it appeared once).
- **The Relations dialog at Ptolemaic's seat:** the same step in `t0.py` (open the dialog, screenshot, count the radios) failed in two re-runs ("no controls found", then the window gone before it could be read), while it worked every time at Carthage's seat in `t0_phase2.py`; unexplained, and the failed step is in `t0.json`. The 64-radio count and the screenshot are Carthage's only.
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 runs/experiments/two-humans/t0.py            # phase 1 (about 3 minutes)
python3 runs/experiments/two-humans/t0_phase2.py     # phase 2, from artifacts/run-exp-two-humans/T0_AUTO0720.SAV
```
