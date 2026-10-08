"""List-box row geometry per dialog, read by win_controls (LB_GETITEMHEIGHT, LB_GETTOPINDEX, ClientToScreen), 2026-10-08.
Old assumption: row r centre at control y + 12 + 12 r. python3 probe_rows.py"""
import sys
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from tests.test_orders import fresh
from harness.driver import ARMY_TOOLBAR_Y

def show(g, title):
    for c in g.controls(title):
        if "item_h" in c:
            old = [c["y"] + 12 + 12 * r for r in range(3)]
            new = [c["cy"] + (r - c["top"]) * c["item_h"] + c["item_h"] // 2 for r in range(3)]
            print(f"{title}: {c['cls']} at ({c['x']},{c['y']}) {c['w']}x{c['h']} item_h={c['item_h']} top={c['top']} client=({c['cx']},{c['cy']}) "
                  f"row centres old {old} new {new}", flush=True)

g, _ = fresh("rows")
g.open_recruit(); show(g, "Army recruits"); g.close_controls("Army recruits", g.controls("Army recruits"))
ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
if not g.army_x: g.calibrate_army_toolbar()
g.open_dialog("Change units", (g.army_x["change"], ARMY_TOOLBAR_Y)); show(g, "Change units")
g.click_control(g.control(g.controls("Change units"), text="Cancel"), pause=1.2)
g2, _ = fresh("rows2")
ax, ay = g2.army_pos(0); g2.select_army(0, ax, ay)
if not g2.army_x: g2.calibrate_army_toolbar()
g2.open_dialog("Split army", (g2.army_x["split"], ARMY_TOOLBAR_Y)); show(g2, "Split army")
