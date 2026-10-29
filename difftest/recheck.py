"""Re-check the registered original-vs-remake tests against a pinned remake build (owner, 2026-10-30): the original side does
not change, so only the remake side is played again and judged against the STORED original runs with the same code.

    python3 -m difftest.pin build <ref>                                   # once per ref
    python3 -m difftest.recheck <short> [--tiers orders stats campaigns] [--version v1]

Tiers:
- orders: every case of the #230 order sweeps (difftest/cases/orders230_b1..b8; their results in
  artifacts/run-exp-diff084-orders*/). The remake plays the case from the same start (a staged start included), and
  sweep.verdict_of judges it against the stored original run folder.
- stats: the #233 scenarios (difftest/cases/stats233). The stored original trials are copied into the new folder (each
  line marked "copied_from"), the remake trials are played again, and stats.analyze runs unchanged.
- campaigns: the #232 bot campaigns (artifacts/run-exp-diff084-campaign/*, run-exp-diff084-allhuman/*). The bot decides
  from each game's own state, as difftest/campaign.py does: the original's states are its stored End-turn checkpoints
  (paired from receipt.jsonl), the remake plays its turns again.

Output: artifacts/run-exp-recheck-<short>/ (runs, results-<tier>.jsonl, report-<version>.json/.md): each test's verdict at
v0.8.4 and now, labelled FIXED (a difference that is gone), REGRESSED (a new difference), CHANGED, or unchanged, with the
finding the registry links to it. Never overwrites a run folder or a report (rule 6).
"""
import argparse
import importlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SAME = {"same", "consistent", "identical", "same-exact"}
BATCHES = {"run-exp-diff084-orders": "orders230_b1", **{f"run-exp-diff084-orders-b{k}": f"orders230_b{k}" for k in range(2, 9)}}


def label(before, after):
    b, a = before in SAME, after in SAME
    if before == after:
        return "unchanged"
    if not b and a:
        return "FIXED"
    if b and not a:
        return "REGRESSED"
    return "CHANGED"


def findings_map():
    reg = json.loads((ROOT / "difftest/registry.json").read_text())
    return {t["test"]: t.get("finding") for t in reg}


def latest_results(d):
    """The stored verdict per case: the newest re-judged file if any, else results.jsonl (latest line per id)."""
    files = sorted(d.glob("results-rejudged-*.jsonl")) or [d / "results.jsonl"]
    return {r["id"]: r for r in (json.loads(l) for l in files[-1].read_text().splitlines() if l.strip())}


def tier_orders(out, log):
    from difftest import actions as act, remake
    from difftest.sweep import fresh_dir, verdict_of
    rows = []
    for batch, module in BATCHES.items():
        src = ROOT / "artifacts" / batch
        if not (src / "results.jsonl").exists():
            log(f"orders: {batch} has no stored results here; skipped")
            continue
        cases = {c["id"]: c for c in importlib.import_module(f"difftest.cases.{module}").CASES}
        for cid, r in latest_results(src).items():
            if r.get("verdict") == "error" or cid not in cases:
                continue
            actions = [act.validate(x) for x in cases[cid]["actions"]] + [{"op": "end_turn"}]
            rb = fresh_dir(out / "orders" / batch / cid / "remake")
            rec = {"tier": "orders", "batch": batch, "test": cid, "before": r["verdict"], "start": r["start"],
                   "original_run": str((src / r["original_run"]).relative_to(ROOT)), "remake_run": str(rb.relative_to(ROOT))}
            try:
                remake.run(actions, r["start"], rb, log=lambda *x: None)
                v, details = verdict_of({"actions": actions}, src / r["original_run"], rb, len(actions) - 1)
                rec.update(after=v, intents=details["intents"], details=details)
            except Exception as e:
                rec.update(after="error", error=f"{type(e).__name__}: {e}"[:500])
            rows.append(rec)
            log(f"orders {cid}: {rec['before']} -> {rec['after']}")
    return rows


def tier_stats(out, log):
    from difftest import stats
    mod = importlib.import_module("difftest.cases.stats233")
    name = out.name + "-stats"
    sdir = ROOT / "artifacts" / name
    sdir.mkdir(parents=True, exist_ok=True)
    tf = sdir / "trials.jsonl"
    if not tf.exists():
        with open(tf, "w") as f:
            for l in (ROOT / "artifacts/run-exp-diff084-stats/trials.jsonl").read_text().splitlines():
                t = json.loads(l)
                if t.get("side") == "original" and "metrics" in t:
                    f.write(json.dumps(dict(t, copied_from="run-exp-diff084-stats")) + "\n")
    stats.run(mod, sdir, sides=("remake",))
    before = json.loads(sorted((ROOT / "artifacts/run-exp-diff084-stats").glob("analysis-*.json"))[-1].read_text())
    stats.analyze(mod, sdir)
    after = json.loads(sorted(sdir.glob("analysis-*.json"))[-1].read_text())
    key = lambda x: (x["scenario"], x["metric"])
    b = {key(x): x for x in before["rows"]} if isinstance(before, dict) and "rows" in before else {key(x): x for x in before}
    a = {key(x): x for x in after["rows"]} if isinstance(after, dict) and "rows" in after else {key(x): x for x in after}
    rows = []
    for k, x in a.items():
        rows.append({"tier": "stats", "test": f"{k[0]}:{k[1]}", "scenario": k[0], "before": b.get(k, {}).get("verdict", "not run"),
                     "after": x.get("verdict"), "mean_remake_before": b.get(k, {}).get("mean_remake"),
                     "mean_remake_after": x.get("mean_remake"), "mean_original": x.get("mean_original"), "p_holm": x.get("p_holm")})
        log(f"stats {k}: {rows[-1]['before']} -> {rows[-1]['after']}")
    return rows


