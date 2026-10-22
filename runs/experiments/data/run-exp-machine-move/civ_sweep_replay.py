#!/usr/bin/env python3
"""Machine-move replay (2026-10-10): a copy of runs/experiments/civ-sweep/sweep.py writing to artifacts/run-exp-machine-move/civ-sweep-replay/; its saves are compared with run-exp-civ-sweep/SAVES.sha256. Original docstring follows.

For each nation row 0-15, seed 12345: New Game with that nation human; record the title bar, CUR_NATION, the turn-order
position, the start popups and the start state; on turn 1: Build fleet (10 ships), open the recruit dialog, select the first
army (and a fleet if the nation has one), End turn; on turn 2: move the first army one tile, End turn. Every step is wrapped:
a failure is a result, recorded, and the sweep goes on with the next nation. Writes artifacts/run-exp-civ-sweep/sweep.json after
each nation and keeps the autosaves as S<row>_<nation>_AUTOnnnn.SAV.

    python3 runs/experiments/civ-sweep/sweep.py [row ...]      # default: all 16
"""
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from harness.driver import CUR_NATION, G, SEL_ARMY, SEL_FLEET, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-machine-move" / "civ-sweep-replay"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 12345
NAMES = ["Rome", "Carthage", "Seleucid", "Ptolemaic", "Macedonia", "Numidia", "Gaul", "Greece", "Celtiberia", "Illyria",
         "Dacia", "Bithynia", "Galatia", "Armenia", "Media", "Thracia"]


