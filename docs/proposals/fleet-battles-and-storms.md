# Plan: fleet battles, armies aboard, and ships lost at sea

**Status:** plan for review and for the player's approval (2026-10-02). Nothing here has been run. Author: Claude Sonnet 5.5.
This plans three experiments that follow from the fleet orders now in `main` (`findings/2026-10-02-fleet-orders-live.md`),
which left **naval battles, battles with an army aboard, and storms at sea** untested.

## 0. Decisions taken (player, 2026-10-02)

Answers to the first version's open questions, which this revision applies:

1. **Not Rome-centric.** Rome was a bot assumption; this is exploration. Choose civilisations that **already have fleets and
   are at war or can go to war soon**. **Pair 1: Carthage + Ptolemaic** (the only two nations with a fleet at the start); **pair 2:
   Seleucid + Ptolemaic** afterwards. Also **a short run with all 16 civilisations (2 turns each)** to find quirks (§4b).
2. **If two human seats cannot be driven reliably: stop and report** (no silent fallback to one human).
3. **Synthetic states are acceptable** for the storm tests, clearly labelled, never presented as play.
4. **10 seeds per cell** in the battle tables, more cells.

## 1. What the player asked for

1. **Two human players.** At New Game more than one nation can be made human. Use two, have them **build or move fleets
   together**, put them **at war with each other**, and **test fleet battles**.
2. **Fleet battles with soldiers aboard**, where the result also depends on the soldiers on the fleets.
3. **Tasks where a fleet is sunk at high sea**, especially in **rough water**.

> **Read §3 and Appendix A with this in mind:** the start facts quoted in this plan are the world from **Rome's seat (11)**; they differ at other seats (T0b sweep).

## 2. What the research already says (to confirm or correct, not to assume)

From `docs/rules-digest.md` §8 and §9 (research reports named there; all **[C]** = from decompiled code, none live yet):

- **Naval battle** (click an enemy fleet): strength = `ships × condition/10`, plus a carried army's `siegeStrength/50`, plus
  a random 0–30 %. **The loser sinks with its army.** Refusal: "You cannot attack a fleet docked at its own city !"
  Clicking an enemy fleet with your unit selected asks "Are you sure you want to attack this fleet ?" (Yes declares war,
  relation 3, with the ally cascade). A human–AI war ends only through the post-battle `TBattlePols` Yes.
- **Storms**, every turn, every launched fleet:
  ```text
  dmg = max(1, Random(100 - condition)/10);  Winter: min(5, dmg*2);  rough sea: min(8, dmg*3)
  not adjacent to one of its own cities: dmg = 2*dmg + 1 (Winter: 1-in-20 spike to 30);  else dmg = dmg/2
  dmg < 6: condition -= dmg
  dmg >= 6: ships and condition lose d/300 each, d = (10000/(dmg+100))^2/100; an army aboard takes casualties,
            and if d > 70 loses whole units
  condition < 40: "A fleet belonging to X is lost at sea."  (the fleet and any army aboard die)
  out of supply: -3 moves and -Random(2) condition per turn
  ```
- **Weather:** 20 fixed sea-region centres (DAT `0x1F876`) are rolled each tick (Spring 1/15 radius 4 in weeks < 6 else 1/30
  radius 3; Summer 1/40 radius 2; Autumn 1/30 radius 3 in weeks < 7 else 1/15 radius 4; **Winter 1/5 radius 5**); a hit paints
  calm sea as **rough sea (code 1)** for a week. Rough sea costs a fleet 3 moves a tile, calm 1.
- **Fleet moves** `30 - (ships-50)/10`, minus `troops aboard/100/ships + 1` when carrying; **capacity** `ships × 500` troops.

Confirmed live already (`findings/2026-10-02-fleet-orders-live.md`): launch after 12 turns, 32 moves for 30 ships,
embark rule and capacity, repair cost, split/join/transfer/scuttle. Not seen: any battle, any storm message; one fleet was at
97 % condition two turns after launch for an untraced reason.

