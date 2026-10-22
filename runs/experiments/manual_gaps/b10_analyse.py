#!/usr/bin/env python3
"""B10 analysis: per fleet and turn, (ships, condition) before -> after from b10-storms.jsonl, the sea under the fleet from the
kept autosaves (fleet +24, 0 calm / 1 rough), and the code's prediction for each storm branch (docs/rules-digest.md §8):

    dmg0 = max(1, Random(100 - c) // 10); Winter: min(5, 2*dmg0); rough: min(8, 3*dmg); away from own cities: 2*dmg + 1,
    and in Winter 1 in 20: dmg = 30. dmg < 6: condition -= dmg; else d = (10000 // (dmg + 100))**2 // 100 and ships, condition
    each lose (x * d) // 300.

    python3 runs/experiments/manual_gaps/b10_analyse.py > runs/experiments/data/run-exp-manual-gaps/b10-table.v1.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import sav  # noqa: E402
from mg import DATA, SAVES  # noqa: E402


def big(x, dmg):
    d = (10000 // (dmg + 100)) ** 2 // 100
    return x * d // 300


def outcomes(ships, cond, rough):
    """{(dships, dcond): label} for every dmg0 the draw can give, plus the spike."""
    out = {}
    for r in range(max(1, 100 - cond)):
        dmg = max(1, r // 10)
        dmg = min(5, 2 * dmg)
        if rough:
            dmg = min(8, 3 * dmg)
        dmg = 2 * dmg + 1
        key = (0, dmg) if dmg < 6 else (big(ships, dmg), big(cond, dmg))
        out.setdefault(key, f"dmg {dmg}")
    out[(big(ships, 30), big(cond, 30))] = "SPIKE dmg 30"
    return out


def main():
    rows = [json.loads(l) for l in (DATA / "b10-storms.jsonl").open()]
    by_seed = {}
    for r in rows:
        by_seed.setdefault(r["seed"], []).append(r)
    print("| seed | turn (after) | fleet | sea | before (ships, cond) | after | loss | matches |")
    print("|---|---|---|---|---|---|---|---|")
    spikes = n = 0
    for seed, rs in by_seed.items():
        rs = [r for r in rs if r.get("phase") == "start" or "k" in r]
        for prev, cur in zip(rs, rs[1:]):
            if "k" not in cur:
                continue
            s = sav.load(SAVES / f"MG_B10_seed{seed}_{cur['autosave']}")
            p_save = SAVES / f"MG_B10_seed{seed}_{prev['autosave']}" if "autosave" in prev else SAVES / "MG_B10_staged_6_rome_fleets_at_sea_winter_270.SAV"
            ps = sav.load(p_save)
            for a, b in zip(prev["state"], cur["state"]):
                if a["owner"] < 0:
                    continue
                sea0, sea1 = ps["fleets"][a["id"]]["cell"], s["fleets"][a["id"]]["cell"]
                sea = f"{sea0}->{sea1}"
                loss = (a["ships"] - b["ships"], a["condition"] - b["condition"]) if b["owner"] >= 0 else "LOST"
                oc = {k: "rough " + v for k, v in outcomes(a["ships"], a["condition"], True).items()}
                oc.update({k: "calm " + v for k, v in outcomes(a["ships"], a["condition"], False).items()})
                oc[(big(a["ships"], 30), big(a["condition"], 30))] = "SPIKE dmg 30"
                # supplies out: an extra -Random(2) on condition; none here (400 supplies, 50 a turn)
                m = oc.get(loss, "?") if loss != "LOST" else "lost"
                n += 1
                spikes += m.startswith("SPIKE")
                print(f"| {seed} | {cur['turn']} | {a['id']} | {sea} | "
                      f"({a['ships']}, {a['condition']}) | ({b['ships']}, {b['condition']}) | {loss} | {m} |")
    print(f"\nfleet-turns: {n}; spikes: {spikes}")


if __name__ == "__main__":
    main()
