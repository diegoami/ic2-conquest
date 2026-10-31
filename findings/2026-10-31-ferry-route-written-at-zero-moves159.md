# The original writes the ferry route for an army with 0 moves: no army-moves gate from the mercenary-run continuation to the route write

**Tag:** [confirmed: code and Wine hook]. Seed build, played in Wine; no Windows run.
**Task:** research [#159](https://github.com/diegoami/imperial-conquest-2-research/issues/159) (remake #1652, the zero-move
case left open by remake #1657). Owner request 2026-10-31.
**Background:** `2026-10-31-fleet0-rows-attributed174.md` (the continuation walk's ferry request). Its "whatever the army's
moves" was a reading, supported but not proven. This finding measures it.

## Answer

- **Measured:** in 7 route writes, the army had **0 moves at the write**. Each came from `F31C`'s continuation after the
  mercenary run:
  - S06 rounds 2, 3 and 4;
  - S13 rounds 1, 3, 4 and 5.
- **The code has no army-moves test** anywhere on the path, from the continuation to the write. The only moves
  condition on it is on the **fleet** (`+0xC > 0`).
- **For the remake** (classical-faithful): the continuation's ferry request must not stop at zero army moves. With 0
  moves, the walk itself moves nothing, but the rendezvous route is still written and the fleet sails on it in its fleet
  phase.

## The path, statically (pinned seed build)

| Step | Instructions | Reads army moves? |
|---|---|---|
| `F31C` after `call FUN_0044e84c` (0x44F485) | army score `[esp+6] > 0x46` → `call DBA8(army, army target)` (0x44F4A3); else city score `[esp+8] > 0x55` → `call DBA8(army, city)` (0x44F4C7) | **no** |
| `DBA8` before `DB38` | 0x44DBC5 `si := [ebx+6]` (moves, kept); 0x44DBC9 aboard test `+8`; 0x44DC06 `CB40(position, target)` (direct line); not direct → 0x44DC26 `call DB38` | **no**: the moves are compared only after `DB38` returns (0x44DC43) |
| `DB38` | locals: the army's point `[ebp-4]`, the target `[ebp-8]`, the class results of `FUN_0044da88` for both (`[ebp-0x10..-9]`), the out pointer `ebx`; different classes → 0x44DB8B `call D9A8` | **no** |
| `D9A8` | the nearest own fleet with owner `+8` = nation, `+0x16 == -1`, `+0xA == -1` and **fleet moves `+0xC > 0`** (strict `<` distance); at distance 1 → embark (`FUN_0044b79c`); else 0x44DA6F `call CD08` → route at fleet `+4` | **no**: its gates are on the fleet only |

Call sites (an `E8 rel32` scan of `.text`):
- `DB38` has one caller (0x44DC26, in `DBA8`), and `D9A8` has one caller (0x44DB8B, in `DB38`). So at the write,
  `D9A8`'s `[ebp+8]` is always `DBA8`'s frame, and `DBA8`'s `[ebp-2]` holds the army.
- `DBA8` has 11 callers, named in the hook's decoder.

## Measured (observation-only hook)

- **Hook:** `patches/routemoves_hook.py`:
  - `DBA8` entry (0x44DBA8): the army, the target, the caller, and the army's moves;
  - the route write (0x44DA74, after `D9A8`'s `CD08`): the fleet, the route, the army from `DBA8`'s frame, and **the
    army's moves at the write**;
  - the fleet phase's two probes.
- **Runs:** S06, S08 and S13 (the starts with the continuation rows), 5 End turns each, seed 12345. The hooked autosaves
  are **byte-identical to the plain build in 15 of 15 turns**.

**S06 round 4, Carthage army 3** (research #159's case), in order:

| seq | Record | Army moves |
|---|---|---|
| 86 | `DBA8` from `E84C`'s run, toward the offer at (67,79) | 9 |
| 87 | `DBA8` re-entering itself (same target) | 5 |
| 88 | `DBA8` from `F31C`'s continuation (city > 85), toward the city at (121,53) | **0** |
| 89 | **route write**: fleet 0, route (85,78), army 3 | **0** |
| 90 | the fleet phase: fleet 0 at (85,78), stored route (85,78), 26 moves → stored-route | |

**All route writes in the three starts:**

| Start | Round | Caller of the writing `DBA8` | Army moves at the write |
|---|---|---|---|
| S06 | 2 | `E84C` run | 9 |
| S06 | 2, 3, 4 | continuation, city > 85 | **0** |
| S06 | 5 | `F31C` city > 100 | 9 |
| S08 | 1 | continuation, army > 70 | 9 |
| S08 | 2, 3 | continuation, city > 85 | 9 |
| S13 | 1, 3 | `E84C` run | 8, 9 |
| S13 | 1 | continuation, army > 70 | **0** |
| S13 | 3, 4, 5 | continuation, city > 85 | **0** |

- In every zero-move write, the army's moves were already 0 at the continuation's `DBA8` entry: `E84C`'s run had spent
  them.
- **The army does not move after such a write.** Its position stays on the run's last tile, as the earlier finding's saves
  show. Only the fleet's route changes.

## What this does not establish

- **No crafted sweep** with fleet eligibility and destination held fixed: the in-play writes answer the question, and
  the code has no army-moves read on the path.
- **The embark branch** (fleet at distance 1, `FUN_0044b79c`) with 0 moves: not exercised here.
- **Windows:** the claim is about the seed build in Wine.
- **Rounds 6+, other seeds.**

## Evidence

- Data: `runs/experiments/data/run-exp-routemoves159/`:
  - `orig-v1/<start>-routemoves.jsonl`;
  - `orig-v1/<start>/inert.json`;
  - `README.md`.
- Release `run-exp-routemoves159` (`routemoves159-saves.tar.xz`; hashes in `SAVES.sha256`).
- Saves cited: starts `S06_Gaul_AUTO0720.SAV`, `S08_Celtiberia_AUTO0720.SAV`, `S13_armenia_AUTO0720.SAV`, and their
  `hooked-tNN-*.SAV` (S06 round 4 = `hooked-t03-AUTO0723.SAV` → `hooked-t04-AUTO0724.SAV`).
- Code:
  - `patches/routemoves_hook.py`;
  - `difftest/probes/fleetphase_hook_run.py` (`IC2_FLEET_HOOK=routemoves_hook IC2_HOOK_LOG=routemoves`).
