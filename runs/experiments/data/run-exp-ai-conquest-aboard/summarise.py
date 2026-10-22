"""Summary of the idle-watch logs: per seed the end turns made, how it ended, the conquests, and every loaded launched fleet seen
(owner, carried army's owner, turns). python3 summarise.py > idle_summary.json"""
import json, glob, collections
from pathlib import Path
D = Path(__file__).parent
out = {}
for f in sorted(D.glob("idle_watch_seed*.jsonl"), key=lambda p: int(p.stem.split("seed")[1])):
    recs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    turns = [r for r in recs if "turn" in r]
    end = next((("game_over", r["game_over"][:90]) for r in recs if "game_over" in r), None) or \
          next((("stuck", r["error"]) for r in recs if "error" in r), None) or ("budget/stopped", None)
    loaded = collections.defaultdict(list)
    for r in turns:
        for lf in r["loaded_fleets"]:
            loaded[(lf["owner"], lf["army_owner"])].append(r["turn"])
    out[f.stem] = {"end_turns": len(turns), "last_turn": turns[-1]["turn"] if turns else None, "ended": end,
                   "conquests": [(r["turn"], c) for r in turns for c in r["new_conquests"]],
                   "loaded_fleets": {f"fleet owner {k[0]}, army owner {k[1]}": [min(v), max(v), len(v)] for k, v in loaded.items()}}
print(json.dumps(out, indent=1))