## 3. Facts about the start position that shape the design

From `saves/run0-start-AUTO0720-seed12345.SAV` (the New Game with Rome human; the nation records are the same for every seat):

- **Only two fleets exist** (read from the start save with `state/sav.py`; Appendix A has the parse, and T1 re-reads and confirms it before relying on it): **Carthage** fleet 0, **90 ships, condition 85 %**, at (49,62); **Ptolemaic** fleet 1, **70 ships,
  condition 100 %**, at (190,93). No other nation has one, and **Seleucid has none**.
- **Carthage** (nation 1): 34 cities (28 coastal), **11,000 talents**, at war only with Celtiberia. **Ptolemaic** (3): 46 cities
  (20 coastal), **−9 talents** (broke), at war with nobody. **Seleucid** (2): 62 cities (16 coastal), 1,840 talents, at war with
  Bithynia and Galatia. **Carthage–Ptolemaic is −10** (peace with a cooldown) and **Seleucid–Ptolemaic −18** (the value
  `rules-digest.md` §Relations gives for "ending a war": they fought recently), so both pairs can be put at war, but the
  cooldown may make the relations dialog refuse; that is something to find out in T0, not to assume.
- The two fleets are about **140 tiles apart** (Carthage in the western Mediterranean, Ptolemaic in the east); a fleet with 32
  moves needs several turns of sailing to meet. Natural **differences** are free test material: 90 v 70 ships, 85 v 100 %
  condition. **Split fleet and Transfer ships** (now tested) can equalise sizes (70 v 70) for the baseline cells.
- The start save has **112 rough-sea tiles** already (code 1).
- The New Game form has **one "human" tick per nation row** (`Game.new_game` clicks `(117, 117 + 21.67·row)`, the measured positions; its `rows` argument takes several); two ticks is the
  expected way to get two humans, **not yet tried**. The nation list rows are the nation order above (Rome 0 ... Thracia 15).
- **Lessons from the fleet work:** a fleet takes 12 turns to launch (Seleucid needs one), and in those 12 turns Gaul took Rome's
  build port; an AI can interrupt a staged state with a field battle. Plans must not depend on 12 quiet turns, and the per-turn
  autosaves are the way back.

