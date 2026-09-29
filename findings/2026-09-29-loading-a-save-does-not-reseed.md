# Loading a save does not reseed the random generator; program start and New Game do

**Status:** draft finding from `ic2-conquest`, awaiting promotion. It corrects one sentence of `2026-09-28-battle-minigame-headless-feasibility.md` ("the load routine reseeds it from the clock (`0x448AB0` → `Randomize` `0x402744`)").

**Answer.**
- `System.Randomize` (`0x402744`, `RandSeed := clock`) has two call sites. `0x448AB0` is inside **`FUN_00448AA4`, New Game's leader and turn-order draw**, not inside the load routine. `FUN_00448AA4` is called from `TPremierForm_InitialiseForm` (`0x45A93A`, program start) and from `TPremierForm_NewGame` (`0x45AA32`). The other site, `0x456759`, sits in a handler with no direct caller and never fired in these runs.
- **File → Open does not reseed.** The load routine `FUN_004487C4` (called only from `OpenGameFile`, `0x45AB1F`) contains no call to `Randomize`.
- Two runs from one save diverge because each **process start** seeds from the clock, not because each load does. A turn is repeatable if the process is started with a fixed seed and the same save and orders follow.

## Method

- **Build:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), made by `patches/seed_patch.py`: `Randomize` is sent through a cave that takes `RandSeed` from `SEED.TXT` beside the exe (falling back to the clock when the file is missing), and appends one line per firing to `SEED.LOG`: `S <seed>` or `C <clock seed>`.
- **Runs** (Wine 9.0, Xvfb, xdotool; `harness/driver.py`), each from a fresh process:
  1. start the game, *File → Open* `BASE.SAV`, end the turn: `SEED.LOG` gains **one** line, written at program start, before the file dialog was opened (its timestamp precedes the load);
  2. start the game, *File → New*, Rome human: **two** lines, one at program start and one at New Game;
  3. a second *File → Open* in a running game: **no** line.
- **Code:** callers found by scanning for `E8 rel32` into `0x402744` and `0x448AA4`; disassembly with capstone.

## Observations

| Run | Seed | `AUTO0721.SAV` after one End turn from `BASE.SAV` |
|---|---|---|
| a | `SEED.TXT` = 12345 | sha256 `48857fdd…1a1e` |
| b | 12345 | `48857fdd…1a1e`, **byte-identical** to a |
| c | 999 | `5dc52eab…9816`, 592 bytes differ from a |
| d | clock (no `SEED.TXT`), `C 0068791596` | `ee4550c1…62eb`, 298 bytes differ from a |
| e | clock, `C 0068818818` | `61723814…a4bb`, 492 bytes differ from d |

A whole scripted turn (a move and a recruit, then End turn) repeated from the same save and seed also gives byte-identical autosaves (`tests/results.md`, `scripted_turn_repeats`), and so does a New Game (`NEW_a.SAV` = `NEW_b.SAV`).

## Inferences

- The seed patch needs no hook in the load routine. A harness that wants turn *N* to be repeatable restarts the game with the chosen seed, then opens the save: turn *N* = f(save, seed, orders).
- Two paint routines also write `RandSeed` from map coordinates (`0x450C7B`, `0x457907`). They are deterministic, and the byte-identical runs show that the UI's repaint order did not break repeatability here.

## What this does not establish

- That repeatability holds through a tactical battle fought with *Computer general* inside the AI phase (no battle occurred in these turns).
- Where `0x456759`'s handler is reached from.

## Reproduction

```text
setup/setup.sh
python3 -m tests.test_orders end_turn scripted_turn_repeats
```
