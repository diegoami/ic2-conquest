# Plan: fleet battles, armies aboard, and ships lost at sea

**Status:** plan for review and for the player's approval (2026-10-02). Nothing here has been run. Author: Claude Sonnet 5.5.
This plans three experiments that follow from the fleet orders now in `main` (`findings/2026-10-02-fleet-orders-live.md`),
which left **naval battles, battles with an army aboard, and storms at sea** untested.

## 1. What the player asked for

1. **Two human players.** At New Game more than one nation can be made human. Use two, have them **build or move fleets
   together**, put them **at war with each other**, and **test fleet battles**.
2. **Fleet battles with soldiers aboard**, where the result also depends on the soldiers on the fleets.
3. **Tasks where a fleet is sunk at high sea**, especially in **rough water**.

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

From `saves/run0-start-AUTO0720-seed12345.SAV`:

- **Carthage** (nation 1): 34 cities, **11,000 talents**, an AI fleet of **90 ships at (49,62)** (fleet 0), at war only with
  Celtiberia, trade with Seleucid, Greece and Thracia. **Rome** (nation 0): 25 cities, 2,200 talents, at war with Gaul.
- Both are coastal (Rome: Pisae, Tarquinii, Caere, Antium, Neapolis, ...; Carthage: Gades, Malaca, Carthago Novo, ...). The start
  save has **112 rough-sea tiles** already.
- The New Game form has **one "human" tick per nation row** (`Game.new_game` clicks `(109, 114 + 20·row)`); two ticks is the
  expected way to get two humans, **not yet tried**.
- **Lessons from the fleet work:** a fleet takes 12 turns to launch, and in those 12 turns Gaul took Caere (the build port);
  an AI can interrupt a staged state with a field battle (it happened to army 0). Plans must not depend on 12 quiet turns.

**Proposed pair: Rome and Carthage.** Carthage already has a 90-ship fleet (no wait), and the money to build more at once;
Rome can build the second fleet while Carthage sails. They are far apart (about 35 tiles), a fleet with 32 moves closes that
in two turns, and putting Rome and Carthage at war is a plain relations change. Alternatives (Rome + Greece, Carthage + Greece)
are listed as open question Q3.

## 4. Task T0: a spike, two human seats

**Goal:** know whether and how the original runs with two humans, before designing anything on it.

1. New Game with two human ticks (Rome and Carthage), seed 12345. Record: does the dialog allow it; the turn order; which seat
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
**Risk:** the save format may carry only one "current" seat; the harness assumes one human. If two humans cannot be driven
reliably, fall back to one human (Rome) plus the AI's own fleet (Carthage's 90-ship fleet) as the opponent, which already
covers T1/T2 but not "two humans building together".

## 5. Task T1: staging two adjacent fleets (shared by T2 and T3)

**Goal:** a committed, small save in which two hostile fleets are one tile apart at sea, plus a recipe to rebuild it.

- **Fleet A** (Carthage): the existing 90-ship fleet, or a new one. **Fleet B** (Rome): ordered at turn 1 (12 turns); order it at
  the safest port available (choose by looking at who is at war with Rome: not Caere, which Gaul took).
- **Move together:** both humans sail toward a meeting tile in open sea; record each fleet's moves per turn (check the
  `30 - (ships-50)/10` formula for 90 and 30 ships), supplies burn (`ships` a turn), condition drift.
- **Relations:** Rome and Carthage at war (T0). Then "adjacent enemy fleets, each with moves" is the state T2 and T3 branch from.
- **Avoid interruptions:** keep both fleets away from AI fleets and from each other's cities until the meeting; keep armies
  out of reach of Gaul; if an AI event breaks the staging, rebuild from the previous autosave (they are per turn).

**Deliverable:** `saves/fleets-adjacent-at-sea-<nnnn>.SAV` (about 130 KB) and `tests/make_fleet_battle_fixture.py`.

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

1. `new_game` with several human rows; a round loop for two seats; end-turn handling per seat (T0).
2. `attack_fleet` and its confirm/result handling, including `TBattlePols` (the post-battle peace; it is also on the open list).
3. A fleet-record writer for synthetic states, with a parse/write round-trip test (T4).
4. Reading rough-sea tiles from an autosave and a sea path for fleets (a fleet analogue of `planner/path.py`: sea codes 0 and 1,
   cost 1 and 3).
5. A trial runner: load a save, set a seed, issue one order, record before/after, repeat over seeds (the Gallic-army experiment is
   the template, `runs/experiments/gallic-army.py`).
6. A Monte-Carlo of the battle and storm formulas for the comparisons (a small module, tested against hand cases).

## 10. Sequencing, size, and approval

T0 (spike, S–M) → T1 (staging, M) → T2 (M) → T3 (M) → T4 natural (L) and T4 synthetic (M); the formula tooling (item 6) can
be built in parallel. After T0, the plan is re-checked: if two humans cannot be driven, T1–T3 use the AI's 90-ship Carthaginian fleet.
Each task ends with a `findings/` draft (Method, Observations with saves, Inferences, What this does not establish) and a release
`run-exp-<name>`. Experiments, not runs: no strategy is being proven, but a long two-seat game is close to one, so **the player's
approval of this plan is requested before T0** (rule 4 applies if any of it is reframed as a run).

## 11. Risks

- Two human seats may not be driveable, or may break the one-save-per-turn assumption (T0 decides).
- AI interference while staging (Gaul took Caere; an AI field battle happened to army 0): mitigated by per-turn saves and by
  choosing quiet ports and sea lanes, not eliminated.
- A naval battle may play out on a screen (like the field battle) rather than instantly; the driver would need `play_battle`
  for it.
- Win-rate cells with a random 0–30 % need enough seeds; 10 per cell gives a coarse answer, enough to separate 50 % from 90 %,
  not 50 % from 60 %.
- Synthetic states test the formula, not the game's play; they must be labelled so, and a natural loss is still wanted.

## 12. Open questions for the reviewers and the player

1. Is **Rome + Carthage** the right pair (Carthage's ready 90-ship fleet and 11,000 talents), or a pair with neighbouring ports?
2. Should T0 be allowed to conclude "use one human + the AI fleet", dropping "two humans building together"?
3. Are synthetic (edited-save) states acceptable as a second evidence class for T4, if labelled?
4. Is 10 seeds per cell enough, or should T2/T3 aim for a smaller number of cells with 30 seeds?
5. Should the weather/rough-sea reading (Task T4) come first, since every storm result depends on finding rough sea reliably?
6. Anything in §2 you believe the original does differently (the research reports are code reading, not play)?

## 13. Review plan

PR with this file only; `python3 scripts/external_review.py --pr <n>` (DeepSeek V4.1 Flash, then GPT-6 Luna); a Claude pass with
`/review-pr <n>`; the player answers §12 and approves T0.
