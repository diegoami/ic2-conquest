# run-exp-diff084-tactical: scripted battle commands in both games (#231, batch 1)

Runner: `python3 -m difftest.tactical` (module docstring: staging, commands, comparison). Cases:
`difftest/cases/tactical231.py`. Remake v0.8.4 (`d9cc71bc`); original `fast rollingsave seed.exe`, seed 12345;
remake battle draw stream 12345.

Each case stages one battle in `saves/fleet-split-antium-0734.SAV`: Rome's army 0 against army 13, handed to
Carthage. Both nations are human, so no computer general acts, and the block is synthetic (morale 70, movement
phase). Per case folder: `staged.SAV` (the original opens it), `strategic.SAV` + `block.bin` (the remake imports
them), `block.json`, `script.txt`, and one jsonl per game with the board after every command.

| Case | Commands | Exact fields (positions, moves, shots, targets, side to move) | Combat (troops, morale) |
|---|---|---|---|
| `walk-1` | each side walks two units and ends | **same** at every step | no combat |
| `shoot-li` | light infantry shoots at distance 2; both end | **same**: refused as out of range in both | no combat |
| `melee-target` | heavy infantry targets the adjacent enemy; both end | **same** | differs, from the random draws (seed 12345: original 2,811 / 2,750 troops left, remake 2,932 / 2,876); compared over seeds in `run-exp-diff084-tactical-stats` |
