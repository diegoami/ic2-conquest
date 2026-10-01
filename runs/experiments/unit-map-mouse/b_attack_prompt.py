#!/usr/bin/env python3
"""(b) Does clicking an adjacent enemy city ask "Are you sure you want to attack this ...?" only when not at war?

Control: Felsina (Gaul), Rome-Gaul relation 3 (war). Test: Aleria (Carthage), Rome-Carthage relation 0 (peace).
The prompt is captured by hand: Game.attack would answer it Yes through dismiss_popups."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *   # noqa: F401,F403
from state import sav

REL = 0x26            # nation record: relation to nation j at +0x26 + 2*j
CARTHAGE, GAUL = 1, 6
res = {}


def rel(g, j):
    return nation_i16(g, ROME, REL + 2 * j)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def clickable_prompt(g):
    """After clicking the target: the confirm box's name, OCR text and buttons, without answering it."""
    time.sleep(1.5)
    ps = [p for p in g.popups() if p[1] in ("Confirm", "Information", "Warning")]
    out = []
    for p in ps:
        out.append({"title": p[1], "text": g.read_popup(p), "controls": [c["text"] for c in g.controls(p[1])]})
    return out


def approach_planned(g, target_city, max_turns=6):
    """March army 0 next to `target_city` with the planner's path, one tile per click, one End turn at a time."""
    from planner.path import path_adjacent, turn_legs
    base = sav.load(str(BASE))
    log = []
    for _ in range(max_turns):
        pos = tuple(g.army_pos(0))
        if cheb(pos, target_city) == 1:
            break
        cost, path = path_adjacent(base, pos, target_city)
        if path is None:
            log.append({'error': 'no path'})
            break
        moves = struct.unpack_from("<h", g.army_rec(0), 6)[0]
        reach, spent = turn_legs(base, path, moves)
        for tile in reach[1:]:
            g.move(0, *tile)
        log.append({"turn": g.turn_number(), "army": g.army_pos(0), "planned_reach": reach[-1], "path_len": len(path)})
        if cheb(g.army_pos(0), target_city) == 1:
            break
        g.end_turn()
    return log


def approach(g, target_city, goal, max_turns=5):
    """March army 0 toward `goal` (a tile), one End turn at a time, until adjacent to the city."""
    log = []
    for turn in range(max_turns):
        pos = g.army_pos(0)
        if cheb(pos, target_city) == 1:
            break
        g.move(0, *goal)
        log.append({"turn": g.turn_number(), "army": g.army_pos(0), "moves": struct.unpack_from("<h", g.army_rec(0), 6)[0]})
        if cheb(g.army_pos(0), target_city) == 1:
            break
        g.end_turn()
    return log


# ---- control: already at war (Gaul) ------------------------------------------------------------------
TEST_ONLY = "--test-only" in sys.argv
if TEST_ONLY:
    res = json.loads((OUT / "b_attack_prompt.json").read_text())
g = None if TEST_ONLY else fresh()
felsina = (98, 31)
if not TEST_ONLY:
  ctl = {"relation_rome_gaul_before": rel(g, GAUL)}
  ctl["march"] = approach(g, felsina, (99, 32))
  ax, ay = g.army_pos(0)
  ctl["army_before_click"] = [ax, ay]
  g.select_army(0, ax, ay)
  keep(g, "B_CONTROL_BEFORE_CLICK.SAV")
  g.click_tile(*felsina, pause=1.5)
  ctl["prompt"] = clickable_prompt(g)
  shot(g, "B_control_after_click.png")
  ctl["selected_after"] = g.i16(SEL_ARMY)
  ctl["relation_after"] = rel(g, GAUL)
  ctl["popups_dismissed"] = g.dismiss_popups()
  keep(g, "B_CONTROL_AFTER_CLICK.SAV")
  res["control_at_war"] = ctl
  Path(OUT / "b_attack_prompt.json").write_text(json.dumps(res, indent=1, default=str))
  g.kill()

# ---- test: at peace (Carthage, Aleria) ----------------------------------------------------------------
g = fresh()
aleria = (89, 30)         # Genua (Greece), reachable by land, relation 0 (peace); named aleria below for brevity
GREECE = 7
t = {"relation_rome_greece_before": rel(g, GREECE), "target": "Genua (Greece) at (89,30)"}
t["march"] = approach_planned(g, aleria)
ax, ay = g.army_pos(0)
t["army_before_click"] = [ax, ay]
if cheb((ax, ay), aleria) != 1:
    t["error"] = "army not adjacent to Genua"
else:
    g.select_army(0, ax, ay)
    keep(g, "B_TEST_BEFORE_CLICK.SAV")
    t["troops_before"] = sav.load(str(OUT / "B_TEST_BEFORE_CLICK.SAV"))["armies"][0]["troops"]
    g.click_tile(*aleria, pause=1.5)
    t["prompt"] = clickable_prompt(g)
    shot(g, "B_test_prompt.png")
    # answer No
    g.answer("Confirm", yes=False)
    time.sleep(1.0)
    t["after_no"] = {"relation": rel(g, GREECE), "selected": g.i16(SEL_ARMY), "army": g.army_pos(0),
                     "moves": struct.unpack_from("<h", g.army_rec(0), 6)[0], "popups": g.dismiss_popups()}
    keep(g, "B_TEST_AFTER_NO.SAV")
    # again, answer Yes
    if g.i16(SEL_ARMY) != 0:
        g.select_army(0, ax, ay)
    g.click_tile(*aleria, pause=1.5)
    t["prompt_second"] = clickable_prompt(g)
    g.answer("Confirm", yes=True)
    time.sleep(3.0)
    t["battle_or_siege"] = "battle" if g.in_battle() else "none"
    if g.in_battle():
        g.play_battle()
    t["after_yes"] = {"relation": rel(g, GREECE), "selected": g.i16(SEL_ARMY), "army": g.army_pos(0),
                      "moves": struct.unpack_from("<h", g.army_rec(0), 6)[0], "popups": g.dismiss_popups()}
    p = keep(g, "B_TEST_AFTER_YES.SAV")
    s = sav.load(str(p))
    t["after_yes"]["troops"] = s["armies"][0]["troops"]
    t["after_yes"]["news_tail"] = s["news"][-4:]
    t["after_yes"]["genua"] = next({k: c[k] for k in ("owner", "loyalty", "fort", "pop")} for c in s["cities"] if c["name"] == "Genua")
res["test_at_peace"] = t
Path(OUT / "b_attack_prompt.json").write_text(json.dumps(res, indent=1, default=str))
g.kill()

Path(OUT / "b_attack_prompt.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
