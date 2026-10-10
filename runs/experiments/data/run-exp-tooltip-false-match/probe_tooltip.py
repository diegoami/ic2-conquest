"""Tooltip vs dialog title (2026-10-08): hover the army toolbar's Split army and the fleet toolbar's Split fleet
buttons; list windows with and without tooltips; then recalibrate the army and fleet toolbars from scratch and compare
with the cached x. python3 probe_tooltip.py"""
import json, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh, fresh_save
from harness.driver import ARMY_TOOLBAR_Y, sh, ARMY_TOOLBAR_CACHE, FLEET_TOOLBAR_CACHE
from pathlib import Path
g, _ = fresh("tooltip")
ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
cached = json.loads(ARMY_TOOLBAR_CACHE.read_text())
sh("xdotool", "mousemove", str(cached["split"]), str(ARMY_TOOLBAR_Y)); time.sleep(1.2)
print("hover Split army: default", [(w[1], w[4], w[5]) for w in g.find_windows("^Split army$")],
      "| tooltips=True", [(w[1], w[4], w[5]) for w in g.find_windows("^Split army$", tooltips=True)])
fresh_army = g.calibrate_army_toolbar(force=True)
print("army toolbar: cached", cached, "| recalibrated", fresh_army, "| same", cached == fresh_army)
g2 = fresh_save((Path(__file__).resolve().parents[4] / "saves/fleet-split-antium-0734.SAV"))
g2.select_fleet(2)
fc = json.loads(FLEET_TOOLBAR_CACHE.read_text())
sh("xdotool", "mousemove", str(fc["split"]), str(ARMY_TOOLBAR_Y)); time.sleep(1.2)
print("hover Split fleet: default", [(w[1], w[4], w[5]) for w in g2.find_windows("^Split fleet$")],
      "| tooltips=True", [(w[1], w[4], w[5]) for w in g2.find_windows("^Split fleet$", tooltips=True)])
fresh_fleet = g2.calibrate_fleet_toolbar(force=True)
print("fleet toolbar: cached", fc, "| recalibrated", fresh_fleet, "| same", fc == fresh_fleet)
