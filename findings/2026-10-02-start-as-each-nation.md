# Starting as each of the 16 nations: one turn order, and a different world at each seat

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task T0b of `docs/proposals/fleet-battles-and-storms.md` (approved by the player 2026-10-02): until now the harness had only ever started the original as Rome. It also changes two facts that plan took from the Rome start (§3 there).

**Answer.**
- **All 16 nations start and play two turns.** For each, New Game with only that nation human worked, the title bar ("<nation>'s turn (<leader>)") and the current-nation variable `CUR_NATION` (`0x4A0320`) named the right nation, the recruit dialog had the same layout, the first army could be selected, and End turn worked; the only things that broke were the driver's New Game click for the later rows and its handling of Build fleet's refusal (both fixed).
- **The turn order is the same in all 16 starts** (one order, from the seed): Illyria, Numidia, Ptolemaic, Galatia, Seleucid, Thracia, Greece, Dacia, Macedonia, Media, Armenia, **Rome (12th)**, Bithynia, Carthage, Gaul, Celtiberia.
- **The starting world is the world as it stands when the human's seat comes up**, so it differs with the nation you choose: the AI seats before you have already moved. Ptolemaic has **−9 talents** and no war in Rome's start, but **4,900 talents and a war with Seleucid** in its own start; Seleucid has 1,840 talents and wars with Bithynia and Galatia in Rome's start, but 2,700 and a third war (with Ptolemaic) in its own.
- **Five nations start with no army** (Numidia, Greece, Illyria, Dacia, Armenia), and only **Carthage and Ptolemaic have a fleet**.
- **Build fleet is refused for Dacia, Galatia and Media** ("Only nations with coastal cities can build fleets"); the other 13 get "The fleet will be built at <city>".
- **End turn's first click did not register in 3 of 21 starts** (Illyria and Armenia in the first pass, Dacia in the re-run), always a nation with no army, and no nation failed twice: intermittent, cause unknown.

## Method

- **Build:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb, `SEED.TXT` = 12345, one fresh process per nation. Script `runs/experiments/civ-sweep/sweep.py`; driver `harness/driver.py`.
- **Per nation (row 0-15 of the New Game form):** `New Game` with only that nation's "human" box ticked (the tick for row *r* is at `(117, 117 + 21.67·r)`; the old `114 + 20·r` was 8 px off by Thracia), then: read the title bar, `CUR_NATION`, the start popups and the autosave `AUTO0720.SAV` (`state/sav.py`); on turn 1 **Build fleet** (10 ships), open the recruit dialog, select the first army and, if there is a launched fleet, the fleet; **End turn**; on turn 2 move the first army one tile; **End turn**. Every step is wrapped: a failure is a result and the sweep goes on. The five nations with a failed step were run again with a screenshot on failure and the Build fleet refusal read.
- **Saves and screenshots** (release `run-exp-civ-sweep`): `S<row>_<nation>_AUTO0720.SAV`, `…AUTO0721.SAV`, `…AUTO0722.SAV`, the recruit and army-selected screenshots, `S10_Dacia_end_turn_stuck.png`, and the two result files `sweep_run1.json` (first pass) and `sweep.json` (final: the five re-run rows replaced).

## Observations

"Seat" is the human's position in the turn order (0 = moves first), read from the autosave (`seat_index`); "cities (coastal)" counts cities adjacent to a sea or rough-sea map cell **by `state/sav.py`'s reading**, not the game's.

| row | nation | seat | cities (coastal) | treasury | armies | fleets | at war with | fleet port | End turn 1 / 2 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | Rome | 11 | 25 (15) | 2,200 | 2 | 0 | Gaul | Caere | ok / ok |
| 1 | Carthage | 13 | 34 (28) | 11,000 | 2 | 1 | Celtiberia | Carthago | ok / ok |
| 2 | Seleucid | 4 | 62 (16) | 2,700 | 2 | 0 | Ptolemaic, Bithynia, Galatia | Issus | ok / ok |
| 3 | Ptolemaic | 2 | 46 (20) | 4,900 | 2 | 1 | Seleucid | Alexandria | ok / ok |
| 4 | Macedonia | 8 | 16 (5) | 775 | 1 | 0 | – | Pynda | ok / ok |
| 5 | Numidia | 1 | 8 (1) | 410 | 0 | 0 | – | Siga | ok / ok |
| 6 | Gaul | 14 | 28 (2) | 315 | 1 | 0 | Rome | Rotomagus | ok / ok |
| 7 | Greece | 6 | 21 (15) | 920 | 0 | 0 | – | Athens | ok / ok |
| 8 | Celtiberia | 15 | 19 (3) | 440 | 1 | 0 | Carthage | Saguntum | ok / ok |
| 9 | Illyria | 0 | 9 (6) | 580 | 0 | 0 | – | Epidamnus | ok / ok |
| 10 | Dacia | 7 | 8 (0) | 180 | 0 | 0 | – | refused | timeout / – |
| 11 | Bithynia | 12 | 13 (11) | 550 | 1 | 0 | Seleucid | Sinope | ok / ok |
| 12 | Galatia | 3 | 9 (0) | 440 | 1 | 0 | Seleucid | refused | ok / ok |
| 13 | Armenia | 10 | 10 (5) | 530 | 0 | 0 | – | Phasis | ok / ok |
| 14 | Media | 9 | 14 (2) | 760 | 1 | 0 | – | refused | ok / ok |
| 15 | Thracia | 5 | 12 (10) | 520 | 1 | 0 | – | Byzantium | ok / ok |

