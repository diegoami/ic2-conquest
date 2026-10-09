"""Reproduce the end-turn timeout of run-exp-ai-conquest-aboard seed 2 (end 29, after 0748): the same start and seed, End turn
until it sticks; then dump the windows (with their controls) and a screenshot and leave the game running for inspection.
python3 repro.py SEED MAX_ENDS [TIMEOUT]"""
import json, sys
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest")
sys.path.insert(0, str(R))
from harness.driver import G, Game
ART = R / "artifacts/run-exp-end-turn-timeout"; DATA = R / "runs/experiments/data/run-exp-end-turn-timeout"
seed, n = int(sys.argv[1]), int(sys.argv[2]); to = int(sys.argv[3]) if len(sys.argv) > 3 else 120
g = Game(); g.load(R / "saves/run0-start-AUTO0720-seed12345.SAV", seed=seed)
log = DATA / f"repro_seed{seed}.jsonl"
for i in range(n):
    try:
        name, texts = g.end_turn(timeout=to)
        with log.open("a") as fh:
            fh.write(json.dumps({"end": i + 1, "autosave": name, "popups": texts}) + "\n")
        print(i + 1, name, texts, flush=True)
    except Exception as e:
        wins = g.find_windows(".", tooltips=True)
        ctl = {}
        for w in wins:
            try:
                ctl[str(w)] = g.controls(w[1])
            except Exception as ce:
                ctl[str(w)] = repr(ce)
        g.shot(ART / f"stuck_seed{seed}_end{i + 1}.png")
        rec = {"end": i + 1, "error": repr(e), "windows": wins, "controls": ctl}
        with log.open("a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        print("STUCK", json.dumps(rec, default=str), flush=True)
        break
