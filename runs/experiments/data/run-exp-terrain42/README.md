# Terrain42 original-instruction controls

Owner-authorized main-session implementation; GLM5.3Flash review selected.
See findings/2026-10-21-strategic-lateral-steps-and-callers.md for conclusions
and the exact distinction between source, emulator and legacy Wine evidence.

original-controls-v1.json is an immutable11-step/2-walk result. The runner hash
and EXE/DAT/source-save hashes are embedded. No proprietary bytes are included.
The runner executes unchanged original code but intercepts two presentation
calls; do not call it unstubbed original gameplay or native Windows validation.

Reproduce with existing Unicorn and explicitly allowed private original inputs,
from repository root, choosing a NEW output name:

```sh
python3 runs/experiments/terrain42/original_steps.py --exe '/path/Imperial Conquest 2.exe' --dat '/path/Imperial Conquest 2.dat' --save saves/run0-start-AUTO0720-seed12345.SAV --output runs/experiments/data/run-exp-terrain42/original-controls-NEW.json
```

No Wine/game process is started, inputs are read only, and existing outputs are
refused. Independent reviewers without the private files must retain that
execution limit rather than claim to have reproduced the x86 results.
