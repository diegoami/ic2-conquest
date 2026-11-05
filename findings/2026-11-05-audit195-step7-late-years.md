# Audit #195 step 7: the late-year (266–264 BC) AI-phase differences by class

**Tag:** [confirmed for the classes from data; derived for the per-row attribution, see Limits]. No new Wine run yet: an
original-side fleet hook on three of the turns is scheduled (§4).
**Status:** draft for research.
**Task:** research #195 inventory, pass-1 step 7: "classify the late-year AI-phase differences (266–264 BC) by class".
Owner 2026-11-05: "ok do step 7 while waiting".

Remake pin: **v0.9.4** = `168dbc04`.

## Data

The long games that reach 266–264 BC and were replayed anchored on `168dbc04`:
- `carthage-rulebot1-150t` (rulebot-1, Carthage, to Summer 264 BC; `anchored-168dbc04-ts`);
- `rome-rulebot1-150t-h1` (Rome's game handed to Seleucid; `anchored-168dbc04-ts`);
- `ptolemaic-rulebot2-150t-h1` (rulebot-2, handed to Seleucid; `anchored-turnseed`, run on `168dbc04` at 10:47).

The three observer games were replayed on `a44c42fc` (v0.9.3) and are left out.

A **position row** is (turn, nation, armies or fleets) whose units end on different tiles after the AI phase
(`pin_diff.py`). There are **222 late-year rows**: Carthage 104, Rome-h1 35, Ptolemaic-rb2-h1 83.

## Method

`runs/experiments/audit195/late_classify.py` reads, for each row, the original's human-phase checkpoint (pre), the
original's end and the remake's end. It assigns the first class that applies:

| class | test |
|---|---|
| human_phase | the nation is the human's, or its units already differ after the human's orders (a carry-over, not an AI decision) |
| diplomacy | the nation's new relations this turn (war, alliance, peace, trade) differ between the games |
| human_battle | the nation's news this turn names the human's nation (a battle or siege with the human: X3/X6 territory) |
| battle | the nation's battle and siege news this turn differs (draws) |
| downstream | a nation that plays earlier in this round already has a row this turn |
| quiet / quiet_fleet / quiet_fleet_ports | none of these. Fleet rows are split by whether both games' tiles are next to an own city (the port draws of `2026-11-04-port-rows-and-carried-army.md`) |

## Result

| class | rows | Carthage | Rome-h1 | Ptolemaic-rb2-h1 |
|---|---|---|---|---|
| human_phase | 53 | 0 | 0 | 53 (Seleucid, the rulebot-2 seat) |
| diplomacy | 27 | 15 | 10 | 2 |
| battle | 26 | 11 | 9 | 6 |
| human_battle | 7 | 7 | 0 | 0 |
| downstream | 41 | 32 | 1 | 8 |
| quiet_fleet_ports | 3 | | | |
| **quiet_fleet** | **45** | | | |
| **quiet (armies)** | **20** | | | |

Notes on the classes:
- **Draws (diplomacy, battle) and their consequences (downstream)**, not counting the 7 human_battle rows, cover 94 rows: 42 % of all rows and 56 % of the 169
  non-human-phase rows. This matches the earlier years, where the stays and most position rows came down to war rolls
  and battle outcomes (X1 and stays findings).
- **human_phase**: all 53 are the rulebot-2 seat's own armies. The difference starts in the human phase (that game's
  bot predates the 2026-11-05 path fix), not in the AI.
- **human_battle**: 7 rows in the Carthage game, where an AI fought the human. That is the territory of X3 (no seat
  replay in Instant) and X6 (instant human battles).

**The quiet rows: 68, the candidates for a rule difference.**

`quiet_distances.jsonl` pairs each original unit with a remake unit of the same size:
- **Armies (20):** 8 differ by at most 3 tiles (tie-like: Macedonia round Pella, Carthage round Carthago, Ptolemaic
  round Alexandria). 11 are farther (Media t100/t102 by about 10 tiles; Rome t123 at (80,73) against (103,47);
  Ptolemaic t130 at (113,72) against (114,95)). 1 is unpaired.
- **Fleets (48):** 8 are within 3 tiles, 39 farther, 1 unpaired. One pattern dominates:
  - **Celtiberia's fleet (fleet 6 in the t127 AI log; the rows carry no fleet id): 12 quiet rows** (14 in all), mostly every other turn from t96 to t145.
    - In the original it sails between (48,56) and the open sea at about (70,67).
    - In the remake it stays at (48,56). Its AI log (`late-ailog-v1`, t127) reads "original zero-move mercenary
      rendezvous army-15: fleet fleet-6 toward (48, 56)" and "fleet phase: fleet-6 stored-route".
    - So this is a recurring fleet-route / rendezvous difference: the remake waits for army-15, the original sails off.
  - **Ptolemaic's fleets (14 rows in the two rulebot-1 games):** at t130 the remake chooses "port" for both fleets.
    The original's choice is unknown.

## 4. Open: the original side of the fleet rows

The hook `patches/fleetphase_hook.py` logs F608's branch per fleet: port, stored route, position, moves and hunt.
Its run on the Carthage game's t127, t129 (Celtiberia's shuttle) and t130 (Ptolemaic) is scheduled:
- starts `late-fleet-starts/` (the stored `t126-a00`, `t128-a00` and `t129-a00`, with their logged RandSeeds; no human
  orders on those turns);
- it runs in `between_games_hooks.sh`, in the long-game queue's next gap, after C22 v4 and the FB7C stays run.

It will show what the original's fleet phase chose, and whether the rendezvous wait exists there.

## Limits

- **The classes are first-match heuristics, so "quiet" means a candidate, not a proven rule difference.**
  - "battle" means only that the nation's battle or siege news differs; it is not traced to a draw.
  - "downstream" assumes that an earlier seat's difference explains a later one. The seat order is read from the save
    (`turn_order`, starting after the human's seat).
  - "diplomacy" compares the nation's own relation changes, and catches a war that came through an ally (the Media
    route of the stays).
- **Only the pin `168dbc04` games.** The observer games (`a44c42fc`, no human seat) would add AI-only late years; a
  `168dbc04` replay of them is a later step.

## Rows

No inventory row changes yet. The fleet-route rows (D19 stored-route lifetime, the mercenary rendezvous) get the
Celtiberia shuttle as a measured candidate once the fleet hook reports.

## Evidence

- `runs/experiments/data/run-exp-audit195/`:
  - `late-classify-v2/` (`rows.jsonl`, `summary.txt`, `quiet_distances.jsonl`);
  - `late-classify-v1/` (before the human_phase class);
  - `late-ailog-v1/` (the remake's AI logs, Carthage t127 and t130);
  - `late-fleet-starts/` (`seeds.json`).
- The games' saves are in releases `ic2-save-corpus` and `run-exp-longgames`; the scheduled starts are hashed in
  `SAVES.sha256`.
- Tooling: `runs/experiments/audit195/late_classify.py`, `between_games_hooks.sh`.
