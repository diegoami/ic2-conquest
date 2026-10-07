# AI-mover contact resolution: the mover onto an occupied tile (in-play corroboration)

**Status:** draft from `ic2-conquest`, awaiting promotion. Research pending request (2026-10-07,
from imperial-conquest-main via the research session): whether `FUN_0044d734`'s contact resolution
differs when the mover is AI. Wine-only.

**Tags.** `[derived]` = the decompile's reading (research repo, `docs/reports/2026-10-07-strategic-ai-turn.md`
and this experiment's own reads of the whole-application dump). `[confirmed]` = this run's saves
(bare filenames; SHA-256 in `runs/experiments/data/run-exp-ai-contact/SAVES.sha256`, binaries in
release `run-exp-ai-contact`, one tar.gz per batch).

## Answer (filled as batches land)

- **The AI mover and the human mover share one contact resolver — no difference in kind** `[confirmed,
  with the decompile]`. `TUnitMap_MoveHumanArmy` and the AI's destination call `FUN_0044dba8` both call
  `FUN_0044d734`, whose end-of-walk dispatch on the destination cell is owner-agnostic; what differs is
  only who resolves the fight when the tile holds an enemy army: a both-computer contact resolves
  instantly (`FUN_0044aee4`), a contact involving the human opens the tactical screen.
