#!/usr/bin/env python3
"""(b) second attempt: the same click, with a full turn's moves, at war (Felsina, Gaul) and at peace (Genua, Greece).

The first attempt (b_attack_prompt.py; b1_first_attempt.json) clicked with 1 and 7 moves left and got no attack and no
prompt in either case, so moves and relation were confounded. Here the army ends a turn adjacent and clicks on the next
turn's full moves. Nothing is auto-answered: the box, if any, is captured, then answered No, then the click is repeated
and answered Yes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *   # noqa: F401,F403
from state import sav

REL = 0x26
res = {}
OUTJ = OUT / "b2_attack_prompt.json"


def rel(g, j):
    return nation_i16(g, ROME, REL + 2 * j)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def moves_of(g):
    return struct.unpack_from("<h", g.army_rec(0), 6)[0]


def boxes(g):
    time.sleep(2.0)
    out = []
    for p in g.popups():
        if p[1] in ("Confirm", "Information", "Warning"):
            row = {"title": p[1], "text": g.read_popup(p)}
            try:
                row["buttons"] = [c["text"] for c in g.controls(p[1]) if c["cls"] == "TButton"]
            except Exception as e:     # noqa: BLE001
                row["buttons_error"] = str(e)
            out.append(row)
    return out


def move_retry(g, tile, tries=3):
    """g.move, retried after a pause: right after End turn the UI needs a few seconds before a select sticks."""
    for k in range(tries):
        try:
            return g.move(0, *tile)
        except Exception:      # noqa: BLE001
            if k == tries - 1:
                raise
            time.sleep(4)
            g.dismiss_popups()


def approach(g, target, max_turns=6):
    from planner.path import path_adjacent, turn_legs
    base = sav.load(str(BASE))
    log = []
    for _ in range(max_turns):
        pos = tuple(g.army_pos(0))
        if cheb(pos, target) == 1:
            break
        cost, path = path_adjacent(base, pos, target)
        reach, spent = turn_legs(base, path, moves_of(g))
        for tile in reach[1:]:
            move_retry(g, tile)
        log.append({"turn": g.turn_number(), "army": list(g.army_pos(0)), "moves_left": moves_of(g)})
        if cheb(g.army_pos(0), target) == 1:
            g.end_turn(); time.sleep(3); g.dismiss_popups()              # next turn the army has its full moves
            log.append({"turn_after_end": g.turn_number(), "army": list(g.army_pos(0)), "moves_full": moves_of(g)})
            break
        g.end_turn()
        time.sleep(3)
        g.dismiss_popups()
    return log


def scenario(tag, target, nation, city_name):
    g = fresh()
    r = {"target": city_name, "xy": target, "relation_before": rel(g, nation)}
    r["march"] = approach(g, target)
    ax, ay = g.army_pos(0)
    r["army_before_click"] = {"xy": [ax, ay], "moves": moves_of(g)}
    if cheb((ax, ay), target) != 1:
        r["error"] = "not adjacent"
        g.kill()
        return r
    # Save FIRST: the File > Save menu clears the army selection, so select the army only afterwards.
    b = keep(g, f"B2_{tag}_BEFORE.SAV")
    try:
        g.select_army(0, ax, ay)
    except Exception as e:     # noqa: BLE001
        r["select_error"] = str(e)
        r["select_state"] = {"selected": g.i16(SEL_ARMY), "moves": moves_of(g), "boxes": boxes(g)}
        shot(g, f"B2_{tag}_select_failed.png")
        g.kill()
        return r
    r["before"] = {k: v for k, v in sav.load(str(b))["armies"][0].items() if k in ("troops", "moves", "supplies")}
    r["city_before"] = next({k: c[k] for k in ("owner", "loyalty", "fort", "pop")} for c in sav.load(str(b))["cities"] if c["name"] == city_name)
    g.click_tile(*target, pause=1.0)
    r["click1_boxes"] = boxes(g)
    shot(g, f"B2_{tag}_click1.png")
    r["click1_selected_army"] = g.i16(SEL_ARMY)
    if any(x["title"] == "Confirm" for x in r["click1_boxes"]):
        g.answer("Confirm", yes=False)
        time.sleep(1.0)
        r["after_no"] = {"relation": rel(g, nation), "selected": g.i16(SEL_ARMY), "army": list(g.army_pos(0)), "moves": moves_of(g)}
        keep(g, f"B2_{tag}_AFTER_NO.SAV")      # (the save clears the selection again)
        g.select_army(0, ax, ay)
        g.click_tile(*target, pause=1.0)
        r["click2_boxes"] = boxes(g)
        shot(g, f"B2_{tag}_click2.png")
        if any(x["title"] == "Confirm" for x in r["click2_boxes"]):
            g.answer("Confirm", yes=True)
            time.sleep(3.0)
            r["battle"] = bool(g.in_battle())
            if g.in_battle():
                g.play_battle()
    r["popups"] = g.dismiss_popups()
    r["final"] = {"relation": rel(g, nation), "selected": g.i16(SEL_ARMY), "army": list(g.army_pos(0)), "moves": moves_of(g)}
    p = keep(g, f"B2_{tag}_AFTER.SAV")
    s = sav.load(str(p))
    r["final"]["troops"] = s["armies"][0]["troops"]
    r["city_after"] = next({k: c[k] for k in ("owner", "loyalty", "fort", "pop")} for c in s["cities"] if c["name"] == city_name)
    r["news_tail"] = s["news"][-3:]
    g.kill()
    return r


for tag, target, nation, name in [("WAR_FELSINA", (98, 31), 6, "Felsina"), ("PEACE_GENUA", (89, 30), 7, "Genua")]:
    res[tag] = scenario(tag, target, nation, name)
    OUTJ.write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