**Pairs:** pair 1 **Carthage + Ptolemaic** (ready fleets, battles after a few turns of sailing, war by relations); pair 2
**Seleucid + Ptolemaic** (Seleucid builds a fleet; the −18 cooldown and Seleucid's own wars are quirks to record). Other pairs
follow from the §4b sweep.

## 4. Task T0: a spike, two human seats

**Goal:** know whether and how the original runs with two humans, before designing anything on it.

1. New Game with two human ticks (Carthage and Ptolemaic), seed 12345. Record: does the dialog allow it; the turn order; which seat
   moves first; what the title bar and `CUR_NATION` (`0x4A0320`) show for each; **what `AUTOSAVE.LOG` and the `AUTOnnnn.SAV` names do
   when two seats are human in one round** (two saves with the same number? one overwritten?).
2. Make a one-turn script: seat A issues an order, ends the turn, seat B issues an order, ends the turn. Check that
   `Game.end_turn` copes (it waits for an autosave line and `CUR_NATION`; with two humans the *next* human seat is not an
   AI round).
3. Put them at war: Strategy → International relations on seat A (row of nation B, *war*), then check **both** nations'
   relation entries (symmetric? does B have to agree? cooldown rules, "-8/-18" values).

**Deliverables:** a findings draft (what two human seats do), `Game` support (`new_game(rows=[0, 1])`, `play_seat`,
a round loop), the new-game save and the first two-seat saves. **Acceptance:** a scripted round with two humans repeats
byte for byte from the seed (as a single-human turn does today).
**Risk, and the decision:** the save format may carry only one "current" seat; the harness assumes one human. If two humans cannot
be driven reliably, **stop and report** (decision 2); nothing from T1 starts until the player chooses what to do.

## 4b. Task T0b: all 16 civilisations, two turns each

**Goal:** find the quirks of starting as each nation, because the harness has only ever started as Rome (the New Game with row 0).

For each nation row 0-15, seed 12345: `New Game` with that nation human, then **two turns** (end the first turn, play a second). Record,
as a table and per nation:

- whether the form and the autosave work; the title bar ("<nation>'s turn (<leader>)") and `CUR_NATION`; the **turn-order position**
  (Rome's seat differs per game, observed 13, 10, 7, 5); the start popups;
- treasury, cities, armies, fleets, relations;
- whether **Build fleet** finds a "free coastal city" (Dacia and Galatia have none, Numidia and Gaul one or two; they may refuse with
  "You do not have a free coastal city at this time."), and the recruit dialog and queue (the queue reader `state/queues.py` already
  loops all 16 nations, so it is not the suspect);
- **anything the harness assumes about nation 0 or Rome**: `Game.relation` (the International relations radio rows, "Rome is row 0",
  `harness/driver.py`); the tests (`fresh()` loads the Rome start, many check `owner == 0` or `armies[0]`, the recruit test's city rows
  "Luceria, ROME"); `runs/experiments/unit-map-mouse/common.py` (`ROME = 0`); the toolbar's nation icons; the unit-map origin per nation
  (record `+0x486/+0x488`).

Each nation's first-turn saves are kept; the table and the oddities go into a findings draft. About three minutes per nation, an hour
for the sweep.
**Acceptance:** 16 rows, each with a save or a stated failure; every driver assumption that broke is listed with a fix or an
open item. **Output also feeds** T0 (seat handling) and the pair choice for later work.

## 5. Task T1: staging two adjacent fleets (shared by T2 and T3)

*(Stage from the starts of the nations that are human, not from the Rome start: see Appendix A's correction.)*

**Goal:** a committed, small save in which two hostile fleets are one tile apart at sea, plus a recipe to rebuild it.

- **Pair 1 (Carthage + Ptolemaic):** both fleets exist at the start (90 ships at 85 %, 70 ships at 100 %, §3), so no 12-turn wait.
  **Move together:** both humans sail toward a meeting tile in open sea (about 140 tiles apart; moves per turn
  `30 - (ships-50)/10` gives **26** for 90 ships and **28** for 70: check it live), recording each
  fleet's position, moves, supplies (`ships` a turn) and condition per turn. Use **Split fleet / Transfer ships** to make the equal-size
  baselines (70 v 70) from the 90 and the 70, and keep the natural 90 v 70 and 85 v 100 % pairs as cells of their own.
- **Pair 2 (Seleucid + Ptolemaic):** Seleucid has no fleet: it orders one (12 turns, at a port that is safe from Bithynia and Galatia,
  its enemies) while Ptolemaic's waits. This also tests Build fleet for a nation that is not Rome, and the "free coastal city" rule
  for a nation with 16 coastal cities of 62.
- **Relations:** put the two at war (T0: Carthage–Ptolemaic is −10, Seleucid–Ptolemaic −18; see whether the dialog refuses). Then
  "adjacent enemy fleets, each with moves" is the state T2 and T3 branch from.
- **Avoid interruptions:** keep both fleets away from AI fleets and from each other's cities until the meeting; keep any army out of
  reach of an enemy; if an AI event breaks the staging, rebuild from the previous autosave (they are per turn).

**Deliverable:** `saves/fleets-adjacent-at-sea-<nnnn>.SAV` (about 130 KB, no armies aboard: the T2 baseline) and
`tests/make_fleet_battle_fixture.py`. **T3 does not branch from this save:** an army can only embark from a land tile next to the fleet, so T3
restages in port with its own fixtures (`fleets-with-cargo-<size>.SAV`: each fleet in port, the chosen army embarked, then sailed to the meeting
tile), built by the same script with a cargo argument.

## 6. Task T2: naval battles, no army aboard

**Goal:** measure how a battle is decided and what it costs, and compare with `ships × condition/10 + random 0–30 %`.

**New driver order:** `attack_fleet(own_fleet, enemy_fleet)`: select the fleet, click the adjacent enemy fleet, answer the
"Are you sure you want to attack this fleet ?" Confirm (capture it first, as in the unit-map experiment; `Game.attack` answers Yes
by itself), read the result (a battle screen? an instant result box? the news line?) and the post-battle `TBattlePols` if any.

**Experiments** (each = load the T1 save, restart the game with a seed, one attack):

| # | Setup | Measures |
|---|---|---|
| 2.1 | at peace first: the prompt, then No (nothing changes), then Yes (war declared, `ROME DECLARES WAR`-style news) | the prompt text, relation before/after |
| 2.2 | the same fleets with relation already 3 | no prompt, as with cities |
| 2.3 | equal fleets (30 v 30), full condition, N seeds | win rate near 50 %; losses; whether the loser always sinks whole |
| 2.4 | unequal fleets (30 v 20, 90 v 30), N seeds | win rate versus the formula's prediction; the ratio at which the weaker never wins |
| 2.5 | equal ships, different condition (100 v 70, from a repair-limited fixture) | the `condition/10` term |
| 2.6 | attacking a fleet next to its own city | "You cannot attack a fleet docked at its own city !" |

N = 10 seeds per cell (a seed is a different `SEED.TXT`, one process start, about a minute). Record per trial: the seed, both
fleets' ships and condition before and after, the winner, news text, treasury, the carried-army field, and a save before and after.
**Acceptance:** each cell has its saves cited; the win-rate table is compared with a Monte-Carlo of the formula; any disagreement
is reported, not smoothed.

## 7. Task T3: battles with soldiers aboard

**Goal:** show that the carried army changes the odds, and by how much.

The formula adds the carried army's `siegeStrength/50` (state/sav.py already computes `siege_strength`). Design:

- **Same fleets** (30 v 30, full condition, same seeds as 2.3) and vary only the army aboard fleet A:
  none; 5,000; 10,000; 15,000 troops (the capacity of 30 ships); of heavy infantry and of archers (siegeStrength weights archers
  ×3, `state/sav.py`), so composition matters, not only size. Also an army aboard **both** fleets.
- **Staging the armies:** an army needs moves to board and a split army has none, so pre-stage armies next to the ports and
  embark them the turn before sailing (as in the embark finding). Capacity rule `troops ≤ ships × 500`.
- **Measures:** the win rate against the 2.3 baseline for each army; what happens to the carried army (the loser's army is
  destroyed with its fleet; is the winner's army touched? casualties?); the post-battle supplies and moves; the effect on
  fleet **moves** of the cargo (`troops/100/ships + 1` fewer).
- **Also:** an army aboard a fleet in a **siege-style** target? (Not in scope: naval battles only.)

**Acceptance:** a table of win rate by cargo; the formula's predicted shift (a Monte-Carlo with the real `siegeStrength`) next
to the observed one; the saves of one win and one loss per cell.

## 8. Task T4: fleets lost at sea, especially in rough water

**Goal:** observe losses at sea, measure the damage distribution, and compare it with the storm formula (§2).

Waiting for a natural loss is slow (a healthy fleet at 100 % takes many winter turns), so the plan has two evidence classes,
kept apart in every report:

- **Natural runs:** from the T1 fleets or a fresh one, park a fleet in open sea far from any own city (damage doubled)
  through a winter (Winter 1/5 weather, radius 5, damage min(5, 2·dmg) then doubled+1, with 1-in-20 spikes to 30), with and without
  an army aboard, and **record every turn**: condition, ships, supplies, moves, news ("lost at sea"), the army's troops/units.
  Do it on several seeds. Rough sea is found by reading the map: weather paints code 1 around the 20 region centres (the
  DAT list is at `0x1F876`); the harness can read those tiles from each autosave and steer the fleet to a rough-sea tile.
- **Synthetic states** (clearly labelled, never presented as play): edit a fleet record in a copy of a save (condition 45, a
  chosen tile on code 1, with or without an army aboard) so that the loss and the large-damage branch are reached in a few turns
  and many seeds. `state/sav.py` already parses the fleet record (26 bytes: x, y, owner, condition at `+20`, carried army at
  `+22`); a writer must be added and the edited save must pass a round-trip check before it is used.

**Experiments:**

| # | Setup | Measures |
|---|---|---|
| 4.1 | calm sea, next to an own city (damage halved), Summer | baseline: condition loss per turn, N turns × seeds |
| 4.2 | calm sea, away from cities, Autumn/Winter | the doubled + spike branch |
| 4.3 | rough sea (code 1), away from cities, Winter | the `min(8, 3·dmg)` branch; time to `condition < 40` |
| 4.4 | same, **army aboard** (5,000 and 15,000 troops) | army casualties on the `dmg ≥ 6` branch; whole units lost when `d > 70`; the army dying with the fleet |
| 4.5 | out of supply (supplies 0) | −3 moves and −Random(2) condition a turn |
| 4.6 | a fleet in a rough-sea tile, moves spent | whether it can leave (cost 3 per tile) and what staying costs |

**Acceptance:** per branch a table of observed damage with its seeds and saves, compared with the formula's distribution; at least
one natural loss "A fleet belonging to X is lost at sea." with the save before and after; the synthetic runs labelled.

## 9. Driver and tooling work this implies

All new orders follow the pitfalls in `CLAUDE.md`: hover before clicking; verify every click's effect (the selected unit, `SEL_ARMY` or
`SEL_FLEET`, or the save) and retry at most twice; **never click End turn twice** unless the first click provably did nothing (with two human seats
the next End turn belongs to the other seat, so "did the turn advance" must be read from `CUR_NATION`, not from the calendar alone); a File > Save clears
the selected-army variable, so select after saving.

1. `new_game` with several human rows; a round loop for two seats; end-turn handling per seat (T0).
2. `attack_fleet` and its confirm/result handling, including `TBattlePols` (the post-battle peace; it is also on the open list).
3. A fleet-record writer for synthetic states, with a parse/write round-trip test (T4).
4. Reading rough-sea tiles from an autosave and a sea path for fleets (a fleet analogue of `planner/path.py`: sea codes 0 and 1,
   cost 1 and 3).
5. A trial runner: load a save, set a seed, issue one order, record before/after, repeat over seeds (the Gallic-army experiment is
   the template, `runs/experiments/gallic-army.py`).
6. A Monte-Carlo of the battle and storm formulas for the comparisons (a small module, tested against hand cases).

## 10. Sequencing, size, and approval

**T0b** (civilisation sweep, M: about an hour of game time) and **T0** (two human seats, S–M) first; they decide how the rest is
driven. Then T1 (staging, M) → T2 (M) → T3 (M) → T4 natural (L) and T4 synthetic (M); the formula tooling (§9 item 6) can be built in
parallel. After T0: if two human seats cannot be driven, **stop and report** (decision 2).
Each task ends with a `findings/` draft (Method, Observations with saves, Inferences, What this does not establish) and a release
`run-exp-<name>` (the bot creates it). These are experiments, not runs: no strategy is being proven. A long two-seat game is close
to a run, so **the player's approval of this revision is requested before T0b/T0** (rule 4 applies if any of it is reframed as a run).

## 11. Risks

- Two human seats may not be driveable, or may break the one-save-per-turn assumption (T0 decides; the answer to "not driveable" is stop and report).
- The sweep (T0b) may show that several nations cannot start cleanly with the current harness (assumptions about nation 0); those are fixes or findings, and may add work before T0.
- Ptolemaic is broke (−9 talents) and Seleucid has wars of its own: an AI-run nation's choices can disturb the staging.
- AI interference while staging (Gaul took Caere; an AI field battle happened to army 0): mitigated by per-turn saves and by
  choosing quiet ports and sea lanes, not eliminated.
- A naval battle may play out on a screen (like the field battle) rather than instantly; the driver would need `play_battle`
  for it.
- Win-rate cells with a random 0–30 % need enough seeds; 10 per cell gives a coarse answer, enough to separate 50 % from 90 %,
  not 50 % from 60 %.
- Synthetic states test the formula, not the game's play; they must be labelled so, and a natural loss is still wanted.

## 12. Questions: answered and still open

**Answered by the player (2026-10-02):** the pair (Carthage + Ptolemaic, then Seleucid + Ptolemaic, not Rome); the civilisation sweep
(all 16, two turns each); stop and report if two humans cannot be driven; synthetic states acceptable, labelled; 10 seeds per cell.

**Still open, for the reviewers:**
1. Should the **rough-sea reading** (finding code-1 tiles from an autosave and steering a fleet onto one) come before T2, since every
   storm result and every rough-water battle depends on it? (The plan puts it in T4; it could be a T1 deliverable.)
2. Are the **cells** in §6-§8 the right ones for 10 seeds each, or is there a cheaper design that answers the same questions
   (for example fewer sizes, more compositions)?
3. In T0b, what else should be recorded per nation that would reveal a quirk (the research reports are code reading, not play)?
4. Anything in §2 you believe the original does differently?
5. Is two turns per nation enough to see a nation-specific start problem, or should some nations (the fleet owners) get more?

## 13. Review plan

PR with this file only; `python3 scripts/external_review.py --pr <n>` (the default chain, GPT-5.6 Luna then MiniMax-M2.7 since 2026-10-10; it was DeepSeek V4.1 Flash then Luna from 2026-10-05; the quota check first, `CLAUDE.md` L50); a Claude pass with
`/review-pr <n>`; the player answers §12 and approves T0b/T0.

## Appendix A. The start-save facts this plan relies on

**Correction (2026-10-02, T0b sweep, `findings/2026-10-02-start-as-each-nation.md`):** the facts below are the world **as seen from Rome's seat (seat 11)**,
after eleven AI seats have moved. The start differs with the nation you choose: in Ptolemaic's own start (seat 2) it has **4,900 talents**, a **war with
Seleucid**, and its fleet at **(189,89) with condition 75** (not (190,93), 100); in Seleucid's own start (seat 4) it has 2,700 talents and a third war
(with Ptolemaic). Carthage's fleet (90 ships at (49,62), condition 85) is the same at seats 11 and 13. Pair 1 and pair 2 should be staged from the starts of the
nations that are human, not from the Rome start.

Parsed from `saves/run0-start-AUTO0720-seed12345.SAV` with `state/sav.py` (`sav.load`), 2026-10-02:

```text
fleets: [(0, Carthage,  (49, 62),  90 ships, condition 85), (1, Ptolemaic, (190, 93), 70 ships, condition 100)]
wars at the start: Bithynia-Seleucid, Carthage-Celtiberia, Galatia-Seleucid, Gaul-Rome
 1 Carthage  cities 34 coastal 28 treasury 11000      3 Ptolemaic cities 46 coastal 20 treasury    -9
 2 Seleucid  cities 62 coastal 16 treasury  1840      Seleucid-Ptolemaic relation -18, Carthage-Ptolemaic -10
rough-sea tiles (map code 1): 112
```

`docs/rules-digest.md` §10 describes Rome's start and does not mention these fleets; the fleet counts here are from the save alone, which is why
T1 starts by re-reading them from a fresh New Game of the chosen pair.
