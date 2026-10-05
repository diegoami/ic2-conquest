#!/usr/bin/env python3
"""B11 aggregates quoted by the finding: from the newest `exchange-check-<trial>.json` of every B5 re-run battle (hooked rep 1; the stand-in `hi-hi-one_s1_r2_hook` for the
first hooked trial, which ran on an earlier build), the copy-in morale base per side, the post-battle draws, the rout tests that drew, the half-round and record counts.

    python3 runs/experiments/battles/b11_aggregate.py          # writes b11-aggregates-<stamp>.json (tracked, never overwritten)
"""
import collections
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402

C = B.C


def newest(tag):
    fs = sorted(C.DATA.glob("exchange-check-%s*.json" % tag), key=lambda p: p.stat().st_mtime)
    return json.loads(fs[-1].read_text()) if fs else None


def main():
    rep = int(sys.argv[sys.argv.index("--rep") + 1]) if "--rep" in sys.argv else 1
    tags = []
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "ok" and r.get("variant") == "hook" and r.get("rep") == rep and r["trial"] != "hi-hi-one_s1_r1_hook" and r["trial"] not in tags:
                tags.append(r["trial"])
    if rep == 1:
        tags.append("hi-hi-one_s1_r2_hook")
    base = {"attacker": collections.Counter(), "defender": collections.Counter()}
    out = collections.Counter()
    offer = collections.Counter()
    for t in tags:
        d = newest(t)
        out["battles"] += 1
        out["half_rounds"] += len(d["per_half_round"])
        for k in ("attacker", "defender"):
            c = d["copy_in"][k]["base_candidates"]
            base[k][str(c[0]) if len(c) == 1 else "ambiguous (clamped at 60 or 90)"] += 1
            out["copy_in_draws_" + k] += d["copy_in"][k]["draws"]
        offer[str(d["post_battle"]["offer_iff_draw_below_2"])] += 1
        for k in ("rout_tests", "rout_with_draws", "rout_removed", "shots", "melee", "flank_draws", "placement_draws"):
            out[k] += d[k]
        pb = d["post_battle"]
        out["survivors"] += pb["survivors"]
        out["promotion_draws"] += pb["promotion_draws"]
        out["promotions_random4_is_0"] += pb["promotions"]
        out["peace_draws"] += pb["peace_draws"]
        out["peace_draws_below_2"] += sum(1 for x in pb["peace_results"] if x < 2)
        out["offer_of_peace_dialogs"] += 1 if pb["dialog_after_battle"] == "Offer of peace" else 0
    res = {"trials": tags, "totals": dict(out), "copy_in_morale_base": {k: dict(v) for k, v in base.items()}, "offer_iff_draw_below_2": dict(offer)}
    p = C.write_new(C.DATA, "b11-aggregates-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(res, indent=1))
    print(p.name)
    print(json.dumps({k: v for k, v in res.items() if k != "trials"}, indent=1))


if __name__ == "__main__":
    main()
