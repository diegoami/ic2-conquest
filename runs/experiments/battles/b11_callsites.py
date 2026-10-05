#!/usr/bin/env python3
"""B11 call-site table: for each of the 14 hooked `Random` sites and each marker / boundary hook, what the game did in every hooked battle of the data folder.

    python3 runs/experiments/battles/b11_callsites.py [--rep 1]

Reads `hooklog-<trial>.csv` of the ok hooked trials (rep given; default 1) and `trials-b11.jsonl`; writes `callsites-<stamp>.csv` and `.json` (tracked, never overwritten):
per site: module, purpose [R-code, the report's draw order], battles with at least one record, total records, the argument (EAX = the range) seen: min, max and the distinct
values for the fixed-range sites (5, 4, 3), and the half-round phase (counter 0 = before the first half-round; the melee / moves split by the melee marker).
"""
import csv
import io
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402
import b11_exchange as X  # noqa: E402

C = B.C
PURPOSE = {
    0x43801A: ("TBattleMap", "copy-in, attacker slots 0..19: Random(quality*4) per live slot (morale = clamp(draw + army morale, 60, 90))"),
    0x43812F: ("TBattleMap", "copy-in, defender slots 20..39: Random(quality*4) per live slot"),
    0x43820D: ("TBattleMap", "AI placement: Random(5) picks the formation row of the side (one per computer-controlled side's placement half-round)"),
    0x438FFB: ("TBattleMap", "Rout(u) test, first draw Random(morale), only when troops >= floor and 20 <= morale <= 39"),
    0x439006: ("TBattleMap", "Rout(u) test, second draw Random(morale)"),
    0x439188: ("TBattleMap", "shot (FUN_0043910C), first draw Random(n)"),
    0x439191: ("TBattleMap", "shot, second draw Random(n); loss = sum of the two"),
    0x439557: ("TBattleMap", "melee (FUN_004393EC), attacker's first draw Random(nA)"),
    0x43955F: ("TBattleMap", "melee, attacker's second draw Random(nA)"),
    0x4395CE: ("TBattleMap", "melee, defender's first draw Random(nD)"),
    0x4395D8: ("TBattleMap", "melee, defender's second draw Random(nD)"),
    0x43AA88: ("TBattleMap", "AI general, flank step (pass 3): Random(3) = 0 flips the horizontal direction"),
    0x4592BD: ("TBattleOver_OK", "after the battle: promotion Random(4) per surviving winner unit (0 = quality + 1)"),
    0x45951C: ("TBattleOver_OK", "after the battle: the peace test Random(5) (< 2 opens the Offer of peace box)"),
}
HOOKS = {X.MARK_SHOT: "marker: entry of the shot routine FUN_0043910C (EAX shooter slot, EDX target slot)", X.MARK_MELEE: "marker: entry of the melee pass FUN_004393EC (no arguments)",
         X.MARK_ROUT: "marker: entry of Rout FUN_00438FB0 (EAX the slot)", 0x437B8C: "boundary: `mov byte [0x4A0B7C],0` in the end-of-battle routine called from 0x439CDE",
         0x45C21F: "boundary: `mov byte [0x4A0B7C],0` in TPremierForm's clean-up (0x45C208)", 0x457907: "boundary before the reseed RandSeed := a + b in the TBattlePols unit",
         0x450C7B: "boundary before the reseed RandSeed := a + b in the function at 0x450C68"}


def main():
    a = sys.argv[1:]
    rep = int(a[a.index("--rep") + 1]) if "--rep" in a else 1
    tags = []
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "ok" and r.get("variant") == "hook" and r.get("rep") == rep and r["trial"] not in tags:
                tags.append(r["trial"])
    per_site = defaultdict(lambda: {"battles": 0, "records": 0, "ranges": Counter(), "phases": Counter()})
    hook_stats = defaultdict(lambda: {"battles": 0, "records": 0})
    for tag in tags:
        p = C.DATA / ("hooklog-%s.csv" % tag)
        if not p.exists():
            continue
        recs = X.load_log(p)
        seen, seen_hook = set(), set()
        melee_seen = {}
        for r in recs:
            if r["kind"] == "marker" and r["site"] == X.MARK_MELEE:
                melee_seen[r["counter"]] = True
            if r["kind"] == "random":
                d = per_site[r["site"]]
                d["records"] += 1
                d["ranges"][r["eax"]] += 1
                ph = "pre-battle" if r["counter"] == 0 else "melee phase" if melee_seen.get(r["counter"]) else "moves phase"
                if r["site"] in X.S_POST:
                    ph = "post-battle"
                if r["site"] == X.S_PLACE:
                    ph = "placement half-round"
                d["phases"][ph] += 1
                seen.add(r["site"])
            elif r["kind"] in ("marker", "flag_clear", "reseed"):
                hook_stats[r["site"]]["records"] += 1
                seen_hook.add(r["site"])
        for s in seen:
            per_site[s]["battles"] += 1
        for s in seen_hook:
            hook_stats[s]["battles"] += 1
    rows = []
    for va, (mod, purpose) in PURPOSE.items():
        d = per_site[va]
        rg = sorted(d["ranges"])
        rows.append({"site": hex(va), "module": mod, "purpose_R_code": purpose, "battles_with_a_record": d["battles"], "records": d["records"],
                     "range_min": rg[0] if rg else "", "range_max": rg[-1] if rg else "", "range_distinct": len(rg), "fixed_range_value": rg[0] if len(rg) == 1 else "",
                     "phases": ";".join("%s=%d" % kv for kv in sorted(d["phases"].items()))})
    for va, what in HOOKS.items():
        d = hook_stats[va]
        rows.append({"site": hex(va), "module": "hook", "purpose_R_code": what, "battles_with_a_record": d["battles"], "records": d["records"], "range_min": "", "range_max": "",
                     "range_distinct": "", "fixed_range_value": "", "phases": ""})
    stamp = time.strftime("%Y%m%d-%H%M%S")
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    C.write_new(C.DATA, "callsites-%s.csv" % stamp, buf.getvalue())
    C.write_new(C.DATA, "callsites-%s.json" % stamp, json.dumps({"battles": len(tags), "rep": rep, "rows": rows}, indent=1))
    print(len(tags), "battles")
    for r in rows:
        print("%-9s %-15s battles %3s records %6s range %s..%s  %s" % (r["site"], r["module"], r["battles_with_a_record"], r["records"], r["range_min"], r["range_max"], r["phases"]))


if __name__ == "__main__":
    main()
