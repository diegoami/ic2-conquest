# The stored fleet route lives for one fleet phase; the fleet phase's order, hunt and port pick

**Tag:** [confirmed] from the disassembly and in emulation, with no helper, Random, movement or contact routine replaced.
- 39 fleet-phase runs: the 22 fleet174 inputs replayed and 17 derived cases. **No instruction in any of them writes a route
  word.**
- A scan of 8,872 distinct original saves.
- No new gameplay.

**Task:** research [#131](https://github.com/diegoami/imperial-conquest-2-research/issues/131) (remake #1405, #1409), parts
1 and 2. Part 3 (E1FC's waypoint choice and target replacement) is covered here only for arrival; the D174 and 939c internals
follow in a second delivery.
**Background (promoted, not repeated):**
- `2026-10-24-strategic-fleet-controls174.md` and `2026-10-24-fleet-accepted-movement174.md`: first destinations,
  stored A/B, the 100/101 threshold, accepted moves, stored route with zero moves.
- `2026-10-30-ai-fleet-moves-in-play1409.md`: direct line, sea waypoint, the no-progress swing.
- `2026-10-21-original-sav-semantic-atlas.md`: route writers and the reset at 0x451723.

## 1. The route fields and their lifetime

**Fields.** Fleet +4 `route_x` and +6 `route_y` are signed words, stored and read as one dword (x | y<<16).
- **A route is present exactly when `route_x ≥ 0`.** F608 tests the signed word (`cmp word [esi+4], -1; jle`, 0x44F65B), so
  every negative x means absent.
- **`route_y` is read only together with a present x,** as the high word of E1FC's target.

**Writers.** These are all of them: the atlas's machine-code index plus the two out-pointer sites.

| Writer | When | Value |
|---|---|---|
| `FUN_0044d9a8` rendezvous, through `FUN_0044cd08` (0x44DA5A) | An AI army's walk (`FUN_0044db38`) needs a ferry. It takes the nearest own fleet that is launched, empty and has moves (strict `<`, so the first in table order wins a tie). | The first sea tile on the line from the army toward that fleet (#187: (101,40)). **No write** when that fleet is already at distance 1: the army embarks instead (`FUN_0044b79c`). |
| `FUN_0044dba8`, army aboard (0x44DBE1) | An AI army that is aboard is given a target. | The carrying fleet's route = the last tile of the target's class on the line from the target to the fleet, i.e. **the landing cell** (#187: (160,62)). The army pays 2 moves. |
| `FUN_0044cd08` itself | Its line walk ends at once. | x = −1 with stack residue in y (atlas). |
| Round tick `FUN_004514ec` (0x451723) | Once per round, after the 16th seat (0x44FA98; the human path 0x45B139). | For every fleet whose owner is ≥ 0: **x = −1, y untouched**. This is the tick's first action on each fleet, so a fleet launched in that tick starts with x = −1. |
| Load, compaction `FUN_0044ad7c`, the fleet-to-fleet dialog | — | Whole-record copies: the route moves with its record. Fleet order `FUN_0044a004` and split `0x447C04` do not set it, so a new record keeps the slot's old bytes (the (0;0) residue). |

**Reader:** only `FUN_0044f608`. The other readers in the index are the saver, compaction and the dialog's record copy.

**Nothing in the fleet phase writes it.** 39 phase runs log every write to any fleet's +4..+7: 0 writes. That covers:
- arrival on a sea route;
- landing an army (`FUN_0044b840` from E1FC at 0x44E38C; the army is put ashore and the fleet's cargo is set to −1);
- docking at an own port (`FUN_0044f7e4` from 0x44E3CE);
- a route on land with no cargo;
- an inland route;
- zero moves;
- the fleet already on its route cell;
- a stop before naval combat.

So the route is **not cleared on arrival, landing, docking, failure or zero moves.**

**Lifetime (state machine):**

```
round tick:     route_x := -1 (every fleet whose owner >= 0)              -> ABSENT
seat N, its army phase (EFC8, then the F31C army loop):
  D9A8 / DBA8 for an own fleet:    route := (x,y) via CD08               -> PRESENT (last writer wins)
seat N, its fleet phase F608, each own launched fleet in table order:
  PRESENT -> E1FC(fleet, route), whatever the moves          (route unchanged)
  ABSENT  -> the hunt / port selection below                 (route unchanged)
seats N+1 .. 15, a human seat and any save in between:       route unchanged, never read
round tick:     route_x := -1                                             -> ABSENT
```

A route is read by exactly one fleet phase: its own nation's phase, in the seat that wrote it. **A route found in a save is
never read.**
- The save is written at a human seat, after that AI seat and before the tick.
- After a load, play resumes at that human seat, so the tick clears x before that nation's next fleet phase.

**In saves.** `runs/experiments/fleetroute131/scan.py` over every distinct original save on this machine:
- 8,872 parsed saves, 44,113 live fleets.
- **558 hold x ≥ 0.** Of the 200 kept as examples:
  - 89 are AI routes from real play, e.g. Carthage's fleet 0 at (74,71) with route (86,76) in several new-game autosaves, and
    nation 3's fleet 1 in `run-exp-ai-intercept-hunt` `hook_s14_AUTO0751.SAV`…`0756`;
  - 111 are (0;0) residues of new or split fleets.
- Under x = −1, y is 0 in 42,092 fleets and leftover elsewhere (55, 76, 46 …).

**For a native model:**
- Keep the route only for the current seat: the army phase writes it, the fleet phase reads it.
- Import, save, load and export can carry +4/+6 as opaque bytes for a byte-faithful round trip. No value read from a save is
  gameplay state, the active-looking x ≥ 0 routes included.

## 2. The fleet phase `FUN_0044f608`: order and selection

For each fleet in table order (0..count−1), only those with owner = the current nation and countdown = −1 (launched). The
fleet-phase flag `DAT_004a0340 = 1` is set once at entry.

1. **Prepass `FUN_0044e5dc`**, always, even with zero moves. For each city in table order within distance < 4 of the fleet:
   - own city: `FUN_0044f7e4(city, fleet)` (supply / repair);
   - foreign city not at war (relation < 3) with supplies > 0: the same, but only while the fleet's money **as read at
     entry** is > 0.
2. **Port pick `FUN_0044e9a8`**, always. It writes the port index (−1 = none).
   - **A port** (`FUN_0044e920`) is a city with a sea cell (map code < 2) in its 3×3, unless `FUN_004496bc` excludes its
     position: x > 247, or x > 213 and y > 98 (the eastern corner).
   - **Pass 1** over the cities, keeping the nearest with a strict `<` (so the first city wins a tie), starting from 1000.
     - An own port with supplies > 20, or any city not at war with supplies > 120 while the fleet's money > 10, is a
       candidate.
     - A foreign port's distance gets +50.
     - An own port at distance 1 while the fleet has supplies > 0 counts as distance −1.
   - **Pass 2** (own ports only, nearest, starting again from 1000) runs when pass 1 found none, or when it found a foreign
     port. The test is "the kept distance > 30", and a foreign port's kept distance already includes +50, so it always
     passes. Pass 2 does not reset the index, so a pass-1 foreign port survives only when no own port is nearer than 1000.
   - **The port test reads map codes:** a fleet standing on a city's only sea neighbour makes that city fail it (control
     `hunt-protected`: port 25 instead of 30).
3. **Stored route:** if route_x ≥ 0, `E1FC(fleet, route)` (0x44F667), **with any moves, 0 included.** No hunt, no draw, no
   port.
4. **Otherwise, if moves > 0, the hunt `FUN_0044f4f8`:**
   - **Actor strength:** `AA54(fleet) = ships·condition/10 + (cargo army strength/50) + Random(4)·(that/10)`, one draw.
   - **Targets,** in table order. A target needs owner ≥ 0, war (relation 3), countdown = −1, and must not be protected.
     - **Protected:** `FUN_004494e4(owner, position) ≠ −1`, i.e. a map city cell coded for the target's owner
       ((code − 20) mod 16 = owner) lies in the 3×3 around the target.
     - Each eligible target costs one strength draw. Draws = 1 + eligible targets.
   - **Score** = `actor·100/target − d`, ×2 when target < actor and d < 18 (32-bit), with d the distance word.
   - **Strict `>`** against the sign-extended stored word, so the first in table order wins a tie.
   - **Then the same word store and final word add as the #130 scorers:** start −10000, `add word score, d` (0x44F5FB).
   - If the score word is **> 100**, `E1FC(fleet, target position)` (0x44F69A).
5. **Else,** if a port was picked, `E1FC(fleet, port position)` (0x44F6BE).
6. **With moves ≤ 0 and no route:** no hunt and no move. The prepass and port pick have already run.

**Controls** (`runs/experiments/fleetroute131/phase.py`, `phase-v2.json`). The scores are the hunt's returned words.

| Case | Input | First E1FC site, goal | Draws | Hunt (score, target) | Port | Result |
|---|---|---|---:|---|---|---|
| stored route, moves 25 (`phase-stored-a`) | route (48,66) | stored, (48,66) | 0 | — | 25 | at (48,66), 21 moves |
| stored route, moves 0 (`route-zero-moves`) | route (48,66) | stored, (48,66) | 0 | — | 25 | no move, 0 |
| route x = −2 (`route-x-minus2`) | (−2,66) | port, (45,68) | 1 | −10000 | 25 | absent: port |
| route x = −1, y = 66 left over | (−1,66) | port, (45,68) | 1 | −10000 | 25 | absent: port |
| route (0,0), the split residue (diagnostic) | (0,0) | stored, (0,0) | 0 | — | 25 | steers to (0,0) |
| no route, moves 0 (`no-route-zero-moves`) | — | none | 0 | — | 25 | no move |
| hunt 100 / 101 (fleet174) | — | port / hunt | 2 / 2 | 100 / 101 | 25 | strict > 100 |
| **hunt tie, table order A** (`hunt-tie-a`) | targets 1 (52,62), 2 (49,65); strength 2, d 3 | hunt, **(52,62)** | 3 | 997, 1 | 30 | first wins |
| **hunt tie, swapped** (`hunt-tie-b`) | targets 1 (49,65), 2 (52,62) | hunt, **(49,65)** | 3 | 997, 1 | 30 | first wins |
| **protected** (`hunt-protected`) | target (48,64) beside a map city coded for its owner (47,63) | port, (45,68) | **1** | −10000 | 25 | not drawn, not hunted |
| **unprotected at 2** (`hunt-unprotected-2`) | target (49,65), 2 from that city cell | hunt, (49,65) | 2 | 997, 1 | 30 | hunted |
| own port, adjacent (`adjacent-own-port`) | fleet (48,64), route = own city 30 (47,63) | stored | 0 | — | 25 | no-progress swing, then `FUN_0044f7e4` from E1FC (0x44E3CE); 18 moves left |
| landing, adjacent (`adjacent-landing-cargo`) | fleet (48,64) with army 3, route (47,64) land | stored | 0 | — | 25 | swing, then `FUN_0044b840` (0x44E38C): army ashore at (47,64), fleet cargo −1, moves 0 |
| fleet already on its route (`route-reached`) | fleet at (48,66) = route | stored | 0 | — | 25 | sails 12 cells to (39,78) and back: **25 → 1 moves** |
| land route across the coast (`route-landing-cargo`, `route-own-port`, `route-inland`) | route (47,64) / (47,63) / (41,57) | stored | 0 | — | 25 | goes east to (74,69), 0 moves left (via `FUN_0044939c`, `FUN_0044d174`; part 3) |

In the hunt controls, 997 = (10·100/2 − 3)·2 + 3. The actor's condition is repaired to 100 by the prepass at its own nearby
city, so its strength is 10. Each target is 1 ship at condition 20, strength 2 (2/10 = 0, so its draw adds nothing).

**Natural "fleet on its route" states exist.** Several saves hold a fleet standing on its own route cell with moves left,
e.g. `run-exp-ai-turn` `AUTO0722.SAV` fleet 0 at (58,78), route (58,78), 23 moves. These are fleets that arrived during their
seat; the case above is a fleet that **starts** its phase on the cell, which a rewritten rendezvous route can produce.

## 3. Arrival (from E1FC's disassembly, 0x44E302–0x44E410)

After the walk, if the distance to the **original** target is exactly 1 and moves > 0, the branch is chosen by the map code
of the original target cell. It was read at entry (0x44E221), before any replacement.
- **< 2 (sea):** walk onto it when its terrain cost < moves.
- **2–11 (land):** `FUN_0044b840` landing, if the fleet carries an army (+0x16 > −1).
- **20–99 (city):** `FUN_0044f7e4` when the nation is **not** at war with the city's owner; nothing at war.
- **300–347 (fleet):** `FUN_0044b5d0` naval combat when the target fleet's owner is at war with the fleet's owner and moves
  > 0.
- **200–247 (army) and every other code:** nothing.

The no-progress swing costs 1 move even when CEC8 finds no cell (the `dec` at 0x44E2CE is reached either way). Recursion
needs distance > 1, moves > 0, the point's x ≥ 0 and the target's x ≥ 0.

## What this does not establish

- **D174's waypoint choice and `FUN_0044939c`'s replacement** for land targets: why the land-route cases go east to (74,69).
  This is part 3's second delivery.
- **Naval-combat outcomes:** runs stop at `FUN_0044b5d0`.
- **Full-seat or global RNG parity:** only the draws inside the fleet phase are counted.
- **Human fleets:** they never run F608. Their routes stay residue until the tick.
- **Compaction during the phase** (a fleet sunk mid-phase moving the last record into its slot) was not staged.

## Evidence

- Scripts: `runs/experiments/fleetroute131/phase.py` (inputs: the private fleet174 `inputs-v1/<case>/input.ram`; derived
  cases declared in the script) and `scan.py`.
- Data: `runs/experiments/data/run-exp-fleetroute131/phase-v1.json` (35 cases), `phase-v2.json` (39 cases, adds the hunt
  rows and the hunt and port outputs), `scan-v1-public.json` (redacted: the full scan, with per-save names and hash prefixes, includes owner-derived material and is kept privately in `artifacts/run-exp-fleetroute131/private/scan-v1.json`; its hash is in `PRIVATE.sha256`).
- Disassembly: F608 0x44F608–0x44F6D6, E9A8 0x44E9A8–0x44EB17, E5DC 0x44E5DC–0x44E66D, F4F8 0x44F4F8–0x44F604, 4494E4,
  E1FC 0x44E1FC–0x44E41B, D9A8 / DBA8 0x44D9A8–0x44DBFC, tick 0x451716–0x451962. Atlas index:
  `runs/experiments/data/run-exp-sav-atlas107/asm-index-v2.csv` (FLEET.route_x / route_y).
- Writers in emulation: research #187 `runs/experiments/data/run-exp-navigation187/branch-controls-v1.json` (`ferry-*`,
  `already-aboard`).
