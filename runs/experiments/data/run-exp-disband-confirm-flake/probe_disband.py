import sys, time, subprocess
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from tests.test_orders import fresh
from harness.driver import ARMY_TOOLBAR_Y, DriverError, WINE, WORK, sh
g, _ = fresh("x")
ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
if not g.army_x: g.calibrate_army_toolbar()
g.click(g.army_x["disband"], ARMY_TOOLBAR_Y, pause=1.5)
for t in range(5):
    print(t, [(w[0], w[1], w[4], w[5]) for w in g.popups()])
    out = sh(WINE, str(WORK / "win_controls.exe"), "Confirm", check=False)
    print("  win_controls:", repr(out[:300]))
    time.sleep(0.8)
subprocess.run(["import", "-window", "root", sys.argv[1]], env={"DISPLAY": ":99"})
