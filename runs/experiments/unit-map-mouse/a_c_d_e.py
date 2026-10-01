#!/usr/bin/env python3
"""(a) click-to-move and selection, (c) left/right click on a unit, (d) Shift+X, (e) where Split army puts the new army."""
import json
import struct
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import BASE, OUT, ROME, SEL_ARMY, SEL_FLEET, fresh, keep, right_click, sh, shot  # noqa: E402
from state import sav  # noqa: E402

res = {}


def army(g, i):
    r = g.army_rec(i)
    x, y, owner, moves = struct.unpack_from("<4h", r, 0)
    return {"x": x, "y": y, "moves": moves}


def snap(g, i=0):
    return {"selected_army": g.i16(SEL_ARMY), "selected_fleet": g.i16(SEL_FLEET), "army": army(g, i),
            "windows": sorted({w[1] for w in g.popups()})}


# ---- (a) select, then click a reachable tile twice ----------------------------------------------------
g = fresh()
a = {"before": snap(g)}
ax, ay = g.army_pos(0)
g.click_tile(ax, ay)
a["after_select_click"] = snap(g)
shot(g, "A_1_selected.png")
steps = []
for target in [(101, 36), (102, 36), (103, 36), (104, 36)]:
    g.click_tile(*target, pause=1.2)
    tex = g.dismiss_popups()
    steps.append({"clicked": target, "popups": tex, **snap(g)})
    # No save between the clicks: File > Save sets the selected-army variable to -1, which would hide whether the
    # army is deselected by the move itself. The state is read from memory after each click; one save at the end.
    if steps[-1]["army"]["moves"] <= 0:
        break
keep(g, "A_AFTER_CLICKS.SAV")
a["clicks"] = steps
shot(g, "A_2_after_moves.png")
res["a"] = a
g.kill()

# ---- (c) left-click and right-click on a unit ---------------------------------------------------------
g = fresh()
c = {"before": snap(g)}
ax, ay = g.army_pos(0)
g.click_tile(ax, ay, pause=1.2)
c["left_click"] = snap(g)
shot(g, "C_1_left_click.png")
sx, sy = g.show(ax, ay)
right_click(g, sx, sy, pause=1.5)
c["right_click"] = snap(g)
c["right_click_windows"] = [(w[1], w[4], w[5]) for w in g.popups()]
shot(g, "C_2_right_click.png")
for w in g.popups():
    if w[1] not in ("Information",):
        try:
            c.setdefault("right_click_controls", {})[w[1]] = [(k["cls"], k["text"]) for k in g.controls(w[1])]
        except Exception as e:     # noqa: BLE001 - a popup without readable controls is a result, not a failure
            c.setdefault("right_click_controls", {})[w[1]] = "unreadable: %s" % e
res["c"] = c
keep(g, "C_AFTER_RIGHT_CLICK.SAV")
g.kill()

# ---- (d) Shift+X (Cancel selection) -------------------------------------------------------------------
g = fresh()
ax, ay = g.army_pos(0)
g.select_army(0, ax, ay)
dd = {"selected": snap(g)}
shot(g, "D_1_selected.png")
sh("xdotool", "key", "shift+x")
time.sleep(1.0)
dd["after_shift_x"] = snap(g)
shot(g, "D_2_after_shift_x.png")
res["d"] = dd
keep(g, "D_AFTER_SHIFT_X.SAV")
g.kill()

# ---- (e) Split army: where is the new army? -----------------------------------------------------------
g = fresh()
before = sav.load(str(BASE))
b = [(a["id"], a["x"], a["y"]) for a in sav.live_armies(before, ROME)]
g.split_army(0, unit_rows=(0,))
p = keep(g, "E_AFTER_SPLIT.SAV")
after = sav.load(str(p))
res["e"] = {"before_armies": b, "after_armies": [(a["id"], a["x"], a["y"], a["troops"]) for a in sav.live_armies(after, ROME)]}
g.kill()

Path(OUT / "a_c_d_e.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
