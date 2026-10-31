#!/usr/bin/env python3
"""AI army decisions, original vs remake main, on equal states (owner, 2026-10-30: "a round of comparing the AI decisions with
the remake code", option 1: run both, then read the code where they disagree).

Original: difftest/probes/decide_hook_run.py (patches/decide_hook.py) logs every input of F31C's branch, per army and AI round,
from 16 New Game starts (seed 12345, the human seat gives no orders). Remake: for AI round t, the remake imports the ORIGINAL's
own autosave from just before that round (the start save for t = 1, else the hooked run's autosave after round t-1) and plays
one End turn with `RemakeAdapter aiprobe ... decisions=<file>` (its own AiArmyTargetTree.DecisionRecord log). So every round
starts from the same state; within a round, seats act in turn, and an army whose position differs at its decision is
reported as "state" (an earlier seat's round already differs), not as a rule difference.

    python3 runs/experiments/aidecide/compare.py remake <orig_dir> <remake_short> <out_dir>
    python3 runs/experiments/aidecide/compare.py compare <orig_dir> <remake_out_dir> <report.json>
"""
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
from state.sav import load  # noqa: E402
import decide_hook as DH  # noqa: E402

DOTNET = Path.home() / ".dotnet/dotnet"
NATIONS = ["rome", "carthage", "seleucid", "ptolemaic", "macedonia", "numidia", "gaul", "greece", "celtiberia", "illyria",
           "dacia", "bithynia", "galatia", "armenia", "media", "thracia"]
KIND = {"army>100": "AttackArmy", "city>100": "AttackCity", "resupply": "MoveToResupplyCity", "e84c+army>70": "MercenaryRun",
        "e84c+city>85": "MercenaryRun", "e84c": "MercenaryRun"}


def starts(orig):
    return sorted(p.parent for p in orig.glob("*/inert.json"))


def round_start(start_dir, t):
    """The save the original's AI round t starts from."""
    inert = json.loads((start_dir / "inert.json").read_text())
    if t == 1:
        return Path(inert["start"]) if Path(inert["start"]).is_absolute() else ROOT / inert["start"]
    return start_dir / inert["hooked"]["saves"][t - 2]["file"]


def remake(orig, short, out):
    out.mkdir(parents=True, exist_ok=True)
    build = ROOT / f"artifacts/diffpin-{short}-build/adapter/bin/RemakeAdapter/release/RemakeAdapter.dll"
    clone = Path.home() / f"projects/ic2-remake-pin-{short}"
    for d in starts(orig):
        turns = json.loads((d / "inert.json").read_text())["turns"]
        for t in range(1, turns + 1):
            dec = out / f"{d.name}-t{t:02d}-decisions.jsonl"
            rel = out / f"{d.name}-t{t:02d}-relations.json"
            if dec.exists():
                continue
            p = subprocess.run([DOTNET, build, "aiprobe", clone, round_start(d, t), "1", out / f"{d.name}-t{t:02d}-probe.jsonl",
                                "seed=12345", f"decisions={dec}", f"relations={rel}",
                                f"ailog={out / f'{d.name}-t{t:02d}-ailog.txt'}", f"events={out / f'{d.name}-t{t:02d}-events.jsonl'}"], capture_output=True, text=True,
                               env=dict(os.environ, DOTNET_ROOT=str(DOTNET.parent)))
            if p.returncode:
                (out / f"{d.name}-t{t:02d}-error.txt").write_text(p.stdout + p.stderr)
            print(d.name, t, "ok" if not p.returncode else "ERROR", flush=True)


def round_end(start_dir, t):
    inert = json.loads((start_dir / "inert.json").read_text())
    return start_dir / inert["hooked"]["saves"][t - 1]["file"]


def wars_of(save, nation):
    """The nations `nation` (a lower-case id) is at war with in an original save (relation 3)."""
    for n in save["nations"]:
        if n["name"].lower() == nation:
            return {k.lower() for k, v in n["relations"].items() if v == 3}
    return set()


def originals(orig, d):
    rows = [json.loads(l) for l in (orig / f"{d.name}-decide.jsonl").read_text().splitlines()]
    by = defaultdict(list)
    for r in rows:
        by[r["turn"]].append(r)
    out = defaultdict(list)
    for t, rs in by.items():
        for i, r in enumerate(rs):
            if r["kind"] != "inputs":
                continue
            nxt = rs[i + 1] if i + 1 < len(rs) else None
            a698 = nxt["a698"] if nxt and nxt["kind"] == "resupply" and nxt["army"] == r["army"] else None
            r = dict(r, a698=a698)
            try:
                r["branch"] = DH.branch(r, a698)
            except ValueError:
                r["branch"] = "?"
            out[t].append(r)
    return out