**One turn order.** `turn_order` is identical in all 16 autosaves and the human flag is set for the chosen nation only. Rome is at seat 11 (the 12th), and the other nations' seats are the positions in the order above. (`docs/rules-digest.md` §2 says Rome's seat differs per game, observed 13, 10, 7, 5: it differs per seed or New Game, and for this seed it is the same whoever is human.)

**The start state depends on the seat.** The Rome start (`saves/run0-start-AUTO0720-seed12345.SAV`, seat 11) and the nations' own starts differ in wars and treasury as above: in Rome's start Ptolemaic is broke and at war with nobody and the news already says "Ptolemaic sues Seleucid for peace" and "Ptolemaic pays reparations of 2,242 talents"; in Ptolemaic's own start (seat 2) it is not. **The Ptolemaic fleet shows it too:** in Ptolemaic's own start (`S03_Ptolemaic_AUTO0720.SAV`) fleet 1 is at (189,89) with **condition 75**; in Rome's start it is at (190,93) with condition 100: consistent with the Ptolemaic AI seat (seat 2) having moved it to a port and repaired it before Rome's seat came up. Carthage's fleet (90 ships at (49,62), condition 85) is the same in both, as Carthage's seat (13) comes after Rome's (11).

**Fleet ports** (Build fleet's message, 13 nations): Rome Caere, Carthage Carthago, Seleucid Issus, Ptolemaic Alexandria, Macedonia Pynda, Numidia Siga, Gaul Rotomagus, Greece Athens, Celtiberia Saguntum, Illyria Epidamnus, Bithynia Sinope, Armenia Phasis, Thracia Byzantium. **Refused:** Dacia, Galatia, Media: a message box, no dialog (the driver now reads the message instead of failing on the missing dialog). Media has 2 cities next to a sea cell by our reading and is still refused.

**The first End turn.** In the three failures the game showed an ordinary turn-1 screen, no dialog or popup, calendar unchanged, `CUR_NATION` correct (`S10_Dacia_end_turn_stuck.png`): the End turn click simply did not take effect, and the driver's single retry did not either. Illyria and Armenia passed when run again (62 s and 59 s). All three nations have no army; Numidia and Greece, also without an army, passed both turns.

**What worked for every nation:** the recruit dialog ("Army recruits": two lists and the buttons Disband, Mobilize, Recruit unit and the unit types, the same controls as Rome's); selecting the first army (`SEL_ARMY` = its id, ids 0, 2, 4, 6, 8, 9, 10, 11, 12, 13, 14 across the nations); moving it one tile; End turn at turns 1 and 2 (wherever it was not one of the three timeouts).

## Inferences

- The Rome start is **one sample of the world**, not the world: it is the state after 11 AI seats have moved. Anything the plan or the research took from it (Ptolemaic broke with its fleet at (190,93) and condition 100, Seleucid–Ptolemaic at −18) is a fact of seat 11 for this seed; Carthage's fleet is the same at seats 11 and 13. The fleet-battle plan's pair 2 (Seleucid + Ptolemaic) has the war it wanted in **both** nations' own starts, and Ptolemaic is not broke there.
- Because the order is fixed by the seed, choosing the human changes only **which AI seats move before you**; two human seats would be two of these positions, and the second human sees the world after the first human's turn as well.
- The refusal for Media suggests the game's idea of "coastal" is not "next to a sea cell" (an inland sea, such as the Caspian for Media, may not count); this was not tested.
- The 21 starts say nothing against the existing harness beyond the two fixes, but they only exercise orders that need no other nation's row: Build fleet, the recruit dialog, selecting and moving an army, End turn.

## What this does not establish

- **Two human seats:** not run (task T0 of the plan).
- **International relations** for a non-Rome human (`Game.relation` assumes "Rome is row 0" in the radio rows): not exercised, so whether it works for another nation is unknown.
- **The cause of the End turn failures:** unexplained; a deeper look (the click's position, focus after the recruit dialog, the calendar) was not made. The sweep did not retry beyond the driver's single retry.
- **Whether the game's "coastal" test differs from ours** (Media): untested. **How the fleet port is chosen:** only the 13 results are listed; no rule is claimed.
- **Other seeds:** the turn order and the seat-dependent start are one seed; a different `SEED.TXT` is not tested.
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 runs/experiments/civ-sweep/sweep.py          # all 16, about 20 minutes; or: ... sweep.py 3 9 14
```
