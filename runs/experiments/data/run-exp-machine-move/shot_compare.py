#!/usr/bin/env python3
"""Machine-move check 2 (2026-10-10): load the research start save 1_rome_270_winter_11.sav with seed 12345 (as
run-exp-battle-probe b0-normal-20261004-081149 did on the old computer), screenshot right after load, and record the
windows. The pixel comparison with the old b0-normal-20261004-081149-01-loaded.png is done by compare.sh. Appends
to shot_compare.jsonl (rule 6)."""
import json, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from harness.driver import Game, G  # noqa: E402
ART = REPO / "artifacts" / "run-exp-machine-move"
tag = time.strftime("%Y%m%d-%H%M%S")
g = Game()
t0 = time.time()
texts = g.load(G / "1_rome_270_winter_11.sav", seed=12345)
png = ART / f"shot-winter11-{tag}.png"
g.shot(png)
import os, subprocess
rec = {"at": tag, "ic2_work": os.environ.get("IC2_WORK", "~/ic2-work"), "wine": subprocess.run(["/usr/lib/wine/wine", "--version"], capture_output=True, text=True).stdout.strip(),
       "fc_liberation": subprocess.run("fc-list | grep -ci liberation", shell=True, capture_output=True, text=True).stdout.strip(), "secs": round(time.time() - t0, 1), "texts": texts, "seed_line": g.seed_line, "file": png.name,
       "windows": [w[1:] for w in g.find_windows()]}
g.kill()
with open(Path(__file__).with_name("shot_compare.jsonl"), "a") as f:
    f.write(json.dumps(rec) + "\n")
print(json.dumps(rec))
