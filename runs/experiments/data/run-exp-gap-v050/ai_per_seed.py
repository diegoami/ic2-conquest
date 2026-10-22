"""Per-seed table of the AI measures on both sides (research's request, 2026-10-09): city captures (owner changes) in the windows
End turn 1-10, 11-20, 21-40, 41-80; AI armies per turn next to an enemy city at war (mean); AI recruitment slots and mean mobilisation, and
Rome's cities, at End turn 25, 40 and the last. From ai_metrics_turns.jsonl and ai_movement.json (and ai_improved.json is separate).
Writes ai_per_seed.md (versioned). python3 ai_per_seed.py"""
import json
from collections import defaultdict
from pathlib import Path
D = Path(__file__).resolve().parent
T = [json.loads(l) for l in (D / "ai_metrics_turns.jsonl").read_text().splitlines()]
M = json.loads((D / "ai_movement.json").read_text())
g = defaultdict(dict)
for r in T: g[(r["engine"], r["seed"])][r["turn"]] = r
W = ((1, 10), (11, 20), (21, 40), (41, 80))
lines = ["| Engine | Seed | End turns | Captures 1-10 | 11-20 | 21-40 | 41-80 | AI armies next to an enemy city / turn | AI slots @25 / @40 / last | AI mobilisation % @25 / @40 / last | Rome's cities @25 / @40 / last |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
for (eng, seed), rows in sorted(g.items(), key=lambda x: (x[0][0] != "original", x[0][1])):
    last = max(rows)
    cap = [sum(rows[t].get("owner_changes", 0) for t in range(a, b + 1) if t in rows) if a <= last else None for a, b in W]
    mv = M[f"{eng}_s{seed}"][1:]
    adj = sum(x["adjacent_to_enemy_city"] for x in mv) / len(mv)
    at = lambda k, t: rows[t][k] if t in rows else "–"
    lines.append(f"| {eng} | {seed} | {last} | " + " | ".join("–" if c is None else str(c) for c in cap) + f" | {adj:.1f} | "
                 f"{at('ai_slots', 25)} / {at('ai_slots', 40)} / {rows[last]['ai_slots']} | {at('ai_mob_mean', 25)} / {at('ai_mob_mean', 40)} / {rows[last]['ai_mob_mean']} | "
                 f"{at('rome_cities', 25)} / {at('rome_cities', 40)} / {rows[last]['rome_cities']} |")
p = D / "ai_per_seed.md"; k = 1
while p.exists(): k += 1; p = D / f"ai_per_seed.v{k}.md"
p.write_text("\n".join(lines) + "\n"); print(p.name); print("\n".join(lines))
