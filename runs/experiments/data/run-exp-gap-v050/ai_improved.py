"""The same idle-Rome AI measures on the remake's `improved` preset (scenario example-classical-improved, seeds 1-3, 80 End turns):
city owner changes by turn, cities under siege, AI armies next to an enemy city at war, AI recruitment slots and mobilisation at the end,
AI fortification rises, Rome's cities. Writes ai_improved.json (versioned). python3 ai_improved.py"""
import json
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); D = R / "runs/experiments/data/run-exp-gap-v050"
out = {}
for seed in (1, 2, 3):
    prev, ch, sieges, adj, forts = None, [], 0, 0, 0
    for t in range(81):
        s = json.load(open(R / f"artifacts/run-exp-gap-v050/ai_improved_rome_s{seed}_t{t:03d}.sav"))["save"]["state"]
        ids = s["relations"]["nationIds"]; m = s["relations"]["matrix"]; war = lambda a, b: m[ids.index(a)][ids.index(b)] == 3
        own = {c["id"]: (c["owner"], c["fortificationCode"]) for c in s["cities"]}
        if prev:
            n = sum(1 for k, (o, _) in own.items() if prev[k][0] != o)
            if n: ch.append((t, n))
            forts += sum(1 for k, (o, f) in own.items() if o and o != "rome" and prev[k][0] == o and f % 100 > prev[k][1] % 100)
        sieges += sum(c["underSiege"] for c in s["cities"])
        adj += sum(1 for a in s["armies"] if a["nation"] != "rome" and a["units"] and any(
            c["owner"] and c["owner"] != a["nation"] and war(a["nation"], c["owner"]) and max(abs(c["x"] - a["x"]), abs(c["y"] - a["y"])) <= 1 for c in s["cities"]))
        prev = own
    ai = [n for n in s["nations"] if n["id"] != "rome"]
    out[f"improved_s{seed}"] = {"owner_changes_by_turn": ch, "city_turns_under_siege": sieges, "ai_army_turns_adjacent_to_enemy_city": adj,
                                "ai_fortify_rises": forts, "end_ai_slots": sum(len(n["recruitmentSlots"]) for n in ai),
                                "end_ai_mob_mean": round(sum(n["mobilizedPercent"] for n in ai) / len(ai), 1),
                                "end_rome_cities": sum(c["owner"] == "rome" for c in s["cities"])}
p = D / "ai_improved.json"; k = 1
while p.exists(): k += 1; p = D / f"ai_improved.v{k}.json"
p.write_text(json.dumps(out, indent=1)); print(p.name); print(json.dumps(out, indent=1))
