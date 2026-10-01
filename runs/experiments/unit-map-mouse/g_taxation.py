#!/usr/bin/env python3
"""(g) The Taxation dialog's range and step. Measures the slider itself, then commits min and max."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *   # noqa: F401,F403

TAX = 0x44A
res = {"question": "g", "start_tax": None, "keys": [], "commit": []}
g = fresh()
res["start_tax"] = nation_i16(g, ROME, TAX)


def open_tax():
    g.tool("taxation")
    g.wait(lambda: g.find_windows("^Change tax level$"), 10, "Change tax level")
    g.raise_window(g.find_windows("^Change tax level$")[0][0])
    cs = g.controls("Change tax level")
    tb = g.control(cs, cls="TTrackBar")
    g.click(tb["x"] + tb["w"] // 2, tb["y"] + tb["h"] // 2, pause=0.5)      # focus the slider
    return cs


cs = open_tax()
res["controls"] = [{k: c[k] for k in ("cls", "text")} for c in cs]
res["slider_at_open"] = sliders("Change tax level")
win = str(g.find_windows("^Change tax level$")[0][0])
shot(g, "tax_open.png", window=win)
for label, keys in [("Home", ["Home"]), ("Right x1", ["Right"]), ("Right x2", ["Right"]), ("End", ["End"]),
                    ("Left x1", ["Left"]), ("Page_Down", ["Next"]), ("Page_Up", ["Prior"]), ("Home again", ["Home"]),
                    ("Page_Up from Home", ["Prior"]), ("End again", ["End"]), ("Right past End", ["Right"])]:
    sh("xdotool", "key", *keys)
    time.sleep(0.4)
    row = {"keys": label, "slider": sliders("Change tax level")}
    res["keys"].append(row)
    if label in ("Home", "End"):
        shot(g, "tax_%s.png" % label.replace(" ", "_").lower(), window=win)
g.click_control(g.control(cs, text="Cancel"), pause=1.0)
g.wait(lambda: not g.find_windows("^Change tax level$"), 15, "tax dialog closed")
Path(OUT / "g_taxation.json").write_text(json.dumps(res, indent=1))

for label, key in (("min", "Home"), ("max", "End")):
    cs = open_tax()
    sh("xdotool", "key", key)
    time.sleep(0.5)
    sl = sliders("Change tax level")
    g.click_control(g.control(cs, text="OK"), pause=1.5)
    g.dismiss_popups()
    g.wait(lambda: not g.find_windows("^Change tax level$"), 15, "tax dialog closed")
    row = {"commit": label, "slider_before_ok": sl, "nation_0x44A_after_ok": nation_i16(g, ROME, TAX)}
    row["save"] = keep(g, "G_TAX_%s.SAV" % label.upper()).name
    res["commit"].append(row)

Path(OUT / "g_taxation.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
g.kill()
