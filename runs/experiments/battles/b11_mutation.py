#!/usr/bin/env python3
"""B11 mutation check of the exchange replay: does it notice a wrong constant? The replay is run on real hooked battles with one constant of the report's formulas changed at a time,
and the number of exchanges it still reproduces is compared with the unmutated run. A check that stays green when a constant is wrong would prove nothing.

    python3 runs/experiments/battles/b11_mutation.py [TRIAL ...]      # default: mix-rg_s1_r3_hook mix-rg_s3_r3_hook ar-ar-three_s1_r1_hook ...; writes b11-mutation-<stamp>.json (tracked)
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402
import b11_exchange as X  # noqa: E402

C = B.C
MUTATIONS = [
    ("none", lambda: None, lambda: None),
    ("M[hi][hi] 5 -> 6", lambda: X.M["hi"].__setitem__(1, 6), lambda: X.M["hi"].__setitem__(1, 5)),
    ("M[li][li] 15 -> 16", lambda: X.M["li"].__setitem__(0, 16), lambda: X.M["li"].__setitem__(0, 15)),
    ("M[hc][li] 18 -> 17", lambda: X.M["hc"].__setitem__(0, 17), lambda: X.M["hc"].__setitem__(0, 18)),
    ("vuln[li] 18 -> 17", lambda: X.VULN.__setitem__("li", 17), lambda: X.VULN.__setitem__("li", 18)),
    ("vuln[ar] 18 -> 19", lambda: X.VULN.__setitem__("ar", 19), lambda: X.VULN.__setitem__("ar", 18)),
    ("rout floor hi 240 -> 100", lambda: X.FLOOR.__setitem__("hi", 100), lambda: X.FLOOR.__setitem__("hi", 240)),
    ("rout floor li 600 -> 700", lambda: X.FLOOR.__setitem__("li", 700), lambda: X.FLOOR.__setitem__("li", 600)),
]


def run(blocks, recs):
    rows, summ = X.reconstruct(blocks, recs)
    out = X.summarize(rows, summ)
    return {k: out[k] for k in ("shots", "shots_n_ok", "melee", "melee_n_ok", "rout_tests", "rout_draw_count_ok", "state_diffs", "misses")}


def main():
    tags = sys.argv[1:] or ["mix-rg_s1_r3_hook", "mix-rg_s3_r3_hook", "ar-hc-three_s3_r1_hook", "hc-hc-three_s1_r1_hook"]
    res = {}
    for tag in tags:
        if not list(C.ART.glob("%s_BATTLE01.SAV" % tag)):
            continue
        blocks, _ = X.load_series(C.ART, tag)
        recs = X.load_log(C.DATA / ("hooklog-%s.csv" % tag))
        res[tag] = {}
        for name, apply, undo in MUTATIONS:
            apply()
            try:
                res[tag][name] = run(blocks, recs)
            finally:
                undo()
    p = C.write_new(C.DATA, "b11-mutation-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(res, indent=1))
    print(p.name)
    for tag, d in res.items():
        for name, r in d.items():
            print("%-24s %-26s shots_ok %d/%d melee_ok %d/%d rout_ok %d/%d state_diffs %d misses %d" % (tag, name, r["shots_n_ok"], r["shots"], r["melee_n_ok"], r["melee"],
                                                                                              r["rout_draw_count_ok"], r["rout_tests"], r["state_diffs"], r["misses"]))


if __name__ == "__main__":
    main()
