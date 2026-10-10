"""The remake's captures of End turns 1-10 (research's question, 2026-10-09): for every city whose owner changed between save t-1 and
save t (idle-Rome games, 8 seeds), the new owner, the news lines of turn t that name the city, and the siege-gate pairs (siege_gate_early_
s<seed>.jsonl, from siege_probe/run.sh <prefix> <out> 0 10) at save t-1 of the new owner's armies adjacent to that city: their ratio
against the required one. Writes early_captures.json (versioned). python3 early_captures.py"""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[4]; D = R / "runs/experiments/data/run-exp-gap-v050"; A = R / "artifacts/run-exp-gap-v050"
def news(s):
    sl = s["newsLog"]["slots"]; k = s["newsLog"]["mostRecentSlot"]
    return [x["text"] for x in (sl[k + 1:] + sl[:k + 1] if len(sl) == 40 else sl)]
out = []
for seed in (1, 2, 3, 10, 11, 12, 14, 12345):
    pairs = [json.loads(l) for l in (D / f"siege_gate_early_s{seed}.jsonl").read_text().splitlines()]
    prev = json.load(open(A / f"ai_rome_s{seed}_t000.sav"))["save"]["state"]
    for t in range(1, 11):
        s = json.load(open(A / f"ai_rome_s{seed}_t{t:03d}.sav"))["save"]["state"]
        po = {c["id"]: c for c in prev["cities"]}
        nl = news(s)
        for c in s["cities"]:
            o = po[c["id"]]
            if o["owner"] == c["owner"]: continue
            pp = [p for p in pairs if p["turn"] == t - 1 and p["city"] == c["id"] and p["nation"] == c["owner"]]
            out.append({"seed": seed, "turn": t, "city": c["id"], "from": o["owner"], "to": c["owner"],
                        "news": [x for x in nl if c["name"] in x][-2:],
                        "fort_before": o["fortificationCode"], "garrison_before": len(o.get("garrison", [])),
                        "capturer_pairs_at_t_minus_1": [{k: p[k] for k in ("army", "ratio_real", "required", "pass_real")} for p in pp]})
        prev = s
p = D / "early_captures.json"; k = 1
while p.exists(): k += 1; p = D / f"early_captures.v{k}.json"
p.write_text(json.dumps(out, indent=1)); print(p.name, len(out))
for o in out: print(o["seed"], o["turn"], o["city"], o["from"], "->", o["to"], o["news"][-1:] , o["capturer_pairs_at_t_minus_1"])
