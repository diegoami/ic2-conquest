import json, sys
from pathlib import Path
sys.path.insert(0, '.')
from difftest import actions as act, remake
from difftest.anchored import end_checkpoint
camp, k, out = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
seeds = [int(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else [12345 + k]
rows = {json.loads(l)["turn"]: json.loads(l) for l in (camp / "turns.jsonl").read_text().splitlines() if l.strip()}
orig = camp / "original"
start = orig / "t00-start.SAV" if k == 1 else end_checkpoint(orig, k - 1)
acts = [act.validate(x) for x in rows[k]["orders_original"]] + [{"op": "end_turn"}]
for s in seeds:
    d = out / f"s{s}"
    remake.run(acts, start, d, log=lambda *x: None, seed=s, options=("ailog",))
    print(d)
