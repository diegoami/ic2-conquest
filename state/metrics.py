"""Per-turn metrics from autosaves.

    python3 -m state.metrics runs/0 AUTO0720.SAV AUTO0721.SAV ...

appends to runs/<id>/metrics.csv (one row per turn and nation) and
runs/<id>/armies.csv (one row per turn and live army), and writes the parsed
state of each save to runs/<id>/state/nnnn.json (without the map grid).
Rows for a turn already in the file are replaced, so re-running is safe.
"""
import csv
import json
import sys
from pathlib import Path

from state.sav import NATIONS, UNIT_TYPES, live_armies, load, owned_cities

NATION_COLS = ["turn", "date", "nation", "alive", "cities", "armies", "troops"] + \
              ["troops_" + t for t in UNIT_TYPES] + \
              ["fleets", "ships", "treasury", "unity", "mobilization", "tax", "tax_base",
               "queue_slots", "queue_troops", "army_supplies", "army_supply_pct_min",
               "army_morale_min", "army_morale_mean", "city_share", "troop_share", "save"]
ARMY_COLS = ["turn", "nation", "army", "x", "y", "troops"] + ["troops_" + t for t in UNIT_TYPES] + \
            ["units", "mercs", "moves", "supplies", "supply_pct", "morale", "money", "embarked", "save"]


def rows(s, save_name):
    total_troops = sum(a["troops"] for a in live_armies(s)) or 1
    out = []
    for n in s["nations"]:
        arm = live_armies(s, n["id"])
        fl = [f for f in s["fleets"] if f["owner"] == n["id"]]
        by = {t: sum(u["troops"] for a in arm for u in a["units"] if u["type"] == t) for t in UNIT_TYPES}
        troops = sum(a["troops"] for a in arm)
        ncities = len(owned_cities(s, n["id"]))
        r = {"turn": s["turn"], "date": s["date"], "nation": n["name"], "alive": int(n["alive"]),
             "cities": ncities, "armies": len(arm), "troops": troops,
             "fleets": len(fl), "ships": sum(f["ships"] for f in fl),
             "treasury": n["treasury"], "unity": n["unity"], "mobilization": n["mobilization"],
             "tax": n["tax"], "tax_base": n["tax_base"],
             "queue_slots": len(n["recruit_slots"]), "queue_troops": sum(q["troops"] for q in n["recruit_slots"]),
             "army_supplies": sum(a["supplies"] for a in arm),
             "army_supply_pct_min": min((a["supply_pct"] for a in arm), default=""),
             "army_morale_min": min((a["morale"] for a in arm), default=""),
             "army_morale_mean": round(sum(a["morale"] for a in arm) / len(arm), 1) if arm else "",
             "city_share": round(ncities / 334, 4), "troop_share": round(troops / total_troops, 4),
             "save": save_name}
        r.update({"troops_" + t: by[t] for t in UNIT_TYPES})
        out.append(r)
    return out


def army_rows(s, save_name):
    out = []
    for a in live_armies(s):
        r = {"turn": s["turn"], "nation": NATIONS[a["owner"]], "army": a["id"], "x": a["x"], "y": a["y"],
             "troops": a["troops"], "units": len(a["units"]), "mercs": sum(1 for u in a["units"] if u["merc"]),
             "moves": a["moves"], "supplies": a["supplies"], "supply_pct": a["supply_pct"],
             "morale": a["morale"], "money": a["money"], "embarked": int(a["embarked"]), "save": save_name}
        r.update({"troops_" + t: sum(u["troops"] for u in a["units"] if u["type"] == t) for t in UNIT_TYPES})
        out.append(r)
    return out


def upsert(path, cols, new_rows):
    turns = {r["turn"] for r in new_rows}
    old = []
    if path.exists():
        with path.open() as f:
            old = [r for r in csv.DictReader(f) if int(r["turn"]) not in turns]
    allr = old + new_rows
    allr.sort(key=lambda r: (int(r["turn"]), str(r.get("nation")), int(r.get("army", 0) or 0)))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(allr)


def record(run_dir, saves):
    run_dir = Path(run_dir)
    (run_dir / "state").mkdir(parents=True, exist_ok=True)
    nrows, arows = [], []
    for p in saves:
        p = Path(p)
        s = load(p)
        nrows += rows(s, p.name)
        arows += army_rows(s, p.name)
        js = {k: v for k, v in s.items() if k != "map"}
        (run_dir / "state" / f"{s['turn']:04d}.json").write_text(json.dumps(js, indent=0))
    upsert(run_dir / "metrics.csv", NATION_COLS, nrows)
    upsert(run_dir / "armies.csv", ARMY_COLS, arows)


if __name__ == "__main__":
    record(sys.argv[1], sys.argv[2:])
