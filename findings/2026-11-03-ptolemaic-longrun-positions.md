# Ptolemaic long run on v0.9.1: all 15 position differences attributed, including two new remake gaps (capital defence after a battle with the human, the new fleet's launch tile)

**Tag:** [confirmed: Wine hooks + remake probes + code in both games]. Wine only.
**Status:** promoted by research PR #183 (merge `c7e206c`) as `docs/reports/2026-11-03-ptolemaic-longrun-positions.md`.
- **Spec gained:** capital defence goes on while a human battle is pending; the launch-tile rule; the resupply tie-break.
- **Other reports:** the 2026-10-30 report's §2 is refined, and its §4 tie edge is marked measured. The IC-main
  remake-fixes report has a new section for the three gaps.
- **Research verified** the disassembly of 939C, 96BC, EFC8 and E670, the remake lines, the hook sequences and the step walk,
  and 15 of 15 inert controls.
- **Rows 11–15** are recorded as an inference (they depend on the draw; which draw is not traced).
- **Not re-checked by research:** the decide-report counts, the control probe, `a004.SAV` and ArmyTick.
- **Research's watch-field detail** is answered in the correction below.
**Task:** owner 2026-11-03, "continue with next tasks", after the v0.9.1 recheck (`2026-11-03-remake-v091-recheck.md`,
research PR #181). Open item there: "the other 14 position nation-turns of the Ptolemaic game". Remake v0.9.1 `0d9d4729`.

## Method

The anchored replay of `ptolemaic-rulebot1-40t` (`run-exp-longrun-v091`) lists 15 AI nation-turns whose armies or fleets
end on other tiles (`positions-v1.txt`, `positions-starts-v1.txt`).

**Starts.** For the 9 turns involved, the start is the original's checkpoint just before End turn, with the human's orders
already given (`decidestarts/ptol-tNNpre.SAV`).

**Hooks on the original:** decide, step, gap-B and fleet-phase. Each was run from those starts with a fresh seeded process
and one End turn. In every run the hooked autosave is byte-identical to the plain build (`inert.json`).

**Remake side:**
- the same starts, with `aiprobe` and `aidecide/compare.py`;
- a control with Galatia's army pinned (`probes/0d9d4729-ptol-t01pre-galatia12-moves0`).

**Draw check:** whether the hooked original, whose random stream differs from the campaign's, ends on the campaign's
original tile (`positions-hooked-vs-campaign-v1.txt`).

Decision comparison (`decide-report-v1.json`): 104 army decisions in these 9 rounds. 85 match exactly, 3 match through an
unlogged garrison move, 1 is diplomacy (Carthage's war with Celtiberia ends in the original's round, turn 2), and 2 differ
in the resupply city (§3).

## Attribution

| # | Turn, nation | Original → remake end | Cause |
|---|---|---|---|
| 1 | 1 Galatia (army 12) | (200,45) → (198,46) | §1 no-command fallback without the AAB4 gate (already reported) |
| 2 | 13 Seleucid (army 9, 1 move) | (187,59) → (188,60) | §1 |
| 3 | 16 Seleucid (army 11, 1 move) | (187,59) → (188,59) | §1 |
| 4 | 16 Bithynia (army 10) | (204,32) → (205,32) | follows from 3: its walk target is that Seleucid army, at (187,59) in the original and (188,59) in the remake (step hook) |
| 5 | 1 Seleucid (army 5) | (178,48) → (178,47) | §2 capital defence after a battle with the human's army |
| 6 | 1 Bithynia (army 11) | (185,38) → (184,38) | follows from 5: its walk target is Seleucid army 5's end tile, (178,48) in the original and (178,47) in the remake |
| 7 | 21 Celtiberia (army 10) | (38,43) → (44,48) | §3 resupply-city tie: table order against city id |
| 8 | 25 Galatia (army 9) | (189,40) → (195,42) | §3 |
| 9 | 30 Numidia (new fleet) | (37,83) → (36,83) | §4 the new fleet's launch tile |
| 10 | 36 Seleucid (new fleet) | (219,55) → (219,54) | §4 |
| 11 | 2 Rome (army 1) | (110,46) → (110,44) | random draws: the hooked original ends on the remake's tile |
| 12–15 | 29 Rome, Macedonia, Gaul, Illyria | various | random draws, as 11. In the campaign's round, Gaul's and Macedonia's armies collected their finished recruits (queue state 24) from their home cities; in the hooked run, as in the remake, they did not |

**Remake gaps:** 4 causes account for 10 rows (§1–§4). **Random:** 5 rows.

## 1. The no-command fallback has no AAB4 gate (rows 1–4)

Already in `2026-11-03-remake-v091-recheck.md` §4 (research `597b996`). Two more measured cases, both Seleucid armies with
1 move at (187,59) and the E84C branch:
- **Original** (decide hook): the army stays.
- **Remake:** "garrison fallback (186, 58)" / "(220, 59)" moves it one tile (`decide-remake-0d9d4729-v1/ptol-t13pre`,
  `ptol-t16pre` ailog).

Research recorded "spent moves earlier" as our reading for turn 1's 8 moves. The remake's own checkpoint before End turn
(`anchored/t01/a004.SAV`) gives army 12 8 moves, and the round tick refills only after all seats (`TurnPhase.ArmyTick`,
round scope). So in the remake, too, the army enters Galatia's seat with 8 of 10 moves.

## 2. Capital defence keeps dispatching while the battle with the human's army is pending (rows 5–6)

**State.** Ptolemaic turn 1. The human's last order moved Ptolemaic army 6 (27,700) to (221,69), next to Antioch; Seleucid
is at war with Ptolemaic.

**Original** (gap-B hook, `hooks-gapb-t01pre-v1`, seq 9–17):
- **Seq 11–13.** Capital defence `FUN_0044efc8` sends army 4: DBA8 called from 0x44F2FE, target (221,69), then AEE4 at
  (222,68) against army 6. The army 6 being attacked is the human's, so the attack opens a battle the human defends: the
  campaign's End-turn reply is "BATTLE Seleucid v Ptolemaic — Ptolemaic to place units".
- **Seq 14–15.** The pass goes on. Army 5 at (172,49), the second responder, gets DBA8 from 0x44F2FE with target (221,69),
  and its line walk heads for the waypoint (227,49) (`hooks-step-v1`, steps (172,49) → (178,48)).
- **Seq 16.** After the battle, the seat is played again (FA20 at seq 16; `2026-10-31-ai-seat-replayed-after-human-battle.md`
  lists this seat as S03 r1).

Why the pass goes on:
- `FUN_0044efc8`'s responder loop has no test of the battle flag `0x4A0B7C`.
- Its alive test is the threat record's owner ≥ 0 (0x44F207).
- While the human's battle is pending, army 6 is still alive.

**Remake** (`AiCapitalDefence.Run`, `0d9d4729`):
- With an interrupting battle (`IAiBattleInterruption.ArmyPhaseInterrupted`), the loop `break`s after the attack
  (`AiCapitalDefence.cs:110`, `:137`).
- With an instant battle, army 6 is destroyed at once, and `NearestThreat` skips it as `null` (line 45–46).

Either way army 5 isn't dispatched. It takes its target-tree decision instead, "approach target army (198, 46)", and ends at
(178,47). The control with Galatia's army pinned at (200,45) gives the same (178,47), so the Galatia move (row 1) isn't the
cause.

**Contrast with S05** (`2026-10-30-ai-decisions-vs-remake-main.md` §2): there the threat was an AI army. The battle resolved
inside the walk, the threat was dead (owner −1), and the second responder took its normal decision. That case and this one
follow the same code. Whether the battle is resolved at once or left pending for the human decides whether the next
responder sees the threat alive.

**Fix direction (for research and IC main):** under Classical Faithful, a threat whose battle with the human is pending stays
a valid threat for the later responders of the same pass, and the pass does not stop at the interruption. The remake's
instant-battle mode has no original counterpart for a battle the human defends, so how it should treat this case is a design
question.

## 3. The resupply-city tie: table order against city id, now in play (rows 7–8)

Already listed as a code-only edge in research's `2026-10-30-ai-decisions-vs-remake-main.md` §4 ("ties go by table order in
the original, against city id in the remake"). Here it is measured.

**What the original does.** `FUN_0044e670` keeps the first city with the smallest adjusted distance (strict `<`, table
order). The remake's `ScoreResupplyCity` breaks equal scores by `string.CompareOrdinal(city.Id)`.

| Turn, army | Cities at the minimum distance (index, name) | Original (hook `home`) | Remake |
|---|---|---|---|
| 21, Celtiberia army 10 at (43,43) | 14 Segovia (31,44), 15 Taletum (31,51), 28 Saguntum (47,55), all 12 | Segovia (31,44) | Saguntum (47,55) |
| 25, Galatia army 9 at (193,38) | 211 Pessinus (188,41), 227 Gordium (195,43), both 5 | Pessinus (188,41) | Gordium (195,43) |

Two of 104 decisions, two rows in 40 turns.

**Not explained from the save.** A nearer city with stock above strength (Numantia at distance 1, Gangra at 4) is not chosen
in either game, probably because stocks change before the seat. Since both games exclude it, it doesn't affect this
comparison.

## 4. A new fleet launches on the last sea tile in column-major order (rows 9–10)

**Original.** The launch `FUN_0044a050` ("… finishes a new fleet at …") places the fleet with
`FUN_0044939c(city xy, mode 0, &out)`:
- It scans rings r = 0, 1, 2 and so on around the city: x from −r to +r in the outer loop, y from −r to +r in the inner one.
  The map is column-major, `DAT_0045e870 + x·0x118 + y·2`.
- It takes the tiles whose terrain code is in [0, 1] and for which `FUN_004496bc` returns 0.
- It **overwrites** `out` at every match, so the last match wins, and returns after the first ring with a match.
- `FUN_004496bc` isn't an occupancy test: it excludes a map region (x ≥ 248, or x ≥ 214 with y ≥ 99).

**Remake.** `CoastalCity.FirstAdjacentSeaTile` takes the first sea tile among the 8 neighbours in row-major order, north-west
first, and has neither the region exclusion nor the outer rings.

Measured, from the save's map cells (`fleet-launch-tiles-v1.txt`) and the fleet-phase hook (`hooks-fleet-v1`, the fleets
built at (0,0) with 0 moves at the start):

