#!/usr/bin/env python3
"""#195 D09: fleets launched during an anchored turn's AI phase (under construction before, launched after, in the
original). For each: the original's leftover moves before launch, and the end tile and moves in the original and in the
remake (same record index, mapped through the remake's own export). Read-only.

    python3 runs/experiments/audit195/d09_launch_moves.py <anchored folder> <campaign dir> [...] > out.jsonl
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def main():
    folder, camps = sys.argv[1], sys.argv[2:]
    for c in map(Path, camps):
        orig = c / "original"
        for rdir in sorted((c / folder).glob("t[0-9][0-9]")):
            t = int(rdir.name[1:])
            ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
            rends = sorted(rdir.glob("a*.SAV"))
            if not ends or not rends:
                continue
            pre_f = ends[-2] if len(ends) > 1 else (orig / "t00-start.SAV" if t == 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1])
            pre, end, rend = load(pre_f), load(ends[-1]), load(rends[-1])
            for k, f in enumerate(pre["fleets"]):
                if not (f["owner"] >= 0 and f.get("building")) or k >= len(end["fleets"]):
                    continue
                e = end["fleets"][k]
                if e.get("building") or e["owner"] != f["owner"] or e["ships"] <= 0:
                    continue
                r = next((x for x in rend["fleets"] if x["owner"] == f["owner"] and not x.get("building")
                          and x["ships"] == e["ships"] and x["id"] == k), None)
                rb = [x for x in rend["fleets"] if x["owner"] == f["owner"]]
                print(json.dumps({"camp": c.name, "turn": t, "fleet": k, "owner": f["owner"], "build_city": f["build_city"],
                                  "leftover_moves": f["moves"], "orig_end": [e["x"], e["y"], e["moves"]],
                                  "remake_end": [r["x"], r["y"], r["moves"]] if r else None,
                                  "remake_owner_fleets": [[x["id"], x["x"], x["y"], x["moves"], bool(x.get("building"))] for x in rb]}),
                      flush=True)


if __name__ == "__main__":
    main()
