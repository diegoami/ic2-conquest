#!/usr/bin/env python3
"""#195 C23: the state effect of the original's D734 resupply tail (F6D8 at the walk's end), which the remake lacks. For each
round of the D734 hook run, the remake plays the same round from the original's own round start (the plain/hooked autosave
of the previous round, or the civ-sweep start for round 1; seed 12345, Instant, the human gives no orders), and the
end-of-round supplies of every army that got a resupply tail in the original are compared with the remake's (same record
index and owner; rows whose index does not hold the same nation in the remake are skipped and counted).

    IC2_REMAKE=... IC2_DIFF_BUILD=... python3 runs/experiments/audit195/c23_supply_effect.py <hook out dir> <out dir> > rows.jsonl

Writes the remake runs under <out dir>/<start>-r<round>/ (never overwrites). Remake only.
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402

CS = Path("/home/diego/projects/ic2-conquest/artifacts/run-exp-civ-sweep")


def main():
    hook, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    remake, build = os.environ["IC2_REMAKE"], Path(os.environ["IC2_DIFF_BUILD"])
    adapter = build / "adapter/bin/RemakeAdapter/release/RemakeAdapter.dll"
    dotnet = Path.home() / ".dotnet/dotnet"
    for log in sorted(hook.glob("*-d734.jsonl")):
        start = log.name[: -len("-d734.jsonl")]
        recs = [json.loads(l) for l in log.read_text().splitlines()]
        # the round is the runner's "turn" tag (the End turn after which the record was read); the week ticks mid-round
        tails = defaultdict(set)
        for r in recs:
            if r["kind"] == "resupply":
                tails[r["turn"]].add(r["army"])
        hooked = sorted((hook / start).glob("hooked-t*.SAV"))
        for rnd, armies in sorted(tails.items()):
            src = CS / f"{start}.SAV" if rnd == 1 else hooked[rnd - 2]
            end = hooked[rnd - 1]
            d = out / f"{start}-r{rnd}"
            d.mkdir()
            (d / "commands.txt").write_text("#checkpoint a000\nend\n#checkpoint a001\n")
            with open(d / "receipt.jsonl", "w") as rec:
                p = subprocess.run([str(dotnet), str(adapter), remake, str(src), str(src), str(d / "commands.txt"), str(d),
                                    "seed=12345"], stdout=rec, stderr=subprocess.PIPE, text=True,
                                   env=dict(os.environ, DOTNET_ROOT=str(dotnet.parent)))
            (d / "stderr.txt").write_text(p.stderr)
            if p.returncode or not (d / "a001.SAV").exists():
                print(json.dumps({"start": start, "round": rnd, "error": p.returncode}), flush=True)
                continue
            o, m, s0 = load(end), load(d / "a001.SAV"), load(src)
            for a in sorted(armies):
                if a >= len(o["armies"]) or a >= len(m["armies"]) or o["armies"][a]["owner"] != m["armies"][a]["owner"]:
                    print(json.dumps({"start": start, "round": rnd, "army": a, "skipped": "index"}), flush=True)
                    continue
                print(json.dumps({"start": start, "round": rnd, "army": a, "owner": o["armies"][a]["owner"],
                                  "supplies_start": s0["armies"][a]["supplies"] if a < len(s0["armies"]) else None,
                                  "original": o["armies"][a]["supplies"], "remake": m["armies"][a]["supplies"],
                                  "orig_xy": [o["armies"][a]["x"], o["armies"][a]["y"]],
                                  "remake_xy": [m["armies"][a]["x"], m["armies"][a]["y"]]}), flush=True)


if __name__ == "__main__":
    main()
