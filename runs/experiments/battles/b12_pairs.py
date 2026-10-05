#!/usr/bin/env python3
"""B12 pair analysis (offline, from the tracked data only): the paired tables with McNemar, the pairing proof of every pair, the point where the two runs' hook logs diverge.

    python3 runs/experiments/battles/b12_pairs.py [--batch b12]       # reads trials-b12.jsonl and hooklog-*.csv; writes b12-pairs-<stamp>.json|csv and prints the table

A PAIR = one plan trial and the `cg` trial (Rome on Computer general) of the same cell and seed, both on the same hooked lab exe and the same start save. A pair is **proven** when
(1) the exe SHA-256 and the start save SHA-256 are equal, (2) the battle block read from game memory at battle open is byte-identical (SHA-256), (3) RandSeed at open and the hook buffer's
records so far (count and SHA-256 of their kind/site/seed_before/seed_after/result tuples) are equal, and (4) both runs' hook logs pass the chain check (`hook_pass`: seed chain unbroken,
no overflow). Only proven pairs enter the McNemar table; the others are listed with the reason. `diverge` = index of the first hook record where the pair's logs differ (kind, site, eax, edx,
ecx, seed_before, seed_after, result, side, flag), with both records' kind and site: before it the two runs drew identical numbers, so a difference after it may be RNG divergence that
the plan did not cause (the plan changes which draws are made); the McNemar test compares OUTCOMES, it does not separate the plan's effect from that divergence, and the finding says so.

McNemar (Rome wins = `winner == attacker`): b = plan wins and cg loses, c = plan loses and cg wins; exact two-sided binomial p = min(1, 2 * P(X <= min(b, c))), X ~ Bin(b + c, 1/2)
(headline for every table here: the discordant counts are small); the continuity-corrected chi-square (|b - c| - 1)^2 / (b + c) is printed beside it; with b + c = 0 the statistic is undefined and p = 1.
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs" / "experiments" / "data" / "run-exp-battle-orders"
COLS = ("kind", "site", "eax", "edx", "ecx", "seed_before", "seed_after", "result", "side", "flag")


def read_trials(batch=None):
    f = DATA / "trials-b12.jsonl"
    out = {}
    for ln in f.read_text().splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("status") == "ok" and (batch is None or r.get("batch") == batch):
            out.setdefault(r["trial"], r)           # the FIRST ok line of a trial (a later duplicate is a re-run, kept in the file, not used)
    return out


def hooklog(name):
    with open(DATA / name, newline="") as f:
        return [tuple(r[c] for c in COLS) for r in csv.DictReader(f)]


def exact_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def chi2(b, c):
    return None if b + c == 0 else (abs(b - c) - 1) ** 2 / (b + c)


def proof(a, p):
    """(ok, reasons) of one pair: a = the cg trial, p = the plan trial."""
    why = []
    for k, label in (("exe_sha256", "exe"), ("start_sha256", "start save")):
        if a[k] != p[k]:
            why.append("%s differs" % label)
    oa, op = a["open"], p["open"]
    for k in ("block_sha256", "seed_mem", "hook_records", "hook_records_sha256", "half_round", "y1", "side_to_move"):
        if oa[k] != op[k]:
            why.append("open.%s differs" % k)
    for t in (a, p):
        if not t.get("hook_pass"):
            why.append("hook check failed (%s)" % t["trial"])
    return (not why), why


def diverge(a, p):
    la, lp = hooklog(a["hooklog"]), hooklog(p["hooklog"])
    n = min(len(la), len(lp))
    for i in range(n):
        if la[i] != lp[i]:
            return {"index": i, "cg": {"kind": la[i][0], "site": la[i][1]}, "plan": {"kind": lp[i][0], "site": lp[i][1]}, "records_cg": len(la), "records_plan": len(lp)}
    return {"index": None if len(la) == len(lp) else n, "records_cg": len(la), "records_plan": len(lp), "identical": len(la) == len(lp)}


def table(batch=None):
    tr = read_trials(batch)
    by = {}
    for t in tr.values():
        by.setdefault((t["cell"], t["seed"], t["rep"]), {})[t["plan"]] = t
    rows, cells = [], {}
    for (cell, seed, rep), d in sorted(by.items()):
        a = d.get("cg")
        for plan, p in d.items():
            if plan == "cg" or a is None:
                continue
            ok, why = proof(a, p)
            row = {"cell": cell, "seed": seed, "plan": plan, "cg_trial": a["trial"], "plan_trial": p["trial"], "proven": ok, "why_not": "; ".join(why),
                   "cg_winner": a["winner"], "plan_winner": p["winner"], "cg_att_loss": a["att_loss"], "plan_att_loss": p["att_loss"], "cg_def_loss": a["def_loss"], "plan_def_loss": p["def_loss"],
                   "cg_seconds": a["battle_seconds"], "plan_seconds": p["battle_seconds"], "cg_half_rounds": a["half_rounds"], "plan_half_rounds": p["half_rounds"], "orders": p.get("orders"),
                   "blocked_moves": p.get("blocked_moves")}
            if ok:
                row["diverge"] = diverge(a, p)
            rows.append(row)
            cells.setdefault((plan, cell), []).append(row)
    summary = []
    for (plan, cell), rs in sorted(cells.items()):
        pr = [r for r in rs if r["proven"]]
        win = lambda w: w == "attacker"
        b = sum(1 for r in pr if win(r["plan_winner"]) and not win(r["cg_winner"]))
        c = sum(1 for r in pr if not win(r["plan_winner"]) and win(r["cg_winner"]))
        both_w = sum(1 for r in pr if win(r["plan_winner"]) and win(r["cg_winner"]))
        both_l = sum(1 for r in pr if not win(r["plan_winner"]) and not win(r["cg_winner"]))
        dv = [r["diverge"]["index"] for r in pr if r["diverge"]["index"] is not None]
        summary.append({"plan": plan, "cell": cell, "pairs": len(rs), "proven": len(pr), "unproven": len(rs) - len(pr), "plan_wins": b + both_w, "plan_losses": c + both_l,
                        "cg_wins": c + both_w, "cg_losses": b + both_l, "b_plan_win_cg_loss": b, "c_plan_loss_cg_win": c, "both_win": both_w, "both_lose": both_l,
                        "mcnemar_chi2_cc": chi2(b, c), "exact_p": exact_p(b, c), "first_divergence_index_min": min(dv) if dv else None, "first_divergence_index_max": max(dv) if dv else None,
                        "identical_logs": sum(1 for r in pr if r["diverge"].get("identical")),
                        "plan_seconds_mean": round(statistics.mean(r["plan_seconds"] for r in pr), 1) if pr else None,
                        "cg_seconds_mean": round(statistics.mean(r["cg_seconds"] for r in pr), 1) if pr else None,
                        "plan_att_loss_mean": round(statistics.mean(r["plan_att_loss"] for r in pr)) if pr else None,
                        "cg_att_loss_mean": round(statistics.mean(r["cg_att_loss"] for r in pr)) if pr else None})
    return rows, summary


def main():
    import common as C
    batch = sys.argv[sys.argv.index("--batch") + 1] if "--batch" in sys.argv else None
    rows, summ = table(batch)
    stamp = C.STAMP
    C.write_new(DATA, "b12-pairs-%s.json" % stamp, json.dumps({"rows": rows, "summary": summ}, indent=1, default=str))
    import io
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, list(summ[0].keys()) if summ else ["empty"], lineterminator="\n")
    w.writeheader()
    for s in summ:
        w.writerow(s)
    C.write_new(DATA, "b12-pairs-summary-%s.csv" % stamp, buf.getvalue())
    for s in summ:
        print("%-8s %-10s pairs %2d proven %2d | plan W/L %2d/%2d  cg W/L %2d/%2d | b=%d c=%d chi2cc=%s exact p=%.4f | diverge idx %s..%s | s plan %s cg %s" % (
            s["plan"], s["cell"], s["pairs"], s["proven"], s["plan_wins"], s["plan_losses"], s["cg_wins"], s["cg_losses"], s["b_plan_win_cg_loss"], s["c_plan_loss_cg_win"],
            "n/a" if s["mcnemar_chi2_cc"] is None else "%.2f" % s["mcnemar_chi2_cc"], s["exact_p"], s["first_divergence_index_min"], s["first_divergence_index_max"],
            s["plan_seconds_mean"], s["cg_seconds_mean"]))


if __name__ == "__main__":
    main()
