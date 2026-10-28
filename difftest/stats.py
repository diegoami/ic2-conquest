"""Many-seed comparison of random outcomes (#233).

    python3 -m difftest.stats run SCENARIOS_MODULE run-exp-<name> [--only ID ...] [--side original|remake]
    python3 -m difftest.stats analyze SCENARIOS_MODULE run-exp-<name>

`run` plays each scenario once per seed in each game (original: startup RandSeed = seed; remake: the state's
RandomSeed = seed) and appends one line per trial to artifacts/<name>/trials.jsonl with the scenario's metrics.
It resumes: a (scenario, side, seed) with a line is skipped; its run folders are never reused.

`analyze` compares the two games' samples of each metric with a two-sided permutation test on the difference of
means (10,000 permutations, numpy RNG seed 0), then Holm's correction over every metric of every scenario. The
sample sizes, metrics and alpha are fixed in the scenarios module before any trial runs (pre-registration).
"""
import argparse
import importlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import actions as act  # noqa: E402
from state.sav import load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def trials(out):
    f = out / "trials.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


def run(mod, out, only=None, sides=("remake", "original")):
    from difftest import original, remake
    out.mkdir(parents=True, exist_ok=True)
    done = {(t["scenario"], t["side"], t["seed"]) for t in trials(out) if "metrics" in t}
    for sc in mod.SCENARIOS:
        if only and sc["id"] not in only:
            continue
        actions = [act.validate(x) for x in sc["actions"]]
        for seed in sc["seeds"]:
            for side in sides:
                if (sc["id"], side, seed) in done:
                    continue
                base = out / sc["id"] / f"{side}-s{seed}"
                d, n = base, 1
                while d.exists():
                    n += 1
                    d = base.with_name(f"{base.name}-r{n}")
                rec = {"scenario": sc["id"], "side": side, "seed": seed, "run": str(d.relative_to(out)),
                       "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
                try:
                    if side == "remake":
                        remake.run(actions, sc["start"], d, log=lambda *x: None, seed=seed)
                    else:
                        original.run(actions, sc["start"], d, seed, f"T{out.name[-5:]}-{sc['id']}-{d.name}", log=lambda *x: None)
                    last = len(actions)
                    rec["metrics"] = sc["metrics"](load(d / "a000.SAV"), load(d / f"a{last:03d}.SAV"))
                except Exception as e:
                    rec["error"] = f"{type(e).__name__}: {e}"[:500]
                rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                with open(out / "trials.jsonl", "a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(f"{sc['id']} {side} seed {seed}: {rec.get('metrics', rec.get('error'))}", flush=True)


def perm_test(x, y, n=10000, rng=None):
    x, y = np.asarray(x, float), np.asarray(y, float)
    obs = x.mean() - y.mean()
    pooled = np.concatenate([x, y])
    rng = rng or np.random.default_rng(0)
    hits = 0
    for _ in range(n):
        rng.shuffle(pooled)
        if abs(pooled[:len(x)].mean() - pooled[len(x):].mean()) >= abs(obs) - 1e-12:
            hits += 1
    return obs, (hits + 1) / (n + 1)


def analyze(mod, out):
    ts = [t for t in trials(out) if "metrics" in t]
    rng = np.random.default_rng(0)
    rows = []
    for sc in mod.SCENARIOS:
        o = [t["metrics"] for t in ts if t["scenario"] == sc["id"] and t["side"] == "original"]
        r = [t["metrics"] for t in ts if t["scenario"] == sc["id"] and t["side"] == "remake"]
        if not o or not r:
            continue
        for m in sorted(o[0]):
            x = [v[m] for v in o if v.get(m) is not None]
            y = [v[m] for v in r if v.get(m) is not None]
            if not x or not y:
                continue
            if np.var(x + y) == 0:
                rows.append({"scenario": sc["id"], "metric": m, "n_original": len(x), "n_remake": len(y),
                             "mean_original": float(np.mean(x)), "mean_remake": float(np.mean(y)), "diff": 0.0, "p": 1.0,
                             "note": "constant in both"})
                continue
            diff, p = perm_test(x, y, rng=rng)
            rows.append({"scenario": sc["id"], "metric": m, "n_original": len(x), "n_remake": len(y),
                         "mean_original": float(np.mean(x)), "mean_remake": float(np.mean(y)),
                         "sd_original": float(np.std(x, ddof=1)) if len(x) > 1 else None,
                         "sd_remake": float(np.std(y, ddof=1)) if len(y) > 1 else None, "diff": float(diff), "p": p})
    # Holm: sort p ascending, compare p_(i) * (m - i) with alpha
    alpha = mod.ALPHA
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    m, still = len(rows), True
    for k, i in enumerate(order):
        adj = min(1.0, rows[i]["p"] * (m - k))
        rows[i]["p_holm"] = adj
        still = still and adj <= alpha
        rows[i]["verdict"] = "differs" if still and rows[i].get("note") != "constant in both" else "consistent"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (out / f"analysis-{stamp}.json").write_text(json.dumps({"alpha": alpha, "tests": m, "rows": rows}, indent=1))
    lines = [f"# {out.name}: original vs remake over many seeds", "",
             f"Permutation test on the difference of means (10,000 permutations), Holm-corrected over {m} tests, alpha {alpha}.", "",
             "| scenario | metric | n (o/r) | mean original | mean remake | p | p Holm | verdict |", "|---|---|---|---|---|---|---|---|"]
    for x in rows:
        lines.append(f"| {x['scenario']} | {x['metric']} | {x['n_original']}/{x['n_remake']} | {x['mean_original']:.3f} | "
                     f"{x['mean_remake']:.3f} | {x['p']:.4f} | {x['p_holm']:.4f} | **{x['verdict']}** |")
    (out / f"analysis-{stamp}.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze"])
    ap.add_argument("module")
    ap.add_argument("name")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--side", choices=["original", "remake"])
    a = ap.parse_args()
    mod = importlib.import_module(a.module)
    out = ROOT / "artifacts" / a.name
    if a.cmd == "run":
        run(mod, out, a.only, (a.side,) if a.side else ("remake", "original"))
    else:
        analyze(mod, out)
