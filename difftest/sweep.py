"""Run a table of single-order cases in both games and give each a verdict (#230).

    python3 -m difftest.sweep CASES_MODULE run-exp-<name> [--only ID ...] [--remake-only]

Each case is one or more actions from a start save, followed by one End turn. Per case, both games play it
(`difftest.run`), then:
- `a001..aN` (the case's own actions) are compared in full: our orders, no AI and no random draw yet;
- the last checkpoint (after End turn) is compared on the acting nation's own records only.
Results go to artifacts/<name>/results.jsonl (one line per case, appended as each case finishes: a stopped
sweep resumes at the first case without a line) and results.md. A case whose folders exist without a result
line is re-run in new folders (`-r2`, ...); nothing is deleted.
"""
import argparse
import importlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import actions as act  # noqa: E402
from difftest.compare import compare, scoped  # noqa: E402
from difftest.intent import check  # noqa: E402
from state.sav import NATIONS, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["harness", "refusal-difference", "differs-immediate", "differs-after-end-turn", "same", "error"]


def fresh_dir(base):
    p, n = base, 1
    while p.exists():
        n += 1
        p = base.with_name(f"{base.name}-r{n}")
    return p


def verdict_of(case, ra, rb, n_actions):
    """(verdict, details) from the two run folders."""
    rows, intents = [], []
    # Differences already present at the start (a000) come from the import -> export round trip of the start save,
    # not from the case's orders: a later difference identical to one of them is set aside as "baseline"
    # (#230 batch 3: fleet-port-antium-0734 starts with 3 city marker cells and the empty pending offer's type).
    d0 = compare(load(ra / "a000.SAV"), load(rb / "a000.SAV"))
    base_fields = {(f["path"], json.dumps(f["a"]), json.dumps(f["b"])) for f in d0["fields"]}
    base_cells = {(c["x"], c["y"], c["a"], c["b"]) for c in d0["map"]["first"]}

    def strip(d):
        fields = [f for f in d["fields"] if (f["path"], json.dumps(f["a"]), json.dumps(f["b"])) not in base_fields]
        cells = [c for c in d["map"]["first"] if (c["x"], c["y"], c["a"], c["b"]) not in base_cells]
        extra = max(0, d["map"]["count"] - len(d["map"]["first"]))      # cells beyond the listed ones are kept
        return fields, len(cells) + extra
    for k in range(1, n_actions + 1):
        a0, a1 = load(ra / f"a{k - 1:03d}.SAV"), load(ra / f"a{k:03d}.SAV")
        b0, b1 = load(rb / f"a{k - 1:03d}.SAV"), load(rb / f"a{k:03d}.SAV")
        act_ = case["actions"][k - 1]
        io, ir = check(act_, a0, a1), check(act_, b0, b1)
        d = compare(a1, b1)
        intents.append({"step": k, "op": act_["op"], "original": io, "remake": ir})
        fields, cells = strip(d)
        if any(x["op"] == "end_turn" for x in case["actions"][:k]):
            # After an End turn inside the case, AI moves and random draws act: only the acting nation's records.
            own = scoped({"fields": fields}, a1, b1, load(ra / "a000.SAV")["current_nation"])
            rows.append({"checkpoint": f"a{k:03d}", "fields": own, "map": 0, "scoped": True})
        else:
            rows.append({"checkpoint": f"a{k:03d}", "fields": fields, "map": cells})
    last = n_actions + 1
    a_end, b_end = load(ra / f"a{last:03d}.SAV"), load(rb / f"a{last:03d}.SAV")
    nation = load(ra / "a000.SAV")["current_nation"]
    end = scoped({"fields": strip(compare(a_end, b_end))[0]}, a_end, b_end, nation)
    details = {"intents": intents, "immediate": rows, "after_end_turn_own": end, "nation": NATIONS[nation],
               "start_baseline": {"fields": d0["fields"], "map_cells": d0["map"]["count"]}}
    acts = [json.loads(l) for l in (ra / "receipt.jsonl").read_text().splitlines() if l.strip()]
    acts = [x for x in acts if x.get("kind") == "action"]
    # An adapter error that came with a game box is a refusal the dialog-driving code did not expect, not a harness
    # failure: the box text is the game's answer (it is kept in details["original_refusals"]).
    details["original_refusals"] = [{"error": x["error"], "box": x.get("reply")} for x in acts if x.get("error") and x.get("reply")]
    details["original_errors"] = [x["error"] for x in acts if x.get("error") and not x.get("reply")]
    # A dialog that never opened while the original's state did not change is a silent refusal (e.g. Split army at 198
    # armies, FUN_00449f08: no box at all): the game's answer, not a harness failure (#230 b8).
    if details["original_errors"] and all("did not open" in e for e in details["original_errors"]) \
            and all(i["original"][0] == "no-change" for i in intents):
        details["original_refusals"] += [{"error": e, "box": None, "silent": True} for e in details["original_errors"]]
        details["original_errors"] = []
    if details["original_errors"] or any(i["original"][0] == "not-met" for i in intents):
        return "harness", details
    if any((i["original"][0] == "no-change") != (i["remake"][0] == "no-change") for i in intents):
        return "refusal-difference", details
    if any(r["fields"] or r["map"] for r in rows):
        return "differs-immediate", details
    if end:
        return "differs-after-end-turn", details
    return "same", details