| City | Sea neighbours, column-major | Original | Remake |
|---|---|---|---|
| Siga (37,84), Numidia, turn 30 | (36,83), (37,83) | (37,83) = the last | (36,83) = row-major first |
| Issus (220,54), Seleucid, turn 36 | (219,54), (219,55) | (219,55) = the last | (219,54) = row-major first |

**Same helper, code only, not observed:**
- `FUN_0044b840`, the AI disembark, calls it with mode 1 (land codes 2–11, no region test) for the landing tile. The remake's
  `LandingTile.FirstAdjacentLandTile` uses the same row-major-first convention as its sea helper.
- `FUN_0044e1fc`, a fleet route to a land target, calls it with mode 0 for the sea tile beside the target.

## Correction (2026-11-03, after research's intake, PR #183)

Research found that in `hooks-gapb-t01pre-v1` the `watch` field shows army 5 still at 8 moves at seq 16–17, while the step
hook has it at 2 after (178,48). The cause is the hook build. The watched armies are compiled into
`… seed gapbhook.exe`, and the runner reuses an existing exe. The exe in the game folder had been built for armies 2 and 5
(`hooks-gapb-v1`, 2026-11-02: the bytes `A1 <0x47C1EC + 0x290·a + 4>` occur for a = 2 and 5 only). So the run's `watch` labels
5 and 4 are armies 2 and 5. Read that way:
- army 5 goes from 8 to 0 at seq 16, matching its own record at seq 22 (0 moves at (178,48));
- army 2 (Macedonia) stays at 8.

