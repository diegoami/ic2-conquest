#!/usr/bin/env python3
"""B11 inertness comparisons (task Work 1 and 4): every hooked battle against the unhooked lab battle of the same cell and seed, byte for byte.

    python3 runs/experiments/battles/b11_compare.py baseline [REF]    # extract the B5 baseline (rep 1 of every ok trial: BATTLEnn and post-battle SHA-256) from the
                                                                      #   B5 branch (default origin/experiment/battle-sweep-b5) into b5-baseline-<stamp>.json (tracked)
    python3 runs/experiments/battles/b11_compare.py inertness [BASELINE.json]
                                                                      # compare each ok hooked trial of trials-b11.jsonl with (a) its own plain trial of this run, if any,
                                                                      #   (b) the B5 baseline, if the cell is in it; writes inertness-<stamp>.json and .csv

The comparison is on the content hashes of the series files (position by position, same length) and of the post-battle save: a hooked battle is inert only if
both are identical. Any difference is reported, never averaged away.
"""
import csv
import io
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402

C = B.C
DEFAULT_REF = "origin/experiment/battle-sweep-b5"
B5_DATA = "runs/experiments/data/run-exp-battle-sweep"


def git_show(ref, path):
    return subprocess.run(["git", "show", "%s:%s" % (ref, path)], cwd=C.ROOT, capture_output=True, text=True, check=True).stdout


def baseline(ref=DEFAULT_REF):
    sha_lines = git_show(ref, B5_DATA + "/SAVES.sha256").splitlines()
    sha = {}
    for line in sha_lines:
        h, _, name = line.partition("  ")
        sha.setdefault(name, set()).add(h)
    commit = subprocess.run(["git", "rev-parse", ref], cwd=C.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    trials = [json.loads(x) for x in git_show(ref, B5_DATA + "/trials.jsonl").splitlines() if x.strip()]
    out, ambiguous = {}, []
    for r in trials:
        if r.get("status") != "ok" or r.get("rep") != 1:
            continue
        names = list(r["series"])
        hs = [sha.get(n) for n in names]
        post = sha.get(r["post_save"])
        if any(h is None or len(h) != 1 for h in hs) or post is None or len(post) != 1:
            ambiguous.append(r["trial"])
            continue
        out[r["trial"]] = {"cell": r["cell"], "seed": r["seed"], "half_rounds": r["half_rounds"], "winner": r["winner"], "series_sha256": [next(iter(h)) for h in hs],
                           "post_sha256": r["post_sha256"], "post_sha256_from_SAVES": next(iter(post)), "start_sha256": r.get("start_sha256"), "loss_rows": None}
    # the B5 sweep table (the newest one) for the loss_rows / unambiguous_rows columns
    tables = sorted(x for x in subprocess.run(["git", "ls-tree", "--name-only", ref, B5_DATA + "/"], cwd=C.ROOT, capture_output=True, text=True).stdout.split()
                    if "/sweep-table-" in x)
    if tables:
        for row in csv.DictReader(io.StringIO(git_show(ref, tables[-1]))):
            if row["trial"] in out:
                out[row["trial"]]["loss_rows"] = int(row["loss_rows"] or 0)
                out[row["trial"]]["unambiguous_rows"] = int(row["unambiguous_rows"] or 0)
                out[row["trial"]]["sweep_table"] = Path(tables[-1]).name
    res = {"ref": ref, "commit": commit, "trials": len(out), "ambiguous_or_missing_hashes": ambiguous, "baseline": out}
    p = C.write_new(C.DATA, "b5-baseline-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(res, indent=1))
    print(p.name, len(out), "trials", "problems", ambiguous)
    return p


def latest(pattern):
    fs = sorted(C.DATA.glob(pattern))
    return fs[-1] if fs else None


def read_trials():
    f = C.DATA / "trials-b11.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def inertness(base_path=None):
    base_path = Path(base_path) if base_path else latest("b5-baseline-*.json")
    base = json.loads(base_path.read_text())["baseline"] if base_path else {}
    ok = {}
    for r in read_trials():
        if r.get("status") == "ok":
            ok[r["trial"]] = r
    rows = []
    for tag, r in sorted(ok.items()):
        if r["variant"] != "hook":
            continue
        row = {"trial": tag, "cell": r["cell"], "seed": r["seed"], "rep": r["rep"], "half_rounds": r["half_rounds"], "hook_pass": r.get("hook_pass")}
        hs = [s["sha256"] for s in r["series"]]
        # (a) the unhooked lab run of this session, the same cell and seed (any rep)
        plain = [p for p in ok.values() if p["variant"] == "plain" and p["cell"] == r["cell"] and p["seed"] == r["seed"]]
        if plain:
            p = plain[0]
            ps = [s["sha256"] for s in p["series"]]
            row.update({"plain_trial": p["trial"], "plain_series_identical": ps == hs, "plain_post_identical": p["post_sha256"] == r["post_sha256"],
                        "plain_start_identical": p["start_sha256"] == r["start_sha256"], "plain_half_rounds": p["half_rounds"]})
        # (b) the B5 baseline (rep 1)
        key = "%s_s%d_r1" % (r["cell"], r["seed"])
        if key in base:
            b = base[key]
            row.update({"b5_trial": key, "b5_series_identical": b["series_sha256"] == hs, "b5_post_identical": b["post_sha256"] == r["post_sha256"],
                        "b5_start_identical": b["start_sha256"] == r["start_sha256"], "b5_half_rounds": b["half_rounds"]})
            if b["series_sha256"] != hs:
                row["b5_first_differing_index"] = next((i for i, (x, y) in enumerate(zip(b["series_sha256"], hs)) if x != y), min(len(hs), len(b["series_sha256"])))
        checks = [v for k, v in row.items() if k in ("plain_series_identical", "plain_post_identical", "b5_series_identical", "b5_post_identical")]
        row["compared_against"] = [k for k in ("plain", "b5") if any(x.startswith(k + "_series") for x in row)]
        row["inert"] = bool(checks) and all(checks)
        rows.append(row)
    summ = {"hooked_battles": len(rows), "inert": sum(1 for r in rows if r["inert"]), "not_inert": [r["trial"] for r in rows if not r["inert"]],
            "with_plain_comparison": sum(1 for r in rows if "plain_trial" in r), "with_b5_comparison": sum(1 for r in rows if "b5_trial" in r),
            "baseline_file": base_path.name if base_path else None, "series_files_compared": sum(r["half_rounds"] for r in rows)}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    C.write_new(C.DATA, "inertness-%s.json" % stamp, json.dumps({"summary": summ, "rows": rows}, indent=1))
    cols = sorted({k for r in rows for k in r})
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    C.write_new(C.DATA, "inertness-%s.csv" % stamp, buf.getvalue())
    print(json.dumps(summ, indent=1))
    return summ


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("baseline", "inertness"):
        sys.exit(__doc__)
    baseline(*a[1:2]) if a[0] == "baseline" else inertness(*a[1:2])
