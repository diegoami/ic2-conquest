"""First-divergence report between two runs of the same action script (#229).

    python3 -m difftest.report RUN_A RUN_B OUT_PREFIX

Compares the checkpoints aNNN.SAV present in both runs, in order. Writes OUT_PREFIX.json (every checkpoint's
differences) and OUT_PREFIX.md (the first differing checkpoint, the action that led to it, and the fields).
For each action it also says whether it changed the state on each side: one side changing and the other not
is a refusal difference (one game accepted the order, the other refused it).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest.compare import compare, project  # noqa: E402
from state.sav import load  # noqa: E402


def actions_of(run):
    return [json.loads(l) for l in (Path(run) / "receipt.jsonl").read_text().splitlines() if l.strip()]


def script_actions(run):
    meta = json.loads((Path(run) / "run.json").read_text())
    from difftest.actions import load as load_script
    return meta, load_script(meta["script"])[1]


def changed(p, q):
    return sorted(k for k in set(p) | set(q) if json.dumps(p.get(k)) != json.dumps(q.get(k)))


def report(run_a, run_b):
    run_a, run_b = Path(run_a), Path(run_b)
    meta_a, acts = script_actions(run_a)
    meta_b, acts_b = script_actions(run_b)
    if meta_a["script_sha256"] != meta_b["script_sha256"]:
        raise SystemExit("the two runs played different scripts")
    names = sorted(p.stem for p in run_a.glob("a[0-9][0-9][0-9].SAV") if (run_b / p.name).exists())
    rows, prev = [], None
    for name in names:
        sa, sb = load(run_a / f"{name}.SAV"), load(run_b / f"{name}.SAV")
        d = compare(sa, sb)
        pa, pb = project(sa), project(sb)
        row = {"checkpoint": name, "date_a": sa["date"], "date_b": sb["date"],
               "differences": len(d["fields"]) + d["map"]["count"], "fields": d["fields"], "map": d["map"]}
        k = int(name[1:])
        if k > 0:
            row["action"] = acts[k - 1]
            ca, cb = changed(prev[0], pa), changed(prev[1], pb)
            row["changed_a"], row["changed_b"] = len(ca), len(cb)
            if bool(ca) != bool(cb):
                row["refusal_difference"] = "a changed nothing" if not ca else "b changed nothing"
        rows.append(row)
        prev = (pa, pb)
    first = next((r for r in rows if r["differences"]), None)
    return {"a": {"run": str(run_a), "side": meta_a["side"], "seed": meta_a.get("seed")},
            "b": {"run": str(run_b), "side": meta_b["side"], "seed": meta_b.get("seed")},
            "script": meta_a["script"], "checkpoints": len(rows), "missing": max(len(acts) + 1 - len(rows), 0),
            "first_divergence": first and first["checkpoint"], "rows": rows}


def markdown(r, n=30):
    a, b = r["a"], r["b"]
    out = [f"# Differential report: {Path(r['script']).name}", "",
           f"- A: {a['side']} `{a['run']}`" + (f", seed {a['seed']}" if a["seed"] is not None else ""),
           f"- B: {b['side']} `{b['run']}`" + (f", seed {b['seed']}" if b["seed"] is not None else ""),
           f"- Checkpoints compared: {r['checkpoints']}" + (f" ({r['missing']} missing: a run stopped early)" if r["missing"] else ""), ""]
    if not r["first_divergence"]:
        out.append("**No difference** at any compared checkpoint.")
    else:
        row = next(x for x in r["rows"] if x["checkpoint"] == r["first_divergence"])
        out += [f"**First divergence: `{row['checkpoint']}`** ({row['date_a']} / {row['date_b']}), "
                f"after action {json.dumps(row.get('action'))}: {len(row['fields'])} fields, {row['map']['count']} map cells.", ""]
        if row.get("refusal_difference"):
            out += [f"Refusal difference: {row['refusal_difference']}.", ""]
        out += ["| field | A | B |", "|---|---|---|"]
        for f in row["fields"][:n]:
            out.append(f"| `{f['path']}` | `{json.dumps(f['a'])[:80]}` | `{json.dumps(f['b'])[:80]}` |")
        if len(row["fields"]) > n:
            out.append(f"| … {len(row['fields']) - n} more | | |")
        for c in row["map"]["first"][:10]:
            out.append(f"| map ({c['x']},{c['y']}) | {c['a']} | {c['b']} |")
        out += ["", "Later checkpoints are consequences unless shown otherwise:", ""]
    out += ["| checkpoint | action | changed A | changed B | differences |", "|---|---|---|---|---|"]
    for x in r["rows"]:
        op = x.get("action", {}).get("op", "start")
        out.append(f"| {x['checkpoint']} | {op} | {x.get('changed_a', '')} | {x.get('changed_b', '')} | {x['differences']}"
                   + (f" ({x['refusal_difference']})" if x.get("refusal_difference") else "") + " |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    r = report(sys.argv[1], sys.argv[2])
    prefix = Path(sys.argv[3])
    for ext, text in ((".json", json.dumps(r, indent=1)), (".md", markdown(r))):
        target = prefix.with_suffix(ext)
        if target.exists():
            raise SystemExit(f"refusing to overwrite {target}")
        target.write_text(text)
    print(f"first divergence: {r['first_divergence']}; {r['checkpoints']} checkpoints")
