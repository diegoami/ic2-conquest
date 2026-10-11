#!/usr/bin/env python3
"""Check 7 of the v0.5.0 gap analysis (rows_g2.md): a fleet carrying an army damaged in a storm, the army's troops before and after.
No new Wine run: the cell R85sA of `run-exp-storms` (findings/2026-10-03-storms-and-losses-at-sea.md; Carthage fleet 0, 90 ships, condition 85,
rough sea, Spring, army 2 aboard (a synthetic cargo), seeds 1-5, one storm each; the fleet is damaged and NOT sunk) already holds the case.
This script re-reads, read-only: the fixture FIX_T4_R85sA.SAV (before) and ST_R85sA_seed1_AUTO0721.SAV (after, seed 1) from the main checkout's
artifacts/run-exp-storms/ (hashes checked against run-exp-storms/SAVES.sha256), and the five seeds' after-state from t4_trials.json (the only
record of seeds 2-5: those saves were not kept). It also recomputes the army-damage routine of the pinned decompile (FUN_0044b4f8 -> FUN_0044ae20)
for the observed fleet losses. Writes c7_storm_reanalysis.json and c7_storm_reanalysis.txt beside it."""
import hashlib, json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from state import sav
SRC = Path("/home/diego/projects/ic2-conquest/artifacts/run-exp-storms")
D = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
want = {}
for line in (R / "runs/experiments/data/run-exp-storms/SAVES.sha256").read_text().splitlines():
    h, n = line.split(); want[n] = h
out = {"files": {}}
for name in ("FIX_T4_R85sA.SAV", "ST_R85sA_seed1_AUTO0721.SAV"):
    p = SRC / name
    out["files"][name] = {"sha256": sha(p), "matches_run_exp_storms_SAVES.sha256": want.get(name) == sha(p)}
before = sav.parse((SRC / "FIX_T4_R85sA.SAV").read_bytes()); after = sav.parse((SRC / "ST_R85sA_seed1_AUTO0721.SAV").read_bytes())


def summ(s, i):
    a = s["armies"][i]; return {"id": i, "owner": a["owner"], "troops": a["troops"], "moves": a["moves"], "units": [(u["type"], u["troops"], u.get("label")) for u in a["units"] if u["troops"]]}


out["before_FIX_T4_R85sA"] = {"army2": summ(before, 2), "fleet0": before["fleets"][0], "turn": before["turn"]}
out["after_seed1"] = {"army2": summ(after, 2), "fleet0": after["fleets"][0], "turn": after["turn"]}
trials = [t for t in json.load(open(R / "runs/experiments/data/run-exp-storms/t4_trials.json")) if t["cell"] == "R85sA"]
rows = []
for t in trials:
    a2 = [a for a in (t.get("carthage_armies_after") or []) if a[0] == 2]
    rows.append({"seed": t["seed"], "fleet_before": (t["before"]["ships"], t["before"]["condition"], t["before"]["army"]),
                 "fleet_after": ((t["after"] or {}).get("ships"), (t["after"] or {}).get("condition"), (t["after"] or {}).get("army")),
                 "news": t["news"], "army2_after": a2[0] if a2 else None})
out["trials_R85sA"] = rows
# the decompile's rule, applied to the observed ship losses: FUN_0044b4f8(fleet, 100, dmg + 100): x = max(1, 100*100/(dmg+100)); d = x*x/100; ships and condition -= value*d/300;
# FUN_0044ae20(army, d): each of the 20 slots: troops -= (troops / (rand(15) + 105)) * d; then a regular unit under size_limit/10 (mercenary: /5) is removed;
# if d > 70: (units*d)/250 + 1 further random slots are removed (FUN_0044ac3c).
lim = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}
sim = []
for dmg in range(6, 14):
    x = max(1, 10000 // (dmg + 100)); d = x * x // 100
    ships = 90 - (90 * d) // 300
    per = {}
    for ty, tr in [(u["type"], u["troops"]) for u in before["armies"][2]["units"] if u["troops"]]:
        lo, hi = tr - (tr // (14 + 105)) * d, tr - (tr // 105) * d
        per[f"{ty}{tr}"] = (lo, hi, lo < lim[ty] // 10 or hi < lim[ty] // 10)
    sim.append({"storm_dmg": dmg, "d": d, "ships_after": ships, "units_after_troops_range_(rand=14..0)_and_below_limit/10": per, "random_whole_unit_removals": (len(per) * d) // 250 + 1 if d > 70 else 0})
out["decompile_rule_recomputed"] = sim
(D / "c7_storm_reanalysis.json").write_text(json.dumps(out, indent=1, default=str))
lines = []
lines.append("army 2 before (FIX_T4_R85sA.SAV, turn %s): %s troops, units %s" % (out["before_FIX_T4_R85sA"]["turn"], out["before_FIX_T4_R85sA"]["army2"]["troops"], out["before_FIX_T4_R85sA"]["army2"]["units"]))
lines.append("fleet 0 before: %s" % out["before_FIX_T4_R85sA"]["fleet0"])
lines.append("seed 1 after (ST_R85sA_seed1_AUTO0721.SAV, turn %s): army 2 %s ; fleet 0 %s" % (out["after_seed1"]["turn"], out["after_seed1"]["army2"], out["after_seed1"]["fleet0"]))
for r in rows: lines.append("seed %(seed)d fleet (ships,condition,army) %(fleet_before)s -> %(fleet_after)s ; army 2 after: %(army2_after)s ; %(news)s" % r)
for s in sim: lines.append(json.dumps(s))
(D / "c7_storm_reanalysis.txt").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
