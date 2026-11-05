#!/usr/bin/env python3
"""#195 X3: the replayed seat nation's unit tiles at the round's end, original (hook run's next save) against each remake
run of x3_seat_replay.py. Prints one JSON line per seat and run: the tiles only in the original / only in the remake
(armies and fleets, troops ignored, since the battle is resolved differently).

    python3 runs/experiments/audit195/x3_positions.py <x3 out dir> > positions.jsonl
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import NATIONS, load  # noqa: E402

AID = Path("/home/diego/projects/ic2-conquest/artifacts/run-exp-aidecide/orig-v1")
END = {"S01r5": AID / "S01_Carthage_AUTO0720/hooked-t05-AUTO0725.SAV", "S02r4": AID / "S02_Seleucid_AUTO0720/hooked-t04-AUTO0724.SAV",
       "S03r1": AID / "S03_Ptolemaic_AUTO0720/hooked-t01-AUTO0721.SAV", "S06r2": AID / "S06_Gaul_AUTO0720/hooked-t02-AUTO0722.SAV",
       "S08r2": AID / "S08_Celtiberia_AUTO0720/hooked-t02-AUTO0722.SAV"}


def tiles(s, o):
    return (Counter((a["x"], a["y"]) for a in s["armies"] if a["owner"] == o and a["troops"] > 0),
            Counter((f["x"], f["y"]) for f in s["fleets"] if f["owner"] == o and f["ships"] > 0 and not f.get("building")))


def main():
    out = Path(sys.argv[1])
    for l in (out / "passes.jsonl").read_text().splitlines():
        r = json.loads(l)
        o = [n.lower() for n in NATIONS].index(r["nation"])
        oa, of = tiles(load(END[r["seat"]]), o)
        ra, rf = tiles(load(out / f"{r['seat']}-{r['mode']}-s{r['seed']}" / "a001.SAV"), o)
        print(json.dumps({"seat": r["seat"], "mode": r["mode"], "seed": r["seed"],
                          "armies": {"only_original": sorted((oa - ra).elements()), "only_remake": sorted((ra - oa).elements())},
                          "fleets": {"only_original": sorted((of - rf).elements()), "only_remake": sorted((rf - of).elements())}}))


if __name__ == "__main__":
    main()
