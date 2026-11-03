# The tile finder in play, and a Macedonia long run on v0.9.1: the remake builds Caspian fleets the original cannot

**Tag:** [confirmed: Wine hooks + remake code and probes] for §1–§3; [measured] for §4's counts. Wine only.
**Status:** promoted by research PR #186 (merge `8810f80`) as `docs/reports/2026-11-03-placement-and-macedonia-longrun.md`.
- **Spec:** the launch scan reads the live map, E1FC and B840 match the remake, and the AI build city excludes the 96BC zone.
- **IC-main fixes report:** the launch fix is ReplaceLandTarget on the live MapCode, the Caspian gap is added, and the
  disembark item is withdrawn.
- **Research's correction to §2:** 496E0's best score starts at 1000 (0x3E8) and is replaced only by a smaller one, so a busy
  city's 2000 never wins. A busy city is skipped in effect, as in the remake, and only the table-order tie remains.
- **Research's question on the global word `0x4A0330` (read at 0x449783):** it is the calendar **week**
  (`harness/driver.py`: `SEASON, WEEK, YEAR_BC = 0x4A032E, 0x4A0330, 0x4A0332`). It runs 0–11 (written as (week + 2) % 12; research PR #187), so `> −1` is always true,
  and the busy test reduces to the fleet's owner and build city.
- **Not re-checked by research:** the Thracia E1FC mismatch, the decide counts, the treasury, Salamis/Alexandria and the war
  roll.
**Task:** owner 2026-11-03, "sure keep going, 1 and 2":
1. check the code-only callers of the tile finder `FUN_0044939c` in play (`2026-11-03-ptolemaic-longrun-positions.md` §4);
2. play another long game on v0.9.1 (Macedonia).

Remake v0.9.1 `0d9d4729`.

## 1. The tile finder in play: the remake already follows it except at a fleet's launch

**Hook.** `patches/place_hook.py` logs every call of `FUN_0044939c(xy, mode, &out)`: its entry (the caller's return address,
xy, mode, and EBX/ESI, where the callers keep the fleet index) and its exit (the tile written to `out`).

**Runs.** Three starts with an AI army aboard a fleet, 3 End turns each (`placestarts/`, from the stored v0.9.0 games:
Rome `t04-a02`, Gaul `t29-a00`, Rome `t37-a00`), in runs `hooks-place-v1` and `hooks-place-v1b`. Every hooked autosave is
byte-identical to the plain build. Rome t37's first control failed to start its game window after a session restart; it was
re-run in `-v1b`, and the first log is kept.

**Comparison** (`place-compare-v1.txt`): each original result against the remake's rule for that caller, computed on the
start save's map cells.

| Caller (return address) | Calls | Same tile | Remake rule |
|---|---|---|---|
| fleet route to a land target, `FUN_0044e1fc` (0x44E275), mode 0 | 26 | 24 | `ClassicalFleetNavigation.ReplaceLandTarget` (T247): last match of the first ring, x outer, the 96BC zone excluded |
| AI disembark, `FUN_0044b840` (0x44B86A), mode 1 | 3 | 3 | `ClassicalFleetNavigation.LandingTarget`, the same rule with codes 2–11 |
| new fleet launch, `FUN_0044a050` (0x44A0CF), mode 0 | 2 | 1 | `CoastalCity.FirstAdjacentSeaTile`: first sea tile in row-major order, terrain only |

**The two E1FC mismatches** are Thracia's fleet 6 routing to (170,38) while it stands on (171,39):
- The original returns its own tile, (171,39), although the start map has its marker (347) there.
- On the start map, the remake's rule gives (171,38).
- In play, the anchored v0.9.1 replay ends the fleet at (171,21) in both games, so no difference shows.

**Correction to `2026-11-03-ptolemaic-longrun-positions.md` §4.** It said the remake's `LandingTile.FirstAdjacentLandTile`
follows the row-major convention. That is so, but it serves only the generic Disembark command. The Classical Faithful AI
disembark and E1FC paths already use the original's rule (`OriginalFleetMove.cs:117–120`, `ClassicalFleetNavigation.cs:15–36`).
**Only the launch is a gap.**

**The launch also respects units.** At Issus (220,54), on Gaul turn 29:
- a Seleucid fleet stood on (219,55) (map code 334), so the original launched on (219,54);
- in the Ptolemaic game the tile was free, and the launch went to (219,55).

The finder accepts only codes 0–1, and the map cell holds the unit's marker. So the fix is
`ReplaceLandTarget(build city)` with the remake's live `OriginalFleetPort.MapCode` (fleets 300, armies 200), not the
static terrain.

## 2. The remake builds fleets on the Caspian; the original cannot (new gap)

Macedonia long run (`macedonia-rulebot1-40t`, 40 turns, seed 12345, rulebot-1, no game over): on turns 19, 25, 26 and 27,
the remake's Media orders a 64-ship fleet at Ardabil (309,37), city 331, on the Caspian. The original's Media orders none.
- On turn 19 Media's treasury goes 3,122 → 1,982 in the remake and 3,122 → 2,622 in the original: the fleet's 640 talents
  plus the same 500.
- The decide-hook rerun of turn 19, with a different random stream, also has no fleet in the original.

**Original** (`FUN_004496e0`, the AI's fleet-build city):
- It skips every own city for which `FUN_004496bc` is true, that is x ≥ 248, or x ≥ 214 with y ≥ 99.
- It needs `FUN_004492c0(&xy, 0)` to leave a value ≥ 0 (not read here; presumably the sea cell), scores the distance to the capital, and gives 2000 to a city where one of the
  nation's fleets is under construction.
- It keeps the minimum, strict `<`, in table order.

Ardabil is at x = 309, so Media never has a build city there.

**Remake** (`CoastalCity.FleetBuildCity`, used by `AiFaithfulEconomy.ChoosePort`): no zone exclusion; any coastal own city,
the Caspian included; busy cities skipped; ties by city id.

**Fix direction:** under Classical Faithful, exclude the 96BC zone (`ClassicalFleetNavigation.ExcludedEasternZone`) from the
AI's build city. One smaller difference from the same code is not observed in play: ties go by table order. (The busy city's
2000 never wins, because the best score starts at 1000: research's correction, PR #186.)

## 3. Macedonia decisions: the resupply tie four more times

`decide_hook_run` was run on the 18 turns with army position rows, each from the checkpoint before End turn
(`decidestarts-mac/`); all 18 controls are byte-identical. The remake side is `aidecide/compare.py`
(`decide-mac-report-v1.json`). Of 212 decisions:

| Verdict | Count |
|---|---|
| same | 198 (7 of them through an unlogged garrison move) |
| diplomacy or battle state | 5 |
| resupply-city tie, table order against city id | 4: Seleucid t19 Synnada/Gordium (5); Celtiberia t23 and t31 Segovia/Saguntum (12, 9); Ptolemaic t23 Naucratis/Busiris (2) |
| same target army under another name | 4: the target is an army created during the round, outside the start table, with the same score and distance. The original gives it the next table index, the remake the next id (`army-13`, `army-16`) |
| state | 1: Illyria t33, city and army scores off by 1–3 |

## 4. Macedonia position rows (33)

`positions-macedonia-v1.txt`. The draw check, `positions-macedonia-hooked-v1.txt`, asks whether the hooked original (a fresh
random stream) ends on the campaign's original tile:

| Cause | Rows |
|---|---|
| §2 Caspian fleet (Media t19, 25, 26, 27) | 4 |
| launch tile (Seleucid fleet t18 at Issus, Numidia fleet t30 at Siga; the same cities and tiles as the Ptolemaic game) | 2 |
| resupply tie (Seleucid t19, Celtiberia t31) | 2 |
| no-command fallback without the AAB4 gate (Carthage army 10, t26: 8 moves, full allowance 9; stays in the original, "garrison fallback (88, 80)" in the remake) | 1 |
| a war roll in the remake's round only (Seleucid t26: "declares war on Media" and, through the alliance, Armenia; the same-start probe without the war walks to the original's (207,44)) | 1 |
| gap C, the port case: Ptolemaic fleet 1 at t23 stays next to its port Salamis (201,73) in the original (fleet hook: port 243); in the remake it sails to (208,82) | 1 |
| a draw: the hooked original ends on the remake's tile (Ptolemaic fleet t25) | 1 |
| depend on the draws: the hooked original ends on neither tile | 21 |

**The 21 draw-dependent rows** can't be attributed further: the campaign did not log its random state. The runner now sets
`IC2_LOG_RANDSEED=1` (`run_all.sh`). A replay with the logged seed may still not be exact, because two paint routines
reseed (`2026-11-02-seleucid-turn26-overthrow.md`).

**Gap C (Salamis).**
- The remake's `OriginalFleetPort.Pick` should also choose Salamis: own, 77 tons > 20, distance 1, fleet supplies 320 > 0,
  score −1.
- In the original, F608 then calls E1FC with Salamis, and the fleet does not move.
- At Alexandria (Rome start, turns 1–3, place hook) the original likewise stays at (189,93), although 939C's replacement
  tile is (191,93), two tiles away. So the original's stop comes after the replacement, in E1FC's path step (D174/E094).
  That part is not traced here.
- The remake's divergence is in its E1FC emulation, not in the port pick.

## Open

- Gap C: why E1FC leaves a fleet next to its port in place (D174/E094); the remake moves it.
- §2's table-order tie (code only).
- The 21 draw-dependent Macedonia rows.

## Evidence

**Data:** `runs/experiments/data/run-exp-longrun-v091/`
- placement: `hooks-place-v1`, `hooks-place-v1b`, `place-compare-v1.txt`, `probes/0d9d4729-rome-t37pre`;
- Macedonia game: `macedonia-rulebot1-40t`, `stays-macedonia-v1.txt`, `classify-macedonia-v1.txt`, `positions-macedonia-v1.txt`,
  `positions-macedonia-hooked-v1.txt`;
- Macedonia hooks: `hooks-decide-mac-v1`, `decide-mac-remake-0d9d4729-v1`, `decide-mac-report-v1.json`, `hooks-step-mac-v1`,
  `hooks-fleet-mac-v1`.

**Saves** (release `run-exp-longrun-v091`): `macedonia-rulebot1-40t-saves.tar.gz`, `place-hook-saves.tar.gz` and
`macedonia-hooks-saves.tar.gz`. The starts are the campaign's checkpoints before End turn, `original/tNN-a00.SAV`.

**Tooling:** `patches/place_hook.py`.
