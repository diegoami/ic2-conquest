#!/usr/bin/env python3
"""B11 seed-chain summary: one row per hooked battle (every ok hooked trial of the data folder) from its `hookcheck-<trial>.json`, plus totals.

    python3 runs/experiments/battles/b11_chains.py

Writes `chains-<stamp>.csv` and `chains-summary-<stamp>.json` (tracked, never overwritten). A battle PASSES when: the overflow flag is clear, the buffer's magic is there,
the seed chain has no break (every record's seed_before is the previous record's seed_after; every Random record is one LCG step; every Random site is one of the 14), the first
record is the battle-start boundary carrying the lab's seed, every Random result equals (range * seed_after) >> 32, the battle flag was cleared by a recorded write, no reseed
came before it, and the end of the draws is pinned: by a reseed record that follows the last post-battle Random (battles that opened the Offer of peace box), else by RandSeed read
from memory after the battle's windows closed.
"""
import csv
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402

C = B.C


def main():
    rows = []
    seen = set()
    exes = sorted(C.DATA.glob("EXES-sha256*.txt"), key=lambda p: p.stat().st_mtime)[-1].read_text().split()
    final = {x for x in exes if len(x) == 64}
    if "--all" in sys.argv:
        final = None                                   # every hooked trial of every build
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") != "ok" or r.get("variant") != "hook" or r["trial"] in seen or (final is not None and r.get("exe_sha256") not in final):
            continue
        seen.add(r["trial"])
        hc = json.loads((C.DATA / r["hookcheck"]).read_text())
        rows.append({"trial": r["trial"], "cell": r["cell"], "seed": r["seed"], "rep": r["rep"], "exe_sha12": r["exe_sha256"][:12], "records": hc["records"], "capacity": hc["capacity"],
                     "overflow": hc["overflow"], "reentered": hc.get("reentered", ""), "chain_breaks": hc["chain_break_count"], "start_boundary_ok": hc["start_boundary_ok"], "first_seed_before": hc["first_seed_before"],
                     "result_formula_misses": hc["result_formula_miss_count"], "flag_clear_sites": ";".join(x[1] for x in hc["flag_clear_records"]),
                     "reseed_sites": ";".join(x[1] for x in hc.get("reseed_records", [])), "end_pin": ("reseed record" if hc.get("end_pin_by_reseed_record") else
                                                                                               "memory read" if hc.get("end_pin_by_memory") else "none"),
                     "sites_outside_list": ";".join(hc["sites_outside_list"]), "pass": hc["pass"], "note": "first hooked build (no reseed boundary caves yet)" if "reseed_records" not in hc else ""})
    stamp = time.strftime("%Y%m%d-%H%M%S")
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    C.write_new(C.DATA, "chains-%s.csv" % stamp, buf.getvalue())
    summ = {"battles": len(rows), "pass": sum(1 for r in rows if r["pass"]), "fail": [r["trial"] for r in rows if not r["pass"]], "overflow_set": sum(1 for r in rows if r["overflow"]), "reentered_set": sum(1 for r in rows if r["reentered"] not in ("", 0)),
            "chain_breaks_total": sum(r["chain_breaks"] for r in rows), "records_total": sum(r["records"] for r in rows), "records_max": max(r["records"] for r in rows),
            "capacity": rows[0]["capacity"], "end_pin": dict(Counter(r["end_pin"] for r in rows)), "flag_clear_sites": dict(Counter(r["flag_clear_sites"] for r in rows)),
            "reseed_sites": dict(Counter(r["reseed_sites"] for r in rows)), "exe_sha12": dict(Counter(r["exe_sha12"] for r in rows))}
    C.write_new(C.DATA, "chains-summary-%s.json" % stamp, json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