def short(details, n=6):
    for r in details["immediate"]:
        if r["fields"] or r["map"]:
            fs = [f"{f['path']}: {json.dumps(f['a'])[:40]} vs {json.dumps(f['b'])[:40]}" for f in r["fields"][:n]]
            return f"{r['checkpoint']}: " + "; ".join(fs) + (f" (+{len(r['fields']) - n})" if len(r["fields"]) > n else "") \
                + (f"; {r['map']} map cells" if r["map"] else "")
    if details["after_end_turn_own"]:
        fs = [f"{f['path']}: {json.dumps(f['a'])[:40]} vs {json.dumps(f['b'])[:40]}" for f in details["after_end_turn_own"][:n]]
        return "after End turn: " + "; ".join(fs) + (f" (+{len(details['after_end_turn_own']) - n})" if len(details["after_end_turn_own"]) > n else "")
    return ""


def render(out, cases):
    res = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines() if l.strip()]
    latest = {r["id"]: r for r in res}
    counts = {}
    for r in latest.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    lines = [f"# {out.name}: single-order sweep", "",
             "Verdicts: " + ", ".join(f"{k} {counts[k]}" for k in ORDER if k in counts), "",
             "| case | orders | original | remake | verdict | first difference |", "|---|---|---|---|---|---|"]
    for c in cases:
        r = latest.get(c["id"])
        if not r:
            lines.append(f"| {c['id']} | | | | not run | |")
            continue
        io = "; ".join(f"{i['original'][0]} {i['original'][1]}"[:70] for i in r.get("intents", []))
        ir = "; ".join(f"{i['remake'][0]} {i['remake'][1]}"[:70] for i in r.get("intents", []))
        lines.append(f"| {c['id']} | {c['note']} | {io} | {ir} | **{r['verdict']}** | {r.get('summary', r.get('error', ''))[:300].replace('|', '/')} |")
    (out / "results.md").write_text("\n".join(lines) + "\n")
    return counts


def rejudge(cases_module, name):
    """Recompute every case's verdict from its saved run folders with the current rules (no game is played).
    Writes results-rejudged-<stamp>.jsonl beside results.jsonl; the original results are kept."""
    cases = {c["id"]: c for c in importlib.import_module(cases_module).CASES}
    out = ROOT / "artifacts" / name
    res = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines() if l.strip()]
    target = out / f"results-rejudged-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    with open(target, "w") as f:
        for r in res:
            if r["verdict"] == "error":
                f.write(json.dumps(r) + "\n")
                continue
            actions = [act.validate(x) for x in cases[r["id"]]["actions"]] + [{"op": "end_turn"}]
            v, details = verdict_of({"actions": actions}, out / r["original_run"], out / r["remake_run"], len(actions) - 1)
            r2 = dict(r, verdict=v, summary=short(details), intents=details["intents"], details=details,
                      rejudged=time.strftime("%Y-%m-%dT%H:%M:%S"), previous_verdict=r["verdict"])
            f.write(json.dumps(r2, default=str) + "\n")
    return target


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "rejudge":
        print(rejudge(sys.argv[2], sys.argv[3]))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("name")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--rerun", nargs="*", default=[], help="play these cases again in new folders (a new result line; the old one is kept)")
    a = ap.parse_args()
    cases = importlib.import_module(a.cases).CASES
    out = ROOT / "artifacts" / a.name
    (out / "scripts").mkdir(parents=True, exist_ok=True)
    resfile = out / "results.jsonl"
    done = {json.loads(l)["id"] for l in resfile.read_text().splitlines() if l.strip()} if resfile.exists() else set()
    done -= set(a.rerun)
    from difftest import original, remake
    for c in cases:
        if c["id"] in done or (a.only and c["id"] not in a.only):
            continue
        actions = [act.validate(x) for x in c["actions"]] + [{"op": "end_turn"}]
        if c.get("stage"):
            # A staged start (difftest/stage.py): written once beside the case's runs and used by both games.
            from difftest import stage
            c = dict(c, start=str(stage.apply(c["start"], c["stage"], out / "staged" / f"{c['id']}.SAV")))
        script = out / "scripts" / f"{c['id']}.jsonl"
        if not script.exists():
            script.write_text("\n".join(json.dumps(x) for x in
                                        [{"format": act.FORMAT, "name": c["id"], "note": c["note"]}] + actions) + "\n")
        rb, ra = fresh_dir(out / c["id"] / "remake"), fresh_dir(out / c["id"] / "original")
        rec = {"id": c["id"], "note": c["note"], "start": c["start"], "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "remake_run": str(rb.relative_to(out)), "original_run": str(ra.relative_to(out))}
        try:
            remake.run(actions, c["start"], rb, log=lambda *x: None)
            original.run(actions, c["start"], ra, a.seed, f"S{a.name[-6:]}-{c['id']}-{ra.name}", log=lambda *x: None)
            for side, d in (("remake", rb), ("original", ra)):
                (d / "run.json").write_text(json.dumps({"side": side, "script": str(script), "case": c["id"],
                                                        "seed": a.seed if side == "original" else None}))
            v, details = verdict_of({"actions": actions}, ra, rb, len(actions) - 1)
            rec.update(verdict=v, summary=short(details), intents=details["intents"], details=details)
        except Exception as e:      # recorded, and the sweep goes on: a failed case is diagnosed from its receipts
            rec.update(verdict="error", error=f"{type(e).__name__}: {e}"[:500])
        rec["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(resfile, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        render(out, cases)
        print(f"{c['id']}: {rec['verdict']} {rec.get('summary', rec.get('error', ''))[:200]}", flush=True)
    print(json.dumps(render(out, cases)))


if __name__ == "__main__":
    main()