def coastal(s, c):
    return any(0 <= c["x"] + dx < sav.MAP_W and 0 <= c["y"] + dy < sav.MAP_H and sav.cell(s, c["x"] + dx, c["y"] + dy) in (0, 1)
               for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def summary(path, row):
    s = sav.load(str(path))
    n = s["nations"][row]
    mine = [c for c in s["cities"] if c["owner"] == row]
    return {"turn": s["turn"], "date": s["date"], "seat_index": s["seat_index"], "current_nation": s["current_nation"],
            "turn_order": s["turn_order"], "human_flags": [i for i, x in enumerate(s["nations"]) if x["human"]],
            "leader": n["leader"], "treasury": n["treasury"], "cities": len(mine), "coastal_cities": sum(coastal(s, c) for c in mine),
            "armies": [(a["id"], a["x"], a["y"], a["troops"], a["moves"]) for a in s["armies"] if a["owner"] == row and a["troops"] > 0],
            "fleets": [(f["id"], f["x"], f["y"], f["ships"], f.get("condition"), f["building"]) for f in s["fleets"] if f["owner"] == row],
            "wars": [k for k, v in n["relations"].items() if v == 3], "tax": n["tax"], "mobilization": n["mobilization"],
            "view": n["view"], "capital": n["capital"]}


def step(rec, name, fn):
    t0 = time.time()
    try:
        r = fn()
        rec["steps"].append({"step": name, "ok": True, "result": r, "secs": round(time.time() - t0, 1)})
        return True, r
    except Exception as e:     # noqa: BLE001 - a failure is a result
        rec["steps"].append({"step": name, "ok": False, "error": f"{type(e).__name__}: {e}", "secs": round(time.time() - t0, 1)})
        return False, None


def one(row, out):
    nation = NAMES[row]
    rec = {"row": row, "nation": nation, "steps": []}
    g = Game()
    tag = f"S{row:02d}_{nation}"
    try:
        ok, r = step(rec, "new_game", lambda: g.new_game(row=row, seed=SEED))
        if not ok:
            return rec
        path, popups = r
        rec["start_popups"] = popups
        rec["cur_nation"] = g.i16(CUR_NATION)
        rec["cur_nation_matches_row"] = rec["cur_nation"] == row
        rec["title"] = [w[1] for w in g.find_windows("^Imperial Conquest 2    ")]
        rec["view_origin_mem"] = list(g.view_origin())
        shutil.copy(path, OUT / f"{tag}_{Path(path).name}")
        rec["start"] = summary(path, row)
        s0 = rec["start"]
        # turn 1: build a fleet, open the recruit dialog, select the first army (and a fleet)
        step(rec, "build_fleet", lambda: g.build_fleet(10))
        def recruit_dialog():
            g.open_recruit()
            cs = g.controls("Army recruits")
            info = {"controls": [(c["cls"], c["text"]) for c in cs if c["cls"] in ("TButton", "TListBox")]}
            g.shot(OUT / f"{tag}_recruit.png", window=str(g.find_windows("^Army recruits$")[0][0]))
            g.close_controls("Army recruits", cs)
            return info
        step(rec, "recruit_dialog", recruit_dialog)
        if s0["armies"]:
            aid, ax, ay = s0["armies"][0][:3]
            def select():
                g.select_army(aid, ax, ay)
                g.shot(OUT / f"{tag}_army_selected.png")
                return {"army": aid, "sel": g.i16(SEL_ARMY)}
            step(rec, "select_first_army", select)
        else:
            rec["steps"].append({"step": "select_first_army", "ok": None, "result": "the nation has no army"})
        if s0["fleets"] and not s0["fleets"][0][5]:
            fid, fx, fy = s0["fleets"][0][:3]
            step(rec, "select_fleet", lambda: (g.select_fleet(fid, fx, fy), {"fleet": fid, "sel": g.i16(SEL_FLEET)})[1])
        ok, r = step(rec, "end_turn_1", lambda: g.end_turn(timeout=90))
        if not ok:
            rec["end_turn_1_stuck"] = {"windows": [(x[1], x[4], x[5]) for x in g.find_windows(".")],
                                       "popups": [(x[1], g.read_popup(x)) for x in g.popups()],
                                       "cur_nation": g.i16(CUR_NATION), "calendar": g.calendar()}
            g.shot(OUT / f"{tag}_end_turn_stuck.png")
            return rec
        shutil.copy(G / r[0], OUT / f"{tag}_{r[0]}")
        rec["after_turn_1"] = {"autosave": r[0], "popups": r[1], **summary(G / r[0], row)}
        # turn 2: move the first army one tile, End turn
        a1 = rec["after_turn_1"]["armies"]
        if a1:
            aid, ax, ay = a1[0][:3]
            s1 = sav.load(str(G / r[0]))
            tgt = next(((ax + dx, ay + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)
                        and 0 <= ax + dx < sav.MAP_W and 0 <= ay + dy < sav.MAP_H
                        and sav.move_cost(sav.cell(s1, ax + dx, ay + dy)) is not None and 2 <= sav.cell(s1, ax + dx, ay + dy) < 12), None)
            if tgt:
                step(rec, "move_first_army", lambda: [list(g.move(aid, *tgt)[0]), g.move.__name__][0])
        ok, r = step(rec, "end_turn_2", lambda: g.end_turn())
        if ok:
            shutil.copy(G / r[0], OUT / f"{tag}_{r[0]}")
            rec["after_turn_2"] = {"autosave": r[0], "popups": r[1], **summary(G / r[0], row)}
    except Exception:     # noqa: BLE001
        rec["fatal"] = traceback.format_exc()[-600:]
    finally:
        try:
            g.kill()
        except Exception:     # noqa: BLE001
            pass
    return rec


def main():
    rows = [int(a) for a in sys.argv[1:]] or list(range(16))
    f = OUT / "sweep.json"
    res = json.loads(f.read_text()) if f.exists() else {}
    for row in rows:
        t0 = time.time()
        res[str(row)] = one(row, OUT)
        res[str(row)]["secs"] = round(time.time() - t0)
        f.write_text(json.dumps(res, indent=1, default=str))
        bad = [s["step"] for s in res[str(row)]["steps"] if s["ok"] is False]
        print(f"{row:2d} {NAMES[row]:11s} {res[str(row)]['secs']:4d}s  cur_nation_ok={res[str(row)].get('cur_nation_matches_row')}  failed={bad}  fatal={'fatal' in res[str(row)]}", flush=True)


if __name__ == "__main__":
    main()
