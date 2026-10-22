#!/usr/bin/env python3
"""Machine-move smoke test (2026-10-10, new computer: Ubuntu 26.04, Wine 10.0).

    python3 runs/experiments/data/run-exp-machine-move/smoke.py [--fixtures]

Loads saves/run0-start-AUTO0720-seed12345.SAV with seed 12345 through harness.driver.Game (one retry if the
first start misses the 40 s main-window wait), screenshots it, then with --fixtures opens every T_*.SAV in the
game folder in the same process and records whether each loaded and which boxes it raised. Writes smoke.jsonl
beside this script (appends; rule 6) and screenshots to artifacts/run-exp-machine-move/."""
import json, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from harness.driver import Game, G, DriverError  # noqa: E402

OUT = Path(__file__).with_name("smoke.jsonl")
ART = REPO / "artifacts" / "run-exp-machine-move"


def rec(**kw):
    kw["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(OUT, "a") as f:
        f.write(json.dumps(kw) + "\n")
    print(json.dumps(kw), flush=True)


from harness import environment as _env  # noqa: E402  every start records the Wine/font environment in smoke.jsonl
_env.add_sink(lambda r: rec(**{k: v for k, v in r.items() if k != "at"}))
g = Game()
save = REPO / "saves" / "run0-start-AUTO0720-seed12345.SAV"
for attempt in (1, 2):
    t0 = time.time()
    try:
        texts = g.load(save, seed=12345)
        rec(step="load", attempt=attempt, ok=g.loaded(), secs=round(time.time() - t0, 1), seed_line=g.seed_line, texts=texts,
            pid=g.pid)
        break
    except DriverError as e:
        rec(step="load", attempt=attempt, ok=False, secs=round(time.time() - t0, 1), error=str(e))
        if attempt == 2:
            g.kill()
            sys.exit(1)
ART.mkdir(parents=True, exist_ok=True)
g.shot(ART / "smoke-run0-AUTO0720.png")
rec(step="shot", file="smoke-run0-AUTO0720.png", windows=[w[1:] for w in g.find_windows()])
if "--fixtures" in sys.argv:
    for p in sorted(G.glob("T_*.SAV")):
        t0 = time.time()
        try:
            texts = g.open(p, strict=False)
            rec(step="fixture", save=p.name, ok=g.loaded(), secs=round(time.time() - t0, 1), texts=texts)
        except DriverError as e:
            rec(step="fixture", save=p.name, ok=False, secs=round(time.time() - t0, 1), error=str(e))
g.kill()
rec(step="killed")
