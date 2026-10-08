# Siege: attrition can remove a small attacking army, and its tile gets its terrain back

**Status:** a draft from `ic2-conquest`, awaiting promotion. It covers the siege path left open in `2026-10-08-removed-army-restores-its-tile.md` (research `6be3778`).

**Tag:** `[confirmed]` for the observations. `[derived]` for the code path behind them (`FUN_0044ae20` is not in our extracts).

## Answer

- **A siege removes nothing directly.** `FUN_0044b27c` (:49786-49838) applies attrition to the attacker through `FUN_0044ae20(army, pct)`, with pct = clamp(defence × 6 / attack, 1, 15) (:49810-49814). A capture (`FUN_0044bb18`) only changes the city's owner and the nations' figures. So an attacking army can vanish only if attrition empties it.
- **Attrition does empty small armies, and the tile is restored.**
  - The setup: Rome's army 0 at (99,32) next to Felsina (Gaul, at war), with a single unit of 99, 100 or 150 men. Its covered cell was patched from the real forest (4) to **5**.
  - The result: the siege removed the army (owner −1, no units), and the tile read **5** afterwards, in the save and in memory. That is the covered cell put back, not 0 and not the real terrain.
  - The attempt was a siege in each case: Felsina's fortification went 65 → 62, and the news says "Rome fails to capture Felsina (Gaul).".
- **Attrition drops whole small units.** An army of units with 1, 6, 7, 13, 100 and 1,000 men lost every unit except the 1,000-man one, which fell to 880 (−12%). The army survived and its tile kept its marker. The size below which a unit is dropped lies between 151 and 999 men (`[derived]`; the rule is in `FUN_0044ae20`, not extracted).
- **A one-man army did not besiege at all.** After the click its moves stayed 8 and Felsina was unchanged. The cause is not known; one possibility is an attack strength of 0 (`FUN_0044a930`) refused before the siege runs.

| Case | Army 0 units before | After the click | Tile (99,32) before → after |
|---|---|---|---|
| one_man | 1 | **no siege** (moves 8, Felsina unchanged) | 200 → 200 |
| spread | 1, 6, 7, 13, 100, 1,000 | siege; only the 1,000 unit is left, at 880 | 200 → 200 |
| u99 | 99 | siege; **army removed** | 200 → **5** |
| u100 | 100 | siege; **army removed** | 200 → **5** |
| u150 | 150 | siege; **army removed** | 200 → **5** |

So every army-removal path run so far restores the covered cell: disband, join, tactical battle loss (`6be3778`) and siege attrition. Research's code reading adds the last-unit loss, through `FUN_0044ac3c` → `FUN_0044ab90`. AI turn-end removals remain untested.

Evidence: run-exp-siege-army-removal, `<case>_{PRE,BEFORE,AFTER}.SAV` for one_man, spread, u99, u100 and u150 (release `run-exp-siege-army-removal`; SHA-256 in `runs/experiments/data/run-exp-siege-army-removal/SAVES.sha256`); `probe_siege.py`, `probe_siege.log`, `probe_siege_*.json`.

## Method

The fixture is `saves/siege-felsina-failed-0721.SAV`: Rome army 0 at (99,32), its real covered cell 4. The patch sets moves 8, covered cell 5, and replaces the units with regular heavy infantry of quality 7 and the listed sizes. Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save `BEFORE`, `g.attack(0, 98, 31)`, save `AFTER`; then read army 0, the map word at (99,32), `Game.cell(99, 32)` and Felsina.

## Not established

- `FUN_0044ae20`'s rule: the unit-size threshold, and how the percentage is applied.
- Why a one-man army does not besiege.
- AI turn-end removals.
