"""Probe (#230 move-far): does the army stay selected when the unit map is scrolled by a click on the area map
WITHOUT the driver's reset_ui (Escape, Escape, neutral click)? If so, a far move is: select, scroll, click target.

    python3 -m difftest.probes.far_move OUT.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harness.driver import AREA_ORIGIN, G, SEL_ARMY, UNIT_PAINT, Game  # noqa: E402

out = Path(sys.argv[1])
if out.exists():
    raise SystemExit("refusing to overwrite " + str(out))
g = Game()
g.move_aside(sorted(G.glob("AUTO*")))
g.load(Path.home() / "ic2-work/fixtures/BASE.SAV", seed=12345)
rec = {"before": g.army_pos(0)}
x0, y0 = g.army_pos(0)
g.select_army(0, x0, y0)
rec["selected_after_select"] = g.i16(SEL_ARMY)
tx, ty = 90, 50
g.click(AREA_ORIGIN[0] + tx, AREA_ORIGIN[1] + ty, pause=0.8)      # scroll: no reset_ui
rec["selected_after_scroll"] = g.i16(SEL_ARMY)
ox, oy = g.view_origin()
rec["view_origin"] = [ox, oy]
c, r = tx - ox, ty - oy
rec["clicks"] = []
for k in range(2):      # the first click into the unit map may only re-activate it (the area map took the focus)
    g.click(UNIT_PAINT[0] + 32 * c + 16, UNIT_PAINT[1] + 30 + 32 * r + 16, pause=1.2)
    rec["clicks"].append({"pos": g.army_pos(0), "selected": g.i16(SEL_ARMY)})
    if g.army_pos(0) != (x0, y0):
        break
rec["texts"] = g.dismiss_popups()
rec["after"] = g.army_pos(0)
rec["moves_after"] = list(g.army_state(0).values())[:6] if isinstance(g.army_state(0), dict) else str(g.army_state(0))
out.write_text(json.dumps(rec, indent=1, default=str))
print(rec)
g.kill()