None of the attribution depends on a watch field. `patches/gapb_hook.py` now names the exe by its watch list
(`… seed gapbhook-w5-4.exe`), so a different list builds its own exe.

## Open

- **§2:** whether the remake should change its instant-battle mode for a battle the human defends (design).
- **§4:** the disembark and E1FC callers (code only).
- **Rows 11–15:** random. Which draw changed the Gaul and Macedonia recruit collection in the campaign's turn-29 round was not
  traced.

## Evidence

**Data:** `runs/experiments/data/run-exp-longrun-v091/`
- `positions-v1.txt`, `positions-starts-v1.txt`, `positions-hooked-vs-campaign-v1.txt`;
- `hooks-decide-v1`, `decide-remake-0d9d4729-v1`, `decide-report-v1.json`, `decide-compare-v1.txt`;
- `hooks-step-v1`, `hooks-gapb-t01pre-v1`, `hooks-fleet-v1`;
- `probes/0d9d4729-ptol-t01pre-galatia12-moves0`, `fleet-launch-tiles-v1.txt`.

**Saves** (release `run-exp-longrun-v091`): `decide-hook-saves.tar.gz` (the `decidestarts/ptol-tNNpre.SAV` starts and the
decide-hook autosaves) and `positions-hooks-saves.tar.gz`. The starts are the campaign's `original/t01-a03.SAV`, `t02-a01`,
`t13-a01`, `t16-a01`, `t21-a01`, `t25-a01`, `t29-a01`, `t30-a01` and `t36-a00`.

**Tooling:** `difftest/probes/step_hook_run.py` now takes start saves (one End turn each).
