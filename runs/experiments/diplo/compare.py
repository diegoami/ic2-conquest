#!/usr/bin/env python3
"""AI diplomacy decisions, original vs remake main, on equal round-start states (owner 2026-10-30).

Original: difftest/probes/diplo_hook_run.py (patches/diplo_hook.py) logs every relation-setter call with its caller, plus the
AI diplomacy phase FUN_0044fb7c's war candidate and its two rolls (Random(10) war, Random(20) alliance search). Remake: the
same rounds replayed from the original's own autosaves (`RemakeAdapter aiprobe ... ailog= events=`), its AI lines and its
diplomacy/peace domain events.

Per seat, both sides become a list of actions:
  ("trade", partner)            FUN_0044fb7c loop 1 (0x44FD0C) or loop 3 (0x44FEEF) / remake ai-form-trade
  ("swap", poorer, richer)      the swap pair 0x44FF7E + 0x44FF8F / remake ai-swap-trade-partner
  ("alliance", partner)         0x44FE5A / remake ai-form-alliance
  ("war", target)               0x44FD47 / remake declare-war
  ("treaty", winner, loser)     FUN_00450c68 after an AI-AI instant battle / remake Peace* events
Each round is walked in seat order; the first seat whose actions differ is classified:
  draw        the actions differ only where one side's chance roll hit (war or alliance) and the other's did not, or the
              war target is the original's own candidate (so only the roll can differ)
  battle      the difference is a treaty (Random(5) after a battle whose result is itself a draw)
  deterministic   a trade or swap differs while no earlier seat of the round differed
Every later differing seat of that round is "after divergence".

    python3 runs/experiments/diplo/compare.py <orig_dir> <remake_dir> <report.json>
With the diagnostic build's <stem>-war.txt beside the logs, the war candidates of the seats before each round's first
divergence are compared too (the original's 0x44FD22 record vs the remake's BestWarTarget).
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

NATIONS = ["rome", "carthage", "seleucid", "ptolemaic", "macedonia", "numidia", "gaul", "greece", "celtiberia", "illyria",
           "dacia", "bithynia", "galatia", "armenia", "media", "thracia"]
IDX = {n: i for i, n in enumerate(NATIONS)}
CHOSE = re.compile(r"chose \[(?:Diplomacy|Military)/(?P<kind>[a-z-]+)\].*? -- (?P<why>.*)$")


def original_seats(rows):
    """{nation: {"actions": [...], "candidate": int, "war_hit": bool|None, "alliance_hit": bool|None}} in seat order."""
    seats = {}
    pending_drop = {}
    for r in rows:
        s = seats.setdefault(r["nation"], {"actions": [], "candidate": None, "war_hit": None, "alliance_hit": None})
        k = r["kind"]
        if k == "war_candidate":
            s["candidate"] = r["candidate"]
        elif k == "war_roll":
            s["war_hit"] = r["hit"]
        elif k == "alliance_roll":
            s["alliance_hit"] = r["hit"]
        elif k == "write":
            site = r["site"]
            if site in ("0x44fd0c", "0x44feef"):
                s["actions"].append(("trade", r["b"]))
            elif site == "0x44fd47":
                s["actions"].append(("war", r["b"]))
            elif site == "0x44fe5a":
                s["actions"].append(("alliance", r["b"]))
            elif site == "0x44ff7e":
                pending_drop[r["nation"]] = r["b"]
            elif site == "0x44ff8f":
                s["actions"].append(("swap", pending_drop.pop(r["nation"], None), r["b"]))
            elif r["caller"] == "treaty":
                if r["before"] == 3 and r["state"] <= 0:
                    s["actions"].append(("treaty", min(r["a"], r["b"]), max(r["a"], r["b"])))
                else:
                    s["actions"].append(("treaty-effect", r["a"], r["b"], r["state"]))   # the sues branch's -10s, ally loop
            else:
                s["actions"].append(("other", r["caller"], r["a"], r["b"], r["state"]))
    return seats


def remake_seats(ailog, events):
    seats = {}
    order = []
    lines = ailog.read_text().splitlines() if ailog.exists() else []
    for i, l in enumerate(lines):
        nation, _, text = l.partition("\t")
        s = seats.setdefault(IDX[nation], {"actions": []})
        if nation not in order:
            order.append(nation)
        m = CHOSE.search(text)
        if not m:
            continue
        issued = i + 1 < len(lines) and "issued" in lines[i + 1]
        if not issued:
            continue
        kind, why = m["kind"], m["why"]
        if kind == "ai-form-trade":
            s["actions"].append(("trade", IDX[why.split()[2].rstrip(":")]))
        elif kind == "ai-swap-trade-partner":
            w = why.split()
            s["actions"].append(("swap", IDX[w[3]], IDX[w[6]]))
        elif kind == "ai-form-alliance":
            s["actions"].append(("alliance", IDX[why.split()[2].rstrip(":")]))
        elif kind == "declare-war":
            s["actions"].append(("war", IDX[why.split()[3].rstrip(":")]))
    # A seat's events are published before its own AiTurnDecided marker: buffer them until the marker arrives.
    buffered = []
    for l in (events.read_text().splitlines() if events.exists() else []):
        e = json.loads(l)
        if "seat" in e:
            seat = IDX[e["seat"]]
            seats.setdefault(seat, {"actions": []})["actions"].extend(buffered)
            buffered = []
            continue
        t, d = e["type"], e["data"]
        if t == "PeaceTreatyTriggered":                 # the instant resolver's Random(5) < 2 and its two gates passed
            a, b = IDX[d["WinnerNationId"]], IDX[d["LoserNationId"]]
            buffered.append(("treaty", min(a, b), max(a, b)))
    return seats, [IDX[n] for n in order]


def classify(o, r):
    # the treaty's own side effects (the sues branch's -10s, the ally loop) follow from the treaty: not compared
    oa = Counter(tuple(a) for a in o["actions"] if a[0] != "treaty-effect")
    ra = Counter(tuple(a) for a in r["actions"] if a[0] != "treaty-effect")
    if oa == ra:
        return "same", []
    diff = list((oa - ra).elements()) + list((ra - oa).elements())
    kinds = {d[0] for d in diff}
    if kinds & {"treaty", "treaty-effect"}:
        return "battle", diff                      # a treaty differs: Random(5) after a battle that is itself a draw
    rolled = [d for d in diff if d[0] in ("war", "alliance")]
    if rolled:
        # a war or alliance on one side only: the original's roll result decides whether that is a draw
        wars_ok = all(d[0] != "war" or o["candidate"] == d[1] for d in rolled)
        if wars_ok:
            return "draw", diff                    # the seat's other differences follow from it (counts, partners)
        return "war-candidate", diff
    return "deterministic", diff


def main():
    orig, rdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    rows_out, counts, first, cand = [], Counter(), Counter(), Counter()
    for f in sorted(orig.glob("*-diplo.jsonl")):
        start = f.name[:-len("-diplo.jsonl")]
        by_turn = defaultdict(list)
        for l in f.read_text().splitlines():
            r = json.loads(l)
            by_turn[r["turn"]].append(r)
        for t, recs in sorted(by_turn.items()):
            o_seats = original_seats(recs)
            r_seats, order = remake_seats(rdir / f"{start}-t{t:02d}-ailog.txt", rdir / f"{start}-t{t:02d}-events.jsonl")
            warf = rdir / f"{start}-t{t:02d}-war.txt"     # diagnostic build only: the remake's BestWarTarget per call
            r_cand = {}
            for l in (warf.read_text().splitlines() if warf.exists() else []):
                n_, _, tgt = l.split("\t")
                r_cand.setdefault(IDX[n_], -1 if tgt == "-" else IDX[tgt])
            diverged = False
            for n in order:
                o = o_seats.get(n, {"actions": [], "candidate": None, "war_hit": None, "alliance_hit": None})
                r = r_seats.get(n, {"actions": []})
                verdict, diff = classify(o, r)
                if verdict != "same":
                    if diverged:
                        verdict = "after divergence"
                    else:
                        first[verdict] += 1
                        diverged = True
                counts[verdict] += 1
                if n in r_cand and o.get("candidate") is not None and verdict in ("same", "draw") and not (diverged and verdict != "draw"):
                    cand[(o["candidate"] == r_cand[n], o["candidate"] != -1)] += 1
                rows_out.append({"start": start, "turn": t, "nation": NATIONS[n], "verdict": verdict,
                                 "orig": o["actions"], "remake": r["actions"], "diff": diff,
                                 "orig_candidate": o.get("candidate"), "orig_war_hit": o.get("war_hit"),
                                 "orig_alliance_hit": o.get("alliance_hit"), "remake_candidate": r_cand.get(n)})
    with open(out, "x") as fh:
        cand_out = {f"{'match' if k[0] else 'differ'}, {'a candidate' if k[1] else 'none'}": v for k, v in cand.items()}
        json.dump({"seat_counts": dict(counts), "first_divergence": dict(first), "war_candidates_before_divergence": cand_out,
                   "rows": rows_out}, fh, indent=1)
        print("war candidates (seats before the round's first divergence):", cand_out)
    print("seats:", dict(counts))
    print("first divergence per round:", dict(first))


if __name__ == "__main__":
    main()