def compare(orig, rdir, report):
    rows, counts = [], Counter()
    for d in starts(orig):
        od = originals(orig, d)
        for t, recs in sorted(od.items()):
            save = load(round_start(d, t))
            end = load(round_end(d, t))
            relf = rdir / f"{d.name}-t{t:02d}-relations.json"
            rrel = json.loads(relf.read_text()) if relf.exists() else None
            decf = rdir / f"{d.name}-t{t:02d}-decisions.jsonl"
            rem = [json.loads(l) for l in decf.read_text().splitlines()] if decf.exists() else []
            probef = rdir / f"{d.name}-t{t:02d}-probe.jsonl"
            aims = {}
            for l in (probef.read_text().splitlines() if probef.exists() else []):
                x = json.loads(l)
                aims.setdefault(x["army"], (x["why"], x["aim"]))
            ailf = rdir / f"{d.name}-t{t:02d}-ailog.txt"
            capdef = set()                      # armies the remake's capital defence dispatched this round
            for l in (ailf.read_text().splitlines() if ailf.exists() else []):
                m_ = l.split("\t", 1)[-1]
                if m_.startswith("capital defence: army-"):
                    capdef.add((l.split("\t", 1)[0], m_.split()[2]))
            first = {}
            for r in rem:                       # the first record per army is the decision; later ones re-evaluate
                first.setdefault(r["ArmyId"], r)
            used = set()
            battle_before = False             # an attack within reach (distance <= moves + 1) decided earlier in the round
            for o in recs:
                if o["branch"] in ("army>100", "city>100") and (o["army_dist"] if o["branch"] == "army>100" else o["city_dist"]) <= o["moves"] + 1:
                    battle_seq = o["seq"]
                else:
                    battle_seq = None
                key = f"army-{o['army']}"
                if key in used:                # the original decides each army once per round
                    continue
                used.add(key)
                m = first.get(key)
                if m is None or m["NationId"] != NATIONS[o["nation"]]:
                    # a slot reused after a death (swap-remove, #117): the remake keeps the import id
                    m = next((r for r in first.values() if r["NationId"] == NATIONS[o["nation"]]
                              and (r["ArmyX"], r["ArmyY"]) == (o["x"], o["y"])), None)
                city = save["cities"][o["city"]] if 0 <= o["city"] < len(save["cities"]) else None
                row = {"start": d.name, "turn": t, "nation": NATIONS[o["nation"]], "army": o["army"],
                       "orig": {k: o[k] for k in ("x", "y", "moves", "supplies", "morale", "home", "city", "city_score",
                                                  "city_dist", "target", "army_score", "army_dist", "a698", "branch")},
                       "orig_city_xy": [city["x"], city["y"]] if city else None}
                row["remake_capdef"] = (NATIONS[o["nation"]], key) in capdef
                if m is None:
                    why, aim = aims.get(key, (None, None))
                    row["remake_why"] = why
                    if o["branch"] == "e84c" and why in ("garrison fallback", None):
                        row["verdict"] = "same-unlogged"   # no offer, no continuation: FUN_0044ebe8 / the garrison fallback
                    else:
                        row["verdict"] = "no-remake-decision"
                else:
                    row["remake"] = {k: m[k] for k in ("ArmyX", "ArmyY", "Kind", "TargetCityId", "TargetCityX", "TargetCityY",
                                                       "TargetArmyId", "CityScore", "ArmyScore", "CityDistance", "ArmyDistance",
                                                       "Skipped")}
                    diffs = []
                    if (m["ArmyX"], m["ArmyY"]) != (o["x"], o["y"]):
                        row["verdict"] = "state"
                    else:
                        oc = row["orig_city_xy"] or [-1, -1]
                        if [m["TargetCityX"], m["TargetCityY"]] != oc:
                            diffs.append("city-target")
                        if m["CityScore"] != o["city_score"] and o["city"] != -1:
                            diffs.append("city-score")
                        if (m["TargetArmyId"] or "army--1") != f"army-{o['target']}" and o["army_score"] != -10000:
                            diffs.append("army-target")
                        if m["ArmyScore"] != o["army_score"] and o["army_score"] != -10000:
                            diffs.append("army-score")
                        if m["Kind"] != KIND.get(o["branch"]):
                            diffs.append("branch")
                        elif o["branch"] == "resupply":     # the destination: the original's home city vs the remake's aim
                            home = save["cities"][o["home"]] if 0 <= o["home"] < len(save["cities"]) else None
                            row["orig_home_xy"] = [home["x"], home["y"]] if home else None
                            why, aim = aims.get(key, (None, None))
                            row["remake_aim"] = aim
                            if aim is not None and aim != row["orig_home_xy"]:
                                diffs.append("resupply-city")
                        row["verdict"] = "same" if not diffs else "differs"
                        nat = row["nation"]
                        w0, w1 = wars_of(save, nat), wars_of(end, nat)
                        rw = {k for k, v in (rrel or {}).get(nat, {}).items() if v == 3} if rrel is not None else None
                        row["wars"] = {"orig_start": sorted(w0), "orig_end": sorted(w1), "remake_end": sorted(rw) if rw is not None else None}
                        if diffs and (w0 != w1 or (rw is not None and rw != w1)):
                            row["verdict"] = "diplomacy"   # the nation's wars changed in the round, or differ at its end
                        row["diffs"] = diffs
                if row["verdict"] == "differs" and set(row["diffs"]) & {"army-target", "army-score", "city-target", "city-score"}:
                    if battle_before:
                        row["verdict"] = "state-battle"  # an attack earlier in the round: battle results are random draws
                    elif len(end["armies"]) < len(save["armies"]):
                        row["verdict"] = "state-death"   # armies died in the original's round (by an order this log does not cover)
                if battle_seq is not None:
                    battle_before = True
                counts[row["verdict"]] += 1
                for x in row.get("diffs", []):
                    counts["diff:" + x] += 1
                rows.append(row)
    with open(report, "x") as f:
        json.dump({"counts": dict(counts), "rows": rows}, f, indent=1)
    print(dict(counts))


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "remake":
        remake(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    else:
        compare(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