- **An AI mover onto an enemy army tile (both seats computer) resolves instantly, with no battle
  screen, and the walk continues past the contact tile** `[confirmed]`. Three natural observations in
  the control run (nothing staged):
  - *Carthage destroys army of Celtiberia* (week 3, `AUTO0720.SAV`→`AUTO0721.SAV`): Carthage army 2
    (42,63)→(39,64) with the contact at Celtiberia 10's (38,64); 33,900→22,806 troops; supplies
    339→228 = 22,806/100 (the `troops div 100` cap); money 597→**697 = +100, the loser's purse,
    exact**.
  - *Seleucid destroys army of Bithynia* (week 5, `AUTO0721.SAV`→`AUTO0722.SAV`): Seleucid army 5
    (179,44)→(185,44), the battle at Bithynia 11's (182,41) **mid-walk** (the mover passes through
    and keeps going); 37,300→23,386 troops; supplies 299→233 = 23,386/100; money 600→738 (+138;
    Bithynia's purse was 100 at the turn's save, its own economy phase runs first — the +38 gap is
    the purse's within-turn growth, not a payment).
  - *Seleucid destroys army of Ptolemaic* (week 1, in `AUTO0721.SAV`'s news) — same news form; the
    pair's records are masked by id churn and are not itemised here.
  In every case the loser's army record is gone, the news line is the destruction notice, and no
  `BATTLE` window ever appears (the control run's `turn_texts` hold the only battle line of the
  twelve turns: the Gaul-v-Rome one).
- **An AI mover onto a human army tile opens the tactical battle at the human's defence** `[confirmed]`.
  `AUTO0721.SAV`→`AUTO0722.SAV`: Gaul army 9 (74,330 troops, money 96) reaches Rome army 0's
  neighbourhood; the window `Gaul  v  Rome — Rome to place units.` opens (the pump plays it with
  Computer general); Rome 0 ends 23,700→6,596 troops, **money 100→196 (+96, the loser's purse)**,
  supplies 123→65 = 6,596/100 (the same cap on the battle's supply absorption), **moves 9→9
  (untouched — the defender is not the mover)**; Gaul's army record is gone; news: *Rome destroys
  army of Gaul*.
- **AI mover onto a city tile at war = the siege path, instant, no screen** `[confirmed]`. Four
  natural captures in the control run — Dimale (Illyria→Macedonia, `AUTO0725.SAV`→`AUTO0726.SAV`),
  Castulo, Iliturgi, Orangis (Celtiberia→Carthage, 0727→0728, 0728→0729, 0729→0730) — each moving
  owner/allegiance, loyalty to the 40 floor, fort −5…−11, pop −5, with the recurring *fails to
  capture* rows showing the retries (`natural_evidence.txt` tabulates every field).
- **An AI mover onto an army tile NOT at war does nothing at all** `[derived]` (the dispatch skips
  the attack unless relation is 3 and moves > 0; no natural observation — the run had no such pair).
- **The army-record id churn at Media's capital (307,58) is the merge sub-phase, not contact**
  `[confirmed]`: identical-stat Media armies vanish in successive turns with no news line and no
  foreign army involved — `FUN_004509f0`'s army merge (one record removed per turn), which otherwise
  looks exactly like a destruction in an id-based diff.
- **A human mover cannot reach the contact branch with a long walk** `[confirmed, staged]`. Two
  staged plays (only the `moves` word edited via the battles `stage.py` — positions and map natural,
  labelled staged; `staged_through0731.SAV`, `staged_onto0732.SAV`):
  - *Through-click*: from (100,33) with 196 moves, clicking the empty tile (55,33) whose straight
    path crosses Gaul's army at (68,33) — the walker **deviates off the row and stops** at (91,32)
    with 186 moves left, no box, no battle (`throughmove_log.v4.json`).
  - *Onto-click*: from (91,32) with 200 moves, clicking Gaul's own tile (68,33) — a **silent
    no-op**: position, moves, treasury, everything unchanged (`ontotile_log.json`), the same
    refusal class as the out-of-reach hire.
  The human's only reachable path onto an enemy army tile is the **adjacent attack click**, which
  opens the tactical battle (the gallic-army experiment) — so "human mover contact, defender
  resolves, no battle" is not reachable through the UI as hypothesised; the shared resolver's
  army-tile branch is, in practice, an AI-mover branch (or an adjacent attack).
- **The adjacent through-click (path crossing the enemy tile within ~3 steps) was not delivered**
  `[not established]`. The chase that was to set it up followed a **ghost**: the game's memory
  retains stale records of destroyed armies (the dead 40,500-strong start army read live at its
  last position), so the driver's memory scan marched Rome to an empty tile while the real Gaul
  army besieged Locri and Rhegium (`b3a_AUTO0733.SAV`–`b3a_AUTO0738.SAV`; the run stopped on the
  owner's wind-down before the closing armies met). Driver caveat recorded: memory army scans must
  filter liveness (a save's dead slots read owner −1; memory's do not). Byproduct: a further
  natural AI-AI destruction in `b3a_AUTO0738.SAV`'s news (*Illyria destroys army of Greece*).

## Method

- **Environment.** A dedicated Wine prefix (`ic2-work-contact`), Xvfb `:601` and a copy of the game
  folder, so other sessions' games cannot interfere; the driver patch in this branch selects the
  game pid by its working directory (the first pgrep match could be another session's game).
- **The decompile read.** `FUN_0044d734` walks the mover to its destination and dispatches on the
  destination cell: an army band (200–247) calls `FUN_0044aee4` **only** when the nations are at war
  and the mover has moves left — otherwise nothing happens at all; a city (20–99) at war calls the
  siege `FUN_0044b27c`, not at war the resupply `FUN_0044f6d8`. The human twin
  `TUnitMap_MoveHumanArmy` calls the same `FUN_0044d734`. `FUN_0044aee4` is the instant resolution:
  it requires both nations' computer-seat flags, zeroes the mover's moves, transfers the loser's
  supplies and money to the winner, destroys the loser (army removed, news line) — no tactical
  battle screen on that path.
- **Batches.**
  - `b1` (control): fresh `new_game` seed 424242, Rome idle, one save per turn 0720–0732; must
    reproduce the ai-turn run's snapshots turn for turn (`control_vs_ai_turn.txt`). It re-collects
    the natural evidence: the AI-mover-vs-human-army contact of 0721→0722 and the Celtiberian
    sieges (`natural_evidence.txt`).
  - `b2`: extension of the same game past 0732, watching for a both-computer army contact (the
    instant `FUN_0044aee4` branch).
  - `b3` (human-mover control): the run-0 start (`BASE.SAV`), the proven join-and-march sequence
    to Gaul's army, then a MOVE (not the attack click) whose destination is the enemy army's tile;
    `humanmover_log.json` records position, popups, battle window and the army record around the
    contact.

## Observations

- The control run's twelve turns contain exactly one battle window (`Gaul  v  Rome — Rome to
  place units.`); every other armed contact — two army destructions between computer seats, four
  city captures, several failed sieges — resolves with **no window and no screen**, only news
  lines and record diffs (`natural_evidence.txt`).
- The destruction news form is always "*<winner> destroys army of <loser>.*", distinct from the
  capture form "*<city> (<nation>) falls to <nation>.*" and the defection form.
- The winner of an instant army contact holds **supplies = troops div 100** afterwards in both
  observed pairs (228 = 22,806/100; 233 = 23,386/100) — the same cap every other supply writer
  applies — and its money rises by the loser's purse (Carthage +100 exact; Seleucid +138 with the
  loser's save-time purse at 100 and its own economy phase in between).
- The defending human's army keeps its `moves` through the battle (Rome 0: 9→9); every AI army
  shows moves 0 in these saves regardless, so the mover's moves-zeroing (`FUN_0044aee4` writes 0
  before resolving) is not separately measurable here.
- A click on a *distant* enemy-army tile (Chebyshev 3) issues a plain walk, not an attack: no
  box, no battle window on that turn (`humanmover_log.json` turn 0).

## Inferences

- The clone's faithful-AI path can share one contact resolver with the human twin (the pending
  request's design goal): the decompile routes both through `FUN_0044d734`, and the plays show the
  observable outcomes match the dispatch table — at-war army tile ⇒ fight (instant between
  computers, screen when a human defends), at-war city tile ⇒ siege, other city ⇒ resupply,
  not-at-war army tile ⇒ nothing.
- The mid-walk contact (Seleucid passing through (182,41) and finishing at (185,44)) says the
  contact check runs **per step of the walk**, not only at the destination — matching
  `FUN_0044d734`'s per-step structure, and meaning a blocked destination is not required to
  provoke a contact.
- The instant path's loss arithmetic (`FUN_0044ae20` with the type matrix) is not re-derived
  here; the two observed losses (11,094 of 33,900 and 13,914 of 37,300) are cited as bounds for
  whoever does.

## What this does not establish

- **Wine-only** throughout; the desktop original should repeat one both-computer contact and the
  refusal behaviours before the clone treats the outcomes as platform-independent.
- The **not-at-war army-tile contact** (dispatch: nothing at all) has no natural observation in
  this run — `[derived]` only.
- The **adjacent through-click** (a short human walk whose path crosses the enemy tile) — the
  chase set up for it followed a stale memory slot and the run stopped before a second attempt;
  not tested.
- The instant path's **exact loss formula** (values, matrix, rounding) — decompile-only here.
- The AI mover's **moves-zeroing** is not separately observable (all AI armies read moves 0 at
  save time).
- Whether a human MOVE onto an **occupied city tile at war** opens the siege dialog or resolves
  silently — not played in this run.
- Why the long walk **deviates and stops** (pathing rule, per-order step cap) — observed, not
  explained; a clone reproducing "refuse/stopper" behaviour needs its own dig.

## Reproduction

```bash
source harness/env.sh   # with IC2_WORK=/home/diego/ic2-work-contact DISPLAY_IC2=:601 for a dedicated prefix
python3 runs/experiments/ai_contact/contact.py control 732
python3 runs/experiments/ai_contact/contact.py control 740 --resume
python3 runs/experiments/ai_contact/contact.py humanmover   # superseded: chased, no contact (see throughmove/ontotile/approach)
python3 runs/experiments/ai_contact/compare_control.py
python3 runs/experiments/ai_contact/analyze_natural.py
python3 runs/experiments/ai_contact/archive_batch.py b1
```
