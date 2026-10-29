"""The registry of every original-vs-remake test that has run, so that none is repeated (owner, 2026-10-29).

    python3 -m difftest.registry          # rewrites difftest/REGISTRY.md and difftest/registry.json

Reads the TRACKED measurements (runs/experiments/data/run-exp-diff084-*/): order sweeps (results.jsonl and the newest
results-rejudged-*.jsonl), many-seed trials (trials.jsonl), tactical cases (results.jsonl with `steps`) and campaigns
(turns.jsonl). One row per test (case, scenario, campaign), with its latest verdict. Before designing a new test,
search this registry for the same start save, order and remake version; re-run a test only to check a fix or a new
remake version, and say so.

FINDINGS maps a test to the finding that reports its difference. Add to it when a finding is written.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "runs/experiments/data"
REMAKE = {"run-exp-diff084": "v0.8.4 `d9cc71bc`"}
FINDINGS = {
    "rel-war-carthage": "2026-10-29-war-declaration-ally-cooldown-diff230.md",
    "rel-war-dacia": "2026-10-29-war-declaration-ally-cooldown-diff230.md",
    "rel-war-bithynia": "2026-10-29-war-declaration-ally-cooldown-diff230.md",
    "rel-war-numidia": "2026-10-29-war-declaration-ally-cooldown-diff230.md",
    "rel-war-thracia": "2026-10-29-war-declaration-ally-cooldown-diff230.md",
    "fleet-10": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "fleet-25": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "fleet-two": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "move-sea": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "move-far": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "toy3-rome-1200": "2026-10-29-v084-known-differences-and-command-gaps.md",
    "storm30": "2026-10-29-ai-fleet-hunt-absent-in-remake233.md",
    "walk-city-on-line": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "walk-city-on-line-near": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "rome-rulebot1-5t": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "walk-carthage-army3": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "walk-gaul-army9": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "carthage-rulebot1-5t-r2": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "gaul-rulebot1-5t-r2": "2026-10-29-walk-stops-at-own-city-on-line230.md",
    "fleet-second-walk-88-32": "2026-10-30-paths-in-play-and-fleet-walks42.md",
    "fleet-second-walk-87-47": "2026-10-30-paths-in-play-and-fleet-walks42.md",
    "storm30b": "2026-10-29-ai-fleet-hunt-absent-in-remake233.md",
    "fleet-sail": "2026-10-29-ai-fleet-hunt-absent-in-remake233.md",
    "embark": "2026-10-29-export-city-marker-variant-and-empty-offer230.md",
}


def remake_of(d):
    return next((v for k, v in REMAKE.items() if d.name.startswith(k)), "?")


def jl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def sweeps(d):
    rows = jl(d / "results.jsonl")
    rej = sorted(d.glob("results-rejudged-*.jsonl"))
    latest = {}
    for r in rows + (jl(rej[-1]) if rej else []):
        latest[r["id"]] = r
    out = []
    for r in latest.values():
        script = d / "scripts" / f"{r['id']}.jsonl"
        orders = [json.loads(l) for l in script.read_text().splitlines()[1:]] if script.exists() else []
        out.append({"test": r["id"], "kind": "single order", "start": Path(r.get("start", "")).name,
                    "orders": "; ".join(_order(o) for o in orders), "verdict": r["verdict"],
                    "detail": (r.get("summary") or r.get("error") or "")[:160], "runs": sum(1 for x in rows if x["id"] == r["id"])})
    return out


def _order(o):
    return o["op"] + "(" + ", ".join(f"{k}={v}" for k, v in o.items() if k not in ("op", "note")) + ")"


def stats(d):
    ts = jl(d / "trials.jsonl")
    out = []
    for sc in sorted({t["scenario"] for t in ts}):
        n = {s: sum(1 for t in ts if t["scenario"] == sc and t["side"] == s and "metrics" in t) for s in ("original", "remake")}
        an = sorted(d.glob("analysis-*.json"))
        verdict = "trials only"
        if an:
            rows = [x for x in json.loads(an[-1].read_text())["rows"] if x["scenario"] == sc]
            diff = [x["metric"] for x in rows if x["verdict"] == "differs"]
            verdict = ("differs: " + ", ".join(diff)) if diff else "consistent"
        out.append({"test": sc, "kind": "many seeds", "start": "", "orders": "", "verdict": verdict,
                    "detail": f"original {n['original']} trials, remake {n['remake']}", "runs": n["original"] + n["remake"]})
    return out


def tactical(d):
    out = []
    for r in jl(d / "results.jsonl"):
        if "steps" in r or r.get("verdict") in ("same-exact", "differs", "error") and "dir" in r:
            out.append({"test": r["id"], "kind": "tactical", "start": "staged battle", "orders": r.get("note", ""),
                        "verdict": r["verdict"], "detail": json.dumps(r.get("first") or r.get("error", ""))[:160], "runs": 1})
    return out


def campaigns(d):
    out = []
    for c in sorted(p.parent for p in d.glob("*/turns.jsonl")):
        turns = jl(c / "turns.jsonl")
        meta = json.loads((c / "run.json").read_text()) if (c / "run.json").exists() else {}
        first = next((t["turn"] for t in turns if t.get("diverged")), None)
        out.append({"test": c.name, "kind": "bot campaign", "start": Path(meta.get("start", "")).name,
                    "orders": f"{meta.get('bot', '?')}, {len(turns)} turns", "verdict": f"first divergence turn {first}" if first else "no divergence",
                    "detail": "", "runs": 1})
    return out


def tooling(d):
    out = []
    for rep in sorted(d.glob("report-*.json")):
        r = json.loads(rep.read_text())
        out.append({"test": Path(r["script"]).stem + f" ({r['a']['side']} vs {r['b']['side']})", "kind": "script",
                    "start": "BASE.SAV", "orders": Path(r["script"]).name,
                    "verdict": f"first divergence {r['first_divergence']}" if r["first_divergence"] else "identical",
                    "detail": "", "runs": 1})
    return out


def build():
    rows = []
    for d in sorted(DATA.glob("run-exp-diff084-*")):
        res = jl(d / "results.jsonl")
        found = []
        if (d / "trials.jsonl").exists():
            found += stats(d)
        if res and any("steps" in r or "dir" in r for r in res):
            found += tactical(d)
        elif res:
            found += sweeps(d)
        found += campaigns(d) + tooling(d)
        for r in found:
            r.update(data=d.name, remake=remake_of(d), finding=FINDINGS.get(r["test"].split(" (")[0], ""))
            rows.append(r)
    return rows


def render(rows):
    lines = ["# Registry of original-vs-remake tests", "",
             "Generated by `python3 -m difftest.registry` from the tracked measurements; do not edit by hand. One row per test,",
             "latest verdict. **Check here before running a test** (owner, 2026-10-29): re-run only to check a fix or a new remake",
             "version. Batch-level results and corrections: [HISTORY.md](HISTORY.md).", "",
             "| test | kind | remake | start | orders | verdict | runs | finding | data |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = f"[{r['finding'][:30]}…](../findings/{r['finding']})" if r["finding"] else ""
        lines.append(f"| `{r['test']}` | {r['kind']} | {r['remake']} | {r['start']} | {r['orders'][:120].replace('|', '/')} | "
                     f"{r['verdict']} | {r['runs']} | {f} | [{r['data']}](../runs/experiments/data/{r['data']}/) |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    rows = build()
    (ROOT / "difftest/REGISTRY.md").write_text(render(rows))
    (ROOT / "difftest/registry.json").write_text(json.dumps(rows, indent=1))
    print(f"{len(rows)} tests registered")