def tier_campaigns(out, log):
    from difftest import actions as act, remake
    from difftest.compare import compare, scoped
    from state.sav import load
    bot = importlib.import_module("difftest.bot")
    rows = []
    for c in sorted([*(ROOT / "artifacts/run-exp-diff084-campaign").glob("*/run.json"),
                     *(ROOT / "artifacts/run-exp-diff084-allhuman").glob("*/run.json")]):
        c = c.parent
        rec_o = c / "original" / "receipt.jsonl"
        if not rec_o.exists():
            continue
        meta = json.loads((c / "run.json").read_text())
        acts = [json.loads(l) for l in rec_o.read_text().splitlines() if l.strip()]
        ends = [x["checkpoint"] for x in acts if x.get("kind") == "action" and x["action"]["op"] == "end_turn" and not x.get("error")]
        if not ends:
            continue
        start = Path(meta["start"]) if Path(meta["start"]).is_absolute() else ROOT / meta["start"]
        rdir = out / "campaigns" / c.parent.name / c.name
        if rdir.exists():
            log(f"campaign {c.name}: {rdir} exists; skipped")
            continue
        rdir.mkdir(parents=True)
        remake.run([], start, rdir / "t00", log=lambda *x: None)
        native, sr = rdir / "t00" / "a000.native", load(rdir / "t00" / "a000.SAV")
        so_prev = load(c / "original" / "t00-start.SAV")
        first, turns = None, []
        for k, cp in enumerate(ends, 1):
            so = load(c / "original" / f"{cp}.SAV")
            oo, orr = bot.decide(so_prev), bot.decide(sr)
            names = act.checkpoint_names(orr + [{"op": "end_turn"}])
            remake.run([act.validate(x) for x in orr + [{"op": "end_turn"}]], native, rdir / f"t{k:02d}", log=lambda *x: None,
                       template=start)
            last = rdir / f"t{k:02d}" / names[-1]
            native, sr = last.with_suffix(".native"), load(last.with_suffix(".SAV"))
            d = compare(so, sr)
            own = scoped(d, so, sr, so_prev["current_nation"])
            row = {"turn": k, "orders_same": oo == orr, "differences": len(d["fields"]) + d["map"]["count"], "own_differences": len(own)}
            if first is None and (not row["orders_same"] or row["differences"]):
                first = k
            turns.append(row)
            so_prev = so
        (rdir / "turns.jsonl").write_text("".join(json.dumps(t) + "\n" for t in turns))
        before = json.loads((c / "summary.json").read_text()).get("first_divergence_turn") if (c / "summary.json").exists() else None
        b = f"first divergence turn {before}" if before else "identical"
        a = f"first divergence turn {first}" if first else "identical"
        rows.append({"tier": "campaigns", "test": c.name, "before": b, "after": a, "turns": len(ends),
                     "own_differences_by_turn": [t["own_differences"] for t in turns]})
        log(f"campaign {c.name}: {b} -> {a}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("short")
    ap.add_argument("--tiers", nargs="*", default=["orders", "stats", "campaigns"])
    ap.add_argument("--version", default="v1")
    a = ap.parse_args()
    from difftest import pin
    os.environ.update(pin.env(a.short))                      # before difftest.remake is imported
    out = ROOT / "artifacts" / f"run-exp-recheck-{a.short}"
    out.mkdir(parents=True, exist_ok=True)
    rep = out / f"report-{a.version}.json"
    if rep.exists():
        raise SystemExit(f"refusing to overwrite {rep}")
    logf = open(out / f"recheck-{a.version}.log", "a")

    def log(m):
        print(m, flush=True)
        logf.write(m + "\n")
    fmap = findings_map()
    allrows = []
    for tier in a.tiers:
        rows = {"orders": tier_orders, "stats": tier_stats, "campaigns": tier_campaigns}[tier](out, log)
        for r in rows:
            r["label"] = label(r["before"], r["after"])
            r["finding"] = fmap.get(r["test"]) or fmap.get(r["test"].split(":")[0])
        with open(out / f"results-{tier}-{a.version}.jsonl", "a") as f:
            for r in rows:
                f.write(json.dumps(r, default=str) + "\n")
        allrows += rows
    pinrec = pin.record(a.short)
    counts = {}
    for r in allrows:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    rep.write_text(json.dumps({"pin": pinrec, "tiers": a.tiers, "counts": counts, "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "changes": [{k: r.get(k) for k in ("tier", "test", "before", "after", "label", "finding")}
                                           for r in allrows if r["label"] != "unchanged"]}, indent=1, default=str))
    md = [f"# Re-check against remake {pinrec['short']} ({pinrec['ref']}: {pinrec['subject']})", "",
          "Counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
          "| tier | test | v0.8.4 | now | label | finding |", "|---|---|---|---|---|---|"]
    for r in sorted(allrows, key=lambda r: (r["label"] == "unchanged", r["tier"], r["test"])):
        md.append(f"| {r['tier']} | {r['test']} | {r['before']} | {r['after']} | **{r['label']}** | {r.get('finding') or ''} |")
    (out / f"report-{a.version}.md").write_text("\n".join(md) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
