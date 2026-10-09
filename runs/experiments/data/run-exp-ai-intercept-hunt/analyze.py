"""Check every hook record of <variant>_s<seed>.jsonl (the LAST complete run in the file) against the autosaves: the state before the AI seats
acted is the previous autosave (the start save for End turn 1), the state after is this End turn's autosave.
Intercept records: the nation's capital city, the threat's owner and its relation to the nation (at war = 3), Chebyshev distances
(FUN_00449018 = max(|dx|, |dy|)) army-capital and army-target recomputed from the before-save, the capital-target distance (< 20 at war), the
responder's moves, the exemption rule (army or city target score > 100, moves > its distance, capital farther than 3 x moves), and the
responder's distance to the target after the turn. Fleet records: the port city's position against the target, the hunt score against 100,
the hunt target's owner and relation, the fleet's distance to the target before and after.
python3 analyze.py <variant> <seed>   -> analysis_<variant>_s<seed>.json (new file; an existing one is kept and a .vN written beside it)"""
import json, sys
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
from state import sav
ART = R / "artifacts/run-exp-ai-intercept-hunt"; DATA = R / "runs/experiments/data/run-exp-ai-intercept-hunt"
variant, seed = sys.argv[1], int(sys.argv[2])
lines = [json.loads(l) for l in (DATA / f"{variant}_s{seed}.jsonl").read_text().splitlines()]
starts = [i for i, l in enumerate(lines) if l["event"] == "start"]
run = lines[starts[-1]:]
cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
def load(name): return sav.load(str(ART / name)) if name else sav.load(str(R / "saves/run0-start-AUTO0720-seed12345.SAV"))
out, prev = [], None
for l in run:
    if l["event"] != "end_turn": continue
    pre, post = load(prev), load(l["copy"])
    prev = l["copy"]
    A0 = {a["id"]: a for a in pre["armies"]}; A1 = {a["id"]: a for a in post["armies"]}
    F0 = {f["id"]: f for f in pre["fleets"]}; F1 = {f["id"]: f for f in post["fleets"]}
    for r in l.get("records", []):
        n = r["nation"]; nat = pre["nations"][n]; tgt = (r["target_x"], r["target_y"])
        cap = pre["cities"][nat["capital"]]; capxy = (cap["x"], cap["y"])
        c = {"end": l["end"], "autosave": l["autosave"], "i": r["i"], "site": r["site"], "nation": nat["name"], "unit": r["unit"], "target": tgt}
        if r["site"].startswith("intercept"):
            a, t = A0.get(r["unit"]), A0.get(r["threat_army"])
            c.update(capital=[cap["name"], capxy], logged={k: r[k] for k in ("threats", "dispatched_incl_this", "dist_capital", "dist_threat",
                     "threat_army", "army_target_score", "army_target_dist", "city_target_score", "city_target_dist") if k in r})
            if a:
                c.update(army_owner=a["owner"], army_before=(a["x"], a["y"]), army_moves=a["moves"],
                         dist_capital_recomputed=cheb((a["x"], a["y"]), capxy), dist_target_recomputed=cheb((a["x"], a["y"]), tgt))
                ex = lambda s, d: s > 100 and a["moves"] > d and cheb((a["x"], a["y"]), capxy) > 3 * a["moves"]
                c["exempt_by_rule"] = ex(r.get("army_target_score", 0), r.get("army_target_dist", 0)) or ex(r.get("city_target_score", 0), r.get("city_target_dist", 0))
            if t:
                own = pre["nations"][t["owner"]]["name"]
                c.update(threat_owner=own, threat_before=(t["x"], t["y"]), relation_to_threat_owner=nat["relations"].get(own),
                         capital_to_target=cheb(capxy, tgt))
            a1 = A1.get(r["unit"])
            c["army_after"] = (a1["x"], a1["y"]) if a1 and a1["owner"] == n else None
            c["dist_target_after"] = cheb(c["army_after"], tgt) if c["army_after"] else None
        else:
            f = F0.get(r["unit"])
            c.update(hunt_score=r["hunt_score"], hunt_fleet=r["hunt_fleet"], port_city=r["port_city"])
            if r["port_city"] >= 0:
                pc = pre["cities"][r["port_city"]]
                c.update(port=[pc["name"], (pc["x"], pc["y"]), pre["nations"][pc["owner"]]["name"] if pc["owner"] >= 0 else None, pc["supplies"]])
            if r["site"] == "fleet_hunt":
                h = F0.get(r["hunt_fleet"])
                if h:
                    own = pre["nations"][h["owner"]]["name"]
                    c.update(hunted_owner=own, hunted_before=(h["x"], h["y"]), relation_to_hunted=nat["relations"].get(own), hunted_ships=h["ships"])
            if f:
                c.update(fleet_owner=f["owner"], fleet_before=(f["x"], f["y"]), fleet_moves=f["moves"], fleet_ships=f["ships"],
                         fleet_supplies=f["supplies"], dist_target_before=cheb((f["x"], f["y"]), tgt))
            f1 = F1.get(r["unit"])
            c["fleet_after"] = (f1["x"], f1["y"]) if f1 and f1["owner"] == n else None
            c["dist_target_after"] = cheb(c["fleet_after"], tgt) if c["fleet_after"] else None
        out.append(c)
p = DATA / f"analysis_{variant}_s{seed}.json"; k = 1
while p.exists(): k += 1; p = DATA / f"analysis_{variant}_s{seed}.v{k}.json"
p.write_text(json.dumps(out, indent=1, default=str))
from collections import Counter
print(p.name, len(out), "records", Counter(c["site"] for c in out))
