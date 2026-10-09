"""Remake v0.5.0 idle-Rome games: per turn, how many AI armies moved (same id, new position), how many are adjacent (Chebyshev 1) to a city
of a nation they are at war with, and how many AI cities are under siege; the same for the original's autosaves (army ids are table
indices there, so 'moved' counts index-matched records of the same owner). Writes ai_movement.json (versioned). python3 ai_movement.py"""
import json, sys
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
from state import sav
D = R / "runs/experiments/data/run-exp-gap-v050"
out = {}
for seed in (1, 2, 3, 10, 11, 12, 14, 12345):
    rows, prev = [], None
    for t in range(81):
        s = json.load(open(R / f"artifacts/run-exp-gap-v050/ai_rome_s{seed}_t{t:03d}.sav"))["save"]["state"]
        ids = [n for n in s["relations"]["nationIds"]]; m = s["relations"]["matrix"]
        war = lambda a, b: m[ids.index(a)][ids.index(b)] == 3
        arm = {a["id"]: a for a in s["armies"] if a["nation"] != "rome" and a["units"]}
        moved = sum(1 for k, a in arm.items() if prev and k in prev and (prev[k]["x"], prev[k]["y"]) != (a["x"], a["y"]))
        near_enemy_city = sum(1 for a in arm.values() if any(c["owner"] and c["owner"] != a["nation"] and war(a["nation"], c["owner"])
                                                             and max(abs(c["x"] - a["x"]), abs(c["y"] - a["y"])) <= 1 for c in s["cities"]))
        rows.append({"t": t, "ai_armies": len(arm), "moved": moved, "adjacent_to_enemy_city": near_enemy_city,
                     "cities_under_siege": sum(c["underSiege"] for c in s["cities"])})
        prev = arm
    out[f"remake_s{seed}"] = rows
OA = R / "artifacts/run-exp-ai-intercept-hunt"
for seed, kind, n in ((12345, "plain", 25), (2, "plain", 40), (10, "hook", 40), (14, "hook", 39)):
    rows, prev = [], None
    files = [R / "saves/run0-start-AUTO0720-seed12345.SAV"] + [OA / f"{kind}_s{seed}_AUTO{720 + t:04d}.SAV" for t in range(1, n + 1)]
    for t, f in enumerate(files):
        s = sav.load(str(f))
        arm = {a["id"]: a for a in s["armies"] if a["troops"] > 0 and a["owner"] != 0}
        rel = lambda a, b: list(s["nations"][a]["relations"].values())[b - (1 if b > a else 0)] if a != b else 0
        moved = sum(1 for k, a in arm.items() if prev and k in prev and prev[k]["owner"] == a["owner"] and (prev[k]["x"], prev[k]["y"]) != (a["x"], a["y"]))
        near = sum(1 for a in arm.values() if any(c["owner"] >= 0 and c["owner"] != a["owner"] and rel(a["owner"], c["owner"]) == 3
                                                  and max(abs(c["x"] - a["x"]), abs(c["y"] - a["y"])) <= 1 for c in s["cities"]))
        rows.append({"t": t, "ai_armies": len(arm), "moved": moved, "adjacent_to_enemy_city": near})
        prev = arm
    out[f"original_s{seed}"] = rows
p = D / "ai_movement.json"; k = 1
while p.exists(): k += 1; p = D / f"ai_movement.v{k}.json"
p.write_text(json.dumps(out, indent=1)); print(p.name)
for k, rows in out.items():
    r = rows[1:]
    print(k, "moved/turn %.1f of %.1f armies" % (sum(x["moved"] for x in r) / len(r), sum(x["ai_armies"] for x in r) / len(r)),
          "| adjacent-to-enemy-city/turn %.1f" % (sum(x["adjacent_to_enemy_city"] for x in r) / len(r)),
          "| moved t>=20: %.1f" % (sum(x["moved"] for x in r[19:]) / max(1, len(r[19:]))),
          ("| under siege/turn %.2f" % (sum(x["cities_under_siege"] for x in r) / len(r))) if "cities_under_siege" in r[0] else "")
