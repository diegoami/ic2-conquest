"""For each fleet_hunt record: does the logged score fit FUN_0044f4f8 as disassembled here (FUN_0044f4f8_f608.asm): in the loop
s = my*100/their - d, doubled when their < my and d < 18 (`cmp bx, 0x12; jge`), the best s kept; on return the chosen target's distance d is ADDED
back (0x44f5f4), so the returned score is my*100/their (not doubled) or 2*(my*100/their - d) + d (doubled). Strengths with strength = ships*condition/10 (+ carried army's
assault strength / 50, ignored here: only fleets with no army are compared) times a jitter factor 1 + Random(4)/10 in {1.0, 1.1, 1.2, 1.3} on each side?
Ships and condition: from a v3 record (decision time) when present; otherwise from the save before the turn, trying also condition 100
(a repair earlier in the same fleet's step).
Integer arithmetic as in Delphi is approximated; a fit is reported when any jitter pair and condition choice gives the logged score within +-1.
python3 hunt_bounds.py <variant> <seed>   -> printed and written to hunt_bounds_<variant>_s<seed>.json (new file, versioned)"""
import json, sys
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
from state import sav
ART = R / "artifacts/run-exp-ai-intercept-hunt"; DATA = R / "runs/experiments/data/run-exp-ai-intercept-hunt"
variant, seed = sys.argv[1], int(sys.argv[2])
L = [json.loads(l) for l in (DATA / f"{variant}_s{seed}.jsonl").read_text().splitlines()]
st = [i for i, l in enumerate(L) if l["event"] == "start"][-1]
prev, out = None, []
cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
for l in L[st:]:
    if l["event"] != "end_turn": continue
    pre = sav.load(str(ART / prev)) if prev else sav.load(str(R / "saves/run0-start-AUTO0720-seed12345.SAV"))
    prev = l["copy"]
    F = {f["id"]: f for f in pre["fleets"]}
    for r in l.get("records", []):
        if r["site"] != "fleet_hunt" or "unit_rec" not in r: continue
        me, him = F.get(r["unit"]), F.get(r["hunt_fleet"])
        u, o = r["unit_rec"], r["other_rec"]
        d = cheb((u["x"], u["y"]), (o["x"], o["y"]))
        fits = []
        A = {a["id"]: a for a in pre["armies"]}
        def armyval(f):                                       # FUN_0044a930 / 50: (sum troops, x3 for archers) / 80 * morale, then / 50
            if f["army"] < 0 or f["army"] not in A: return 0
            a = A[f["army"]]; tr = sum(u["troops"] * (3 if u["type"] == "ar" else 1) for u in a["units"])
            return tr // 80 * a["morale"] // 50
        v3 = "ships" in u                                     # v3 records carry the decision-time ships and condition
        if v3:
            me = dict(me or {}, ships=u["ships"], condition=u["condition"], army=u["army"])
            him = dict(him or {}, ships=o["ships"], condition=o["condition"], army=o["army"])
        if me and him:
            for cm in ([me["condition"]] if v3 else sorted({me["condition"], 100})):
                for ch in ([him["condition"]] if v3 else sorted({him["condition"], 100})):
                    vm, vh = me["ships"] * cm // 10 + armyval(me), him["ships"] * ch // 10 + armyval(him)
                    for jm in range(4):
                        for jh in range(4):
                            sm, sh = vm + jm * vm // 10, vh + jh * vh // 10
                            sc = sm * 100 // sh - d
                            if sh < sm and d < 18: sc = 2 * sc
                            sc += d
                            if abs(sc - r["hunt_score"]) <= 1: fits.append((cm, ch, jm, jh, sc))
        out.append({"end": l["end"], "nation": r["nation"], "fleet": r["unit"], "hunted": r["hunt_fleet"], "score": r["hunt_score"], "dist": d,
                    "me": me and (me["ships"], me["condition"], me["army"]), "him": him and (him["ships"], him["condition"], him["army"]),
                    "fits": fits[:6], "n_fits": len(fits), "decision_time_records": v3})
p = DATA / f"hunt_bounds_{variant}_s{seed}.json"; k = 1
while p.exists(): k += 1; p = DATA / f"hunt_bounds_{variant}_s{seed}.v{k}.json"
p.write_text(json.dumps(out, indent=1))
for o in out: print(o["end"], o["nation"], o["fleet"], "->", o["hunted"], "score", o["score"], "dist", o["dist"], "me", o["me"], "him", o["him"], "fits", o["n_fits"], o["fits"][:2])
