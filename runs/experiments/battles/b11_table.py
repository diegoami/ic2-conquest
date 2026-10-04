#!/usr/bin/env python3
"""B11 sweep table with the exchange columns (task Work 4): one row per hooked B5 re-run battle, joined with its exchange check and with the B5 baseline row.

    python3 runs/experiments/battles/b11_table.py [--rep 1]

Writes `sweep-table-b11-<stamp>.csv` and `sweep-table-b11-summary-<stamp>.json` into the tracked data folder (never overwritten). The B5 columns `loss_rows` and
`unambiguous_rows` are the old diff-inferred attribution (battles plan B2: a loss row is unambiguous when the diff alone fixes actor and kind); the new columns
`loss_rows_exact` are the loss rows the exchange replay explains exactly (the replay's troops for that slot at that snapshot equal the snapshot), each with its actor, target
and draws in `exchanges-<trial>.jsonl`.
"""
import csv
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402

C = B.C


def newest(pattern):
    fs = sorted(C.DATA.glob(pattern), key=lambda p: p.stat().st_mtime)
    return fs[-1] if fs else None


def main():
    a = sys.argv[1:]
    rep = int(a[a.index("--rep") + 1]) if "--rep" in a else 1
    base_f = sorted(C.DATA.glob("b5-baseline-*.json"))[-1]
    base = json.loads(base_f.read_text())["baseline"]
    last = {}
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "ok" and r.get("variant") == "hook" and r.get("rep") == rep:
                last[r["trial"]] = r
    rows, miss_files = [], []
    for tag, r in sorted(last.items()):
        ef = newest("exchange-check-%s*.json" % tag)
        if ef is None:
            miss_files.append(tag)
            continue
        e = json.loads(ef.read_text())
        hc = json.loads((C.DATA / r["hookcheck"]).read_text())
        b5 = base.get("%s_s%d_r1" % (r["cell"], r["seed"]), {})
        a_t, d_t, size = (r["cell"].split("-") + ["", "", ""])[:3] if r["cell"] != "mix-rg" else ("mix", "mix", "natural")
        lr, lx = e["loss_rows"], e["loss_rows_exact"]
        rows.append({"trial": tag, "cell": r["cell"], "attacker": a_t, "defender": d_t, "size": size, "seed": r["seed"], "half_rounds": r["half_rounds"], "winner": r["winner"],
                     "att_loss": r["att_loss"], "def_loss": r["def_loss"], "hook_records": hc["records"], "hook_overflow": hc["overflow"], "hook_chain_breaks": hc["chain_break_count"],
                     "hook_pass": hc["pass"], "shots": e["shots"], "shots_n_ok": e["shots_n_ok"], "melee": e["melee"], "melee_n_ok": e["melee_n_ok"], "rout_tests": e["rout_tests"],
                     "rout_draw_count_ok": e["rout_draw_count_ok"], "rout_removed": e["rout_removed"], "flank_draws": e["flank_draws"], "placement_draws": e["placement_draws"],
                     "state_diffs": e["state_diffs"], "misses": e["misses"], "loss_rows": lr, "loss_rows_exact": lx,
                     "b5_loss_rows": b5.get("loss_rows", ""), "b5_unambiguous_rows": b5.get("unambiguous_rows", ""),
                     "copy_in_ok": all(v.get("count_ok") and v.get("ranges_ok") and v.get("morale_rule_ok") for v in e["copy_in"].values()),
                     "post_battle_ok": bool(e["post_battle"]["promotion_draws_equal_survivors"] and e["post_battle"]["promotion_ranges_all_4"] and e["post_battle"]["peace_draws"] <= 1
                                            and e["post_battle"]["peace_range_5"] and e["post_battle"]["offer_iff_draw_below_2"] in (True, None)),
                     "dialog": r.get("dialog", ""), "exchange_check": ef.name})
    cols = list(rows[0]) if rows else []
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    C.write_new(C.DATA, "sweep-table-b11-%s.csv" % stamp, buf.getvalue())
    tot = lambda k: sum(int(r[k]) for r in rows)
    b5_lr = sum(int(r["b5_loss_rows"]) for r in rows if r["b5_loss_rows"] != "")
    b5_un = sum(int(r["b5_unambiguous_rows"]) for r in rows if r["b5_unambiguous_rows"] != "")
    summ = {"rep": rep, "battles": len(rows), "battles_without_exchange_check": miss_files, "hook_pass": sum(1 for r in rows if r["hook_pass"]),
            "shots": tot("shots"), "shots_n_ok": tot("shots_n_ok"), "melee": tot("melee"), "melee_n_ok": tot("melee_n_ok"), "rout_tests": tot("rout_tests"),
            "rout_draw_count_ok": tot("rout_draw_count_ok"), "rout_removed": tot("rout_removed"), "flank_draws": tot("flank_draws"), "state_diffs": tot("state_diffs"),
            "misses": tot("misses"), "loss_rows": tot("loss_rows"), "loss_rows_exact": tot("loss_rows_exact"), "b5_loss_rows_same_battles": b5_lr, "b5_unambiguous_same_battles": b5_un,
            "b5_unambiguous_share": round(b5_un / b5_lr, 4) if b5_lr else None, "hook_exact_share": round(tot("loss_rows_exact") / tot("loss_rows"), 4) if rows and tot("loss_rows") else None,
            "battles_with_misses": [r["trial"] for r in rows if r["misses"] or r["state_diffs"]],
            "copy_in_ok": sum(1 for r in rows if r["copy_in_ok"]), "post_battle_ok": sum(1 for r in rows if r["post_battle_ok"]),
            "draw_order_mismatch_battles": [r["trial"] for r in rows if not (r["copy_in_ok"] and r["post_battle_ok"])],
            "placement_draws_per_battle": sorted({int(r["placement_draws"]) for r in rows})}
    C.write_new(C.DATA, "sweep-table-b11-summary-%s.json" % stamp, json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
