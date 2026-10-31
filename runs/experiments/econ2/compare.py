#!/usr/bin/env python3
"""The rest of #176, original vs remake main, per seat (owner 2026-10-31): the army phase's supply and hire pass FUN_0044e41c,
the unit consolidation FUN_00450858, the army and fleet merges FUN_004509f0 / FUN_00450b30 and the fleet order FUN_00450768.

Original: difftest/probes/fleetphase_hook_run.py with IC2_FLEET_HOOK=econ2_hook IC2_HOOK_LOG=econ2 (patches/econ2_hook.py).
Remake: the same rounds from those autosaves (the AI logs of runs/experiments/aidecide/compare.py remake), lines
  resupply: N army transfers, F fleet transfers, T tons, P talents
  mercenary hire: N offer(s) hired across M army/armies
  faithful consolidate: joined|disbanded army-N slot S
  faithful merge: army A into B   /   faithful merge: fleet A into B
  faithful fleet order: N ships at CITY (fleet-N)

Per seat:
  transfers   original: FUN_0044f6d8 calls that changed the army's supplies or money (the remake counts a visit that changed
              anything, AiResupplyPass.Declines); tons = the supplies added; talents = the money paid at FOREIGN cities (the
              owner from the round-start save; an own city moves the purse to or from the treasury, which the remake does not
              log)
  hires       offers taken, armies that took one
  consolidate joins and disbands (FUN_0044ac3c calls from FUN_00450858: a disband is the slot of a mercenary unit)
  merges      army merges (FUN_0044acb4 calls from FUN_004509f0, one per donor), fleet merges (FUN_0044ad38 from FUN_00450b30)
  fleet order FUN_0044a004 calls from FUN_00450768

    python3 runs/experiments/econ2/compare.py <orig_dir> <remake_dir> <saves_dir> <out.json>
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs/experiments/aidecide"))
from state.sav import load  # noqa: E402
import compare as AD  # noqa: E402

NATIONS = AD.NATIONS
RANGES = {"consolidate": (0x450858, 0x4509F0), "army-merge": (0x4509F0, 0x450B30), "fleet-merge": (0x450B30, 0x450C68),
          "fleet-order": (0x450768, 0x450858)}
RES = re.compile(r"resupply: (-?\d+) army transfers, (-?\d+) fleet transfers, (-?\d+) tons, (-?\d+) talents")
HIRE = re.compile(r"mercenary hire: (\d+) offer\(s\) hired across (\d+) army")
CONS = re.compile(r"faithful consolidate: (joined|disbanded) (army-\d+) slot (\d+)")
MERGE = re.compile(r"faithful merge: (army|fleet) (\S+) into (\S+)")
FORDER = re.compile(r"faithful fleet order: (\d+) ships at (\S+)")


def within(addr, name):
    lo, hi = RANGES[name]
    return lo <= addr < hi


def original_seats(rows, owners_by_turn):
    seats = defaultdict(lambda: {"transfers": 0, "tons": 0, "talents": 0, "own_purse": 0, "hires": 0, "hire_armies": set(),
                                 "joined": 0, "disbanded": 0, "army_merges": set(), "fleet_merges": 0, "fleet_orders": 0})
    by_turn = defaultdict(list)
    for r in rows:
        by_turn[r["turn"]].append(r)
    for t, recs in by_turn.items():
        owners = owners_by_turn.get(t, {})
        for i, r in enumerate(recs):
            s = seats[(t, NATIONS[r["nation"]])]
            k = r["kind"]
            if k == "transfer":
                nxt = next((x for x in recs[i + 1:] if x["kind"] in ("transfer", "e41c-out") and x["army"] == r["army"]), None)
                if nxt is None:
                    continue
                ds, dm = nxt["supplies"] - r["supplies"], nxt["money"] - r["money"]
                if ds or dm:
                    s["transfers"] += 1
                s["tons"] += ds
                if owners.get(r["city"]) == r["nation"]:
                    s["own_purse"] += dm
                else:
                    s["talents"] -= dm
            elif k == "hire":
                s["hires"] += 1
                s["hire_armies"].add(r["army"])
            elif k == "remove-slot" and within(r["caller"], "consolidate"):
                s["disbanded" if r["merc"] > 0 else "joined"] += 1
            elif k == "move-slot" and within(r["caller"], "army-merge"):
                s["army_merges"].add((r["src"], r["dst"]))
            elif k == "delete-fleet" and within(r["caller"], "fleet-merge"):
                s["fleet_merges"] += 1
            elif k == "fleet-order" and within(r["caller"], "fleet-order"):
                s["fleet_orders"] += 1
    out = {}
    for key, s in seats.items():
        out[key] = {"transfers": s["transfers"], "tons": s["tons"], "talents": s["talents"], "own_purse": s["own_purse"],
                    "hires": s["hires"], "hire_armies": len(s["hire_armies"]), "joined": s["joined"], "disbanded": s["disbanded"],
                    "army_merges": len(s["army_merges"]), "fleet_merges": s["fleet_merges"], "fleet_orders": s["fleet_orders"]}
    return out


def remake_seats(ailog):
    seats = {}
    for line in (ailog.read_text().splitlines() if ailog.exists() else []):
        nation, _, text = line.partition("\t")
        s = seats.setdefault(nation, {"transfers": 0, "tons": 0, "talents": 0, "hires": 0, "hire_armies": 0, "joined": 0,
                                      "disbanded": 0, "army_merges": 0, "fleet_merges": 0, "fleet_orders": 0, "seen": False})
        if m := RES.search(text):
            s.update(transfers=int(m[1]), tons=int(m[3]), talents=int(m[4]), seen=True)
        elif m := HIRE.search(text):
            s.update(hires=int(m[1]), hire_armies=int(m[2]))
        elif m := CONS.search(text):
            s[m[1]] += 1
        elif m := MERGE.search(text):
            s["army_merges" if m[1] == "army" else "fleet_merges"] += 1
        elif FORDER.search(text):
            s["fleet_orders"] += 1
    return {n: s for n, s in seats.items() if s.pop("seen")}


ITEMS = ["transfers", "tons", "talents", "hires", "hire_armies", "joined", "disbanded", "army_merges", "fleet_merges",
         "fleet_orders"]


def main():
    orig, rdir, saves, out = (Path(a) for a in sys.argv[1:5])
    rows_out, per_item, verdicts = [], Counter(), Counter()
    for f in sorted(orig.glob("*-econ2.jsonl")):
        start = f.name[:-len("-econ2.jsonl")]
        d = saves / start
        if not (d / "inert.json").exists():
            continue
        owners = {}
        for t in range(1, 6):
            st = load(AD.round_start(d, t))
            owners[t] = {i: c["owner"] for i, c in enumerate(st["cities"])}
        recs = [json.loads(l) for l in f.read_text().splitlines()]
        o = original_seats(recs, owners)
        for t in sorted({r["turn"] for r in recs}):
            rem = remake_seats(rdir / f"{start}-t{t:02d}-ailog.txt")
            for nation, r in rem.items():
                a = o.get((t, nation))
                if a is None:
                    a = {k: 0 for k in ITEMS}
                diff = [k for k in ITEMS if a[k] != r[k]]
                for k in ITEMS:
                    per_item[(k, k not in diff)] += 1
                verdicts["same" if not diff else "differs"] += 1
                rows_out.append({"start": start, "turn": t, "nation": nation, "diff": diff, "orig": a, "remake": r})
    summary = {k: {"same": per_item[(k, True)], "differs": per_item[(k, False)]} for k in ITEMS}
    with open(out, "x") as fh:
        json.dump({"verdicts": dict(verdicts), "items": summary, "rows": rows_out}, fh, indent=1)
    print(dict(verdicts))
    for k, v in summary.items():
        print(f"  {k:12s} {v}")


if __name__ == "__main__":
    main()
